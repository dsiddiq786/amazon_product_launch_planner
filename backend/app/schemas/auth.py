from pydantic import BaseModel, EmailStr, Field


class Token(BaseModel):
    """Schema for authentication token"""
    access_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """Schema for token payload (data encoded in JWT)"""
    sub: str  # User ID
    exp: int  # Expiration time (Unix timestamp)


class Login(BaseModel):
    """Schema for login credentials"""
    email: EmailStr
    password: str = Field(..., min_length=8)


class EmailRequest(BaseModel):
    """Schema for requests related to email operations"""
    email: EmailStr


class PasswordReset(BaseModel):
    """Schema for password reset"""
    token: str  # Password reset token
    new_password: str = Field(..., min_length=8) 