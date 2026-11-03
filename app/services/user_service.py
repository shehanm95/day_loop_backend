from time import timezone
from typing import Optional
from sqlmodel import Session, select
from app.models.user import User, UserRole
from app.schemas.user import UserCreate , UserUpdate, UserUpdateWithPassword
from app.core.security import get_password_hash, verify_password
from datetime import datetime, timezone

from app.services import emailService

def get_user_by_email(db: Session, email: str) -> Optional[User]:
    statement = select(User).where(User.email == email)
    return db.exec(statement).first()

def create_user(db: Session, user_in: UserCreate) -> User:
    hashed_password = get_password_hash(user_in.password)
    db_user = User(
        first_name=user_in.first_name,
        last_name=user_in.last_name,
        email=user_in.email,
        password_hash=hashed_password,
        role=user_in.role # type: ignore
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # Send the setup password email to the newly created user
    try:
        emailService.send_setup_password_email(db_user.email, db_user.first_name)
    except Exception as e:
        # Log the error if email fails, but don't break the user creation process
        print(f"Failed to send setup email to {db_user.email}: {e}")
        
    return db_user

def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    user = get_user_by_email(db, email)
    if not user or not verify_password(password, user.password_hash):
        return None
    print("authentication complete")
    return user

def get_users(db: Session) -> list[User]:
    statement = select(User)
    return list(db.exec(statement).all())

def get_user_by_id(user_id:int, db:Session) -> Optional[User]:
    return db.exec(select(User).where(User.id == user_id)).first()

def update_user(db: Session, user_id: int, user_in: UserUpdate) -> Optional[User]:
    db_user = get_user_by_id(user_id, db)
    if not db_user:
        return None
    
    # Get only the fields that were actually sent in the request
    update_data = user_in.model_dump(exclude_unset=True)
    
    for key, value in update_data.items():
        setattr(db_user, key, value)
    
    # Automatically update the timestamp if your model has updated_at
    db_user.updated_at = datetime.now(timezone.utc) # type: ignore
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user



def update_with_password(db: Session, user_id: int, new_password_plain: str) -> Optional[User]:
    # 1. Fetch the existing user from the database
    db_user = get_user_by_id( user_id, db)
    if not db_user:
        return None
    
    # 2. Hash the new password securely
    hashed_password = get_password_hash(new_password_plain)
    
    # 3. Update the specific fields on the existing instance
    db_user.password_hash = hashed_password
    db_user.updated_at = datetime.now(timezone.utc)
    # 4. Commit changes
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def delete_user(db: Session, user_id: int) -> bool:
    db_user = get_user_by_id(user_id, db)
    if not db_user:
        return False
    
    db.delete(db_user)
    db.commit()
    return True