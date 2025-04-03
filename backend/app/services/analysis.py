import logging
import uuid
import json
from datetime import datetime
from typing import Dict, Any, List, Optional

from app.database.mongodb import get_collection, MongoDBCollections
from app.utils.gemini import get_gemini_response, get_prompts_by_category

logger = logging.getLogger(__name__)

RECIPE_GENERATION_THRESHOLD = 10


def get_default_recipe_prompt(prompt_type: str) -> Dict[str, str]:
    """
    Fallback prompt generator if no saved prompt exists in DB.
    """
    if prompt_type == "product_recipe":
        return {
            "id": "default-product-recipe",
            "content": "Given the product data and the analysis results, generate a clear, actionable success recipe highlighting key strengths and strategies for success."
        }
    elif prompt_type == "category_recipe":
        return {
            "id": "default-category-recipe",
            "content": "You are given a list of successful product recipes within a specific category and subcategory. Summarize common winning strategies, patterns, and recommendations in a single master recipe."
        }
    else:
        raise ValueError(f"Unsupported prompt type: {prompt_type}")
    

def format_prompt(template: str, input_data: Dict[str, Any]) -> str:
    # Simple recursive string formatter
    return template.replace("{{ product_data }}", json.dumps(input_data.get("product_data", ""), indent=2)) \
                   .replace("{{ analyses }}", json.dumps(input_data.get("analyses", ""), indent=2)) \
                   .replace("{{ product_success_recipes }}", json.dumps(input_data.get("product_success_recipes", ""), indent=2)) \
                   .replace("{{ category }}", input_data.get("category", "")) \
                   .replace("{{ subcategory }}", input_data.get("subcategory", ""))


async def analyze_product(product_id: str, user_id: str, project_id: str) -> Optional[Dict[str, Any]]:
    try:
        products_collection = get_collection(MongoDBCollections.SCRAPED_DATA)
        product = await products_collection.find_one({"id": product_id})
        
        print(product)

        if not product:
            logger.error(f"Product not found: {product_id}")
            return None

        prompts = await get_prompts_by_category("competitor_analysis")
        if not prompts:
            logger.error("No competitor analysis prompts found in DB")
            return None

        analyses_collection = get_collection(MongoDBCollections.ANALYSIS)
        now = datetime.utcnow()
        all_responses = []

        for prompt in prompts:
            input_data = {
                "product_data": product
            }

            response = await get_gemini_response(
                prompt_content=prompt["content"],
                input_data=input_data,
                prompt_id=prompt["id"],
                project_id=project_id,
                user_id=user_id,
            )

            if not response.get("success"):
                logger.error(f"Prompt failed: {prompt['id']} - {response.get('error')}")
                continue

            analysis_entry = {
                "id": str(uuid.uuid4()),
                "product_id": product_id,
                "project_id": project_id,
                "user_id": user_id,
                "prompt_id": prompt["id"],
                "category": product.get("project_category", ""),
                "subcategory": product.get("project_subcategory", ""),
                "content": response["response"],
                "created_at": now,
                "updated_at": now,
            }
            all_responses.append(response["response"])
            await analyses_collection.insert_one(analysis_entry)

        if all_responses:
            logger.info(f"All prompts analyzed for product {product_id}, creating product success recipe")
            await create_product_success_recipe(product_id, user_id, project_id, product, all_responses)
            await check_and_generate_master_recipe(product.get("project_category", ""), product.get("project_subcategory", ""), user_id)

        return {"status": "completed"}

    except Exception as e:
        logger.error(f"Error analyzing product {product_id}: {str(e)}")
        return None


async def create_product_success_recipe(product_id: str, user_id: str, project_id: str, product: Dict[str, Any], analyses: List[str]) -> None:
    try:
        prompts = await get_prompts_by_category("product_recipe")
        prompt = next((p for p in prompts if p.get("is_active", True)), None) or get_default_recipe_prompt("product_recipe")

        input_data = {
            "product_data": product,
            "analyses": analyses
        }

        response = await get_gemini_response(
            prompt_content=prompt["content"],
            input_data=input_data,
            prompt_id=prompt["id"],
            project_id=project_id,
            user_id=user_id,
        )

        if not response.get("success"):
            logger.error(f"Failed to create success recipe for product {product_id}: {response.get('error')}")
            return

        recipes_collection = get_collection(MongoDBCollections.RECIPES)
        now = datetime.utcnow()
        recipe = {
            "id": str(uuid.uuid4()),
            "type": "success_recipe",
            "product_id": product_id,
            "project_id": project_id,
            "user_id": user_id,
            "category": product.get("category", ""),
            "subcategory": product.get("subcategory", ""),
            "content": response["response"],
            "created_at": now,
            "updated_at": now,
        }
        await recipes_collection.insert_one(recipe)
        logger.info(f"Product success recipe created for product {product_id}")

    except Exception as e:
        logger.error(f"Exception while creating product success recipe: {str(e)}")


async def check_and_generate_master_recipe(category: str, subcategory: str, user_id: str) -> None:
    try:
        if not category or not subcategory:
            return

        master_recipes_collection = get_collection(MongoDBCollections.MASTER_RECIPES)
        exists = await master_recipes_collection.find_one({"category": category, "subcategory": subcategory})
        if exists:
            logger.info(f"Master recipe already exists for {category} > {subcategory}")
            return

        recipes_collection = get_collection(MongoDBCollections.RECIPES)
        count = await recipes_collection.count_documents({
            "type": "success_recipe",
            "category": category,
            "subcategory": subcategory
        })

        if count < RECIPE_GENERATION_THRESHOLD:
            logger.info(f"Threshold not met for {category} > {subcategory}: {count}/{RECIPE_GENERATION_THRESHOLD}")
            return

        cursor = recipes_collection.find({
            "type": "success_recipe",
            "category": category,
            "subcategory": subcategory
        })
        all_recipes = await cursor.to_list(length=RECIPE_GENERATION_THRESHOLD)
        recipe_contents = [r["content"] for r in all_recipes]

        prompts = await get_prompts_by_category("category_recipe")
        prompt = next((p for p in prompts if p.get("is_active", True)), None) or get_default_recipe_prompt("category_recipe")

        input_data = {
            "category": category,
            "subcategory": subcategory,
            "product_success_recipes": recipe_contents
        }

        response = await get_gemini_response(
            prompt_content=prompt["content"],
            input_data=input_data,
            prompt_id=prompt["id"],
            user_id=user_id,
        )

        if not response.get("success"):
            logger.error(f"Failed to generate master recipe for {category} > {subcategory}: {response.get('error')}")
            return

        master_recipe = {
            "id": str(uuid.uuid4()),
            "type": "master_recipe",
            "user_id": user_id,
            "category": category,
            "subcategory": subcategory,
            "content": response["response"],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }

        await master_recipes_collection.insert_one(master_recipe)
        logger.info(f"Master recipe created for {category} > {subcategory}")

    except Exception as e:
        logger.error(f"Exception in check_and_generate_master_recipe: {str(e)}")


# import logging
# import uuid
# from datetime import datetime
# from typing import Dict, Any, List, Optional

# from app.database.mongodb import get_collection, MongoDBCollections
# from app.utils.gemini import get_gemini_response, get_prompts_by_category

# logger = logging.getLogger(__name__)


# async def analyze_product(product_id: str, user_id: str, project_id: str) -> Optional[Dict[str, Any]]:
#     """
#     Analyze a scraped product using Gemini API and generate a recipe
    
#     Args:
#         product_id: ID of the product to analyze
#         user_id: ID of the user who owns the product
#         project_id: ID of the project the product belongs to
        
#     Returns:
#         Generated recipe or None if failed
#     """
#     try:
#         # Get product data
#         products_collection = get_collection(MongoDBCollections.SCRAPED_DATA)
#         product = await products_collection.find_one({"id": product_id})
        
#         if not product:
#             logger.error(f"Product not found: {product_id}")
#             return None
        
#         # Get competitor analysis prompts
#         prompts = await get_prompts_by_category("competitor_analysis")
#         if not prompts:
#             logger.error("No competitor analysis prompts found")
#             return None
        
#         # Use the first active prompt (in a real app, you might want to select the specific prompt)
#         prompt = next((p for p in prompts if p.get("is_active", True)), None)
#         if not prompt:
#             logger.error("No active competitor analysis prompts found")
#             return None
        
#         # Prepare input data for the prompt
#         input_data = {
#             "product_data": {
#                 "title": product.get("title", ""),
#                 "description": product.get("description", ""),
#                 "features": product.get("features", []),
#                 "price": product.get("price", ""),
#                 "category": product.get("category", ""),
#                 "subcategory": product.get("subcategory", ""),
#                 "rating": product.get("rating", ""),
#                 "review_count": product.get("review_count", ""),
#             }
#         }
        
#         # Call Gemini API
#         response = await get_gemini_response(
#             prompt_content=prompt["content"],
#             input_data=input_data,
#             prompt_id=prompt["id"],
#             project_id=project_id,
#             user_id=user_id,
#         )
        
#         if not response.get("success"):
#             logger.error(f"Failed to get response from Gemini API: {response.get('error')}")
#             return None
        
#         # Create recipe
#         recipes_collection = get_collection(MongoDBCollections.RECIPES)
#         now = datetime.utcnow()
        
#         recipe = {
#             "id": str(uuid.uuid4()),
#             "project_id": project_id,
#             "user_id": user_id,
#             "product_id": product_id,
#             "category": product.get("category", ""),
#             "subcategory": product.get("subcategory", ""),
#             "content": response["response"],
#             "created_at": now,
#             "updated_at": now
#         }
        
#         # Save recipe to database
#         await recipes_collection.insert_one(recipe)
        
#         # Check if we should generate a master recipe
#         await check_and_generate_master_recipe(
#             category=product.get("category", ""),
#             subcategory=product.get("subcategory", ""),
#             user_id=user_id
#         )
        
#         return recipe
    
#     except Exception as e:
#         logger.error(f"Error analyzing product: {str(e)}")
#         return None


# async def check_and_generate_master_recipe(category: str, subcategory: str, user_id: str) -> None:
#     """
#     Check if there are enough product recipes to generate a master recipe,
#     and generate it if needed
    
#     Args:
#         category: Product category
#         subcategory: Product subcategory
#         user_id: User ID
#     """
#     if not category or not subcategory:
#         return
    
#     # Check if master recipe already exists
#     master_recipes_collection = get_collection(MongoDBCollections.MASTER_RECIPES)
#     master_recipe = await master_recipes_collection.find_one({
#         "category": category,
#         "subcategory": subcategory
#     })
    
#     if master_recipe:
#         # Master recipe already exists
#         return
    
#     # Count product recipes for this category/subcategory
#     recipes_collection = get_collection(MongoDBCollections.RECIPES)
#     product_recipes_count = await recipes_collection.count_documents({
#         "category": category,
#         "subcategory": subcategory
#     })
    
#     # Check if we have enough recipes to generate a master recipe
#     # In a real app, this threshold might be configurable
#     if product_recipes_count >= 5:
#         await generate_master_recipe(category, subcategory, user_id)


# async def generate_master_recipe(category: str, subcategory: str, user_id: str) -> Optional[Dict[str, Any]]:
#     """
#     Generate a master recipe for a category/subcategory by analyzing all product recipes
    
#     Args:
#         category: Product category
#         subcategory: Product subcategory
#         user_id: User ID
        
#     Returns:
#         Generated master recipe or None if failed
#     """
#     try:
#         # Get all product recipes for this category/subcategory
#         recipes_collection = get_collection(MongoDBCollections.RECIPES)
#         cursor = recipes_collection.find({
#             "category": category,
#             "subcategory": subcategory
#         })
        
#         product_recipes = await cursor.to_list(length=100)
        
#         if not product_recipes:
#             logger.error(f"No product recipes found for category: {category}, subcategory: {subcategory}")
#             return None
        
#         # Get launch planner prompts
#         prompts = await get_prompts_by_category("launch_planner")
#         if not prompts:
#             logger.error("No launch planner prompts found")
#             return None
        
#         # Use the first active prompt
#         prompt = next((p for p in prompts if p.get("is_active", True)), None)
#         if not prompt:
#             logger.error("No active launch planner prompts found")
#             return None
        
#         # Prepare input data for the prompt
#         recipe_contents = [recipe["content"] for recipe in product_recipes]
        
#         input_data = {
#             "category": category,
#             "subcategory": subcategory,
#             "product_recipes": recipe_contents
#         }
        
#         # Call Gemini API
#         response = await get_gemini_response(
#             prompt_content=prompt["content"],
#             input_data=input_data,
#             prompt_id=prompt["id"],
#             user_id=user_id,
#         )
        
#         if not response.get("success"):
#             logger.error(f"Failed to get response from Gemini API: {response.get('error')}")
#             return None
        
#         # Create master recipe
#         master_recipes_collection = get_collection(MongoDBCollections.MASTER_RECIPES)
#         now = datetime.utcnow()
        
#         master_recipe = {
#             "id": str(uuid.uuid4()),
#             "user_id": user_id,
#             "category": category,
#             "subcategory": subcategory,
#             "content": response["response"],
#             "created_at": now,
#             "updated_at": now
#         }
        
#         # Save master recipe to database
#         await master_recipes_collection.insert_one(master_recipe)
        
#         logger.info(f"Generated master recipe for category: {category}, subcategory: {subcategory}")
        
#         return master_recipe
    
#     except Exception as e:
#         logger.error(f"Error generating master recipe: {str(e)}")
#         return None