from typing import Any, List, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
import uuid
from datetime import datetime

from app.schemas.mongodb_models import Recipe, CategoryGroup
from app.models.user import User, UserRole
from app.database.mongodb import get_collection, MongoDBCollections
from app.database.postgresql import get_db
from app.utils.security import get_current_active_user, get_current_admin_user
from sqlalchemy.orm import Session

router = APIRouter(
    prefix="/recipes",
    tags=["recipes"],
    responses={404: {"description": "Not found"}},
)


@router.get("/", response_model=List[Recipe])
async def list_recipes(
    skip: int = 0,
    limit: int = 100,
    category: str = Query(None, description="Filter by category"),
    subcategory: str = Query(None, description="Filter by subcategory"),
    include_master: bool = Query(False, description="Include master recipes"),
    only_master: bool = Query(False, description="Only fetch master recipes"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    List recipes
    """
    result = []
    
    # Get master recipes if requested
    if include_master or only_master:
        master_recipes_collection = get_collection(MongoDBCollections.MASTER_RECIPES)
        master_filter = {}
        
        if category:
            master_filter["category"] = category
        if subcategory:
            master_filter["subcategory"] = subcategory
        
        # For non-admins, only show master recipes they created
        if current_user.role != UserRole.ADMIN:
            master_filter["user_id"] = current_user.id
        
        master_cursor = master_recipes_collection.find(master_filter)
        master_recipes = await master_cursor.to_list(length=100)
        
        # Process recipes to make them serializable
        for recipe in master_recipes:
            # Convert ObjectId to string to make it serializable
            if "_id" in recipe:
                recipe["_id"] = str(recipe["_id"])
            
            # Ensure dates are in ISO format strings if they're datetime objects
            if isinstance(recipe.get("created_at"), datetime):
                recipe["created_at"] = recipe["created_at"].isoformat()
            if isinstance(recipe.get("updated_at"), datetime):
                recipe["updated_at"] = recipe["updated_at"].isoformat()
                
            # Add is_master flag for compatibility with the Recipe model
            recipe["is_master"] = True
        
        result.extend(master_recipes)
    
    # Get regular recipes if not only_master
    if not only_master:
        # Get product recipes
        recipes_collection = get_collection(MongoDBCollections.RECIPES)
        
        # Build filter
        filter_query = {}
        
        # Regular users can only see their own recipes
        if current_user.role != UserRole.ADMIN:
            filter_query["user_id"] = current_user.id
        
        if category:
            filter_query["category"] = category
        
        if subcategory:
            filter_query["subcategory"] = subcategory
        
        # Get product recipes
        cursor = recipes_collection.find(filter_query).skip(skip).limit(limit)
        product_recipes = await cursor.to_list(length=limit)
        
        # Process recipes to make them serializable
        for recipe in product_recipes:
            # Convert ObjectId to string to make it serializable
            if "_id" in recipe:
                recipe["_id"] = str(recipe["_id"])
            
            # Ensure dates are in ISO format strings if they're datetime objects
            if isinstance(recipe.get("created_at"), datetime):
                recipe["created_at"] = recipe["created_at"].isoformat()
            if isinstance(recipe.get("updated_at"), datetime):
                recipe["updated_at"] = recipe["updated_at"].isoformat()
                
            # Add is_master flag (always false for regular recipes)
            recipe["is_master"] = False
            
        result.extend(product_recipes)
    
    return result


@router.get("/master/grouped", response_model=List[CategoryGroup])
async def get_grouped_master_recipes(
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Get one master recipe for each category/subcategory combination,
    grouped by category and subcategory
    """
    master_recipes_collection = get_collection(MongoDBCollections.MASTER_RECIPES)
    
    # For non-admins, only show their own recipes
    filter_query = {}
    if current_user.role != UserRole.ADMIN:
        filter_query["user_id"] = current_user.id
    
    # Get all master recipes
    cursor = master_recipes_collection.find(filter_query).sort("created_at", -1)
    all_recipes = await cursor.to_list(length=1000)
    
    # Group recipes by category/subcategory
    category_groups = {}
    for recipe in all_recipes:
        category = recipe.get("category", "")
        subcategory = recipe.get("subcategory", "")
        
        # Skip recipes without category or subcategory
        if not category or not subcategory:
            continue
        
        key = f"{category}:{subcategory}"
        
        # Only keep the most recent recipe for each category/subcategory
        if key not in category_groups:
            # Ensure required fields
            if "title" not in recipe or not recipe["title"]:
                recipe["title"] = f"{category} - {subcategory} Recipe"
                
            # Handle content if it's an object
            if isinstance(recipe.get("content"), dict):
                if "response" in recipe["content"]:
                    recipe["content"] = recipe["content"]["response"]
                else:
                    # Convert the dictionary to a JSON string
                    import json
                    recipe["content"] = json.dumps(recipe["content"])
            elif "content" not in recipe:
                recipe["content"] = f"Recipe for {category} - {subcategory}"
                
            # Convert ObjectId to string
            if "_id" in recipe:
                recipe["_id"] = str(recipe["_id"])
                
            # Ensure dates are in ISO format strings
            if isinstance(recipe.get("created_at"), datetime):
                recipe["created_at"] = recipe["created_at"].isoformat()
            if isinstance(recipe.get("updated_at"), datetime):
                recipe["updated_at"] = recipe["updated_at"].isoformat()
                
            # Ensure is_master flag
            recipe["is_master"] = True
            
            category_groups[key] = {
                "category": category,
                "subcategory": subcategory,
                "recipe": recipe
            }
    
    # Convert to list
    result = list(category_groups.values())
    
    return result


@router.get("/master/{category}/{subcategory}", response_model=List[Recipe])
async def get_master_recipes_by_category(
    category: str,
    subcategory: str,
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Get all master recipes for a specific category and subcategory
    """
    master_recipes_collection = get_collection(MongoDBCollections.MASTER_RECIPES)
    
    # Build filter
    filter_query = {
        "category": category,
        "subcategory": subcategory
    }
    
    # Regular users can only see their own recipes
    if current_user.role != UserRole.ADMIN:
        filter_query["user_id"] = current_user.id
    
    # Get all matching master recipes
    cursor = master_recipes_collection.find(filter_query).sort("created_at", -1)
    recipes = await cursor.to_list(length=100)
    
    # Process recipes to make them serializable
    for recipe in recipes:
        # Convert ObjectId to string to make it serializable
        if "_id" in recipe:
            recipe["_id"] = str(recipe["_id"])
        
        # Ensure dates are in ISO format strings if they're datetime objects
        if isinstance(recipe.get("created_at"), datetime):
            recipe["created_at"] = recipe["created_at"].isoformat()
        if isinstance(recipe.get("updated_at"), datetime):
            recipe["updated_at"] = recipe["updated_at"].isoformat()
            
        # Add is_master flag for compatibility
        recipe["is_master"] = True
        
        # Ensure title field exists
        if "title" not in recipe or not recipe["title"]:
            recipe["title"] = f"{category} - {subcategory} Recipe"
            
        # Ensure content is a string
        if "content" in recipe and isinstance(recipe["content"], dict):
            if "response" in recipe["content"]:
                recipe["content"] = recipe["content"]["response"]
            else:
                # Convert the dictionary to a JSON string
                import json
                recipe["content"] = json.dumps(recipe["content"])
        elif "content" not in recipe:
            recipe["content"] = f"Recipe for {category} - {subcategory}"
    
    return recipes


@router.post("/", response_model=Recipe)
async def create_recipe(
    recipe_data: Dict[str, Any] = Body(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Create a new recipe
    """
    # Check if this is a master recipe
    is_master = recipe_data.pop("is_master", False)
    
    # Add required fields
    now = datetime.utcnow()
    recipe_data["id"] = str(uuid.uuid4())
    recipe_data["user_id"] = current_user.id
    recipe_data["created_at"] = now
    recipe_data["updated_at"] = now
    
    # Insert recipe into appropriate collection
    if is_master:
        # Only admins can create master recipes directly
        if current_user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admins can create master recipes directly"
            )
        
        # Ensure required fields for master recipe
        if not recipe_data.get("category") or not recipe_data.get("subcategory"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Category and subcategory are required for master recipes"
            )
        
        # Insert into master recipes collection
        master_recipes_collection = get_collection(MongoDBCollections.MASTER_RECIPES)
        await master_recipes_collection.insert_one(recipe_data)
        
        # Add is_master flag for response compatibility
        recipe_data["is_master"] = True
    else:
        # Insert into regular recipes collection
        recipes_collection = get_collection(MongoDBCollections.RECIPES)
        await recipes_collection.insert_one(recipe_data)
    
    return recipe_data


@router.get("/{recipe_id}", response_model=Recipe)
async def get_recipe(
    recipe_id: str,
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Get recipe by ID
    """
    # Check in regular recipes collection first
    recipes_collection = get_collection(MongoDBCollections.RECIPES)
    recipe = await recipes_collection.find_one({"id": recipe_id})
    
    if not recipe:
        # If not found, check master recipes collection
        master_recipes_collection = get_collection(MongoDBCollections.MASTER_RECIPES)
        recipe = await master_recipes_collection.find_one({"id": recipe_id})
        
        if recipe:
            # Add is_master flag for compatibility
            recipe["is_master"] = True
    else:
        # Add is_master flag (always false for regular recipes)
        recipe["is_master"] = False
    
    if not recipe:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recipe not found"
        )
    
    # Check if user has access to this recipe
    if current_user.role != UserRole.ADMIN and recipe["user_id"] != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    return recipe


@router.put("/{recipe_id}", response_model=Recipe)
async def update_recipe(
    recipe_id: str,
    recipe_data: Dict[str, Any] = Body(...),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Update recipe
    """
    # Don't allow changing these fields
    recipe_data.pop("id", None)
    recipe_data.pop("user_id", None)
    recipe_data.pop("created_at", None)
    
    # Update timestamps
    recipe_data["updated_at"] = datetime.utcnow()
    
    # Check if recipe exists and user has access
    recipes_collection = get_collection(MongoDBCollections.RECIPES)
    master_recipes_collection = get_collection(MongoDBCollections.MASTER_RECIPES)
    
    # Check in regular recipes collection first
    recipe = await recipes_collection.find_one({"id": recipe_id})
    is_master = False
    
    if not recipe:
        # If not found, check master recipes collection
        recipe = await master_recipes_collection.find_one({"id": recipe_id})
        is_master = True
    
    if not recipe:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recipe not found"
        )
    
    # Only recipe owner or admin can update
    if current_user.role != UserRole.ADMIN and recipe["user_id"] != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Update in correct collection
    if is_master:
        # Only admins can update master recipes
        if current_user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admins can update master recipes"
            )
        
        await master_recipes_collection.update_one(
            {"id": recipe_id},
            {"$set": recipe_data}
        )
    else:
        await recipes_collection.update_one(
            {"id": recipe_id},
            {"$set": recipe_data}
        )
    
    # Get updated recipe
    if is_master:
        updated_recipe = await master_recipes_collection.find_one({"id": recipe_id})
        updated_recipe["is_master"] = True
    else:
        updated_recipe = await recipes_collection.find_one({"id": recipe_id})
        updated_recipe["is_master"] = False
    
    return updated_recipe


@router.delete("/{recipe_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_recipe(
    recipe_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    Delete recipe
    """
    recipes_collection = get_collection(MongoDBCollections.RECIPES)
    master_recipes_collection = get_collection(MongoDBCollections.MASTER_RECIPES)
    
    # Check in regular recipes collection first
    recipe = await recipes_collection.find_one({"id": recipe_id})
    is_master = False
    
    if not recipe:
        # If not found, check master recipes collection
        recipe = await master_recipes_collection.find_one({"id": recipe_id})
        is_master = True
    
    if not recipe:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recipe not found"
        )
    
    # Only recipe owner or admin can delete
    if current_user.role != UserRole.ADMIN and recipe["user_id"] != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Delete from correct collection
    if is_master:
        await master_recipes_collection.delete_one({"id": recipe_id})
    else:
        await recipes_collection.delete_one({"id": recipe_id})
    # No return value for 204 response


@router.post("/generate-master", response_model=Recipe)
async def generate_master_recipe(
    category: str = Body(..., embed=True),
    subcategory: str = Body(..., embed=True),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Generate a master recipe for a category/subcategory by analyzing all product recipes
    """
    from app.services.analysis import check_and_generate_master_recipes
    
    # Check if a master recipe already exists
    master_recipes_collection = get_collection(MongoDBCollections.MASTER_RECIPES)
    existing_master = await master_recipes_collection.find_one({
        "category": category,
        "subcategory": subcategory
    })
    
    if existing_master and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A master recipe already exists for this category/subcategory"
        )
    
    # Generate master recipe
    import asyncio

    try:
        master_recipe = await asyncio.wait_for(
            check_and_generate_master_recipes(
                category=category,
                subcategory=subcategory,
                user_id=current_user.id
            ),
            timeout=600  # 10 minutes
        )
        return {"msg": "Master recipe generated successfully"}
    except asyncio.TimeoutError:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Master recipe generation timed out. Try again later."
        )


@router.get("/master/single/{category}/{subcategory}", response_model=Recipe)
async def get_single_master_recipe_by_category(
    category: str,
    subcategory: str,
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Get the most recent single master recipe for a specific category and subcategory
    """
    master_recipes_collection = get_collection(MongoDBCollections.MASTER_RECIPES)
    prompts_collection = get_collection(MongoDBCollections.PROMPTS)
    
    # Build filter
    filter_query = {
        "category": category,
        "subcategory": subcategory
    }
    
    # Regular users can only see their own recipes
    if current_user.role != UserRole.ADMIN:
        filter_query["user_id"] = current_user.id
    
    # Get the most recent matching master recipe
    # Sort by created_at in descending order to get the latest one
    recipe = await master_recipes_collection.find_one(
        filter_query, 
        sort=[("created_at", -1)]
    )
    
    if not recipe:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No master recipe found for category '{category}' and subcategory '{subcategory}'"
        )
    
    # Convert ObjectId to string to make it serializable
    if "_id" in recipe:
        recipe["_id"] = str(recipe["_id"])
    
    # Ensure dates are in ISO format strings if they're datetime objects
    if isinstance(recipe.get("created_at"), datetime):
        recipe["created_at"] = recipe["created_at"].isoformat()
    if isinstance(recipe.get("updated_at"), datetime):
        recipe["updated_at"] = recipe["updated_at"].isoformat()
        
    # Add is_master flag for compatibility
    recipe["is_master"] = True
    
    # Ensure title field exists
    if "title" not in recipe or not recipe["title"]:
        # Try to get the prompt block's title if prompt_block_id exists
        if "prompt_block_id" in recipe and recipe["prompt_block_id"]:
            prompt_block = await prompts_collection.find_one({"id": recipe["prompt_block_id"]})
            if prompt_block and "block_title" in prompt_block:
                recipe["title"] = prompt_block["block_title"]
            else:
                recipe["title"] = f"{category} - {subcategory} Recipe"
        else:
            recipe["title"] = f"{category} - {subcategory} Recipe"
    
    # Ensure content is a string
    if "content" in recipe and isinstance(recipe["content"], dict):
        if "response" in recipe["content"]:
            recipe["content"] = recipe["content"]["response"]
        else:
            # Convert the dictionary to a JSON string
            import json
            recipe["content"] = json.dumps(recipe["content"])
    elif "content" not in recipe:
        recipe["content"] = f"Recipe for {category} - {subcategory}"
    
    return recipe 