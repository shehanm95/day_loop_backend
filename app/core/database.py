from sqlmodel import create_engine, Session, SQLModel
from app.core.config import settings

# Import all models here so SQLModel metadata registers them
from app.models.user import User 
from app.models.category import Category, Location, LocationImage, LocationCategoryLink

engine = create_engine(
    settings.SQLALCHEMY_DATABASE_URI,
    echo=False,
    pool_pre_ping=True
)

def init_db():
    """Create database tables based on SQLModel metadata."""
    print("database tables created")
    SQLModel.metadata.create_all(engine)

def get_db():
    with Session(engine) as session:
        yield session