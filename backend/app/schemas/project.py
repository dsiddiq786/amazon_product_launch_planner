from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime


class ProjectBase(BaseModel):
    """Base schema for project data"""
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None


class ProjectCreate(ProjectBase):
    """Schema for creating a new project"""
    pass


class ProjectUpdate(BaseModel):
    """Schema for updating project data"""
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None
    is_active: Optional[bool] = None
    
    model_config = ConfigDict(
        extra="forbid"
    )


class ProjectInDB(ProjectBase):
    """Schema for project data stored in DB"""
    id: str
    owner_id: str
    created_at: datetime
    updated_at: datetime
    is_active: bool
    
    model_config = ConfigDict(
        from_attributes=True
    )


class Project(ProjectInDB):
    """Schema for project data returned from API"""
    pass


class ProjectList(BaseModel):
    """Schema for a list of projects"""
    projects: List[Project]
    count: int 

# Product response model
class ProductResponse(BaseModel):
    id: int
    asin: str
    title: str
    brand: str = None
    price: str = None
    rating: float = None
    image_url: str = None
    description: str = None
    best_sellers_rank: str = None
    date_first_available: str = None
    product_type: str
    created_at: datetime
    project_id: int

    class Config:
        orm_mode = True

# List response model
class ProductListResponse(BaseModel):
    products: List[ProductResponse]
    total: int