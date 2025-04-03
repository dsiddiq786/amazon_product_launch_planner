from sqlalchemy import Boolean, Column, String, DateTime, ForeignKey, Integer, Text, Float
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime

from app.database.postgresql import Base


class Plan(Base):
    """SQLAlchemy model for subscription plans"""
    __tablename__ = "plans"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)
    price = Column(Float, nullable=False, default=0.0)
    scrape_quota = Column(Integer, nullable=False, default=10)
    is_active = Column(Boolean, default=True)
    features = Column(String, nullable=True)  # Comma-separated list of features
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    subscriptions = relationship("Subscription", back_populates="plan", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Plan {self.name}>"
        

class Subscription(Base):
    """SQLAlchemy model for user subscriptions"""
    __tablename__ = "subscriptions"
    
    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    plan_id = Column(String, ForeignKey("plans.id", ondelete="CASCADE"), nullable=False)
    start_date = Column(DateTime, default=datetime.utcnow)
    end_date = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    plan = relationship("Plan", back_populates="subscriptions")
    
    def __repr__(self):
        return f"<Subscription {self.id}>" 