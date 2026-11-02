from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session
from app.core.config import settings
from app.core.database import create_initial_admin, init_db , engine
from app.api.v1.router import api_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    with Session(engine) as session:
        # Call your admin creation function here
        create_initial_admin(session)
        pass
    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

# ==========================================
# Configure CORS for React Frontend
# ==========================================
origins = [
    "http://localhost:5173", # Vite React development server
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], # Allows all HTTP methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"], # Allows all headers (Authorization, Content-Type, etc.)
)

# Include API v1 Router
app.include_router(api_router, prefix=settings.API_V1_STR)

# Mount the static directory so files under 'static/' can be accessed via URL
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def root():
    return {"message": "Welcome to the Travel App API", "docs": "/docs"}