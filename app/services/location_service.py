import math
from typing import List, Optional
from fastapi import UploadFile, HTTPException, status
from sqlmodel import Session, select, col
from app.models.category import Location, Category, LocationImage
from app.utils.helpers import save_upload_file


class LocationService:

    @staticmethod
    def get_locations(
        db: Session,
        category: Optional[str] = None,
        district: Optional[str] = None,
        city: Optional[str] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Location]:
        statement = select(Location).where(Location.is_active == True)

        if district:
            statement = statement.where(col(Location.district).ilike(f"%{district}%"))
        if city:
            statement = statement.where(col(Location.city).ilike(f"%{city}%"))
        if search:
            statement = statement.where(
                col(Location.name).ilike(f"%{search}%") | col(Location.description).ilike(f"%{search}%")
            )
        
        locations = db.exec(statement.offset(skip).limit(limit)).all()

        if category:
            filtered = []
            for loc in locations:
                if any(cat.slug == category or cat.name.lower() == category.lower() for cat in loc.categories):
                    filtered.append(loc)
            return filtered

        return list(locations)

    @staticmethod
    def get_nearby_locations(db: Session, lat: float, lon: float, radius_km: float) -> List[Location]:
        locations = db.exec(select(Location).where(Location.is_active == True)).all()
        nearby = []
        R = 6371.0  # Earth radius in kilometers

        for loc in locations:
            dlat = math.radians(loc.latitude - lat)
            dlon = math.radians(loc.longitude - lon)
            a = (
                math.sin(dlat / 2) ** 2
                + math.cos(math.radians(lat)) * math.cos(math.radians(loc.latitude)) * math.sin(dlon / 2) ** 2
            )
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
            distance = R * c

            if distance <= radius_km:
                nearby.append(loc)

        return nearby

    @staticmethod
    def get_location_by_id(db: Session, location_id: int) -> Location:
        location = db.get(Location, location_id)
        if not location:
            raise HTTPException(status_code=404, detail="Location not found")
        return location

    @staticmethod
    def create_location(
        db: Session,
        name: str,
        slug: str,
        description: Optional[str],
        latitude: float,
        longitude: float,
        address: str,
        city: str,
        district: str,
        province: str,
        opening_time: Optional[str],
        closing_time: Optional[str],
        average_visit_duration: Optional[float],
        entry_fee_local: float,
        entry_fee_foreign: float,
        contact_number: Optional[str],
        website: Optional[str],
        category_ids_str: str,
        cover_image: Optional[UploadFile],
        gallery_files: List[UploadFile]
    ) -> Location:
        # Parse comma-separated category IDs
        try:
            cat_ids = [int(cid.strip()) for cid in category_ids_str.split(",") if cid.strip()]
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid format for category_ids. Use comma-separated numbers.")

        if not cat_ids:
            raise HTTPException(status_code=400, detail="A location must belong to at least one category.")

        # Validate categories exist
        categories = db.exec(select(Category).where(col(Category.id).in_(cat_ids))).all()
        if len(categories) != len(cat_ids):
            raise HTTPException(status_code=400, detail="One or more specified category IDs do not exist.")

        # Handle Cover Image Upload
        cover_image_url = save_upload_file(cover_image, "locations/covers") if cover_image and cover_image.filename else None

        new_location = Location(
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
            cover_image=cover_image_url,
            categories=list(categories)
        )

        db.add(new_location)
        db.commit()
        db.refresh(new_location)

        # Handle Gallery Images Upload
        for file in gallery_files:
            if file.filename:
                img_url = save_upload_file(file, "locations/gallery")
                gallery_img = LocationImage(location_id=new_location.id, image_url=img_url)  # type: ignore
                db.add(gallery_img)
        
        db.commit()
        db.refresh(new_location)
        return new_location

    @staticmethod
    def update_location(
        db: Session,
        location_id: int,
        name: Optional[str],
        slug: Optional[str],
        description: Optional[str],
        latitude: Optional[float],
        longitude: Optional[float],
        address: Optional[str],
        city: Optional[str],
        district: Optional[str],
        province: Optional[str],
        opening_time: Optional[str],
        closing_time: Optional[str],
        average_visit_duration: Optional[float],
        entry_fee_local: Optional[float],
        entry_fee_foreign: Optional[float],
        contact_number: Optional[str],
        website: Optional[str],
        is_active: Optional[bool],
        category_ids_str: Optional[str],
        cover_image: Optional[UploadFile],
        gallery_files: List[UploadFile]
    ) -> Location:
        location = LocationService.get_location_by_id(db, location_id)

        if name is not None: location.name = name
        if slug is not None: location.slug = slug
        if description is not None: location.description = description
        if latitude is not None: location.latitude = latitude
        if longitude is not None: location.longitude = longitude
        if address is not None: location.address = address
        if city is not None: location.city = city
        if district is not None: location.district = district
        if province is not None: location.province = province
        if opening_time is not None: location.opening_time = opening_time
        if closing_time is not None: location.closing_time = closing_time
        if average_visit_duration is not None: location.average_visit_duration = average_visit_duration
        if entry_fee_local is not None: location.entry_fee_local = entry_fee_local
        if entry_fee_foreign is not None: location.entry_fee_foreign = entry_fee_foreign
        if contact_number is not None: location.contact_number = contact_number
        if website is not None: location.website = website
        if is_active is not None: location.is_active = is_active

        if category_ids_str is not None:
            try:
                cat_ids = [int(cid.strip()) for cid in category_ids_str.split(",") if cid.strip()]
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid format for category_ids. Use comma-separated numbers.")
            
            categories = db.exec(select(Category).where(col(Category.id).in_(cat_ids))).all()
            if len(categories) != len(cat_ids):
                raise HTTPException(status_code=400, detail="One or more specified category IDs do not exist.")
            location.categories = list(categories)

        if cover_image and cover_image.filename:
            location.cover_image = save_upload_file(cover_image, "locations/covers")

        for file in gallery_files:
            if file.filename:
                img_url = save_upload_file(file, "locations/gallery")
                gallery_img = LocationImage(location_id=location.id, image_url=img_url)  # type: ignore
                db.add(gallery_img)

        db.add(location)
        db.commit()
        db.refresh(location)
        return location

    @staticmethod
    def delete_location(db: Session, location_id: int, soft_delete: bool = True) -> dict:
        location = LocationService.get_location_by_id(db, location_id)
        
        if soft_delete:
            location.is_active = False
            db.add(location)
            db.commit()
            return {"message": "Location soft-deleted successfully"}
        else:
            db.delete(location)
            db.commit()
            return {"message": "Location permanently deleted successfully"}