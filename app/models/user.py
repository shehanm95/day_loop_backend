from datetime import datetime
from enum import Enum
from typing import Optional
from sqlmodel import SQLModel, Field

class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"

from datetime import datetime, timezone
from typing import Optional
from sqlmodel import SQLModel, Field
from app.models.user import UserRole  # Or wherever your enum lives

class User(SQLModel, table=True):
    __tablename__: str = "users"

    id: Optional[int] = Field(default=None, primary_key=True)
    first_name: str = Field(max_length=50)
    last_name: str = Field(max_length=50)
    email: str = Field(max_length=100, unique=True, index=True)
    password_hash: str = Field(max_length=255)
    role: UserRole = Field(default=UserRole.USER)
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))