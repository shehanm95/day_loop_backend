from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session
from app.schemas.OTP import OTPRequest
from app.schemas.user import UserCreate, UserRead, UserLogin, Token, RefreshTokenRequest, UserUpdate

from app.core.database import get_db
from app.core.security import create_access_token, create_refresh_token
from app.models.user import UserRole
from app.services import emailService
import app.services.user_service as userService
from jose import JWTError, jwt
from app.core.config import settings

router = APIRouter()

@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    existing_user = userService.get_user_by_email(db, user_in.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered in the system."
        )
    
    try:
        # Handles concurrent race conditions via database integrity safeguards
        return userService.create_user(db=db, user_in=user_in)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered in the system."
        )

@router.post("/login", response_model=Token)
def getAllUsers(form_data: UserLogin, db: Session = Depends(get_db)):
    user = userService.authenticate_user(db, email=form_data.email, password=form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Issue both access and refresh tokens
    access_token = create_access_token(subject=user.id)
    refresh_token = create_refresh_token(subject=user.id)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": user
    }

@router.post("/get_all_users", response_model=list[UserRead])
def get_all_users(db: Session = Depends(get_db)):
    users = userService.get_users(db)
    return users


@router.get("/user/{user_id}", response_model=UserRead)
def get_user_by_id(
    user_id: int, 
    db: Session = Depends(get_db)
    # current_user: User = Depends(get_current_active_user)  # Optional: add if authentication is needed here too
):
    user = userService.get_user_by_id(user_id, db)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    return user

@router.post("/refresh", response_model=Token)
def refresh_token(body: RefreshTokenRequest, db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate refresh token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(body.refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str | None = payload.get("sub")
        token_type: str | None = payload.get("type")
        
        if user_id is None or token_type != "refresh":
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    # Issue a new access token while keeping the refresh token valid
    new_access_token = create_access_token(subject=user_id)
    
    return {
        "access_token": new_access_token,
        "refresh_token": body.refresh_token,
        "token_type": "bearer"
    }

@router.put("/user/{user_id}", response_model=UserRead)
def update_user_endpoint(
    user_id: int,
    user_in: UserUpdate,
    db: Session = Depends(get_db)
):
    # Check if email is being updated and already taken by someone else
    if user_in.email:
        existing_user = userService.get_user_by_email(db, user_in.email)
        if existing_user and existing_user.id != user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered by another user."
            )

    updated_user = userService.update_user(db=db, user_id=user_id, user_in=user_in)
    
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
        
    return updated_user

@router.delete("/user/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user_endpoint(
    user_id: int,
    db: Session = Depends(get_db)
):
    success = userService.delete_user(db=db, user_id=user_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
        
    return None