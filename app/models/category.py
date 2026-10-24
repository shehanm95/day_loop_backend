from datetime import datetime, timezone
from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, Integer, ForeignKey

# Many-to-many association table linking Locations and Categories
class LocationCategoryLink(SQLModel, table=True):
    __tablename__: str = "location_categories"
    
    location_id: int = Field(
        sa_column=Column(
            Integer,
            ForeignKey("locations.id", ondelete="CASCADE"),
            primary_key=True
        )
    )
    category_id: int = Field(
        sa_column=Column(
            Integer,
            ForeignKey("categories.id", ondelete="CASCADE"),
            primary_key=True
        )
    )


class Category(SQLModel, table=True):
    __tablename__: str = "categories"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=255, unique=True, index=True)
    slug: str = Field(max_length=255, unique=True, index=True)
    description: Optional[str] = Field(default=None)
    icon_url: Optional[str] = Field(default=None, max_length=500)
    is_active: bool = Field(default=True)
    display_order: int = Field(default=0)

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Relationship back to locations
    locations: List["Location"] = Relationship(
        back_populates="categories", 
        link_model=LocationCategoryLink
    )


class LocationImage(SQLModel, table=True):
    __tablename__: str = "location_images"

    id: Optional[int] = Field(default=None, primary_key=True)
    location_id: int = Field(
        sa_column=Column(
            Integer,
            ForeignKey("locations.id", ondelete="CASCADE"),
            nullable=False
        )
    )
    image_url: str = Field(max_length=500)
    caption: Optional[str] = Field(default=None, max_length=150)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    location: "Location" = Relationship(back_populates="gallery_images")


class Location(SQLModel, table=True):
    __tablename__: str = "locations"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=255, index=True)
    slug: str = Field(max_length=255, unique=True, index=True)
    description: Optional[str] = Field(default=None)
    
    latitude: float
    longitude: float
    address: str = Field(max_length=500)
    city: str = Field(max_length=100, index=True)
    district: str = Field(max_length=100, index=True)
    province: str = Field(max_length=100)

    opening_time: Optional[str] = Field(default=None)  # Store as "HH:MM" string or time string
    closing_time: Optional[str] = Field(default=None)
    average_visit_duration: Optional[float] = Field(default=None) # in hours or minutes

    entry_fee_local: float = Field(default=0.0)
    entry_fee_foreign: float = Field(default=0.0)
    rating: float = Field(default=0.0)

    cover_image: Optional[str] = Field(default=None, max_length=500)
    contact_number: Optional[str] = Field(default=None, max_length=50)
    website: Optional[str] = Field(default=None, max_length=500)

    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Relationships
    categories: List[Category] = Relationship(
        back_populates="locations", 
        link_model=LocationCategoryLink
    )
    gallery_images: List[LocationImage] = Relationship(
        back_populates="location", 
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )