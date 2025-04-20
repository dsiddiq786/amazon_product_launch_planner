from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid


class MongoBaseModel(BaseModel):
    """Base model for MongoDB documents with common fields"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "created_at": "2023-01-01T00:00:00",
                "updated_at": "2023-01-01T00:00:00"
            }
        }
    )


class CategoryHierarchy(BaseModel):
    """Model representing Amazon product category hierarchy"""
    main_category: str
    sub_categories: List[str]
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "main_category": "Home & Kitchen",
                "sub_categories": ["Kitchen & Dining", "Storage & Organization", "Cups & Mugs"]
            }
        }
    )


class ScrapedProduct(MongoBaseModel):
    """Model representing a scraped product"""
    user_id: str
    url: str
    title: str
    price: Optional[str] = None
    description: Optional[str] = None
    category_hierarchy: Optional[CategoryHierarchy] = None
    image_url: Optional[str] = None
    rating: Optional[str] = None
    review_count: Optional[str] = None
    features: Optional[List[str]] = None
    raw_data: Optional[Dict[str, Any]] = None
    analysis_results: Optional[Dict[str, Any]] = None  # Store results from each prompt block
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "user_id": "123e4567-e89b-12d3-a456-426614174002",
                "url": "https://example.com/product",
                "title": "Example Product",
                "price": 99.99,
                "description": "This is an example product",
                "category_hierarchy": {
                    "main_category": "Home & Kitchen",
                    "sub_categories": ["Kitchen & Dining", "Storage & Organization"]
                },
                "image_url": "https://example.com/image.jpg",
                "rating": 4.5,
                "review_count": 100,
                "features": ["Feature 1", "Feature 2"],
                "raw_data": {},
                "analysis_results": {
                    "keyword_strategy": "Analysis result...",
                    "pricing_insights": "Analysis result..."
                },
                "created_at": "2023-01-01T00:00:00",
                "updated_at": "2023-01-01T00:00:00"
            }
        }
    )


class Recipe(MongoBaseModel):
    """Model representing a product success recipe or master recipe"""
    user_id: str
    title: str
    content: str
    category: str
    subcategory: Optional[str] = None
    product_id: Optional[str] = None  # For product-specific recipes
    project_id: Optional[str] = None  # For project-specific recipes
    is_master: bool = False  # Flag to indicate if this is a master recipe
    prompt_block_id: Optional[str] = None  # For recipes generated from prompt blocks
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "user_id": "123e4567-e89b-12d3-a456-426614174002",
                "title": "Product Success Recipe",
                "content": "This is a recipe for product success...",
                "category": "Home & Kitchen",
                "subcategory": "Kitchen & Dining",
                "product_id": "123e4567-e89b-12d3-a456-426614174003",
                "project_id": "123e4567-e89b-12d3-a456-426614174004",
                "is_master": False,
                "prompt_block_id": "123e4567-e89b-12d3-a456-426614174005",
                "created_at": "2023-01-01T00:00:00",
                "updated_at": "2023-01-01T00:00:00"
            }
        }
    )


class PromptBlock(MongoBaseModel):
    """Model representing a prompt block within a category"""
    prompt_category: str
    block_title: str
    input_prompt: str
    output_example: str
    rerun_on_existing: bool = False
    is_active: bool = True
    user_id: Optional[str] = None  # If created by an admin
    master_recipe_prompt: Optional[str] = None  # The master recipe for this block
    analyzed_products_count: int = 0  # Count of products analyzed with this block
    limit: Optional[int] = None  # Limit the number of products to analyze
    skip: Optional[int] = None  # Skip the first N products
    sort_field: Optional[str] = "created_at"  # Field to sort by
    sort_order: Optional[str] = "desc"  # Sort order (asc or desc)
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "prompt_category": "competitor_analysis",
                "block_title": "Keyword Strategy",
                "input_prompt": "Analyze the following product for keyword opportunities: {{product_data}}",
                "output_example": "Key findings:\n1. Primary keyword: ...\n2. Secondary keywords: ...",
                "rerun_on_existing": False,
                "is_active": True,
                "user_id": "123e4567-e89b-12d3-a456-426614174002",
                "master_recipe_prompt": "Master recipe content...",
                "analyzed_products_count": 5,
                "limit": 2000,
                "skip": 0,
                "sort_field": "created_at",
                "sort_order": "desc",
                "created_at": "2023-01-01T00:00:00",
                "updated_at": "2023-01-01T00:00:00"
            }
        }
    )


class PromptBlockInput(BaseModel):
    """Input for creating or updating a prompt block"""
    prompt_category: str
    block_title: str
    input_prompt: str
    output_example: str
    rerun_on_existing: Optional[bool] = False
    is_active: Optional[bool] = True
    limit: Optional[int] = None
    skip: Optional[int] = None
    sort_field: Optional[str] = "created_at"
    sort_order: Optional[str] = "desc"
    master_recipe: Optional[str] = None


class AnalysisResult(MongoBaseModel):
    """Model representing a single product analysis result for a prompt block"""
    product_id: str
    prompt_block_id: str
    user_id: str
    input_data: Dict[str, Any]
    output: str
    model: str
    duration_ms: Optional[int] = None
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "product_id": "123e4567-e89b-12d3-a456-426614174003",
                "prompt_block_id": "123e4567-e89b-12d3-a456-426614174004",
                "user_id": "123e4567-e89b-12d3-a456-426614174002",
                "input_data": {"product_data": "Example product data"},
                "output": "Analysis result...",
                "model": "gemini-pro",
                "duration_ms": 1500,
                "created_at": "2023-01-01T00:00:00",
                "updated_at": "2023-01-01T00:00:00"
            }
        }
    )


class AnalysisTask(MongoBaseModel):
    """Model representing a product analysis task"""
    task_id: str
    product_id: str
    prompt_block_id: str
    user_id: str
    scheduled_time: datetime
    executed: bool = False
    success: Optional[bool] = None
    error: Optional[str] = None
    completed_at: Optional[datetime] = None
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "task_id": "1621234567_123e4567-e89b-12d3-a456-426614174003",
                "product_id": "123e4567-e89b-12d3-a456-426614174003",
                "prompt_block_id": "123e4567-e89b-12d3-a456-426614174004",
                "user_id": "123e4567-e89b-12d3-a456-426614174002",
                "scheduled_time": "2023-01-01T00:00:00",
                "executed": True,
                "success": True,
                "error": None,
                "completed_at": "2023-01-01T00:01:30",
                "created_at": "2023-01-01T00:00:00",
                "updated_at": "2023-01-01T00:01:30"
            }
        }
    ) 