from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import BaseModel, AuditModel
from datetime import datetime, timedelta


class Role(BaseModel):
    """Role model for RBAC system"""
    __tablename__ = "roles"
    
    name = Column(String(50), unique=True, nullable=False)
    description = Column(String(200), nullable=True)
    permissions = Column(JSON, nullable=False, default=list)
    is_system_role = Column(Boolean, default=False)
    
    # Relationships
    users = relationship("User", back_populates="role")
    
    def __repr__(self):
        return f"<Role {self.name}>"


class User(BaseModel):
    """User model for healthcare professionals and staff"""
    __tablename__ = "users"
    
    # Authentication
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    
    # Profile Information
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    middle_name = Column(String(50), nullable=True)
    title = Column(String(20), nullable=True)  # Dr., Nurse, etc.
    
    # Contact Information
    phone = Column(String(20), nullable=True)
    mobile = Column(String(20), nullable=True)
    address = Column(String(200), nullable=True)
    
    # Professional Information
    license_number = Column(String(50), nullable=True)
    npi_number = Column(String(20), nullable=True)  # National Provider Identifier
    dea_number = Column(String(20), nullable=True)  # Drug Enforcement Administration
    specialty = Column(String(100), nullable=True)
    department = Column(String(100), nullable=True)
    
    # Role and Permissions
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)
    
    # Security
    is_two_factor_enabled = Column(Boolean, default=False)
    two_factor_secret = Column(String(100), nullable=True)
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime(timezone=True), nullable=True)
    last_login = Column(DateTime(timezone=True), nullable=True)
    password_changed_at = Column(DateTime(timezone=True), default=func.now())
    must_change_password = Column(Boolean, default=False)
    
    # Session Management
    active_sessions = Column(JSON, default=list)
    
    # Relationships
    role = relationship("Role", back_populates="users")
    created_patients = relationship("Patient", back_populates="created_by_user")
    appointments = relationship("Appointment", back_populates="provider")
    clinical_notes = relationship("ClinicalNote", back_populates="provider")
    prescriptions = relationship("Prescription", back_populates="prescriber")
    lab_orders = relationship("LabOrder", back_populates="ordering_provider")
    
    @property
    def full_name(self):
        """Get full name with title"""
        name_parts = [self.first_name]
        if self.middle_name:
            name_parts.append(self.middle_name)
        name_parts.append(self.last_name)
        full_name = " ".join(name_parts)
        
        if self.title:
            return f"{self.title} {full_name}"
        return full_name
    
    def has_permission(self, permission: str) -> bool:
        """Check if user has specific permission"""
        return permission in (self.role.permissions or [])
    
    def can_access_patient(self, patient_id: int) -> bool:
        """Check if user can access specific patient"""
        # Implementation depends on business rules
        return True  # Placeholder
    
    def is_locked(self) -> bool:
        """Check if user account is locked"""
        return self.locked_until and self.locked_until > datetime.utcnow()
    
    def lock_account(self, duration_minutes: int = 30):
        """Lock user account for specified duration"""
        self.locked_until = datetime.utcnow() + timedelta(minutes=duration_minutes)
        self.failed_login_attempts = 0
    
    def unlock_account(self):
        """Unlock user account"""
        self.locked_until = None
        self.failed_login_attempts = 0
    
    def __repr__(self):
        return f"<User {self.username}>"


class UserSession(BaseModel):
    """Track user sessions for security"""
    __tablename__ = "user_sessions"
    
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    session_token = Column(String(255), unique=True, nullable=False)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    last_activity = Column(DateTime(timezone=True), default=func.now())
    
    # Relationships
    user = relationship("User")
    
    def is_expired(self) -> bool:
        """Check if session is expired"""
        return self.expires_at < datetime.utcnow()
    
    def is_valid(self) -> bool:
        """Check if session is valid"""
        return self.is_active and not self.is_expired()


class PasswordHistory(BaseModel):
    """Track password history for compliance"""
    __tablename__ = "password_history"
    
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), default=func.now())
    
    # Relationships
    user = relationship("User")


class AuditLog(AuditModel):
    """Audit log table for tracking all system actions"""
    __tablename__ = "audit_logs"