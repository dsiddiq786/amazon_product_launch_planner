from sqlalchemy import Boolean, Column, String, DateTime, ForeignKey, Integer, Text
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime

from app.database.postgresql import Base


class Project(Base):
    """SQLAlchemy model for project data"""
    __tablename__ = "projects"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, index=True, nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String, nullable=True)
    subcategory = Column(String, nullable=True)
    owner_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    owner = relationship("User", back_populates="projects")
    
    def __repr__(self):
        return f"<Project {self.name}>" 