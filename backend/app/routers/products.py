from typing import Any, List, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from datetime import datetime
import uuid

from app.schemas.mongodb_models import ScrapedProduct, CategoryHierarchy
from app.models.user import User, UserRole
from app.database.mongodb import get_collection, MongoDBCollections
from app.utils.security import get_current_active_user
from app.services.analysis import analyze_product
from app.services.scheduler import scheduler

router = APIRouter(
    prefix="/products",
    tags=["products"],
    responses={404: {"description": "Not found"}},
)


@router.get("/count", response_model=Dict[str, int])
async def get_products_count(
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Get the total count of products
    """
    products_collection = get_collection(MongoDBCollections.PRODUCTS)
    
    # Count all products
    count = await products_collection.count_documents({})
    
    return {"count": count}


@router.get("/", response_model=List[ScrapedProduct])
async def list_products(
    skip: int = 0,
    limit: int = 100,
    category: str = None,
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    List products for the current user
    """
    products_collection = get_collection(MongoDBCollections.PRODUCTS)
    
    # Build filter
    filter_query = {"user_id": current_user.id}
    if category:
        filter_query["category_hierarchy.main_category"] = category
    
    # Get products
    cursor = products_collection.find(filter_query).skip(skip).limit(limit)
    products = await cursor.to_list(length=limit)
    
    return products


@router.post("/", response_model=ScrapedProduct)
async def create_product(
    product_data: Dict[str, Any],
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Create a new product from scraped data
    """
    products_collection = get_collection(MongoDBCollections.PRODUCTS)
    
    # Extract category hierarchy from breadcrumbs
    category_hierarchy = None
    if "breadcrumbs" in product_data:
        breadcrumbs = product_data["breadcrumbs"]
        if breadcrumbs:
            main_category = breadcrumbs[0]
            sub_categories = breadcrumbs[1:] if len(breadcrumbs) > 1 else []
            category_hierarchy = CategoryHierarchy(
                main_category=main_category,
                sub_categories=sub_categories
            )
    
    # Create new product
    now = datetime.utcnow()
    new_product = {
        "id": str(uuid.uuid4()),
        **product_data,
        "analysis_results": {},
        "created_at": now,
        "updated_at": now
    }
    
    await products_collection.insert_one(new_product)
    
    # Schedule product analysis in background
    # background_tasks.add_task(analyze_product, new_product["id"], current_user.id)
    # 🔁 Schedule background analysis using the improved scheduler
    background_tasks.add_task(
        scheduler.schedule_task,
        product_id=new_product["id"],
        user_id=current_user.id,
        project_id=new_product.get("project_id", "default"),
        delay_seconds=0,
        task_type="standard_analysis"
    )
    
    return new_product


@router.get("/{product_id}", response_model=ScrapedProduct)
async def get_product(
    product_id: str,
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Get product by ID
    """
    products_collection = get_collection(MongoDBCollections.PRODUCTS)
    product = await products_collection.find_one({
        "id": product_id,
        "user_id": current_user.id
    })
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    return product


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    Delete product
    """
    products_collection = get_collection(MongoDBCollections.PRODUCTS)
    
    # Check if product exists and belongs to user
    product = await products_collection.find_one({
        "id": product_id,
        "user_id": current_user.id
    })
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    # Delete product
    await products_collection.delete_one({"id": product_id})
    # No return value for 204 response


@router.post("/{product_id}/analyze", response_model=Dict[str, Any])
async def analyze_product_manually(
    product_id: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Manually trigger product analysis
    """
    products_collection = get_collection(MongoDBCollections.PRODUCTS)
    
    # Check if product exists and belongs to user
    product = await products_collection.find_one({
        "id": product_id,
        "user_id": current_user.id
    })
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    # Schedule product analysis in background
    background_tasks.add_task(analyze_product, product_id, current_user.id)
    
    return {"message": "Product analysis scheduled"} 