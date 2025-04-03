from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
import uuid

from app.schemas.project import Project, ProjectCreate, ProjectUpdate, ProjectList, ProductListResponse, ProductResponse
from app.models.project import Project as ProjectModel
from app.models.user import User, UserRole
from app.database.postgresql import get_db
from app.utils.security import get_current_active_user,get_current_admin_user
from app.database.mongodb import get_collection, MongoDBCollections
from app.schemas.user import User

router = APIRouter(
    prefix="/projects",
    tags=["projects"],
    responses={404: {"description": "Not found"}},
)


@router.get("/", response_model=ProjectList)
async def list_projects(
    skip: int = 0,
    limit: int = 100,
    search: str = Query(None, description="Search in project name and description"),
    category: str = Query(None, description="Filter by category"),
    subcategory: str = Query(None, description="Filter by subcategory"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Retrieve user's projects (admin can see all projects)
    """
    query = db.query(ProjectModel)
    
    # Regular users can only see their own projects
    if current_user.role != UserRole.ADMIN:
        query = query.filter(ProjectModel.owner_id == current_user.id)
    
    # Apply filters if provided
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (ProjectModel.name.ilike(search_term)) |
            (ProjectModel.description.ilike(search_term))
        )
    
    if category:
        query = query.filter(ProjectModel.category == category)
    
    if subcategory:
        query = query.filter(ProjectModel.subcategory == subcategory)
    
    # Get total count for pagination
    total_count = query.count()
    
    # Apply pagination
    projects = query.offset(skip).limit(limit).all()
    
    return {
        "projects": projects,
        "count": total_count
    }


@router.post("/", response_model=Project)
async def create_project(
    project_data: ProjectCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Create a new project
    """
    # Create project
    new_project = ProjectModel(
        id=str(uuid.uuid4()),
        name=project_data.name,
        description=project_data.description,
        category=project_data.category,
        subcategory=project_data.subcategory,
        owner_id=current_user.id
    )
    
    db.add(new_project)
    db.commit()
    db.refresh(new_project)
    
    return new_project


@router.get("/{project_id}", response_model=Project)
async def get_project(
    project_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get project by ID
    """
    project = db.query(ProjectModel).filter(ProjectModel.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Check if user has permission to access this project
    if current_user.role != UserRole.ADMIN and project.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    return project


@router.put("/{project_id}", response_model=Project)
async def update_project(
    project_id: str,
    project_data: ProjectUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Update project
    """
    project = db.query(ProjectModel).filter(ProjectModel.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Check if user has permission to update this project
    if current_user.role != UserRole.ADMIN and project.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Update project fields
    update_data = project_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(project, field, value)
    
    db.commit()
    db.refresh(project)
    
    return project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Delete project
    """
    project = db.query(ProjectModel).filter(ProjectModel.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Check if user has permission to delete this project
    if current_user.role != UserRole.ADMIN and project.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    db.delete(project)
    db.commit()
    # No return value for 204 response


@router.get("/categories/list", response_model=List[str])
async def list_categories(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get list of unique project categories
    """
    # Regular users only see categories from their projects
    query = db.query(ProjectModel.category).distinct()
    if current_user.role != UserRole.ADMIN:
        query = query.filter(ProjectModel.owner_id == current_user.id)
    
    categories = [cat[0] for cat in query.all() if cat[0]]  # Filter out None values
    return categories


@router.get("/subcategories/{category}", response_model=List[str])
async def list_subcategories(
    category: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get list of unique project subcategories for a specific category
    """
    # Regular users only see subcategories from their projects
    query = db.query(ProjectModel.subcategory).filter(
        ProjectModel.category == category
    ).distinct()
    
    if current_user.role != UserRole.ADMIN:
        query = query.filter(ProjectModel.owner_id == current_user.id)
    
    subcategories = [subcat[0] for subcat in query.all() if subcat[0]]  # Filter out None values
    return subcategories 


@router.get("/{project_id}/products/list", response_model=dict)
async def get_project_products(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    # Check if project exists and belongs to user
    # Check if current user is admin
    is_admin = current_user.role == "admin"  # Adjust this field name if different

    # Fetch project based on role
    if is_admin:
        project = db.query(ProjectModel).filter(ProjectModel.id == project_id).first()
    else:
        project = db.query(ProjectModel).filter(
            ProjectModel.id == project_id,
            ProjectModel.owner_id == current_user.id
        ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Get products from MongoDB collection
    products_collection = get_collection(MongoDBCollections.SCRAPED_DATA)
    
    # Query products for this project
    cursor = products_collection.find({"project_id": project_id})
    products = await cursor.to_list(length=None)
    
    # Convert products to response format
    product_list = []
    for product in products:
        product_dict = {
            "id": str(product.get("_id")),
            "asin": product.get("asin"),
            "title": product.get("title"),
            "brand": product.get("brand"),
            "price": product.get("price"),
            "rating": product.get("rating"),
            "image_url": product.get("image_url"),
            # "description": product.get("description"),
            "best_sellers_rank": product.get("best_sellers_rank"),
            "date_first_available": product.get("date_first_available"),
            "product_type": product.get("product_type", "SCRAPED"),
            "created_at": product.get("created_at"),
            "project_id": product.get("project_id")
        }
        product_list.append(product_dict)
    
    return {
        "products": product_list,
        "total": len(product_list)
    }