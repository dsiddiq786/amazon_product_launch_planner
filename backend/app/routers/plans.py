from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
import uuid
from datetime import datetime, timedelta

from app.schemas.plan import (
    Plan, PlanCreate, PlanUpdate, PlanList,
    Subscription, SubscriptionCreate, SubscriptionUpdate, SubscriptionList, SubscriptionWithPlan
)
from app.models.plan import Plan as PlanModel, Subscription as SubscriptionModel
from app.models.user import User, UserRole
from app.database.postgresql import get_db
from app.utils.security import get_current_active_user, get_current_admin_user

router = APIRouter(
    prefix="/plans",
    tags=["plans"],
    responses={404: {"description": "Not found"}},
)


@router.get("/", response_model=PlanList)
async def list_plans(
    skip: int = 0,
    limit: int = 100,
    active_only: bool = True,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    List all plans
    """
    query = db.query(PlanModel)
    
    if active_only:
        query = query.filter(PlanModel.is_active == True)
    
    # Get total count for pagination
    total_count = query.count()
    
    # Apply pagination
    plans = query.offset(skip).limit(limit).all()
    
    return {
        "plans": plans,
        "count": total_count
    }


@router.post("/", response_model=Plan)
async def create_plan(
    plan_data: PlanCreate,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Create a new plan (admin only)
    """
    # Check if plan with the same name already exists
    existing_plan = db.query(PlanModel).filter(PlanModel.name == plan_data.name).first()
    if existing_plan:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Plan with this name already exists"
        )
    
    # Create new plan
    new_plan = PlanModel(
        id=str(uuid.uuid4()),
        name=plan_data.name,
        description=plan_data.description,
        price=plan_data.price,
        scrape_quota=plan_data.scrape_quota,
        features=plan_data.features
    )
    
    db.add(new_plan)
    db.commit()
    db.refresh(new_plan)
    
    return new_plan


@router.get("/{plan_id}", response_model=Plan)
async def get_plan(
    plan_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get plan by ID
    """
    plan = db.query(PlanModel).filter(PlanModel.id == plan_id).first()
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plan not found"
        )
    
    return plan


@router.put("/{plan_id}", response_model=Plan)
async def update_plan(
    plan_id: str,
    plan_data: PlanUpdate,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Update plan (admin only)
    """
    plan = db.query(PlanModel).filter(PlanModel.id == plan_id).first()
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plan not found"
        )
    
    # Check if trying to update name to an existing name
    if plan_data.name and plan_data.name != plan.name:
        existing_plan = db.query(PlanModel).filter(PlanModel.name == plan_data.name).first()
        if existing_plan:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Plan with this name already exists"
            )
    
    # Update plan fields
    update_data = plan_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(plan, field, value)
    
    db.commit()
    db.refresh(plan)
    
    return plan


@router.delete("/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_plan(
    plan_id: str,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Delete plan (admin only)
    """
    plan = db.query(PlanModel).filter(PlanModel.id == plan_id).first()
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plan not found"
        )
    
    # Check if plan has active subscriptions
    active_subscriptions = db.query(SubscriptionModel).filter(
        SubscriptionModel.plan_id == plan_id,
        SubscriptionModel.is_active == True
    ).count()
    
    if active_subscriptions > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete plan with {active_subscriptions} active subscriptions"
        )
    
    db.delete(plan)
    db.commit()
    # No return value for 204 response


# Subscription routes
@router.get("/subscriptions/", response_model=SubscriptionList)
async def list_subscriptions(
    skip: int = 0,
    limit: int = 100,
    active_only: bool = True,
    user_id: str = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    List subscriptions (admin can see all, users can only see their own)
    """
    query = db.query(SubscriptionModel)
    
    # Regular users can only see their own subscriptions
    if current_user.role != UserRole.ADMIN:
        query = query.filter(SubscriptionModel.user_id == current_user.id)
    elif user_id:  # Admin can filter by user_id
        query = query.filter(SubscriptionModel.user_id == user_id)
    
    if active_only:
        query = query.filter(SubscriptionModel.is_active == True)
    
    # Get total count for pagination
    total_count = query.count()
    
    # Apply pagination
    subscriptions = query.offset(skip).limit(limit).all()
    
    return {
        "subscriptions": subscriptions,
        "count": total_count
    }


@router.post("/subscriptions/", response_model=Subscription)
async def create_subscription(
    subscription_data: SubscriptionCreate,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Create a new subscription (admin only)
    """
    # Check if plan exists
    plan = db.query(PlanModel).filter(PlanModel.id == subscription_data.plan_id).first()
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plan not found"
        )
    
    # Check if user exists
    user = db.query(User).filter(User.id == subscription_data.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check if user already has an active subscription
    existing_subscription = db.query(SubscriptionModel).filter(
        SubscriptionModel.user_id == subscription_data.user_id,
        SubscriptionModel.is_active == True
    ).first()
    
    if existing_subscription:
        # Deactivate existing subscription
        existing_subscription.is_active = False
        existing_subscription.end_date = datetime.utcnow()
    
    # Create new subscription
    end_date = subscription_data.end_date
    if not end_date:
        # Default to 1 month subscription
        end_date = datetime.utcnow() + timedelta(days=30)
    
    new_subscription = SubscriptionModel(
        id=str(uuid.uuid4()),
        user_id=subscription_data.user_id,
        plan_id=subscription_data.plan_id,
        start_date=datetime.utcnow(),
        end_date=end_date,
        is_active=True
    )
    
    # Update user's scrape quota based on the plan
    user.scrape_quota = plan.scrape_quota
    
    db.add(new_subscription)
    db.commit()
    db.refresh(new_subscription)
    
    return new_subscription


@router.get("/subscriptions/{subscription_id}", response_model=SubscriptionWithPlan)
async def get_subscription(
    subscription_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get subscription by ID
    """
    subscription = db.query(SubscriptionModel).filter(SubscriptionModel.id == subscription_id).first()
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found"
        )
    
    # Regular users can only access their own subscriptions
    if current_user.role != UserRole.ADMIN and subscription.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Get plan details
    plan = db.query(PlanModel).filter(PlanModel.id == subscription.plan_id).first()
    
    # Return subscription with plan
    return {
        **subscription.__dict__,
        "plan": plan
    }


@router.put("/subscriptions/{subscription_id}", response_model=Subscription)
async def update_subscription(
    subscription_id: str,
    subscription_data: SubscriptionUpdate,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Update subscription (admin only)
    """
    subscription = db.query(SubscriptionModel).filter(SubscriptionModel.id == subscription_id).first()
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found"
        )
    
    # Check if plan exists if changing plan
    if subscription_data.plan_id:
        plan = db.query(PlanModel).filter(PlanModel.id == subscription_data.plan_id).first()
        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Plan not found"
            )
        
        # Update user's scrape quota if changing plan
        if subscription.plan_id != subscription_data.plan_id and subscription.is_active:
            user = db.query(User).filter(User.id == subscription.user_id).first()
            user.scrape_quota = plan.scrape_quota
    
    # Update subscription fields
    update_data = subscription_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(subscription, field, value)
    
    db.commit()
    db.refresh(subscription)
    
    return subscription


@router.delete("/subscriptions/{subscription_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_subscription(
    subscription_id: str,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Delete subscription (admin only)
    """
    subscription = db.query(SubscriptionModel).filter(SubscriptionModel.id == subscription_id).first()
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found"
        )
    
    db.delete(subscription)
    db.commit()
    # No return value for 204 response


@router.get("/user-subscription/{user_id}", response_model=SubscriptionWithPlan)
async def get_user_subscription(
    user_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get user's active subscription
    """
    # Regular users can only access their own subscription
    if current_user.role != UserRole.ADMIN and user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Get active subscription
    subscription = db.query(SubscriptionModel).filter(
        SubscriptionModel.user_id == user_id,
        SubscriptionModel.is_active == True
    ).first()
    
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active subscription found for this user"
        )
    
    # Get plan details
    plan = db.query(PlanModel).filter(PlanModel.id == subscription.plan_id).first()
    
    # Return subscription with plan
    return {
        **subscription.__dict__,
        "plan": plan
    } 