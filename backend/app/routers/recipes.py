from typing import Any, List, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
import uuid
from datetime import datetime

from app.schemas.mongodb_models import Recipe
from app.models.user import User, UserRole
from app.models.project import Project as ProjectModel
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
    project_id: str = Query(None, description="Filter by project ID"),
    category: str = Query(None, description="Filter by category"),
    subcategory: str = Query(None, description="Filter by subcategory"),
    include_master: bool = Query(False, description="Include master recipes"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    List recipes
    """
    result = []
    
    # Get product recipes
    recipes_collection = get_collection(MongoDBCollections.RECIPES)
    
    # Build filter
    filter_query = {}
    
    # Regular users can only see their own recipes
    if current_user.role != UserRole.ADMIN:
        filter_query["user_id"] = current_user.id
    
    if project_id:
        # Check if user has access to the project
        project = db.query(ProjectModel).filter(ProjectModel.id == project_id).first()
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        if current_user.role != UserRole.ADMIN and project.owner_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
        
        filter_query["project_id"] = project_id
    
    if category:
        filter_query["category"] = category
    
    if subcategory:
        filter_query["subcategory"] = subcategory
    
    # Get product recipes
    cursor = recipes_collection.find(filter_query).skip(skip).limit(limit)
    product_recipes = await cursor.to_list(length=limit)
    result.extend(product_recipes)
    
    # Get master recipes if requested
    if include_master:
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
        
        # Add is_master flag for compatibility with the Recipe model
        for recipe in master_recipes:
            recipe["is_master"] = True
        
        result.extend(master_recipes)
    
    return result


@router.post("/", response_model=Recipe)
async def create_recipe(
    recipe_data: Dict[str, Any] = Body(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Create a new recipe
    """
    # Validate project_id if provided
    project_id = recipe_data.get("project_id")
    if project_id:
        project = db.query(ProjectModel).filter(ProjectModel.id == project_id).first()
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        # Check if user has access to the project
        if current_user.role != UserRole.ADMIN and project.owner_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
    
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
    # Find the recipe in either collection
    recipes_collection = get_collection(MongoDBCollections.RECIPES)
    recipe = await recipes_collection.find_one({"id": recipe_id})
    is_master = False
    
    if not recipe:
        # Check master recipes collection
        master_recipes_collection = get_collection(MongoDBCollections.MASTER_RECIPES)
        recipe = await master_recipes_collection.find_one({"id": recipe_id})
        is_master = True
    
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
    
    # Only admins can update master recipes
    if is_master and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can update master recipes"
        )
    
    # Prevent switching between master and regular recipe
    if "is_master" in recipe_data and recipe_data["is_master"] != is_master:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot change the master status of a recipe"
        )
    
    # Remove is_master flag from update data
    if "is_master" in recipe_data:
        del recipe_data["is_master"]
    
    # Update recipe
    recipe_data["updated_at"] = datetime.utcnow()
    
    if is_master:
        collection = get_collection(MongoDBCollections.MASTER_RECIPES)
    else:
        collection = recipes_collection
    
    await collection.update_one(
        {"id": recipe_id},
        {"$set": recipe_data}
    )
    
    # Get updated recipe
    updated_recipe = await collection.find_one({"id": recipe_id})
    
    # Add is_master flag for response compatibility
    updated_recipe["is_master"] = is_master
    
    return updated_recipe


@router.delete("/{recipe_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_recipe(
    recipe_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    Delete recipe
    """
    # Find the recipe in either collection
    recipes_collection = get_collection(MongoDBCollections.RECIPES)
    recipe = await recipes_collection.find_one({"id": recipe_id})
    is_master = False
    
    if not recipe:
        # Check master recipes collection
        master_recipes_collection = get_collection(MongoDBCollections.MASTER_RECIPES)
        recipe = await master_recipes_collection.find_one({"id": recipe_id})
        is_master = True
    
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
    
    # Only admins can delete master recipes
    if is_master and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can delete master recipes"
        )
    
    # Delete recipe from appropriate collection
    if is_master:
        await master_recipes_collection.delete_one({"id": recipe_id})
    else:
        await recipes_collection.delete_one({"id": recipe_id})
    # No return value for 204 response


@router.get("/master/{category}/{subcategory}", response_model=Optional[Recipe])
async def get_master_recipe_by_category(
    category: str,
    subcategory: str,
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Get master recipe for a specific category and subcategory
    """
    master_recipes_collection = get_collection(MongoDBCollections.MASTER_RECIPES)
    
    recipe = await master_recipes_collection.find_one({
        "category": category,
        "subcategory": subcategory
    })
    
    if recipe:
        # Add is_master flag for compatibility
        recipe["is_master"] = True
    
    # If not found, return None (not an error)
    return recipe


@router.post("/generate-master", response_model=Recipe)
async def generate_master_recipe(
    category: str = Body(..., embed=True),
    subcategory: str = Body(..., embed=True),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Generate a master recipe for a category/subcategory by analyzing all product recipes
    """
    from app.services.analysis import generate_master_recipe
    
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
    try:
        master_recipe = await generate_master_recipe(
            category=category,
            subcategory=subcategory,
            user_id=current_user.id
        )
        
        if not master_recipe:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to generate master recipe. Not enough product recipes found."
            )
        
        # Add is_master flag for compatibility
        master_recipe["is_master"] = True
        
        return master_recipe
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating master recipe: {str(e)}"
        ) 