from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query
from sqlmodel import Session, select

from app.core.database import get_db
from app.api.deps import get_current_active_admin, get_current_user
from app.models.user import User, UserRole
from app.models.category import Category
# from app.models.location import Location
from app.schemas.category import CategoryCreate, CategoryReorderItem, CategoryUpdate, CategoryRead
from sqlmodel import Session, select, or_, col
from app.services import category_service
from app.utils.helpers import save_upload_file

router = APIRouter()

# ==========================================
# 1. RETRIEVAL & SEARCH ENDPOINTS (Public)
# ==========================================

@router.get("/", response_model=List[CategoryRead])
def get_categories(
    db: Session = Depends(get_db), 
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
        # Using col() satisfies Pylance/Pyright type checking for SQLAlchemy expressions inside or_()
        statement = statement.where(
            or_(
                col(Category.name).like(search_filter),
                col(Category.description).like(search_filter),
                col(Category.slug).like(search_filter)
            )
        )
        
    statement = statement.offset(skip).limit(limit)
    return list(db.exec(statement).all())

@router.get("/search", response_model=List[CategoryRead])
def search_categories(
    q: str = Query(..., min_length=1),
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """Search categories by name, slug, or description."""
    return category_service.get_categories(db, search=q, is_active=is_active)

@router.get("/slug/{slug}", response_model=CategoryRead)
def read_category_by_slug(slug: str, db: Session = Depends(get_db)):
    """Get a single category by its slug for frontend routing."""
    category = category_service.get_category_by_slug(db, slug)
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    return category

@router.get("/{id}", response_model=CategoryRead)
def read_category_by_id(id: int, db: Session = Depends(get_db)):
    """Get a single category by its ID."""
    category = category_service.get_category_by_id(db, id)
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    return category

# @router.get("/{id}/locations", response_model=List[dict])
# def read_category_locations(id: int, db: Session = Depends(get_db)):
#     """Get all locations belonging to a specific category."""
#     category = category_service.get_category_by_id(db, id)
#     if not category:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    
#     statement = select(Location).join(Location.categories).where(Category.id == id)
#     locations = db.exec(statement).all()
#     return locations


# ==========================================
# 2. CREATION ENDPOINTS [Admin Only]
# ==========================================

@router.post("/", response_model=CategoryRead, status_code=status.HTTP_201_CREATED)
def create_category_endpoint(
    name: str = Form(...),
    slug: str = Form(...),
    description: Optional[str] = Form(None),
    is_active: bool = Form(True),
    display_order: int = Form(0),
    file: Optional[UploadFile] = File(None),  # Optional icon file upload
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_active_admin)
):
    """
    Create a new category with an optional icon image upload in a single request [Admin Only].
    """
    existing = category_service.get_category_by_slug(db, slug)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Category with this slug already exists."
        )
    
    category_in = CategoryCreate(
        name=name,
        slug=slug,
        description=description,
        is_active=is_active,
        display_order=display_order
    )
    return category_service.create_category(db=db, category_in=category_in, file=file)

@router.post("/bulk", response_model=List[CategoryRead], status_code=status.HTTP_201_CREATED)
def create_categories_bulk(
    categories_in: List[CategoryCreate],
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_active_admin)
):
    """Create multiple categories in bulk [Admin Only]."""
    created = []
    for cat_in in categories_in:
        existing = category_service.get_category_by_slug(db, cat_in.slug)
        if not existing:
            new_cat = category_service.create_category(db, cat_in, file=None)
            created.append(new_cat)
    return created


# ==========================================
# 3. UPDATING ENDPOINTS [Admin Only]
# ==========================================

@router.put("/{id}", response_model=CategoryRead)
def update_category_full(
    id: int,
    category_in: CategoryCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_active_admin)
):
    """Fully update a category [Admin Only]."""
    category = category_service.get_category_by_id(db, id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    update_data = CategoryUpdate(**category_in.model_dump())
    return category_service.update_category(db, category, update_data)

@router.patch("/{id}", response_model=CategoryRead)
def update_category_partial(
    id: int,
    category_in: CategoryUpdate,
    db: Session = Depends(get_db),  # <-- Fixed!
    admin: User = Depends(get_current_active_admin)
):
    """Partially update a category [Admin Only]."""
    category = category_service.get_category_by_id(db, id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return category_service.update_category(db, category, category_in)

@router.patch("/reorder", status_code=status.HTTP_200_OK)
def reorder_categories(
    items: List[CategoryReorderItem],
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_active_admin)
):
    """Update display order for multiple categories at once [Admin Only]."""
    for item in items:
        cat = category_service.get_category_by_id(db, item.id)
        if cat:
            cat.display_order = item.display_order
            db.add(cat)
    db.commit()
    return {"message": "Categories reordered successfully"}


# ==========================================
# 4. MANAGEMENT & UTILITIES [Admin Only]
# ==========================================

@router.patch("/{id}/status", response_model=CategoryRead)
def toggle_category_status(
    id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_active_admin)
):
    """Toggle a category's active/inactive status [Admin Only]."""
    category = category_service.get_category_by_id(db, id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    category.is_active = not category.is_active
    db.add(category)
    db.commit()
    db.refresh(category)
    return category

@router.post("/{id}/image", response_model=CategoryRead)
def upload_category_image(
    id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_active_admin)
):
    """Upload or update a category icon/image file [Admin Only]."""
    category = category_service.get_category_by_id(db, id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    # Save file using your helper and update icon URL
    icon_url = save_upload_file(file, subfolder="categories/icons")
    category.icon_url = icon_url
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


# ==========================================
# 5. DELETION ENDPOINTS [Admin Only]
# ==========================================

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(
    id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_active_admin)
):
    """Delete a single category [Admin Only]."""
    category = category_service.get_category_by_id(db, id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    category_service.delete_category(db, category)
    return None

@router.delete("/bulk", status_code=status.HTTP_200_OK)
def delete_categories_bulk(
    payload: dict,  # Expected format: {"ids": [1, 2, 3]}
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_active_admin)
):
    """Delete multiple selected categories in bulk [Admin Only]."""
    ids = payload.get("ids", [])
    count = 0
    for cat_id in ids:
        cat = category_service.get_category_by_id(db, cat_id)
        if cat:
            category_service.delete_category(db, cat)
            count += 1
    return {"message": f"Successfully deleted {count} categories."}

@router.delete("/", status_code=status.HTTP_200_OK)
def delete_all_categories(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_active_admin)
):
    """Delete all categories [Admin Only / High Security]."""
    categories = category_service.get_categories(db, limit=10000)
    for cat in categories:
        category_service.delete_category(db, cat)
    return {"message": "All categories deleted successfully."}