"""
Dawood's Code

"""
import asyncio
import logging
import uuid
from datetime import datetime
from typing import Dict, Any, List

from app.database.mongodb import get_collection, MongoDBCollections
from app.utils.gemini import use_stored_prompt
from app.config.settings import settings
from app.utils.gemini import get_gemini_response

logger = logging.getLogger(__name__)

# ========== In-Memory Structures ==========

category_queues: Dict[str, List[str]] = {}
category_locks: Dict[str, asyncio.Lock] = {}

def get_category_key(main: str, sub: str) -> str:
    return f"{main}>{sub}"

# ========== STEP 1: Analyze Product ==========
PROMPT_BATCH_INTERVAL_SEC = 30  # seconds
PROMPT_BATCH_SIZE = 2

async def analyze_product(product_id: str, user_id: str) -> Dict[str, Any]:
    products = get_collection(MongoDBCollections.PRODUCTS)
    prompts = get_collection(MongoDBCollections.PROMPTS)
    analysis = get_collection(MongoDBCollections.ANALYSIS)

    product = await products.find_one({"id": product_id})
    if not product:
        raise ValueError("Product not found")

    category_hierarchy = product.get("category_hierarchy", {})
    main_category = category_hierarchy.get("main_category")
    sub_categories = category_hierarchy.get("sub_categories", [])
    if not main_category or not sub_categories:
        raise ValueError("Category hierarchy incomplete")

    subcategory = sub_categories[-1]
    category_key = get_category_key(main_category, subcategory)

    if category_key not in category_locks:
        category_locks[category_key] = asyncio.Lock()

    active_blocks = await prompts.find({
        "is_active": True,
        "prompt_category": "competitor_analysis"
    }).to_list(length=100)

    input_data = {
        "product_data": {
            "title": product.get("title"),
            "description": product.get("description"),
            "price": product.get("price"),
            "features": product.get("features"),
            "rating": product.get("rating"),
            "review_count": product.get("review_count"),
            "category": category_hierarchy
        }
    }

    analysis_results = {}

    for i in range(0, len(active_blocks), PROMPT_BATCH_SIZE):
        batch = active_blocks[i:i + PROMPT_BATCH_SIZE]
        for block in batch:
            try:
                result = await use_stored_prompt(
                    prompt_id=block["id"],
                    input_data=input_data,
                    user_id=user_id
                )
                if result.get("success") and result.get("response"):
                    if len(result["response"]) < 200:
                        print(f"Result is too short, rerunning prompt {block['id']}")
                        result = await use_stored_prompt(
                            prompt_id=block["id"],
                            input_data=input_data,
                            user_id=user_id
                        )

                # summary = await summarize_analysis_output(result, user_id)
                summary = result["response"]

                doc = {
                    "id": str(uuid.uuid4()),
                    "product_id": product_id,
                    "prompt_block_id": block["id"],
                    "user_id": user_id,
                    "input_data": input_data,
                    "output": result,
                    "summary": summary,
                    "model": settings.DEFAULT_LLM_MODEL,
                    "duration_ms": 0,
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                    "category": main_category,
                    "subcategory": subcategory
                }
                await analysis.insert_one(doc)
                analysis_results[block["block_title"]] = result
            except Exception as e:
                logger.error(f"Error analyzing prompt {block['id']}: {e}")
                analysis_results[block["block_title"]] = f"Error: {str(e)}"

        if i + PROMPT_BATCH_SIZE < len(active_blocks):
            logger.info(f"Sleeping for {PROMPT_BATCH_INTERVAL_SEC}s before next prompt batch...")
            await asyncio.sleep(PROMPT_BATCH_INTERVAL_SEC)

    await products.update_one(
        {"id": product_id},
        {"$set": {"analysis_results": analysis_results, "updated_at": datetime.utcnow()}}
    )

# async def analyze_product(product_id: str, user_id: str) -> Dict[str, Any]:
#     products = get_collection(MongoDBCollections.PRODUCTS)
#     prompts = get_collection(MongoDBCollections.PROMPTS)
#     analysis = get_collection(MongoDBCollections.ANALYSIS)

#     product = await products.find_one({"id": product_id})
#     if not product:
#         raise ValueError("Product not found")

#     category_hierarchy = product.get("category_hierarchy", {})
#     main_category = category_hierarchy.get("main_category")
#     sub_categories = category_hierarchy.get("sub_categories", [])
#     if not main_category or not sub_categories:
#         raise ValueError("Category hierarchy incomplete")

#     subcategory = sub_categories[-1]
#     category_key = get_category_key(main_category, subcategory)

#     if category_key not in category_locks:
#         category_locks[category_key] = asyncio.Lock()

#     active_blocks = await prompts.find({
#         "is_active": True,
#         "prompt_category": "competitor_analysis"
#     }).to_list(length=100)

#     input_data = {
#         "product_data": {
#             "title": product.get("title"),
#             "description": product.get("description"),
#             "price": product.get("price"),
#             "features": product.get("features"),
#             "rating": product.get("rating"),
#             "review_count": product.get("review_count"),
#             "category": category_hierarchy
#         }
#     }

#     analysis_results = {}

#     for block in active_blocks:
#         try:
#             result = await use_stored_prompt(
#                 prompt_id=block["id"],
#                 input_data=input_data,
#                 user_id=user_id
#             )

#             summary = await summarize_analysis_output(result, user_id)

#             doc = {
#                 "id": str(uuid.uuid4()),
#                 "product_id": product_id,
#                 "prompt_block_id": block["id"],
#                 "user_id": user_id,
#                 "input_data": input_data,
#                 "output": result,
#                 "summary": summary,
#                 "model": settings.DEFAULT_LLM_MODEL,
#                 "duration_ms": 0,
#                 "created_at": datetime.utcnow(),
#                 "updated_at": datetime.utcnow(),
#                 "category": main_category,
#                 "subcategory": subcategory
#             }
#             await analysis.insert_one(doc)
#             analysis_results[block["block_title"]] = result
#         except Exception as e:
#             logger.error(f"Error analyzing prompt {block['id']}: {e}")
#             analysis_results[block["block_title"]] = f"Error: {str(e)}"

#     await products.update_one(
#         {"id": product_id},
#         {"$set": {"analysis_results": analysis_results, "updated_at": datetime.utcnow()}}
#     )

# async def analyze_product(product_id: str, user_id: str) -> Dict[str, Any]:
#     products = get_collection(MongoDBCollections.PRODUCTS)
#     prompts = get_collection(MongoDBCollections.PROMPTS)
#     analysis = get_collection(MongoDBCollections.ANALYSIS)

#     product = await products.find_one({"id": product_id})
#     if not product:
#         raise ValueError("Product not found")

#     category_hierarchy = product.get("category_hierarchy", {})
#     main_category = category_hierarchy.get("main_category")
#     sub_categories = category_hierarchy.get("sub_categories", [])
#     if not main_category or not sub_categories:
#         raise ValueError("Category hierarchy incomplete")

#     subcategory = sub_categories[-1]
#     category_key = get_category_key(main_category, subcategory)

#     if category_key not in category_locks:
#         category_locks[category_key] = asyncio.Lock()

#     active_blocks = await prompts.find({
#         "is_active": True,
#         "prompt_category": "competitor_analysis"
#     }).to_list(length=100)

#     input_data = {
#         "product_data": {
#             "title": product.get("title"),
#             "description": product.get("description"),
#             "price": product.get("price"),
#             "features": product.get("features"),
#             "rating": product.get("rating"),
#             "review_count": product.get("review_count"),
#             "category": category_hierarchy
#         }
#     }

#     analysis_results = {}

#     async def run_prompt(block):
#         try:
#             result = await use_stored_prompt(
#                 prompt_id=block["id"],
#                 input_data=input_data,
#                 user_id=user_id
#             )

#             # Summarize analysis for master recipe use
#             summary = await summarize_analysis_output(result, user_id)

#             doc = {
#                 "id": str(uuid.uuid4()),
#                 "product_id": product_id,
#                 "prompt_block_id": block["id"],
#                 "user_id": user_id,
#                 "input_data": input_data,
#                 "output": result,
#                 "summary": summary,
#                 "model": settings.DEFAULT_LLM_MODEL,
#                 "duration_ms": 0,
#                 "created_at": datetime.utcnow(),
#                 "updated_at": datetime.utcnow(),
#                 "category": main_category,
#                 "subcategory": subcategory
#             }
#             await analysis.insert_one(doc)
#             analysis_results[block["block_title"]] = result
#         except Exception as e:
#             logger.error(f"Error analyzing prompt {block['id']}: {e}")
#             analysis_results[block["block_title"]] = f"Error: {str(e)}"

#     await asyncio.gather(*(run_prompt(b) for b in active_blocks))

#     await products.update_one(
#         {"id": product_id},
#         {"$set": {"analysis_results": analysis_results, "updated_at": datetime.utcnow()}}
#     )

    # ========== STEP 2: Queue product in memory ==========

    await queue_product_for_analysis(product_id, main_category, subcategory, user_id)

    return analysis_results

async def summarize_analysis_output(output: str, user_id: str) -> str:
    prompt = f"Summarize the following competitive analysis into 1-3 bullet points. here is the analysis: {output['response']}"
    response = await get_gemini_response(
        prompt_content=prompt,
        input_data={"text": output['response']},
        user_id=user_id,
        prompt_id="analysis-summary"
    )
    return response["response"] if response.get("success") else output[:300] + "..."


# ========== STEP 2: Queue Product & Trigger Master Recipe ==========

async def queue_product_for_analysis(product_id: str, main_category: str, subcategory: str, user_id: str):
    key = get_category_key(main_category, subcategory)

    if key not in category_queues:
        category_queues[key] = []

    if key not in category_locks:
        category_locks[key] = asyncio.Lock()

    async with category_locks[key]:
        category_queues[key].append(product_id)
        await check_and_generate_master_recipes(main_category, subcategory, user_id)

# ========== STEP 3: Check if All Analyzed ==========

async def check_and_generate_master_recipes(category: str, subcategory: str, user_id: str):
    products = get_collection(MongoDBCollections.PRODUCTS)
    analysis = get_collection(MongoDBCollections.ANALYSIS)
    prompts = get_collection(MongoDBCollections.PROMPTS)

    total_expected = await products.count_documents({
        "category_hierarchy.main_category": category,
        "category_hierarchy.sub_categories": subcategory
    })

    max_wait_time = 20  # seconds
    check_interval = 2  # seconds
    elapsed = 0

    while elapsed < max_wait_time:
        analyzed_ids = await analysis.distinct("product_id", {
            "category": category,
            "subcategory": subcategory
        })

        print(f"[Check] Analyzed: {len(analyzed_ids)} / Expected: {total_expected}")

        if len(analyzed_ids) >= total_expected:
            break

        await asyncio.sleep(check_interval)
        elapsed += check_interval

    # Final re-check after loop
    if len(analyzed_ids) < total_expected:
        logger.warning(f"[Timeout] Not all products analyzed for {category} > {subcategory}")
        return

    prompt_blocks = await prompts.find({
        "is_active": True,
        "prompt_category": "competitor_analysis"
    }).to_list(length=100)

    for block in prompt_blocks:
        await create_master_recipe(block, category, subcategory, user_id)


# ========== STEP 4: Create Master Recipe for Block ==========

async def create_master_recipe(block: Dict[str, Any], category: str, subcategory: str, user_id: str):
    master = get_collection(MongoDBCollections.MASTER_RECIPES)
    analysis = get_collection(MongoDBCollections.ANALYSIS)

    exists = await master.find_one({
        "prompt_block_id": block["id"],
        "category": category,
        "subcategory": subcategory
    })
    if exists:
        return

    analyses = await analysis.find({
        "prompt_block_id": block["id"],
        "category": category,
        "subcategory": subcategory
    }).to_list(length=1000)

    if not analyses:
        return

    input_data = {
        "prompt_block": {
            "master_recipe_check": True,
            "master_recipe_prompt": block.get("master_recipe_prompt")
        },
        "analysis_results": [a["output"] for a in analyses]
        # "analysis_results": [
        #     a.get("summary") or a.get("output", "")[:300]
        #     for a in analyses[:100]  # Limit to first 100 for prompt safety
        # ]
    }

    result = await use_stored_prompt(
        prompt_id=block["id"],
        input_data=input_data,
        user_id=user_id
    )

    if result.get("success") and result.get("response"):
        if len(result["response"]) < 200:
            print(f"Result is too short, rerunning master recipe prompt {block['id']}")
            result = await use_stored_prompt(
                prompt_id=block["id"],
                input_data=input_data,
                user_id=user_id
            )

    doc = {
        "id": str(uuid.uuid4()),
        "type": "master_recipe",
        "user_id": user_id,
        "prompt_block_id": block["id"],
        "category": category,
        "subcategory": subcategory,
        "content": result,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    await master.insert_one(doc)
    logger.info(f"Created master recipe for {category} > {subcategory} [block: {block['id']}]")


# ========== Market Research Analysis ==========

async def perform_market_research_analysis(product_id: str, user_id: str, prompt_block_id: str) -> Dict[str, Any]:
    """
    Perform market research analysis for a specific product using the specified prompt.
    
    Args:
        product_id: The ID of the product to analyze
        user_id: The ID of the user who owns the product
        prompt_block_id: The ID of the prompt block to use for analysis
        
    Returns:
        Dict containing the analysis results
    """
    products = get_collection(MongoDBCollections.PRODUCTS)
    prompts = get_collection(MongoDBCollections.PROMPTS)
    analysis = get_collection(MongoDBCollections.ANALYSIS)
    
    # Get the product
    product = await products.find_one({"id": product_id})
    if not product:
        logger.error(f"Product not found: {product_id}")
        return {"error": "Product not found"}
    
    # Get the prompt block
    prompt_block = await prompts.find_one({"id": prompt_block_id})
    if not prompt_block:
        logger.error(f"Prompt block not found: {prompt_block_id}")
        return {"error": "Prompt block not found"}
    
    logger.info(f"Starting market research analysis for product {product_id} with prompt {prompt_block_id}")
    
    # Prepare input data for the LLM
    input_data = {
        "product_data": {
            "title": product.get("title", ""),
            "description": product.get("description", ""),
            "price": product.get("price", ""),
            "features": product.get("features", []),
            "rating": product.get("rating", 0),
            "review_count": product.get("review_count", 0),
            "category": product.get("category_hierarchy", {})
        }
    }
    
    try:
        # Use the stored prompt to analyze the product
        result = await use_stored_prompt(
            prompt_id=prompt_block_id,
            input_data=input_data,
            user_id=user_id
        )
        
        # Create an analysis document
        analysis_doc = {
            "id": str(uuid.uuid4()),
            "product_id": product_id,
            "prompt_block_id": prompt_block_id,
            "user_id": user_id,
            "input_data": input_data,
            "output": result,
            "model": settings.DEFAULT_LLM_MODEL,
            "duration_ms": result.get("duration_ms", 0),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        # Store the analysis
        await analysis.insert_one(analysis_doc)
        
        # Update the product with some analysis information
        await products.update_one(
            {"id": product_id},
            {"$set": {
                "analysis_status": "completed",
                "analyzed_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }}
        )
        
        logger.info(f"Market research analysis completed for product {product_id}")
        return analysis_doc
        
    except Exception as e:
        logger.error(f"Error performing market research analysis: {str(e)}")
        
        # Update the product with error status
        await products.update_one(
            {"id": product_id},
            {"$set": {
                "analysis_status": "error",
                "analysis_error": str(e),
                "updated_at": datetime.utcnow()
            }}
        )
        
        return {"error": str(e)}



"""
Cursor CODE
"""
# import logging
# import uuid
# import json
# from datetime import datetime
# from typing import Dict, Any, List, Optional
# import asyncio

# from app.database.mongodb import get_collection, MongoDBCollections
# from app.utils.gemini import get_gemini_response, get_prompts_by_category, use_stored_prompt
# from app.config.settings import settings

# logger = logging.getLogger(__name__)

# RECIPE_GENERATION_THRESHOLD = 10


# def get_default_recipe_prompt(prompt_type: str) -> Dict[str, str]:
#     """
#     Fallback prompt generator if no saved prompt exists in DB.
#     """
#     if prompt_type == "product_recipe":
#         return {
#             "id": "default-product-recipe",
#             "content": "Given the product data and the analysis results, generate a clear, actionable success recipe highlighting key strengths and strategies for success."
#         }
#     elif prompt_type == "category_recipe":
#         return {
#             "id": "default-category-recipe",
#             "content": "You are given a list of successful product recipes within a specific category and subcategory. Summarize common winning strategies, patterns, and recommendations in a single master recipe."
#         }
#     else:
#         raise ValueError(f"Unsupported prompt type: {prompt_type}")
    

# def format_prompt(template: str, input_data: Dict[str, Any]) -> str:
#     # Simple recursive string formatter
#     return template.replace("{{ product_data }}", json.dumps(input_data.get("product_data", ""), indent=2)) \
#                    .replace("{{ analyses }}", json.dumps(input_data.get("analyses", ""), indent=2)) \
#                    .replace("{{ product_success_recipes }}", json.dumps(input_data.get("product_success_recipes", ""), indent=2)) \
#                    .replace("{{ category }}", input_data.get("category", "")) \
#                    .replace("{{ subcategory }}", input_data.get("subcategory", ""))


# async def analyze_product(product_id: str, user_id: str) -> Dict[str, Any]:
#     """
#     Analyze a product using all active prompt blocks in its category
#     """
#     products_collection = get_collection(MongoDBCollections.PRODUCTS)
#     prompts_collection = get_collection(MongoDBCollections.PROMPTS)
#     analysis_collection = get_collection(MongoDBCollections.ANALYSIS)
    
#     # Get product
#     product = await products_collection.find_one({"id": product_id})
#     if not product:
#         raise ValueError(f"Product {product_id} not found")
    
#     # print(product)
#     # Get all active prompt blocks for the competitor_analysis
#     prompt_blocks = await prompts_collection.find({
#         "is_active": True,
#         "prompt_category": "competitor_analysis"
#     }).to_list(length=100)
    
#     # print(prompt_blocks)
#     if not prompt_blocks:
#         return {"message": "No active prompt blocks found for this category"}
    
#     print("RECEIVED ANALYZE PRODUCT REQUEST")
#     # Analyze product with each prompt block
#     analysis_results = {}
#     for block in prompt_blocks:
#         try:
#             # Prepare input data
#             input_data = {
#                 "product_data": {
#                     "title": product["title"],
#                     "description": product.get("description"),
#                     "price": product.get("price"),
#                     "features": product.get("features"),
#                     "rating": product.get("rating"),
#                     "review_count": product.get("review_count"),
#                     "category": product["category_hierarchy"]
#                 }
#             }
            
#             # Run analysis
#             start_time = datetime.utcnow()
#             result = await use_stored_prompt(
#                 prompt_id=block["id"],
#                 input_data=input_data,
#                 user_id=user_id
#             )
#             duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
#             # Store analysis result
#             analysis_result = {
#                 "id": str(uuid.uuid4()),
#                 "product_id": product_id,
#                 "prompt_block_id": block["id"],
#                 "user_id": user_id,
#                 "input_data": input_data,
#                 "output": result,
#                 "model": settings.DEFAULT_LLM_MODEL,
#                 "duration_ms": duration_ms,
#                 "created_at": datetime.utcnow(),
#                 "updated_at": datetime.utcnow()
#             }
#             await analysis_collection.insert_one(analysis_result)
            
#             # Store result in product's analysis_results
#             analysis_results[block["block_title"]] = result
            
#             # Update prompt block's analyzed_products_count
#             await prompts_collection.update_one(
#                 {"id": block["id"]},
#                 {"$inc": {"analyzed_products_count": 1}}
#             )
            
#             # Check if we should update the master recipe
#             if block["analyzed_products_count"] + 1 >= settings.MIN_PRODUCTS_FOR_MASTER_RECIPE:
#                 await update_master_recipe(block["id"])
            
#         except Exception as e:
#             print(f"Error analyzing product {product_id} with block {block['id']}: {str(e)}")
#             analysis_results[block["block_title"]] = f"Error: {str(e)}"
    
#     # Update product with analysis results
#     await products_collection.update_one(
#         {"id": product_id},
#         {
#             "$set": {
#                 "analysis_results": analysis_results,
#                 "updated_at": datetime.utcnow()
#             }
#         }
#     )
    
#     return analysis_results


# async def update_master_recipe(prompt_block_id: str) -> None:
#     """
#     Update the master recipe for a prompt block based on all analysis results
#     """
#     prompts_collection = get_collection(MongoDBCollections.PROMPTS)
#     analysis_collection = get_collection(MongoDBCollections.ANALYSIS)
    
#     # Get prompt block
#     block = await prompts_collection.find_one({"id": prompt_block_id})
#     if not block:
#         raise ValueError(f"Prompt block {prompt_block_id} not found")
    
#     # Get all analysis results for this block
#     analysis_results = await analysis_collection.find({
#         "prompt_block_id": prompt_block_id
#     }).to_list(length=100)
    
#     if not analysis_results:
#         return
    
#     # Prepare input for master recipe generation
#     input_data = {
#         "prompt_block": {
#             "master_recipe_check": True,
#             "master_recipe_prompt": block["master_recipe_prompt"]
#         },
#         "analysis_results": [result["output"] for result in analysis_results]
#     }
    
#     # Generate master recipe using LLM
#     master_recipe = await use_stored_prompt(
#         prompt_id=prompt_block_id,
#         input_data=input_data,
#         user_id=block["user_id"]
#     )
    
#     # Update prompt block with new master recipe
#     await prompts_collection.update_one(
#         {"id": prompt_block_id},
#         {
#             "$set": {
#                 "master_recipe": master_recipe,
#                 "updated_at": datetime.utcnow()
#             }
#         }
#     )


# async def rerun_analysis_for_block(prompt_block_id: str) -> None:
#     """
#     Rerun analysis for all products using a specific prompt block
#     """
#     prompts_collection = get_collection(MongoDBCollections.PROMPTS)
#     products_collection = get_collection(MongoDBCollections.PRODUCTS)
    
#     # Get prompt block
#     block = await prompts_collection.find_one({"id": prompt_block_id})
#     if not block:
#         raise ValueError(f"Prompt block {prompt_block_id} not found")
    
#     # Build query for products
#     query = {
#         "category_hierarchy.main_category": block["prompt_category"]
#     }
    
#     # Build sort criteria
#     sort_field = block.get("sort_field", "created_at")
#     sort_order = block.get("sort_order", "desc")
#     sort_direction = -1 if sort_order == "desc" else 1
#     sort_criteria = [(sort_field, sort_direction)]
    
#     # Get products with pagination and sorting
#     products = await products_collection.find(query).sort(sort_criteria).skip(block.get("skip", 0)).limit(block.get("limit", 2000)).to_list(length=None)
    
#     # Rerun analysis for each product
#     for product in products:
#         try:
#             await analyze_product(product["id"], product["user_id"])
#         except Exception as e:
#             print(f"Error rerunning analysis for product {product['id']}: {str(e)}")
#             continue


# async def create_product_success_recipe(product_id: str, user_id: str, project_id: str, product: Dict[str, Any], analyses: List[str]) -> None:
#     try:
#         prompts = await get_prompts_by_category("product_recipe")
#         prompt = next((p for p in prompts if p.get("is_active", True)), None) or get_default_recipe_prompt("product_recipe")

#         input_data = {
#             "product_data": product,
#             "analyses": analyses
#         }

#         response = await get_gemini_response(
#             prompt_content=prompt["content"],
#             input_data=input_data,
#             prompt_id=prompt["id"],
#             project_id=project_id,
#             user_id=user_id,
#         )

#         if not response.get("success"):
#             logger.error(f"Failed to create success recipe for product {product_id}: {response.get('error')}")
#             return

#         recipes_collection = get_collection(MongoDBCollections.RECIPES)
#         now = datetime.utcnow()
#         recipe = {
#             "id": str(uuid.uuid4()),
#             "type": "success_recipe",
#             "product_id": product_id,
#             "project_id": project_id,
#             "user_id": user_id,
#             "category": product.get("category", ""),
#             "subcategory": product.get("subcategory", ""),
#             "content": response["response"],
#             "created_at": now,
#             "updated_at": now,
#         }
#         await recipes_collection.insert_one(recipe)
#         logger.info(f"Product success recipe created for product {product_id}")

#     except Exception as e:
#         logger.error(f"Exception while creating product success recipe: {str(e)}")


# async def check_and_generate_master_recipe(category: str, subcategory: str, user_id: str) -> None:
#     try:
#         if not category or not subcategory:
#             return

#         master_recipes_collection = get_collection(MongoDBCollections.MASTER_RECIPES)
#         exists = await master_recipes_collection.find_one({"category": category, "subcategory": subcategory})
#         if exists:
#             logger.info(f"Master recipe already exists for {category} > {subcategory}")
#             return

#         recipes_collection = get_collection(MongoDBCollections.RECIPES)
#         count = await recipes_collection.count_documents({
#             "type": "success_recipe",
#             "category": category,
#             "subcategory": subcategory
#         })

#         if count < RECIPE_GENERATION_THRESHOLD:
#             logger.info(f"Threshold not met for {category} > {subcategory}: {count}/{RECIPE_GENERATION_THRESHOLD}")
#             return

#         cursor = recipes_collection.find({
#             "type": "success_recipe",
#             "category": category,
#             "subcategory": subcategory
#         })
#         all_recipes = await cursor.to_list(length=RECIPE_GENERATION_THRESHOLD)
#         recipe_contents = [r["content"] for r in all_recipes]

#         prompts = await get_prompts_by_category("category_recipe")
#         prompt = next((p for p in prompts if p.get("is_active", True)), None) or get_default_recipe_prompt("category_recipe")

#         input_data = {
#             "category": category,
#             "subcategory": subcategory,
#             "product_success_recipes": recipe_contents
#         }

#         response = await get_gemini_response(
#             prompt_content=prompt["content"],
#             input_data=input_data,
#             prompt_id=prompt["id"],
#             user_id=user_id,
#         )

#         if not response.get("success"):
#             logger.error(f"Failed to generate master recipe for {category} > {subcategory}: {response.get('error')}")
#             return

#         master_recipe = {
#             "id": str(uuid.uuid4()),
#             "type": "master_recipe",
#             "user_id": user_id,
#             "category": category,
#             "subcategory": subcategory,
#             "content": response["response"],
#             "created_at": datetime.utcnow(),
#             "updated_at": datetime.utcnow()
#         }

#         await master_recipes_collection.insert_one(master_recipe)
#         logger.info(f"Master recipe created for {category} > {subcategory}")

#     except Exception as e:
#         logger.error(f"Exception in check_and_generate_master_recipe: {str(e)}")