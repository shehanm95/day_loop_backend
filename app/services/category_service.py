import os
from typing import Optional, List
from fastapi import UploadFile
from sqlmodel import Session, select
from app.models.category import Category
from app.schemas.category import CategoryCreate, CategoryUpdate
from app.utils.helpers import save_upload_file
from sqlmodel import Session, select, or_, col

def get_category_by_id(db: Session, category_id: int) -> Optional[Category]:
    """Retrieve a single category by its primary key ID."""
    return db.get(Category, category_id)

def get_category_by_slug(db: Session, slug: str) -> Optional[Category]:
    """Retrieve a single category by its unique slug."""
    statement = select(Category).where(Category.slug == slug)
    return db.exec(statement).first()

def get_categories(
    db: Session, 
    skip: int = 0, 
    limit: int = 100, 
    is_active: Optional[bool] = None,
    search: Optional[str] = None
) -> List[Category]:
    """Retrieve a filtered, searched, and paginated list of categories."""
    statement = select(Category)
    
    if is_active is not None:
        statement = statement.where(Category.is_active == is_active)
        
    if search:
        search_filter = f"%{search}%"
        statement = statement.where(
            or_(
                col(Category.name).like(search_filter),
                col(Category.description).like(search_filter),
                col(Category.slug).like(search_filter)
            )
        )
        
    statement = statement.offset(skip).limit(limit)
    return list(db.exec(statement).all())

def create_category(db: Session, category_in: CategoryCreate, file: Optional[UploadFile] = None) -> Category:
    """Create a new category, saving an optional uploaded icon file."""
    icon_url = None
    if file and file.filename:
        icon_url = save_upload_file(file, subfolder="categories/icons")
        
    db_category = Category(
        name=category_in.name,
        slug=category_in.slug,
        description=category_in.description,
        is_active=category_in.is_active,
        display_order=category_in.display_order,
        icon_url=icon_url
    )
    
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category

def update_category(db: Session, db_category: Category, category_in: CategoryUpdate) -> Category:
    """Fully or partially update an existing category record."""
    update_data = category_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_category, key, value)
        
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category

def delete_category(db: Session, db_category: Category):
    """Delete a category from the database and remove its icon file from disk."""
    if db_category.icon_url:
        # Convert relative URL path to local file path (e.g., /static/... -> static/...)
        file_path = db_category.icon_url.lstrip("/")
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception:
                pass  # Ignore file deletion errors to prevent blocking DB deletion
                
    db.delete(db_category)
    db.commit()