from datetime import timedelta
from typing import Any
from fastapi import APIRouter, Body, Depends, HTTPException, status, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
import uuid

from app.schemas.auth import Token, Login, EmailRequest, PasswordReset
from app.schemas.user import User, UserCreate, UserWithToken
from app.models.user import User as UserModel, UserStatus
from app.database.postgresql import get_db
from app.utils.security import (
    verify_password, get_password_hash, create_access_token,
    get_current_user
)
from app.utils.email import send_verification_email, send_reset_password_email
from app.config.settings import settings

router = APIRouter(
    prefix="/auth",
    tags=["authentication"],
    responses={404: {"description": "Not found"}},
)


@router.post("/login", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
) -> Any:
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    user = db.query(UserModel).filter(UserModel.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if user.status == UserStatus.INACTIVE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user account"
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=user.id, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


@router.post("/login/json", response_model=UserWithToken)
async def login_json(
    login_data: Login,
    db: Session = Depends(get_db)
) -> Any:
    """
    JSON login endpoint, returns user data with token
    """
    user = db.query(UserModel).filter(UserModel.email == login_data.email).first()
    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    
    if user.status == UserStatus.INACTIVE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user account"
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=user.id, expires_delta=access_token_expires
    )
    
    return {
        **user.__dict__,
        "access_token": access_token,
        "token_type": "bearer"
    }


@router.post("/register", response_model=User)
async def register(
    user_data: UserCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
) -> Any:
    """
    Register a new user
    """
    existing_user = db.query(UserModel).filter(UserModel.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    new_user = UserModel(
        id=str(uuid.uuid4()),
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password),
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        # Set status based on email verification setting
        status=UserStatus.ACTIVE if not settings.EMAIL_VERIFICATION_ENABLED else UserStatus.PENDING,
        is_email_verified=not settings.EMAIL_VERIFICATION_ENABLED,
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Only send verification email if email verification is enabled
    if settings.EMAIL_VERIFICATION_ENABLED:
        # Generate verification token and send email
        token = create_access_token(
            subject=f"verify:{new_user.id}",
            expires_delta=timedelta(hours=48)
        )
        
        # Send email in the background
        background_tasks.add_task(send_verification_email, new_user.email, token)
    
    return new_user


@router.post("/verify-email")
async def verify_email(
    token: str = Body(..., embed=True),
    db: Session = Depends(get_db)
) -> Any:
    """
    Verify user email with token
    """
    try:
        from jose import jwt
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        token_data = payload["sub"]
        
        if not token_data.startswith("verify:"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid verification token"
            )
        
        user_id = token_data.split(":", 1)[1]
        user = db.query(UserModel).filter(UserModel.id == user_id).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Update user to verified status
        user.is_email_verified = True
        user.status = UserStatus.ACTIVE
        db.commit()
        
        return {"message": "Email verified successfully"}
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid token: {str(e)}"
        )


@router.post("/forgot-password")
async def forgot_password(
    email_request: EmailRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
) -> Any:
    """
    Send a password reset email
    """
    # Don't reveal if user exists or not
    if not settings.EMAIL_VERIFICATION_ENABLED:
        return {"message": "Email verification is currently disabled. Please contact an administrator for assistance."}
    
    user = db.query(UserModel).filter(UserModel.email == email_request.email).first()
    if not user:
        # Don't reveal that the user doesn't exist
        return {"message": "Password reset email sent if account exists"}
    
    # Generate reset token
    token = create_access_token(
        subject=f"reset:{user.id}",
        expires_delta=timedelta(hours=1)
    )
    
    # Send email in the background
    background_tasks.add_task(send_reset_password_email, user.email, token)
    
    return {"message": "Password reset email sent if account exists"}


@router.post("/reset-password")
async def reset_password(
    password_reset: PasswordReset,
    db: Session = Depends(get_db)
) -> Any:
    """
    Reset user password with token
    """
    try:
        from jose import jwt
        payload = jwt.decode(
            password_reset.token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        token_data = payload["sub"]
        
        if not token_data.startswith("reset:"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid reset token"
            )
        
        user_id = token_data.split(":", 1)[1]
        user = db.query(UserModel).filter(UserModel.id == user_id).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Update password
        user.hashed_password = get_password_hash(password_reset.new_password)
        db.commit()
        
        return {"message": "Password reset successful"}
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid token: {str(e)}"
        )


@router.get("/me", response_model=User)
async def get_current_user_info(
    current_user: UserModel = Depends(get_current_user)
) -> Any:
    """
    Get current user information
    """
    return current_user 