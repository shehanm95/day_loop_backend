# from typing import Optional, List
# from pydantic import BaseModel, Field

# class LocationImageResponse(BaseModel):
#     id: int
#     image_url: str
#     caption: Optional[str] = None

#     model_config = {"from_attributes": True}


# class LocationBase(BaseModel):
#     name: str
#     slug: str
#     description: Optional[str] = None
#     latitude: float
#     longitude: float
#     address: str
#     city: str
#     district: str
#     province: str
#     opening_time: Optional[str] = None
#     closing_time: Optional[str] = None
#     average_visit_duration: Optional[float] = None
#     entry_fee_local: float = 0.0
#     entry_fee_foreign: float = 0.0
#     contact_number: Optional[str] = None
#     website: Optional[str] = None
#     is_active: bool = True


# class LocationCreate(LocationBase):
#     # Enforces that a location must belong to at least one category ID
#     category_ids: List[int] = Field(..., min_length=1, description="Must belong to at least one category")


# class LocationUpdate(BaseModel):
#     name: Optional[str] = None
#     slug: Optional[str] = None
#     description: Optional[str] = None
#     latitude: Optional[float] = None
#     longitude: Optional[float] = None
#     address: Optional[str] = None
#     city: Optional[str] = None
#     district: Optional[str] = None
#     province: Optional[str] = None
#     opening_time: Optional[str] = None
#     closing_time: Optional[str] = None
#     average_visit_duration: Optional[float] = None
#     entry_fee_local: Optional[float] = None
#     entry_fee_foreign: Optional[float] = None
#     rating: Optional[float] = None
#     contact_number: Optional[str] = None
#     website: Optional[str] = None
#     is_active: Optional[bool] = None
#     category_ids: Optional[List[int]] = Field(default=None, min_length=1)


# class LocationResponse(LocationBase):
#     id: int
#     rating: float
#     cover_image: Optional[str] = None
#     categories: List = []
#     gallery_images: List[LocationImageResponse] = []

#     model_config = {"from_attributes": True}