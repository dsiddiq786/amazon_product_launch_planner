from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Body
from sqlalchemy.orm import Session
import uuid

from app.schemas.user import User, UserCreate, UserUpdate, UserPasswordUpdate
from app.models.user import User as UserModel, UserRole, UserStatus
from app.database.postgresql import get_db
from app.utils.security import (
    get_password_hash, verify_password,
    get_current_active_user, get_current_admin_user
)
from app.utils.email import send_invitation_email
from app.config.settings import settings

router = APIRouter(
    prefix="/users",
    tags=["users"],
    responses={404: {"description": "Not found"}},
)


@router.get("/", response_model=List[User])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    current_admin: UserModel = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Retrieve all users (admin only)
    """
    users = db.query(UserModel).offset(skip).limit(limit).all()
    return users


@router.post("/", response_model=User)
async def create_user(
    user_data: UserCreate,
    background_tasks: BackgroundTasks,
    current_admin: UserModel = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Create a new user (admin only)
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
        status=UserStatus.PENDING,  # User starts as pending until email verification
        is_email_verified=False,
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Generate verification token and send invitation email
    token = f"verify:{new_user.id}"
    
    # Send invitation email (from admin) in the background
    admin_name = f"{current_admin.first_name} {current_admin.last_name}".strip()
    if not admin_name:
        admin_name = current_admin.email
        
    background_tasks.add_task(
        send_invitation_email, 
        new_user.email, 
        admin_name,
        token
    )
    
    return new_user


@router.get("/{user_id}", response_model=User)
async def get_user(
    user_id: str,
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get user by ID (admin can get any user, regular users can only get themselves)
    """
    # Regular users can only get their own profile
    if current_user.role != UserRole.ADMIN and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user


@router.put("/{user_id}", response_model=User)
async def update_user(
    user_id: str,
    user_data: UserUpdate,
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Update user information (admin can update any user, regular users can only update themselves)
    """
    # Regular users can only update their own profile and can't change role/status
    if current_user.role != UserRole.ADMIN:
        if current_user.id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
        # Regular users can't change these fields
        if user_data.role is not None or user_data.status is not None or user_data.is_email_verified is not None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not allowed to change role/status fields"
            )
    
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Update fields if provided
    update_data = user_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)
    
    db.commit()
    db.refresh(user)
    
    return user


@router.put("/{user_id}/password", response_model=User)
async def update_password(
    user_id: str,
    password_data: UserPasswordUpdate,
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Update user password (users can only update their own password)
    """
    # Users can only update their own password
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Verify current password
    if not verify_password(password_data.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect password"
        )
    
    # Update password
    current_user.hashed_password = get_password_hash(password_data.new_password)
    db.commit()
    db.refresh(current_user)
    
    return current_user


@router.put("/{user_id}/activate", response_model=User)
async def activate_user(
    user_id: str,
    current_admin: UserModel = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Activate user account (admin only)
    """
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user.status = UserStatus.ACTIVE
    db.commit()
    db.refresh(user)
    
    return user


@router.put("/{user_id}/deactivate", response_model=User)
async def deactivate_user(
    user_id: str,
    current_admin: UserModel = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Deactivate user account (admin only)
    """
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Prevent deactivating the last admin
    if user.role == UserRole.ADMIN:
        admin_count = db.query(UserModel).filter(
            UserModel.role == UserRole.ADMIN,
            UserModel.status == UserStatus.ACTIVE
        ).count()
        
        if admin_count <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot deactivate the last admin user"
            )
    
    user.status = UserStatus.INACTIVE
    db.commit()
    db.refresh(user)
    
    return user 