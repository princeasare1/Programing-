from sqlalchemy import Column, DateTime, Integer, String, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime
import uuid


Base = declarative_base()


class BaseModel(Base):
    """Base model class with common fields for all tables"""
    __abstract__ = True
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    uuid = Column(String(36), default=lambda: str(uuid.uuid4()), unique=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String(100), nullable=True)
    updated_by = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True)
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    version = Column(Integer, default=1)
    
    def soft_delete(self):
        """Soft delete the record"""
        self.is_deleted = True
        self.deleted_at = datetime.utcnow()
        self.is_active = False
    
    def restore(self):
        """Restore a soft-deleted record"""
        self.is_deleted = False
        self.deleted_at = None
        self.is_active = True


class AuditModel(Base):
    """Audit trail model for tracking changes"""
    __abstract__ = True
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(Integer, nullable=False)
    action = Column(String(20), nullable=False)  # CREATE, UPDATE, DELETE, VIEW
    old_values = Column(Text, nullable=True)
    new_values = Column(Text, nullable=True)
    user_id = Column(Integer, nullable=True)
    user_role = Column(String(50), nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    session_id = Column(String(100), nullable=True)
    reason = Column(String(200), nullable=True)
    
    @classmethod
    def log_action(cls, entity_type: str, entity_id: int, action: str, 
                   old_values: str = None, new_values: str = None,
                   user_id: int = None, user_role: str = None,
                   ip_address: str = None, user_agent: str = None,
                   session_id: str = None, reason: str = None):
        """Create an audit log entry"""
        return cls(
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            old_values=old_values,
            new_values=new_values,
            user_id=user_id,
            user_role=user_role,
            ip_address=ip_address,
            user_agent=user_agent,
            session_id=session_id,
            reason=reason
        )