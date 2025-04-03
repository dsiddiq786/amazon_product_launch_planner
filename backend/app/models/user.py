from sqlalchemy import Boolean, Column, String, DateTime, ForeignKey, Integer, Enum as SQLAlchemyEnum
from sqlalchemy.orm import relationship
import uuid
import enum
from datetime import datetime

from app.database.postgresql import Base


class UserRole(str, enum.Enum):
    """User roles in the system"""
    ADMIN = "admin"
    USER = "user"


class UserStatus(str, enum.Enum):
    """User status in the system"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"  # For users who haven't confirmed their email yet


class User(Base):
    """SQLAlchemy model for user data"""
    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    first_name = Column(String)
    last_name = Column(String)
    role = Column(SQLAlchemyEnum(UserRole), default=UserRole.USER)
    status = Column(SQLAlchemyEnum(UserStatus), default=UserStatus.PENDING)
    is_email_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    scrape_quota = Column(Integer, default=10)  # Default quota of scrapes allowed

    # Relationships
    projects = relationship("Project", back_populates="owner", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User {self.email}>" 