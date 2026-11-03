from sqlmodel import create_engine, Session, SQLModel, select
from app.core.config import settings

# Import all models here so SQLModel metadata registers them
from app.core.security import get_password_hash
from app.models.user import User, UserRole 
from app.models.category import Category, Location, LocationImage, LocationCategoryLink
from app.services import user_service

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

def create_initial_admin(session: Session) -> None:
    """Check if any user exists. If not, create a default admin user."""
    # Check if any user already exists in the table
    statement = select(User).limit(1)
    existing_user = session.exec(statement).first()

    if not existing_user:
        print("No users found. Creating default admin user...")
        hashed_password = get_password_hash("Admin@123") 
        
        admin_user = User(
            first_name="Admin",
            last_name="User",
            email="admin@gmail.com",
            password_hash=hashed_password,
            role=UserRole.ADMIN
        )
        
        session.add(admin_user)
        session.commit()
        print("Default admin user created successfully!")
    else:
        print("Users table already populated. Skipping default admin creation.")