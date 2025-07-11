from datetime import datetime, timedelta
from typing import Optional, Union
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from jose import JWTError, jwt
from passlib.context import CryptContext
from passlib.hash import bcrypt
import pyotp
import secrets
import logging

from ..core.config import settings
from ..database import get_db
from ..models.user import User, UserSession, Role
from ..models.base import AuditModel

logger = logging.getLogger(__name__)

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Security scheme
security = HTTPBearer()


class SecurityManager:
    """Security manager for authentication and authorization"""
    
    def __init__(self):
        self.secret_key = settings.SECRET_KEY
        self.algorithm = settings.ALGORITHM
        self.access_token_expire_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES
        self.refresh_token_expire_minutes = settings.REFRESH_TOKEN_EXPIRE_MINUTES
    
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None):
        """Create JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        
        to_encode.update({"exp": expire, "type": "access"})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def create_refresh_token(self, data: dict, expires_delta: Optional[timedelta] = None):
        """Create JWT refresh token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.refresh_token_expire_minutes)
        
        to_encode.update({"exp": expire, "type": "refresh"})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def verify_token(self, token: str) -> dict:
        """Verify JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except JWTError as e:
            logger.error(f"JWT verification failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    def hash_password(self, password: str) -> str:
        """Hash password"""
        return pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password"""
        return pwd_context.verify(plain_password, hashed_password)
    
    def generate_2fa_secret(self) -> str:
        """Generate 2FA secret"""
        return pyotp.random_base32()
    
    def verify_2fa_token(self, secret: str, token: str) -> bool:
        """Verify 2FA token"""
        totp = pyotp.TOTP(secret)
        return totp.verify(token, valid_window=1)
    
    def generate_session_token(self) -> str:
        """Generate secure session token"""
        return secrets.token_urlsafe(32)


# Global security manager instance
security_manager = SecurityManager()


# Authentication functions
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create access token"""
    return security_manager.create_access_token(data, expires_delta)


def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create refresh token"""
    return security_manager.create_refresh_token(data, expires_delta)


def verify_token(token: str) -> dict:
    """Verify token"""
    return security_manager.verify_token(token)


def hash_password(password: str) -> str:
    """Hash password"""
    return security_manager.hash_password(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password"""
    return security_manager.verify_password(plain_password, hashed_password)


async def authenticate_user(
    db: AsyncSession,
    username: str,
    password: str,
    two_factor_token: Optional[str] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
) -> Optional[User]:
    """Authenticate user with credentials"""
    try:
        # Get user by username or email
        stmt = select(User).where(
            (User.username == username) | (User.email == username)
        ).join(Role)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user:
            logger.warning(f"Authentication failed: User not found - {username}")
            return None
        
        # Check if account is locked
        if user.is_locked():
            logger.warning(f"Authentication failed: Account locked - {username}")
            return None
        
        # Verify password
        if not verify_password(password, user.password_hash):
            # Increment failed login attempts
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= 5:
                user.lock_account()
                logger.warning(f"Account locked due to failed attempts - {username}")
            
            await db.commit()
            logger.warning(f"Authentication failed: Invalid password - {username}")
            return None
        
        # Check 2FA if enabled
        if user.is_two_factor_enabled:
            if not two_factor_token:
                logger.warning(f"Authentication failed: 2FA token required - {username}")
                return None
            
            if not security_manager.verify_2fa_token(user.two_factor_secret, two_factor_token):
                logger.warning(f"Authentication failed: Invalid 2FA token - {username}")
                return None
        
        # Reset failed attempts on successful login
        user.failed_login_attempts = 0
        user.last_login = datetime.utcnow()
        
        # Log successful authentication
        await log_audit_event(
            db, "LOGIN", "users", user.id, user.id,
            ip_address=ip_address, user_agent=user_agent
        )
        
        await db.commit()
        logger.info(f"Authentication successful - {username}")
        return user
        
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        await db.rollback()
        return None


async def get_current_user(
    user_id: int,
    db: AsyncSession = Depends(get_db)
) -> User:
    """Get current user from token"""
    try:
        stmt = select(User).where(User.id == user_id).join(Role)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Inactive user"
            )
        
        return user
        
    except Exception as e:
        logger.error(f"Get current user error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not retrieve user"
        )


async def create_user_session(
    db: AsyncSession,
    user: User,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
) -> UserSession:
    """Create user session"""
    try:
        session_token = security_manager.generate_session_token()
        expires_at = datetime.utcnow() + timedelta(minutes=settings.SESSION_TIMEOUT_MINUTES)
        
        session = UserSession(
            user_id=user.id,
            session_token=session_token,
            ip_address=ip_address,
            user_agent=user_agent,
            expires_at=expires_at
        )
        
        db.add(session)
        await db.commit()
        
        logger.info(f"Session created for user {user.username}")
        return session
        
    except Exception as e:
        logger.error(f"Session creation error: {e}")
        await db.rollback()
        raise


async def revoke_user_session(
    db: AsyncSession,
    session_token: str
) -> bool:
    """Revoke user session"""
    try:
        stmt = select(UserSession).where(UserSession.session_token == session_token)
        result = await db.execute(stmt)
        session = result.scalar_one_or_none()
        
        if session:
            session.is_active = False
            await db.commit()
            logger.info(f"Session revoked: {session_token}")
            return True
        
        return False
        
    except Exception as e:
        logger.error(f"Session revocation error: {e}")
        await db.rollback()
        return False


async def check_permission(
    user: User,
    permission: str,
    resource_id: Optional[int] = None
) -> bool:
    """Check if user has permission"""
    try:
        # Check role permissions
        if user.role and user.role.permissions:
            if permission in user.role.permissions:
                return True
        
        # Additional resource-specific checks can be added here
        
        return False
        
    except Exception as e:
        logger.error(f"Permission check error: {e}")
        return False


async def log_audit_event(
    db: AsyncSession,
    action: str,
    entity_type: str,
    entity_id: int,
    user_id: Optional[int] = None,
    old_values: Optional[str] = None,
    new_values: Optional[str] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    session_id: Optional[str] = None,
    reason: Optional[str] = None
):
    """Log audit event"""
    try:
        audit_log = AuditModel.log_action(
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            old_values=old_values,
            new_values=new_values,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            session_id=session_id,
            reason=reason
        )
        
        db.add(audit_log)
        # Note: Commit is handled by the calling function
        
    except Exception as e:
        logger.error(f"Audit logging error: {e}")


# Permission decorators
def require_permission(permission: str):
    """Decorator to require specific permission"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Extract user from kwargs or dependencies
            user = kwargs.get('current_user')
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            if not await check_permission(user, permission):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def require_role(role_name: str):
    """Decorator to require specific role"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            user = kwargs.get('current_user')
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            if not user.role or user.role.name != role_name:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


# Dependency for getting current user
async def get_current_active_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Get current active user dependency"""
    try:
        payload = verify_token(credentials.credentials)
        user_id = payload.get("sub")
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        
        user = await get_current_user(int(user_id), db)
        return user
        
    except Exception as e:
        logger.error(f"Authentication dependency error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )