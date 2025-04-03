from typing import Any, List, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
import uuid
from datetime import datetime

from app.schemas.mongodb_models import Prompt, PromptInput
from app.models.user import User, UserRole
from app.database.mongodb import get_collection, MongoDBCollections
from app.utils.security import get_current_active_user, get_current_admin_user

router = APIRouter(
    prefix="/prompts",
    tags=["prompts"],
    responses={404: {"description": "Not found"}},
)


@router.get("/", response_model=List[Prompt])
async def list_prompts(
    skip: int = 0,
    limit: int = 100,
    category: str = Query(None, description="Filter by category"),
    active_only: bool = True,
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    List prompts
    """
    prompts_collection = get_collection(MongoDBCollections.PROMPTS)
    
    # Build filter
    filter_query = {}
    if category:
        filter_query["category"] = category
    if active_only:
        filter_query["is_active"] = True
    
    # Get prompts
    cursor = prompts_collection.find(filter_query).skip(skip).limit(limit)
    prompts = await cursor.to_list(length=limit)
    
    return prompts


@router.post("/", response_model=Prompt)
async def create_prompt(
    prompt_data: PromptInput,
    current_admin: User = Depends(get_current_admin_user)
) -> Any:
    """
    Create a new prompt (admin only)
    """
    prompts_collection = get_collection(MongoDBCollections.PROMPTS)
    
    # Check if prompt with the same name already exists
    existing_prompt = await prompts_collection.find_one({"name": prompt_data.name})
    if existing_prompt:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Prompt with this name already exists"
        )
    
    # Create new prompt
    now = datetime.utcnow()
    new_prompt = {
        "id": str(uuid.uuid4()),
        "name": prompt_data.name,
        "description": prompt_data.description,
        "content": prompt_data.content,
        "category": prompt_data.category,
        "is_active": prompt_data.is_active if prompt_data.is_active is not None else True,
        "user_id": current_admin.id,
        "created_at": now,
        "updated_at": now
    }
    
    await prompts_collection.insert_one(new_prompt)
    
    return new_prompt


@router.get("/{prompt_id}", response_model=Prompt)
async def get_prompt(
    prompt_id: str,
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Get prompt by ID
    """
    prompts_collection = get_collection(MongoDBCollections.PROMPTS)
    prompt = await prompts_collection.find_one({"id": prompt_id})
    
    if not prompt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prompt not found"
        )
    
    return prompt


@router.put("/{prompt_id}", response_model=Prompt)
async def update_prompt(
    prompt_id: str,
    prompt_data: PromptInput,
    current_admin: User = Depends(get_current_admin_user)
) -> Any:
    """
    Update prompt (admin only)
    """
    prompts_collection = get_collection(MongoDBCollections.PROMPTS)
    
    # Check if prompt exists
    prompt = await prompts_collection.find_one({"id": prompt_id})
    if not prompt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prompt not found"
        )
    
    # Check if trying to update name to an existing name
    if prompt_data.name != prompt["name"]:
        existing_prompt = await prompts_collection.find_one({"name": prompt_data.name})
        if existing_prompt:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Prompt with this name already exists"
            )
    
    # Update prompt
    update_data = {
        "name": prompt_data.name,
        "description": prompt_data.description,
        "content": prompt_data.content,
        "category": prompt_data.category,
        "is_active": prompt_data.is_active if prompt_data.is_active is not None else prompt["is_active"],
        "updated_at": datetime.utcnow()
    }
    
    await prompts_collection.update_one(
        {"id": prompt_id},
        {"$set": update_data}
    )
    
    # Get updated prompt
    updated_prompt = await prompts_collection.find_one({"id": prompt_id})
    return updated_prompt


@router.delete("/{prompt_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_prompt(
    prompt_id: str,
    current_admin: User = Depends(get_current_admin_user)
):
    """
    Delete prompt (admin only)
    """
    prompts_collection = get_collection(MongoDBCollections.PROMPTS)
    
    # Check if prompt exists
    prompt = await prompts_collection.find_one({"id": prompt_id})
    if not prompt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prompt not found"
        )
    
    # Delete prompt
    await prompts_collection.delete_one({"id": prompt_id})
    # No return value for 204 response


@router.get("/categories/list", response_model=List[str])
async def list_prompt_categories(
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Get list of unique prompt categories
    """
    prompts_collection = get_collection(MongoDBCollections.PROMPTS)
    
    # Aggregate to get unique categories
    pipeline = [
        {"$group": {"_id": "$category"}},
        {"$sort": {"_id": 1}}
    ]
    
    cursor = prompts_collection.aggregate(pipeline)
    categories = await cursor.to_list(length=100)
    
    return [cat["_id"] for cat in categories if cat["_id"]]


@router.post("/test", response_model=Dict[str, Any])
async def test_prompt(
    prompt_id: str = Body(..., embed=True),
    input_data: Dict[str, Any] = Body(..., embed=True),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Test a prompt with sample input data
    """
    from app.utils.gemini import use_stored_prompt
    
    # Call the Gemini API with the stored prompt
    response = await use_stored_prompt(
        prompt_id=prompt_id,
        input_data=input_data,
        user_id=current_user.id
    )
    
    return response 