from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
from app.models.user import UserRole, UserStatus


class UserBase(BaseModel):
    """Base schema for user data"""
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class UserCreate(UserBase):
    """Schema for creating a new user"""
    password: str = Field(..., min_length=8)


class UserUpdate(BaseModel):
    """Schema for updating user data"""
    email: Optional[EmailStr] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    is_email_verified: Optional[bool] = None
    status: Optional[UserStatus] = None
    role: Optional[UserRole] = None
    scrape_quota: Optional[int] = None
    
    model_config = ConfigDict(
        extra="forbid"
    )


class UserPasswordUpdate(BaseModel):
    """Schema for updating user password"""
    current_password: str
    new_password: str = Field(..., min_length=8)


class UserInDB(UserBase):
    """Schema for user data stored in DB"""
    id: str
    role: UserRole
    status: UserStatus
    is_email_verified: bool
    created_at: datetime
    updated_at: datetime
    scrape_quota: int
    
    model_config = ConfigDict(
        from_attributes=True
    )


class User(UserInDB):
    """Schema for user data returned from API"""
    pass


class UserWithToken(User):
    """Schema for user data with access token"""
    access_token: str
    token_type: str = "bearer" 