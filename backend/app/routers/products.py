from typing import Any, List, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Body, BackgroundTasks
import uuid
from datetime import datetime

from app.schemas.mongodb_models import ScrapedProduct, Recipe
from app.models.user import User, UserRole
from app.models.project import Project as ProjectModel
from app.database.mongodb import get_collection, MongoDBCollections
from app.database.postgresql import get_db
from app.utils.security import get_current_active_user
from app.services.scheduler import scheduler
from sqlalchemy.orm import Session

router = APIRouter(
    prefix="/products",
    tags=["products"],
    responses={404: {"description": "Not found"}},
)


@router.get("/", response_model=List[ScrapedProduct])
async def list_products(
    skip: int = 0,
    limit: int = 100,
    project_id: str = Query(None, description="Filter by project ID"),
    category: str = Query(None, description="Filter by category"),
    subcategory: str = Query(None, description="Filter by subcategory"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    List scraped products
    """
    # If project_id is provided, check if user has access to that project
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
    
    products_collection = get_collection(MongoDBCollections.SCRAPED_DATA)
    
    # Build filter
    filter_query = {}
    
    # Regular users can only see their own products
    if current_user.role != UserRole.ADMIN:
        filter_query["user_id"] = current_user.id
    
    if project_id:
        filter_query["project_id"] = project_id
    
    if category:
        filter_query["category"] = category
    
    if subcategory:
        filter_query["subcategory"] = subcategory
    
    # Get products
    cursor = products_collection.find(filter_query).skip(skip).limit(limit)
    products = await cursor.to_list(length=limit)
    
    return products


@router.post("/", response_model=ScrapedProduct)
async def create_product(
    product_data: Dict[str, Any] = Body(...),
    background_tasks: BackgroundTasks = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Create a new scraped product
    """
    # Check user's scrape quota
    if current_user.scrape_quota <= 0:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Scrape quota exceeded. Please upgrade your plan."
        )
    
    # Validate project_id
    project_id = product_data.get("project_id")
    if not project_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="project_id is required"
        )
    
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
    
    # Add required fields
    now = datetime.utcnow()
    product_id = str(uuid.uuid4())
    product_data["id"] = product_id
    product_data["user_id"] = current_user.id
    product_data["created_at"] = now
    product_data["updated_at"] = now
    
    # Insert product
    products_collection = get_collection(MongoDBCollections.SCRAPED_DATA)
    await products_collection.insert_one(product_data)
    
    # Decrease user's scrape quota
    current_user.scrape_quota -= 1
    db.commit()
    
    # Schedule analysis using the scheduler service
    task_id = await scheduler.schedule_task(
        product_id=product_id,
        user_id=current_user.id,
        project_id=project_id,
        delay_seconds=5  # Small delay to allow the transaction to complete
    )
    
    # Add task_id to the response
    product_data["analysis_task_id"] = task_id
    
    return product_data


@router.get("/{product_id}", response_model=ScrapedProduct)
async def get_product(
    product_id: str,
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Get scraped product by ID
    """
    products_collection = get_collection(MongoDBCollections.SCRAPED_DATA)
    
    product = await products_collection.find_one({"id": product_id})
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    # Check if user has access to this product
    if current_user.role != UserRole.ADMIN and product["user_id"] != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    return product


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    Delete scraped product
    """
    products_collection = get_collection(MongoDBCollections.SCRAPED_DATA)
    
    product = await products_collection.find_one({"id": product_id})
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    # Check if user has access to this product
    if current_user.role != UserRole.ADMIN and product["user_id"] != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Delete product
    await products_collection.delete_one({"id": product_id})
    
    # Delete associated recipes
    recipes_collection = get_collection(MongoDBCollections.RECIPES)
    await recipes_collection.delete_many({"product_id": product_id})
    # No return value for 204 response


@router.post("/{product_id}/analyze", response_model=Dict[str, Any])
async def analyze_product_manually(
    product_id: str,
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Manually trigger product analysis
    """
    products_collection = get_collection(MongoDBCollections.SCRAPED_DATA)
    
    product = await products_collection.find_one({"id": product_id})
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    # Check if user has access to this product
    if current_user.role != UserRole.ADMIN and product["user_id"] != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Schedule analysis using the scheduler service
    task_id = await scheduler.schedule_task(
        product_id=product_id,
        user_id=current_user.id,
        project_id=product["project_id"],
        delay_seconds=0  # Execute immediately
    )
    
    return {
        "message": "Analysis started", 
        "product_id": product_id,
        "task_id": task_id
    }


@router.get("/{product_id}/recipe", response_model=Recipe)
async def get_product_recipe(
    product_id: str,
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Get recipe for a specific product
    """
    products_collection = get_collection(MongoDBCollections.SCRAPED_DATA)
    recipes_collection = get_collection(MongoDBCollections.RECIPES)
    
    # Check if product exists and user has access to it
    product = await products_collection.find_one({"id": product_id})
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    if current_user.role != UserRole.ADMIN and product["user_id"] != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Get recipe
    recipe = await recipes_collection.find_one({
        "product_id": product_id,
        "is_master": False
    })
    
    if not recipe:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recipe not found for this product. Try analyzing the product first."
        )
    
    return recipe


@router.get("/project/{project_id}/master-recipe", response_model=Optional[Recipe])
async def get_master_recipe(
    project_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get master recipe for a project's category and subcategory
    """
    # Check if project exists and user has access to it
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
    
    # Get master recipe for this category/subcategory
    master_recipes_collection = get_collection(MongoDBCollections.MASTER_RECIPES)
    recipe = await master_recipes_collection.find_one({
        "category": project.category,
        "subcategory": project.subcategory
    })
    
    # Add is_master flag for compatibility with the Recipe model
    if recipe:
        recipe["is_master"] = True
    
    # If not found, return None (not an error)
    return recipe


@router.get("/check-master-recipe/{project_id}", response_model=Dict[str, Any])
async def check_master_recipe_exists(
    project_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Check if a master recipe exists for the project's category and subcategory.
    Used by the Chrome extension to determine if scraping is needed.
    """
    # Check if project exists and user has access to it
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
    
    # Get master recipe for this category/subcategory
    master_recipes_collection = get_collection(MongoDBCollections.MASTER_RECIPES)
    recipe = await master_recipes_collection.find_one({
        "category": project.category,
        "subcategory": project.subcategory
    })
    
    # Count products for this category/subcategory
    products_collection = get_collection(MongoDBCollections.SCRAPED_DATA)
    product_count = await products_collection.count_documents({
        "category": project.category,
        "subcategory": project.subcategory
    })
    
    return {
        "exists": recipe is not None,
        "message": "Success recipe already available. Please proceed." if recipe else "Please scrape the top 10 products in this category.",
        "product_count": product_count,
        "quota_remaining": current_user.scrape_quota,
        "category": project.category,
        "subcategory": project.subcategory
    }


@router.get("/analysis/task/{task_id}", response_model=Dict[str, Any])
async def get_analysis_task_status(
    task_id: str,
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Get the status of an analysis task
    """
    # Get task status
    task_status = await scheduler.get_task_status(task_id)
    
    if not task_status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    # Check if user has access to this task
    if current_user.role != UserRole.ADMIN and task_status.get("user_id") != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    return task_status 