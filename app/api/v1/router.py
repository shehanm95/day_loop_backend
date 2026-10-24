from fastapi import APIRouter
from app.api.v1.endpoints import auth, categories, locations

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(categories.router, prefix="/categories", tags=["Categories"])
api_router.include_router(locations.router, prefix="/locations", tags=["Locations"])