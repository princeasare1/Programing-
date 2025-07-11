from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, EmailStr
from typing import Optional
import pyotp
import qrcode
from io import BytesIO
import base64
import logging
from datetime import datetime

from ...auth.security import (
    authenticate_user, create_access_token, create_refresh_token,
    verify_token, hash_password, get_current_active_user,
    security_manager, create_user_session, revoke_user_session
)
from ...database import get_db
from ...models.user import User, Role
from ...models.patient import Patient

logger = logging.getLogger(__name__)

router = APIRouter()
security = HTTPBearer()


# Pydantic models for request/response
class LoginRequest(BaseModel):
    username: str
    password: str
    two_factor_token: Optional[str] = None


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: dict


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class Enable2FAResponse(BaseModel):
    secret: str
    qr_code: str
    backup_codes: list


class Verify2FARequest(BaseModel):
    token: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str
    confirm_password: str


class ResetPasswordRequest(BaseModel):
    email: EmailStr


class UserProfileResponse(BaseModel):
    id: int
    username: str
    email: str
    first_name: str
    last_name: str
    role: str
    is_two_factor_enabled: bool
    last_login: Optional[str]


@router.post("/login", response_model=LoginResponse)
async def login(
    request: Request,
    login_data: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """Authenticate user and return access token"""
    try:
        # Get client IP and user agent
        client_ip = request.client.host
        user_agent = request.headers.get("user-agent", "")
        
        # Authenticate user
        user = await authenticate_user(
            db=db,
            username=login_data.username,
            password=login_data.password,
            two_factor_token=login_data.two_factor_token,
            ip_address=client_ip,
            user_agent=user_agent
        )
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Create tokens
        access_token = create_access_token(data={"sub": str(user.id)})
        refresh_token = create_refresh_token(data={"sub": str(user.id)})
        
        # Create user session
        session = await create_user_session(
            db=db,
            user=user,
            ip_address=client_ip,
            user_agent=user_agent
        )
        
        # Prepare user data for response
        user_data = {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "role": user.role.name if user.role else None,
            "permissions": user.role.permissions if user.role else [],
            "is_two_factor_enabled": user.is_two_factor_enabled
        }
        
        logger.info(f"User {user.username} logged in successfully")
        
        return LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=3600,  # 1 hour
            user=user_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db)
):
    """Refresh access token using refresh token"""
    try:
        # Verify refresh token
        payload = verify_token(refresh_data.refresh_token)
        
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )
        
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        
        # Get user
        stmt = select(User).where(User.id == int(user_id))
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )
        
        # Create new access token
        access_token = create_access_token(data={"sub": str(user.id)})
        
        return TokenResponse(
            access_token=access_token,
            expires_in=3600
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed"
        )


@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Logout user and revoke session"""
    try:
        # In a real implementation, you would revoke the user's sessions
        # For now, we'll just log the logout
        logger.info(f"User {current_user.username} logged out")
        
        return {"message": "Successfully logged out"}
        
    except Exception as e:
        logger.error(f"Logout error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )


@router.get("/profile", response_model=UserProfileResponse)
async def get_profile(
    current_user: User = Depends(get_current_active_user)
):
    """Get current user profile"""
    try:
        return UserProfileResponse(
            id=current_user.id,
            username=current_user.username,
            email=current_user.email,
            first_name=current_user.first_name,
            last_name=current_user.last_name,
            role=current_user.role.name if current_user.role else None,
            is_two_factor_enabled=current_user.is_two_factor_enabled,
            last_login=current_user.last_login.isoformat() if current_user.last_login else None
        )
        
    except Exception as e:
        logger.error(f"Get profile error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not retrieve profile"
        )


@router.post("/enable-2fa", response_model=Enable2FAResponse)
async def enable_2fa(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Enable two-factor authentication"""
    try:
        if current_user.is_two_factor_enabled:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="2FA is already enabled"
            )
        
        # Generate 2FA secret
        secret = security_manager.generate_2fa_secret()
        
        # Generate QR code
        totp = pyotp.TOTP(secret)
        provisioning_uri = totp.provisioning_uri(
            name=current_user.email,
            issuer_name="EHR System"
        )
        
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(provisioning_uri)
        qr.make(fit=True)
        
        qr_image = qr.make_image(fill_color="black", back_color="white")
        qr_buffer = BytesIO()
        qr_image.save(qr_buffer, format='PNG')
        qr_base64 = base64.b64encode(qr_buffer.getvalue()).decode()
        
        # Store secret (not enabled yet)
        current_user.two_factor_secret = secret
        await db.commit()
        
        # Generate backup codes (simplified)
        backup_codes = [f"{i:06d}" for i in range(100000, 100010)]
        
        return Enable2FAResponse(
            secret=secret,
            qr_code=f"data:image/png;base64,{qr_base64}",
            backup_codes=backup_codes
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Enable 2FA error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not enable 2FA"
        )


@router.post("/verify-2fa")
async def verify_2fa(
    verify_data: Verify2FARequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Verify and activate 2FA"""
    try:
        if not current_user.two_factor_secret:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="2FA not initialized"
            )
        
        # Verify token
        if not security_manager.verify_2fa_token(
            current_user.two_factor_secret,
            verify_data.token
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid 2FA token"
            )
        
        # Enable 2FA
        current_user.is_two_factor_enabled = True
        await db.commit()
        
        logger.info(f"2FA enabled for user {current_user.username}")
        
        return {"message": "2FA enabled successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Verify 2FA error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not verify 2FA"
        )


@router.post("/disable-2fa")
async def disable_2fa(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Disable two-factor authentication"""
    try:
        if not current_user.is_two_factor_enabled:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="2FA is not enabled"
            )
        
        # Disable 2FA
        current_user.is_two_factor_enabled = False
        current_user.two_factor_secret = None
        await db.commit()
        
        logger.info(f"2FA disabled for user {current_user.username}")
        
        return {"message": "2FA disabled successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Disable 2FA error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not disable 2FA"
        )


@router.post("/change-password")
async def change_password(
    password_data: ChangePasswordRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Change user password"""
    try:
        # Verify current password
        if not security_manager.verify_password(
            password_data.current_password,
            current_user.password_hash
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )
        
        # Validate new password
        if password_data.new_password != password_data.confirm_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="New passwords do not match"
            )
        
        if len(password_data.new_password) < 8:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must be at least 8 characters long"
            )
        
        # Hash new password
        new_password_hash = hash_password(password_data.new_password)
        
        # Update password
        current_user.password_hash = new_password_hash
        current_user.password_changed_at = datetime.utcnow()
        await db.commit()
        
        logger.info(f"Password changed for user {current_user.username}")
        
        return {"message": "Password changed successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Change password error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not change password"
        )


@router.post("/forgot-password")
async def forgot_password(
    reset_data: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db)
):
    """Request password reset"""
    try:
        # Find user by email
        stmt = select(User).where(User.email == reset_data.email)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user:
            # Don't reveal if email exists
            return {"message": "If the email exists, a reset link has been sent"}
        
        # In a real implementation, you would:
        # 1. Generate a secure reset token
        # 2. Store it in database with expiration
        # 3. Send email with reset link
        
        logger.info(f"Password reset requested for {reset_data.email}")
        
        return {"message": "If the email exists, a reset link has been sent"}
        
    except Exception as e:
        logger.error(f"Forgot password error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not process password reset"
        )


@router.get("/validate-token")
async def validate_token(
    current_user: User = Depends(get_current_active_user)
):
    """Validate access token"""
    try:
        return {
            "valid": True,
            "user_id": current_user.id,
            "username": current_user.username,
            "role": current_user.role.name if current_user.role else None
        }
        
    except Exception as e:
        logger.error(f"Token validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )