from typing import Any, List, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
import uuid
from datetime import datetime

from app.schemas.mongodb_models import PromptBlock, PromptBlockInput, AnalysisResult
from app.models.user import User, UserRole
from app.database.mongodb import get_collection, MongoDBCollections
from app.utils.security import get_current_active_user, get_current_admin_user
from app.utils.gemini import use_stored_prompt

router = APIRouter(
    prefix="/prompts",
    tags=["prompts"],
    responses={404: {"description": "Not found"}},
)


@router.get("/", response_model=List[PromptBlock])
async def list_prompt_blocks(
    skip: int = 0,
    limit: int = 100,
    category: str = Query(None, description="Filter by category"),
    active_only: bool = True,
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    List prompt blocks
    """
    prompts_collection = get_collection(MongoDBCollections.PROMPTS)
    
    # Build filter
    filter_query = {}
    if category:
        filter_query["prompt_category"] = category
    if active_only:
        filter_query["is_active"] = True
    
    # Get prompt blocks
    cursor = prompts_collection.find(filter_query).skip(skip).limit(limit)
    prompt_blocks = await cursor.to_list(length=limit)
    
    return prompt_blocks


@router.post("/", response_model=PromptBlock)
async def create_prompt_block(
    prompt_data: PromptBlockInput,
    current_admin: User = Depends(get_current_admin_user)
) -> Any:
    """
    Create a new prompt block (admin only)
    """
    prompts_collection = get_collection(MongoDBCollections.PROMPTS)
    
    # Check if prompt block with the same title in the same category already exists
    existing_prompt = await prompts_collection.find_one({
        "prompt_category": prompt_data.prompt_category,
        "block_title": prompt_data.block_title
    })
    if existing_prompt:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Prompt block with this title already exists in this category"
        )
    
    # Create new prompt block
    now = datetime.utcnow()
    new_prompt = {
        "id": str(uuid.uuid4()),
        "prompt_category": prompt_data.prompt_category,
        "block_title": prompt_data.block_title,
        "input_prompt": prompt_data.input_prompt,
        "output_example": prompt_data.output_example,
        "rerun_on_existing": prompt_data.rerun_on_existing,
        "is_active": prompt_data.is_active if prompt_data.is_active is not None else True,
        "user_id": current_admin.id,
        "master_recipe_prompt": prompt_data.master_recipe_prompt,
        "analyzed_products_count": 0,
        "limit": prompt_data.limit,
        "skip": prompt_data.skip,
        "sort_field": prompt_data.sort_field,
        "sort_order": prompt_data.sort_order,
        "created_at": now,
        "updated_at": now
    }
    
    await prompts_collection.insert_one(new_prompt)
    
    # If rerun_on_existing is True, trigger reanalysis of existing products
    if prompt_data.rerun_on_existing:
        # TODO: Implement background task to reanalyze existing products
        pass
    
    return new_prompt


@router.get("/{prompt_id}", response_model=PromptBlock)
async def get_prompt_block(
    prompt_id: str,
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Get prompt block by ID
    """
    prompts_collection = get_collection(MongoDBCollections.PROMPTS)
    prompt = await prompts_collection.find_one({"id": prompt_id})
    
    if not prompt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prompt block not found"
        )
    
    return prompt


@router.put("/{prompt_id}", response_model=PromptBlock)
async def update_prompt_block(
    prompt_id: str,
    prompt_data: PromptBlockInput,
    current_admin: User = Depends(get_current_admin_user)
) -> Any:
    """
    Update prompt block (admin only)
    """
    prompts_collection = get_collection(MongoDBCollections.PROMPTS)
    
    # Check if prompt block exists
    prompt = await prompts_collection.find_one({"id": prompt_id})
    if not prompt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prompt block not found"
        )
    
    # Check if trying to update title to an existing one in the same category
    if prompt_data.block_title != prompt["block_title"] or prompt_data.prompt_category != prompt["prompt_category"]:
        existing_prompt = await prompts_collection.find_one({
            "prompt_category": prompt_data.prompt_category,
            "block_title": prompt_data.block_title
        })
        if existing_prompt:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Prompt block with this title already exists in this category"
            )
    
    # Update prompt block
    update_data = {
        "prompt_category": prompt_data.prompt_category,
        "block_title": prompt_data.block_title,
        "input_prompt": prompt_data.input_prompt,
        "output_example": prompt_data.output_example,
        "rerun_on_existing": prompt_data.rerun_on_existing,
        "is_active": prompt_data.is_active if prompt_data.is_active is not None else prompt["is_active"],
        "master_recipe_prompt": prompt_data.master_recipe_prompt,
        "limit": prompt_data.limit,
        "skip": prompt_data.skip,
        "sort_field": prompt_data.sort_field,
        "sort_order": prompt_data.sort_order,
        "updated_at": datetime.utcnow()
    }
    
    await prompts_collection.update_one(
        {"id": prompt_id},
        {"$set": update_data}
    )
    
    # Get updated prompt block
    updated_prompt = await prompts_collection.find_one({"id": prompt_id})
    
    # If rerun_on_existing is True, trigger reanalysis of existing products
    if prompt_data.rerun_on_existing:
        # TODO: Implement background task to reanalyze existing products
        pass
    
    return updated_prompt


@router.delete("/{prompt_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_prompt_block(
    prompt_id: str,
    current_admin: User = Depends(get_current_admin_user)
):
    """
    Delete prompt block (admin only)
    """
    prompts_collection = get_collection(MongoDBCollections.PROMPTS)
    
    # Check if prompt block exists
    prompt = await prompts_collection.find_one({"id": prompt_id})
    if not prompt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prompt block not found"
        )
    
    # Delete prompt block
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
        {"$group": {"_id": "$prompt_category"}},
        {"$sort": {"_id": 1}}
    ]
    
    cursor = prompts_collection.aggregate(pipeline)
    categories = await cursor.to_list(length=100)
    
    return [cat["_id"] for cat in categories if cat["_id"]]


@router.post("/test", response_model=Dict[str, Any])
async def test_prompt_block(
    prompt_id: str = Body(..., embed=True),
    input_data: Dict[str, Any] = Body(..., embed=True),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Test a prompt block with sample input data
    """
    # Call the Gemini API with the stored prompt
    response = await use_stored_prompt(
        prompt_id=prompt_id,
        input_data=input_data,
        user_id=current_user.id
    )
    
    return response 