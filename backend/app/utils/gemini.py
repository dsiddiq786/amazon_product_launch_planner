import time
import google.generativeai as genai
from typing import Dict, Any, List, Optional
import logging
import json
from bson import ObjectId
from datetime import datetime
from app.config.settings import settings
from app.database.mongodb import get_collection, MongoDBCollections

# Configure the Gemini API with the API key
genai.configure(api_key=settings.GEMINI_API_KEY)



def sanitize_for_json(obj: Any) -> Any:
    """Recursively convert ObjectId, datetime, etc. to serializable format"""
    if isinstance(obj, dict):
        return {k: sanitize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [sanitize_for_json(i) for i in obj]
    elif isinstance(obj, ObjectId):
        return str(obj)
    elif isinstance(obj, datetime):
        return obj.isoformat()
    else:
        return obj


async def get_gemini_response(
    prompt_content: str,
    input_data: Dict[str, Any],
    prompt_id: Optional[str] = None,
    project_id: Optional[str] = None,
    user_id: Optional[str] = None,
    temperature: float = 0.7,
    max_output_tokens: int = 1024,
    top_p: float = 0.95,
    top_k: int = 40,
) -> Dict[str, Any]:
    try:
        # --- Clean the input data ---
        sanitized_data = sanitize_for_json(input_data)

        # --- Format full prompt ---
        full_prompt = prompt_content.strip() + "\n\n---\n\n"

        if "product_data" in sanitized_data:
            full_prompt += "**Product Data:**\n"
            full_prompt += json.dumps(sanitized_data["product_data"], indent=2)
            full_prompt += "\n\n"

        if "analyses" in sanitized_data:
            full_prompt += "**Analyses:**\n"
            full_prompt += json.dumps(sanitized_data["analyses"], indent=2)
            full_prompt += "\n\n"

        if "product_success_recipes" in sanitized_data:
            full_prompt += "**Product Success Recipes:**\n"
            full_prompt += json.dumps(sanitized_data["product_success_recipes"], indent=2)
            full_prompt += "\n\n"

        if "category" in sanitized_data or "subcategory" in sanitized_data:
            full_prompt += "**Category Context:**\n"
            full_prompt += f"Category: {sanitized_data.get('category', '')}\n"
            full_prompt += f"Subcategory: {sanitized_data.get('subcategory', '')}\n"

        # --- Gemini Config ---
        generation_config = {
            "temperature": temperature,
            "top_p": top_p,
            "top_k": top_k,
            "max_output_tokens": max_output_tokens,
        }

        model = genai.GenerativeModel(settings.MODEL_NAME)
        start_time = time.time()
        response = model.generate_content(full_prompt, generation_config=generation_config)
        duration_ms = int((time.time() - start_time) * 1000)
        text_response = getattr(response, "text", str(response))

        # --- Logging ---
        if user_id:
            log_collection = get_collection(MongoDBCollections.LOGS)
            await log_collection.insert_one({
                "user_id": user_id,
                "project_id": project_id,
                "prompt_id": prompt_id,
                "prompt_content": prompt_content,
                "final_prompt_sent": full_prompt,
                "input_data": sanitized_data,
                "output": text_response,
                "model": settings.MODEL_NAME,
                "duration_ms": duration_ms,
                "created_at": time.time(),
            })

        return {
            "success": True,
            "response": text_response,
            "duration_ms": duration_ms,
            "model": settings.MODEL_NAME,
        }

    except Exception as e:
        logging.error(f"Error calling Gemini API: {e}")
        return {
            "success": False,
            "error": str(e),
            "model": settings.MODEL_NAME,
        }

# async def get_gemini_response(
#     prompt_content: str,
#     input_data: Dict[str, Any],
#     prompt_id: Optional[str] = None,
#     project_id: Optional[str] = None,
#     user_id: Optional[str] = None,
#     temperature: float = 0.7,
#     max_output_tokens: int = 1024,
#     top_p: float = 0.95,
#     top_k: int = 40,
# ) -> Dict[str, Any]:
#     """
#     Get a response from Google's Gemini API.
    
#     Args:
#         prompt_content: The prompt template to use
#         input_data: Data to inject into the prompt template
#         prompt_id: Optional ID of the stored prompt
#         project_id: Optional project ID
#         user_id: Optional user ID
#         temperature: Sampling temperature (0.0 to 1.0)
#         max_output_tokens: Maximum output length
#         top_p: Nucleus sampling parameter
#         top_k: Top-k sampling parameter
        
#     Returns:
#         Dict containing the response and metadata
#     """
#     # Format the prompt template with the input data
#     try:
#         # Simple string format for basic templates
#         formatted_prompt = prompt_content.format(**input_data)
#     except KeyError as e:
#         # If simple format fails, it might be a more complex template
#         logging.warning(f"Simple string format failed: {e}. Using as-is.")
#         formatted_prompt = prompt_content
    
#     # Set up generation config
#     generation_config = {
#         "temperature": temperature,
#         "top_p": top_p,
#         "top_k": top_k,
#         "max_output_tokens": max_output_tokens,
#     }
    
#     # Record start time for tracking duration
#     start_time = time.time()
    
#     # Call the Gemini API
#     model = genai.GenerativeModel(settings.MODEL_NAME)
    
#     try:
#         response = model.generate_content(
#             formatted_prompt,
#             generation_config=generation_config,
#         )
        
#         # Calculate duration in milliseconds
#         duration_ms = int((time.time() - start_time) * 1000)
        
#         # Extract the text response
#         if hasattr(response, 'text'):
#             text_response = response.text
#         else:
#             text_response = str(response)
        
#         # Log the interaction to MongoDB if user_id is provided
#         if user_id:
#             log_collection = get_collection(MongoDBCollections.LOGS)
#             log_entry = {
#                 "user_id": user_id,
#                 "project_id": project_id,
#                 "prompt_id": prompt_id,
#                 "prompt_content": prompt_content,
#                 "input_data": input_data,
#                 "output": text_response,
#                 "model": settings.MODEL_NAME,
#                 "duration_ms": duration_ms,
#                 "created_at": time.time(),
#             }
#             await log_collection.insert_one(log_entry)
        
#         # Return the response and metadata
#         return {
#             "success": True,
#             "response": text_response,
#             "duration_ms": duration_ms,
#             "model": settings.MODEL_NAME,
#         }
    
#     except Exception as e:
#         logging.error(f"Error calling Gemini API: {e}")
#         return {
#             "success": False,
#             "error": str(e),
#             "model": settings.MODEL_NAME,
#         }


async def get_stored_prompt(prompt_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve a stored prompt from MongoDB
    
    Args:
        prompt_id: ID of the prompt to retrieve
        
    Returns:
        The prompt document or None if not found
    """
    prompts_collection = get_collection(MongoDBCollections.PROMPTS)
    return await prompts_collection.find_one({"id": prompt_id})


async def get_prompts_by_category(category: str) -> List[Dict[str, Any]]:
    """
    Retrieve all prompts for a specific category
    
    Args:
        category: Category to filter by
        
    Returns:
        List of prompt documents
    """
    prompts_collection = get_collection(MongoDBCollections.PROMPTS)
    cursor = prompts_collection.find({"category": category, "is_active": True})
    return await cursor.to_list(length=100)


async def use_stored_prompt(
    prompt_id: str,
    input_data: Dict[str, Any],
    project_id: Optional[str] = None,
    user_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Use a stored prompt to get a response from Gemini
    
    Args:
        prompt_id: ID of the stored prompt
        input_data: Data to inject into the prompt template
        project_id: Optional project ID
        user_id: Optional user ID
        
    Returns:
        Dict containing the response and metadata
    """
    # Get the prompt from MongoDB
    prompt = await get_stored_prompt(prompt_id)
    if not prompt:
        return {
            "success": False,
            "error": f"Prompt with ID {prompt_id} not found",
        }
    
    # Call Gemini with the prompt
    return await get_gemini_response(
        prompt_content=prompt["content"],
        input_data=input_data,
        prompt_id=prompt_id,
        project_id=project_id,
        user_id=user_id,
    ) 