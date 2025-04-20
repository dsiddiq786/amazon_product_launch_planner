import logging
import uuid
import json
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
import asyncio

from app.database.mongodb import get_collection, MongoDBCollections
from app.utils.gemini import get_gemini_response, get_prompts_by_category, use_stored_prompt
from app.config.settings import settings

logger = logging.getLogger(__name__)

# Threshold for triggering master recipe generation
MASTER_RECIPE_THRESHOLD = 10


async def process_product_analysis(product_id: str, user_id: str, project_id: str) -> Dict[str, Any]:
    """
    Process a product analysis request in the queue
    
    Args:
        product_id: ID of the product to analyze
        user_id: ID of the user who owns the product
        project_id: ID of the project the product belongs to
        
    Returns:
        Analysis results
    """
    try:
        # Get product details
        products_collection = get_collection(MongoDBCollections.PRODUCTS)
        product = await products_collection.find_one({"id": product_id})
        
        if not product:
            logger.error(f"Product {product_id} not found")
            return {"error": f"Product {product_id} not found"}
        
        # Run competitor analysis
        analysis_results = await run_competitor_analysis(product_id, user_id, project_id)
        
        # Check if category/subcategory master recipe should be generated
        if product.get("category_hierarchy") and len(product.get("category_hierarchy", [])) >= 2:
            category = product["category_hierarchy"][0]
            subcategory = product["category_hierarchy"][1]
            
            # Check if all products in this category/subcategory are processed
            await check_category_completion(category, subcategory, user_id, project_id)
        
        return analysis_results
    
    except Exception as e:
        logger.error(f"Error processing product analysis: {str(e)}")
        return {"error": str(e)}


async def run_competitor_analysis(product_id: str, user_id: str, project_id: str) -> Dict[str, Any]:
    """
    Run competitor analysis on a product using all active prompt blocks
    """
    products_collection = get_collection(MongoDBCollections.PRODUCTS)
    prompts_collection = get_collection(MongoDBCollections.PROMPTS)
    analysis_collection = get_collection(MongoDBCollections.ANALYSIS)
    
    # Get product
    product = await products_collection.find_one({"id": product_id})
    if not product:
        raise ValueError(f"Product {product_id} not found")
    
    # Extract category and subcategory
    category = product["category_hierarchy"][0] if product.get("category_hierarchy") else ""
    subcategory = product["category_hierarchy"][1] if len(product.get("category_hierarchy", [])) > 1 else ""
    
    if not category or not subcategory:
        logger.error(f"Product {product_id} missing category or subcategory")
        await products_collection.update_one(
            {"id": product_id},
            {"$set": {"analysis_status": "failed", "analysis_error": "Missing category or subcategory", "updated_at": datetime.utcnow()}}
        )
        return {"error": "Product missing category or subcategory"}
    
    # Update product status to in_progress
    await products_collection.update_one(
        {"id": product_id},
        {"$set": {"analysis_status": "in_progress", "updated_at": datetime.utcnow()}}
    )
    
    # Get all active prompt blocks for competitor_analysis
    prompt_blocks = await prompts_collection.find({
        "is_active": True,
        "prompt_category": "competitor_analysis"
    }).to_list(length=100)
    
    if not prompt_blocks:
        await products_collection.update_one(
            {"id": product_id},
            {"$set": {"analysis_status": "failed", "analysis_error": "No active prompt blocks found", "updated_at": datetime.utcnow()}}
        )
        return {"error": "No active prompt blocks found for competitor_analysis"}
    
    # Analyze product with each prompt block
    analysis_results = {}
    for block in prompt_blocks:
        try:
            # Prepare input data
            input_data = {
                "product_data": {
                    "id": product["id"],
                    "title": product["title"],
                    "description": product.get("description", ""),
                    "price": product.get("price", ""),
                    "features": product.get("features", []),
                    "rating": product.get("rating", ""),
                    "review_count": product.get("review_count", ""),
                    "category_hierarchy": product.get("category_hierarchy", []),
                    "images": product.get("images", [])
                }
            }
            
            # Run analysis
            start_time = datetime.utcnow()
            result = await use_stored_prompt(
                prompt_id=block["id"],
                input_data=input_data,
                user_id=user_id
            )
            duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            # Store analysis result in dedicated collection
            analysis_result = {
                "id": str(uuid.uuid4()),
                "product_id": product_id,
                "project_id": project_id,
                "prompt_block_id": block["id"],
                "prompt_block_title": block["block_title"],
                "category": category,
                "subcategory": subcategory,
                "category_hierarchy": product.get("category_hierarchy", []),
                "user_id": user_id,
                "input_data": input_data,
                "output": result,
                "model": settings.DEFAULT_LLM_MODEL,
                "duration_ms": duration_ms,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            await analysis_collection.insert_one(analysis_result)
            
            # Store result in results dict
            analysis_results[block["block_title"]] = result
            
            # Update prompt block's analyzed_products_count
            await prompts_collection.update_one(
                {"id": block["id"]},
                {"$inc": {"analyzed_products_count": 1}}
            )
            
            # Create success recipe for this prompt block, category, and subcategory
            if not isinstance(result, str) or not result.startswith("Error:"):
                await create_prompt_block_success_recipe(
                    prompt_block_id=block["id"],
                    prompt_block_title=block["block_title"],
                    category=category,
                    subcategory=subcategory,
                    product_id=product_id,
                    product_title=product["title"],
                    analysis_result=result,
                    user_id=user_id,
                    project_id=project_id
                )
            
        except Exception as e:
            logger.error(f"Error analyzing product {product_id} with block {block['id']}: {str(e)}")
            analysis_results[block["block_title"]] = f"Error: {str(e)}"
    
    # Update product status to completed (only status, not storing results in product)
    await products_collection.update_one(
        {"id": product_id},
        {"$set": {"analysis_status": "completed", "updated_at": datetime.utcnow()}}
    )
    
    return analysis_results


async def create_prompt_block_success_recipe(
    prompt_block_id: str,
    prompt_block_title: str,
    category: str,
    subcategory: str,
    product_id: str,
    product_title: str,
    analysis_result: str,
    user_id: str,
    project_id: str
) -> None:
    """
    Create a success recipe for a specific prompt block, category, and subcategory
    based on a product analysis result
    """
    try:
        prompts_collection = get_collection(MongoDBCollections.PROMPTS)
        recipes_collection = get_collection(MongoDBCollections.RECIPES)
        
        # Get product recipe prompt
        prompt_doc = await prompts_collection.find_one({
            "is_active": True,
            "prompt_category": "product_recipe",
            "prompt_block_id": prompt_block_id
        })
        
        if not prompt_doc:
            # Try to get a generic product recipe prompt
            prompt_doc = await prompts_collection.find_one({
                "is_active": True,
                "prompt_category": "product_recipe"
            })
        
        if not prompt_doc:
            logger.warning(f"No active product recipe prompt found for block {prompt_block_id}, using default")
            prompt_content = "Based on the product analysis results, generate a comprehensive success recipe that highlights key strengths, strategies, and recommendations."
            prompt_id = "default-product-recipe"
        else:
            prompt_content = prompt_doc["content"]
            prompt_id = prompt_doc["id"]
        
        # Prepare input data
        input_data = {
            "product_title": product_title,
            "category": category,
            "subcategory": subcategory,
            "prompt_block_title": prompt_block_title,
            "analysis": analysis_result
        }
        
        # Generate recipe using LLM
        result = await get_gemini_response(
            prompt_content=prompt_content,
            input_data=input_data,
            prompt_id=prompt_id,
            project_id=project_id,
            user_id=user_id
        )
        
        if not result.get("success"):
            logger.error(f"Failed to create success recipe: {result.get('error')}")
            return
        
        recipe_content = result["response"]
        
        # Save recipe to database
        now = datetime.utcnow()
        
        await recipes_collection.insert_one({
            "id": str(uuid.uuid4()),
            "type": "product_recipe",
            "product_id": product_id,
            "product_title": product_title,
            "category": category,
            "subcategory": subcategory,
            "category_hierarchy": [category, subcategory],
            "prompt_block_id": prompt_block_id,
            "prompt_block_title": prompt_block_title,
            "content": recipe_content,
            "user_id": user_id,
            "project_id": project_id,
            "created_at": now,
            "updated_at": now
        })
        
        logger.info(f"Created success recipe for product {product_id} with block {prompt_block_id}")
        
    except Exception as e:
        logger.error(f"Error creating prompt block success recipe: {str(e)}")


async def check_category_completion(category: str, subcategory: str, user_id: str, project_id: str) -> None:
    """
    Check if all products in a category/subcategory have been processed
    If yes, trigger master recipe generation
    """
    products_collection = get_collection(MongoDBCollections.PRODUCTS)
    
    # Get total count of products in this category/subcategory
    total_count = await products_collection.count_documents({
        "category_hierarchy.0": category,
        "category_hierarchy.1": subcategory
    })
    
    # Get count of completed products
    completed_count = await products_collection.count_documents({
        "category_hierarchy.0": category,
        "category_hierarchy.1": subcategory,
        "analysis_status": "completed"
    })
    
    # Check if master recipe should be generated
    if completed_count >= MASTER_RECIPE_THRESHOLD and completed_count == total_count:
        # Check if master recipe already exists and needs updating
        await generate_master_recipes(category, subcategory, user_id, project_id)


async def generate_master_recipes(category: str, subcategory: str, user_id: str, project_id: str) -> None:
    """
    Generate master recipes for a category/subcategory using all active prompt blocks
    """
    try:
        logger.info(f"Generating master recipes for {category} > {subcategory}")
        
        prompts_collection = get_collection(MongoDBCollections.PROMPTS)
        recipes_collection = get_collection(MongoDBCollections.RECIPES)
        analysis_collection = get_collection(MongoDBCollections.ANALYSIS)
        
        # Get all active prompt blocks
        prompt_blocks = await prompts_collection.find({
            "is_active": True,
            "prompt_category": "competitor_analysis"
        }).to_list(length=100)
        
        # Process each prompt block to generate its master recipe
        for block in prompt_blocks:
            # Check if master recipe already exists
            existing_recipe = await recipes_collection.find_one({
                "type": "master_recipe",
                "category": category,
                "subcategory": subcategory,
                "prompt_block_id": block["id"]
            })
            
            # Get product success recipes for this category, subcategory, and prompt block
            product_recipes = await recipes_collection.find({
                "type": "product_recipe",
                "category": category,
                "subcategory": subcategory,
                "prompt_block_id": block["id"]
            }).to_list(length=100)
            
            if not product_recipes:
                # If no product recipes, try to get analysis results directly
                analysis_results = await analysis_collection.find({
                    "category": category,
                    "subcategory": subcategory,
                    "prompt_block_id": block["id"]
                }).to_list(length=100)
                
                if not analysis_results:
                    logger.warning(f"No analysis results or product recipes found for {category} > {subcategory} with prompt block {block['id']}")
                    continue
                
                # Use analysis results to generate master recipe
                input_data = {
                    "category": category,
                    "subcategory": subcategory,
                    "prompt_block_title": block["block_title"],
                    "products_count": len(analysis_results),
                    "analysis_results": [
                        {
                            "product_id": result["product_id"],
                            "product_title": result["input_data"]["product_data"]["title"],
                            "analysis": result["output"]
                        }
                        for result in analysis_results
                    ]
                }
            else:
                # Use product recipes to generate master recipe
                input_data = {
                    "category": category,
                    "subcategory": subcategory,
                    "prompt_block_title": block["block_title"],
                    "products_count": len(product_recipes),
                    "product_recipes": [
                        {
                            "product_id": recipe["product_id"],
                            "product_title": recipe["product_title"],
                            "content": recipe["content"]
                        }
                        for recipe in product_recipes
                    ]
                }
            
            try:
                # Use the master recipe prompt from the block
                master_recipe_prompt = block.get("master_recipe_prompt", "")
                if not master_recipe_prompt:
                    logger.warning(f"No master recipe prompt defined for block {block['id']}")
                    continue
                
                # Generate master recipe using LLM
                result = await get_gemini_response(
                    prompt_content=master_recipe_prompt,
                    input_data=input_data,
                    prompt_id=block["id"],
                    project_id=project_id,
                    user_id=user_id
                )
                
                if not result.get("success"):
                    logger.error(f"Failed to generate master recipe: {result.get('error')}")
                    continue
                
                master_recipe_content = result["response"]
                
                # Prepare recipe document
                now = datetime.utcnow()
                recipe_data = {
                    "type": "master_recipe",
                    "category": category,
                    "subcategory": subcategory,
                    "category_hierarchy": [category, subcategory],
                    "prompt_block_id": block["id"],
                    "prompt_block_title": block["block_title"],
                    "content": master_recipe_content,
                    "products_count": len(product_recipes) if product_recipes else len(analysis_results),
                    "product_ids": [p["product_id"] for p in (product_recipes or analysis_results)],
                    "user_id": user_id,
                    "project_id": project_id,
                    "updated_at": now
                }
                
                if existing_recipe:
                    # Update existing recipe
                    await recipes_collection.update_one(
                        {"_id": existing_recipe["_id"]},
                        {"$set": recipe_data}
                    )
                    logger.info(f"Updated master recipe for {category} > {subcategory} with block {block['id']}")
                else:
                    # Create new recipe
                    recipe_data["id"] = str(uuid.uuid4())
                    recipe_data["created_at"] = now
                    await recipes_collection.insert_one(recipe_data)
                    logger.info(f"Created master recipe for {category} > {subcategory} with block {block['id']}")
                
            except Exception as e:
                logger.error(f"Error generating master recipe for {category} > {subcategory} with block {block['id']}: {str(e)}")
    
    except Exception as e:
        logger.error(f"Error in generate_master_recipes for {category} > {subcategory}: {str(e)}")


async def get_queue_status(category: str = None, subcategory: str = None) -> Dict[str, Any]:
    """
    Get the status of the analysis queue for a category/subcategory
    
    Returns:
        Queue status information
    """
    products_collection = get_collection(MongoDBCollections.PRODUCTS)
    
    # Build query
    query = {}
    if category:
        query["category_hierarchy.0"] = category
    if subcategory:
        query["category_hierarchy.1"] = subcategory
    
    # Get counts
    total_count = await products_collection.count_documents(query)
    completed_count = await products_collection.count_documents({**query, "analysis_status": "completed"})
    in_progress_count = await products_collection.count_documents({**query, "analysis_status": "in_progress"})
    pending_count = await products_collection.count_documents({**query, "analysis_status": {"$exists": False}})
    failed_count = await products_collection.count_documents({**query, "analysis_status": "failed"})
    
    # Get master recipe status
    recipes_collection = get_collection(MongoDBCollections.RECIPES)
    master_recipe_query = {"type": "master_recipe"}
    if category:
        master_recipe_query["category"] = category
    if subcategory:
        master_recipe_query["subcategory"] = subcategory
        
    master_recipe_count = await recipes_collection.count_documents(master_recipe_query)
    
    # Get prompt block count
    prompts_collection = get_collection(MongoDBCollections.PROMPTS)
    prompt_block_count = await prompts_collection.count_documents({
        "is_active": True, 
        "prompt_category": "competitor_analysis"
    })
    
    return {
        "category": category,
        "subcategory": subcategory,
        "total_products": total_count,
        "completed_products": completed_count,
        "in_progress_products": in_progress_count,
        "pending_products": pending_count,
        "failed_products": failed_count,
        "active_prompt_blocks": prompt_block_count,
        "master_recipes_generated": master_recipe_count,
        "percentage_complete": round((completed_count / total_count) * 100, 2) if total_count > 0 else 0
    } 