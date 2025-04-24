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
import re

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
    # filter_query = {"user_id": current_user.id}
    # if category:
    #     filter_query["category_hierarchy.main_category"] = category
    
    # Get products
    cursor = products_collection.find().skip(skip).limit(limit)
    products = await cursor.to_list(length=limit)
    
    return products


@router.get("/user_analyzed_products", response_model=Dict[str, Any])
async def get_user_analyzed_products(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Get all analyzed products for the current user with their analysis results
    """
    # Get collections
    prompts_collection = get_collection(MongoDBCollections.PROMPTS)
    analysis_collection = get_collection(MongoDBCollections.ANALYSIS)
    products_collection = get_collection(MongoDBCollections.PRODUCTS)

    # Find the latest market research prompt
    cursor = prompts_collection.find({
        "prompt_category": "market_research",
        "is_active": True
    }).sort("created_at", -1).limit(1)
    
    market_research_prompt = await cursor.to_list(length=1)
    
    if not market_research_prompt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No market research prompt found"
        )
    
    prompt_block_id = market_research_prompt[0]["id"]
    
    # Find all analyses for this user with the prompt block
    cursor = analysis_collection.find({
        "user_id": current_user.id,
        "prompt_block_id": prompt_block_id
    }).skip(skip).limit(limit).sort("created_at", -1)
    
    analyses = await cursor.to_list(length=limit)
    
    # Get total count for pagination
    total_count = await analysis_collection.count_documents({
        "user_id": current_user.id,
        "prompt_block_id": prompt_block_id
    })
    
    # Enrich analyses with product info
    enriched_analyses = []
    for analysis in analyses:
        product = await products_collection.find_one({
            "id": analysis["product_id"],
            "user_id": current_user.id
        })
        
        if product:
            # Add product details to analysis
            enriched_analysis = {
                "id": analysis["id"],
                "product_id": analysis["product_id"],
                "created_at": analysis["created_at"],
                "analysis": analysis["output"],
                "product_title": product.get("title", ""),
                "product_asin": product.get("asin", ""),
                "product_image": product.get("image_url", "")
            }
            enriched_analyses.append(enriched_analysis)
    
    return {
        "analyses": enriched_analyses,
        "total": total_count
    }


@router.post("/analyze_user_product", response_model=Dict[str, Any])
async def analyze_user_product(
    product_data: Dict[str, Any],
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Analyze a product from scrapped data
    """
    products_collection = get_collection(MongoDBCollections.PRODUCTS)
    prompts_collection = get_collection(MongoDBCollections.PROMPTS)
    analysis_collection = get_collection(MongoDBCollections.ANALYSIS)
    
    # Check if product exists in database by ASIN
    if "asin" in product_data:
        existing_product = await products_collection.find_one({
            "asin": product_data["asin"],
            "user_id": current_user.id
        })
        
        if existing_product:
            # Check if this product has already been analyzed
            existing_analysis = await analysis_collection.find_one({
                "product_id": existing_product["id"],
                "user_id": current_user.id
            })
            
            # if existing_analysis:
            #     return {
            #         "id": existing_product["id"],
            #         "message": "Product already analyzed",
            #         "is_analyzed": True
            #     }
            
            product_id = existing_product["id"]
        else:
            # Product does not exist, create it first
            now = datetime.utcnow()
            new_product = {
                "id": str(uuid.uuid4()),
                **product_data,
                "user_id": current_user.id,
                "analysis_results": {},
                "created_at": now,
                "updated_at": now
            }
            
            await products_collection.insert_one(new_product)
            product_id = new_product["id"]
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Product data must include ASIN"
        )
    
    # Find the latest market research prompt
    cursor = prompts_collection.find({
        "prompt_category": "market_research",
        "is_active": True
    }).sort("created_at", -1).limit(1)
    
    market_research_prompt = await cursor.to_list(length=1)
    
    if not market_research_prompt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No market research prompt found"
        )
    
    # Schedule analysis task
    background_tasks.add_task(
        scheduler.schedule_task,
        product_id=product_id,
        user_id=current_user.id,
        project_id="default",
        delay_seconds=0,
        task_type="market_research",
        prompt_block_id=market_research_prompt[0]["id"]
    )
    
    return {
        "id": product_id,
        "message": "Product analysis scheduled",
        "is_analyzed": False
    }

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

    asin = product_data.get("asin")
    existing_product = await products_collection.find_one({"asin": asin}) if asin else None
    product_description = product_data.get("description")
    clean_product_description = re.sub(r'<.*?>', '', product_description.split('See more product details')[0]).strip()
    product_data["description"] = clean_product_description

    if existing_product:
        return existing_product

    now = datetime.utcnow()
    new_product = {
        "id": str(uuid.uuid4()),
        **product_data,
        "analysis_results": {},
        "created_at": now,
        "updated_at": now
    }
    await products_collection.insert_one(new_product)

    # Schedule background analysis ONLY for new product
    background_tasks.add_task(
        scheduler.schedule_task,
        product_id=new_product["id"],
        user_id=current_user.id,
        project_id=product_data.get("project_id", "default"),
        delay_seconds=0,
        task_type="standard_analysis"
    )

    return new_product

# @router.post("/", response_model=ScrapedProduct)
# async def create_product(
#     product_data: Dict[str, Any],
#     background_tasks: BackgroundTasks,
#     current_user: User = Depends(get_current_active_user)
# ) -> Any:
#     """
#     Create a new product from scraped data
#     """
#     products_collection = get_collection(MongoDBCollections.PRODUCTS)
    
#     # Extract category hierarchy from breadcrumbs
#     category_hierarchy = None
#     if "breadcrumbs" in product_data:
#         breadcrumbs = product_data["breadcrumbs"]
#         if breadcrumbs:
#             main_category = breadcrumbs[0]
#             sub_categories = breadcrumbs[1:] if len(breadcrumbs) > 1 else []
#             category_hierarchy = CategoryHierarchy(
#                 main_category=main_category,
#                 sub_categories=sub_categories
#             )
    
#     # Create new product
#     now = datetime.utcnow()
#     new_product = {
#         "id": str(uuid.uuid4()),
#         **product_data,
#         "analysis_results": {},
#         "created_at": now,
#         "updated_at": now
#     }
    
#     await products_collection.insert_one(new_product)
    
#     # Schedule product analysis in background
#     # background_tasks.add_task(analyze_product, new_product["id"], current_user.id)
#     # 🔁 Schedule background analysis using the improved scheduler
#     # background_tasks.add_task(
#     #     scheduler.schedule_task,
#     #     product_id=new_product["id"],
#     #     user_id=current_user.id,
#     #     project_id=new_product.get("project_id", "default"),
#     #     delay_seconds=0,
#     #     task_type="standard_analysis"
#     # )
    
#     return new_product


@router.get("/{product_id}", response_model=ScrapedProduct)
async def get_product(
    product_id: str,
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Get product by ID
    """
    products_collection = get_collection(MongoDBCollections.PRODUCTS)
    
    # First try to find the product belonging to the current user
    product = await products_collection.find_one({
        "id": product_id,
        "user_id": current_user.id
    })
    
    # If not found, check if the product exists at all (for admin users)
    if not product and current_user.role == UserRole.ADMIN:
        product = await products_collection.find_one({
            "id": product_id
        })
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found or you don't have permission to view it"
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
    prompts_collection = get_collection(MongoDBCollections.PROMPTS)
    analysis_collection = get_collection(MongoDBCollections.ANALYSIS)
    
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
    
    # Find the latest market research prompt
    cursor = prompts_collection.find({
        "prompt_category": "market_research",
        "is_active": True
    }).sort("created_at", -1).limit(1)
    
    market_research_prompt = await cursor.to_list(length=1)
    
    if not market_research_prompt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No market research prompt found"
        )
    
    # Check if this product has already been analyzed
    existing_analysis = await analysis_collection.find_one({
        "product_id": product_id,
        "prompt_block_id": market_research_prompt[0]["id"],
        "user_id": current_user.id
    })
    
    if existing_analysis:
        return {
            "id": product_id,
            "message": "Product already analyzed",
            "is_analyzed": True
        }
    
    # Schedule analysis task using the scheduler
    background_tasks.add_task(
        scheduler.schedule_task,
        product_id=product_id,
        user_id=current_user.id,
        project_id=product.get("project_id", "default"),
        delay_seconds=0,
        task_type="market_research",
        prompt_block_id=market_research_prompt[0]["id"]
    )
    
    return {"message": "Product analysis scheduled"}


@router.get("/{product_id}/analysis", response_model=Dict[str, Any])
async def get_product_analysis(
    product_id: str,
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Get the analysis for a specific product
    """
    prompts_collection = get_collection(MongoDBCollections.PROMPTS)
    analysis_collection = get_collection(MongoDBCollections.ANALYSIS)
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
    
    # Find the latest market research prompt
    cursor = prompts_collection.find({
        "prompt_category": "market_research",
        "is_active": True
    }).sort("created_at", -1).limit(1)
    
    market_research_prompt = await cursor.to_list(length=1)
    
    if not market_research_prompt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No market research prompt found"
        )
    
    prompt_block_id = market_research_prompt[0]["id"]
    
    # Find the analysis for this product with the prompt block
    analysis = await analysis_collection.find_one({
        "product_id": product_id,
        "prompt_block_id": prompt_block_id,
        "user_id": current_user.id
    })
    
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis not found for this product"
        )
    
    # Return the analysis result with product info
    return {
        "id": analysis["id"],
        "product_id": product_id,
        "created_at": analysis["created_at"],
        "analysis": analysis["output"],
        "product_title": product.get("title", ""),
        "product_asin": product.get("asin", ""),
        "product_image": product.get("image_url", "")
    } 