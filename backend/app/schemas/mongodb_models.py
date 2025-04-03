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


class ScrapedProduct(MongoBaseModel):
    """Model representing a scraped product"""
    project_id: str
    user_id: str
    url: str
    title: str
    price: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None
    image_url: Optional[str] = None
    rating: Optional[str] = None
    review_count: Optional[str] = None
    features: Optional[List[str]] = None
    raw_data: Optional[Dict[str, Any]] = None
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "project_id": "123e4567-e89b-12d3-a456-426614174001",
                "user_id": "123e4567-e89b-12d3-a456-426614174002",
                "url": "https://example.com/product",
                "title": "Example Product",
                "price": 99.99,
                "description": "This is an example product",
                "category": "Electronics",
                "subcategory": "Smartphones",
                "image_url": "https://example.com/image.jpg",
                "rating": 4.5,
                "review_count": 100,
                "features": ["Feature 1", "Feature 2"],
                "raw_data": {},
                "created_at": "2023-01-01T00:00:00",
                "updated_at": "2023-01-01T00:00:00"
            }
        }
    )


class Prompt(MongoBaseModel):
    """Model representing a stored prompt for LLM interaction"""
    name: str
    description: Optional[str] = None
    content: str
    category: str  # E.g., "competitor_analysis", "launch_planner"
    is_active: bool = True
    user_id: Optional[str] = None  # If created by an admin
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "Competitor Analysis Base Prompt",
                "description": "Base prompt for analyzing competitor products",
                "content": "Analyze the following product data: {{product_data}}",
                "category": "competitor_analysis",
                "is_active": True,
                "user_id": "123e4567-e89b-12d3-a456-426614174002",
                "created_at": "2023-01-01T00:00:00",
                "updated_at": "2023-01-01T00:00:00"
            }
        }
    )


class PromptInput(BaseModel):
    """Input for creating or updating a prompt"""
    name: str
    description: Optional[str] = None
    content: str
    category: str
    is_active: Optional[bool] = True


class Recipe(MongoBaseModel):
    """Model representing a generated recipe for product launch"""
    project_id: str
    user_id: str
    product_id: Optional[str] = None  # If linked to a specific scraped product
    category: str
    subcategory: Optional[str] = None
    content: str  # The actual recipe content
    is_master: bool = False  # True if this is a master recipe for a category
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "project_id": "123e4567-e89b-12d3-a456-426614174001",
                "user_id": "123e4567-e89b-12d3-a456-426614174002",
                "product_id": "123e4567-e89b-12d3-a456-426614174003",
                "category": "Electronics",
                "subcategory": "Smartphones",
                "content": "Recipe content with launch strategy",
                "is_master": False,
                "created_at": "2023-01-01T00:00:00",
                "updated_at": "2023-01-01T00:00:00"
            }
        }
    )


class Log(MongoBaseModel):
    """Model representing a log entry for LLM interactions"""
    user_id: str
    project_id: Optional[str] = None
    prompt_id: Optional[str] = None
    prompt_content: str
    input_data: Dict[str, Any]
    output: str
    model: str
    duration_ms: Optional[int] = None
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "user_id": "123e4567-e89b-12d3-a456-426614174002",
                "project_id": "123e4567-e89b-12d3-a456-426614174001",
                "prompt_id": "123e4567-e89b-12d3-a456-426614174004",
                "prompt_content": "Analyze the following product data: {{product_data}}",
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
    user_id: str
    project_id: str
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
                "user_id": "123e4567-e89b-12d3-a456-426614174002",
                "project_id": "123e4567-e89b-12d3-a456-426614174001",
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