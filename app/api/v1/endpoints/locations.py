from typing import List, Optional
from fastapi import APIRouter, Depends, status, UploadFile, File, Form, Query
from sqlmodel import Session
from app.core.database import get_db
from app.api.deps import get_current_active_admin
from app.models.user import User
from app.schemas.location import LocationResponse
from app.services.location_service import LocationService

router = APIRouter(prefix="", tags=["Locations"])


@router.get("/", response_model=List[LocationResponse])
def get_locations(
    db: Session = Depends(get_db),
    category: Optional[str] = Query(None, description="Filter by category slug or name"),
    district: Optional[str] = Query(None, description="Filter by district"),
    city: Optional[str] = Query(None, description="Filter by city"),
    search: Optional[str] = Query(None, description="Search term for name or description"),
    skip: int = 0,
    limit: int = 100
):
    return LocationService.get_locations(db, category, district, city, search, skip, limit)


@router.get("/nearby", response_model=List[LocationResponse])
def get_nearby_locations(
    lat: float = Query(..., description="User latitude"),
    lon: float = Query(..., description="User longitude"),
    radius_km: float = Query(25.0, description="Radius in kilometers"),
    db: Session = Depends(get_db)
):
    """Find active locations within a specific radius using the Haversine formula."""
    return LocationService.get_nearby_locations(db, lat, lon, radius_km)


@router.get("/{location_id}", response_model=LocationResponse)
def get_location_by_id(location_id: int, db: Session = Depends(get_db)):
    return LocationService.get_location_by_id(db, location_id)

@router.get("/name/{location_name}", response_model=LocationResponse)
def get_location_by_name(location_name: str, db: Session = Depends(get_db)):
    return LocationService.get_location_by_name(db, location_name)


@router.post("/", response_model=LocationResponse, status_code=status.HTTP_201_CREATED)
def create_location(
    name: str = Form(...),
    slug: str = Form(...),
    description: Optional[str] = Form(None),
    latitude: float = Form(...),
    longitude: float = Form(...),
    address: str = Form(...),
    city: str = Form(...),
    district: str = Form(...),
    province: str = Form(...),
    opening_time: Optional[str] = Form(None),
    closing_time: Optional[str] = Form(None),
    average_visit_duration: Optional[float] = Form(None),
    entry_fee_local: float = Form(0.0),
    entry_fee_foreign: float = Form(0.0),
    contact_number: Optional[str] = Form(None),
    website: Optional[str] = Form(None),
    category_ids: str = Form(..., description="Comma-separated category IDs, e.g., '1,2'"),
    cover_image: Optional[UploadFile] = File(None),
    gallery_files: List[UploadFile] = File([]),
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_active_admin)
):
    return LocationService.create_location(
        db=db,
        name=name,
        slug=slug,
        description=description,
        latitude=latitude,
        longitude=longitude,
        address=address,
        city=city,
        district=district,
        province=province,
        opening_time=opening_time,
        closing_time=closing_time,
        average_visit_duration=average_visit_duration,
        entry_fee_local=entry_fee_local,
        entry_fee_foreign=entry_fee_foreign,
        contact_number=contact_number,
        website=website,
        category_ids_str=category_ids,
        cover_image=cover_image,
        gallery_files=gallery_files
    )


@router.put("/{location_id}", response_model=LocationResponse)
def update_location(
    location_id: int,
    name: Optional[str] = Form(None),
    slug: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    latitude: Optional[float] = Form(None),
    longitude: Optional[float] = Form(None),
    address: Optional[str] = Form(None),
    city: Optional[str] = Form(None),
    district: Optional[str] = Form(None),
    province: Optional[str] = Form(None),
    opening_time: Optional[str] = Form(None),
    closing_time: Optional[str] = Form(None),
    average_visit_duration: Optional[float] = Form(None),
    entry_fee_local: Optional[float] = Form(None),
    entry_fee_foreign: Optional[float] = Form(None),
    contact_number: Optional[str] = Form(None),
    website: Optional[str] = Form(None),
    is_active: Optional[bool] = Form(None),
    category_ids: Optional[str] = Form(None, description="Comma-separated category IDs, e.g., '1,2'"),
    cover_image: Optional[UploadFile] = File(None),
    gallery_files: List[UploadFile] = File([]),
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_active_admin)
):
    """Update/Edit a location via form fields, supporting cover image and gallery file uploads."""
    return LocationService.update_location(
        db=db,
        location_id=location_id,
        name=name,
        slug=slug,
        description=description,
        latitude=latitude,
        longitude=longitude,
        address=address,
        city=city,
        district=district,
        province=province,
        opening_time=opening_time,
        closing_time=closing_time,
        average_visit_duration=average_visit_duration,
        entry_fee_local=entry_fee_local,
        entry_fee_foreign=entry_fee_foreign,
        contact_number=contact_number,
        website=website,
        is_active=is_active,
        category_ids_str=category_ids,
        cover_image=cover_image,
        gallery_files=gallery_files
    )


@router.delete("/{location_id}", status_code=status.HTTP_200_OK)
def delete_location(
    location_id: int, 
    soft_delete: bool = True, 
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_active_admin)
):
    return LocationService.delete_location(db, location_id, soft_delete)