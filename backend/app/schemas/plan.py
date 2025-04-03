from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime


class PlanBase(BaseModel):
    """Base schema for plan data"""
    name: str
    description: Optional[str] = None
    price: float = 0.0
    scrape_quota: int = 10
    features: Optional[str] = None


class PlanCreate(PlanBase):
    """Schema for creating a new plan"""
    pass


class PlanUpdate(BaseModel):
    """Schema for updating plan data"""
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    scrape_quota: Optional[int] = None
    features: Optional[str] = None
    is_active: Optional[bool] = None
    
    model_config = ConfigDict(
        extra="forbid"
    )


class PlanInDB(PlanBase):
    """Schema for plan data stored in DB"""
    id: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(
        from_attributes=True
    )


class Plan(PlanInDB):
    """Schema for plan data returned from API"""
    pass


class PlanList(BaseModel):
    """Schema for a list of plans"""
    plans: List[Plan]
    count: int


class SubscriptionBase(BaseModel):
    """Base schema for subscription data"""
    plan_id: str
    user_id: str
    end_date: Optional[datetime] = None


class SubscriptionCreate(BaseModel):
    """Schema for creating a new subscription"""
    plan_id: str
    user_id: str
    end_date: Optional[datetime] = None


class SubscriptionUpdate(BaseModel):
    """Schema for updating subscription data"""
    plan_id: Optional[str] = None
    end_date: Optional[datetime] = None
    is_active: Optional[bool] = None
    
    model_config = ConfigDict(
        extra="forbid"
    )


class SubscriptionInDB(SubscriptionBase):
    """Schema for subscription data stored in DB"""
    id: str
    start_date: datetime
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(
        from_attributes=True
    )


class Subscription(SubscriptionInDB):
    """Schema for subscription data returned from API"""
    pass


class SubscriptionWithPlan(Subscription):
    """Schema for subscription data with plan details"""
    plan: Plan


class SubscriptionList(BaseModel):
    """Schema for a list of subscriptions"""
    subscriptions: List[Subscription]
    count: int 