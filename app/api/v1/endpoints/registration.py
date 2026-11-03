from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query
from sqlmodel import Session
from app.models.user import User
from app.schemas.OTP import OTPRequest
from app.schemas.ReSetPassword import ReSetPassword
from app.schemas.location import LocationResponse
from app.services import emailService
from app.services.location_service import LocationService
import app.services.user_service as userService
from app.core.database import get_db

router = APIRouter(prefix="", tags=["Rgistration"])
@router.post("/send-otp", status_code=status.HTTP_200_OK)
def send_otp_endpoint(body: OTPRequest):
    # Call the service method we created
    success, otp_code = emailService.send_otp_to_email(body.email)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send verification email. Please try again later."
        )
    
    # NOTE: In a real production application, you should save `otp_code` 
    # associated with this user/email in your database with an expiration time (e.g., 10 minutes) 
    # so you can verify it later when the user submits it back.
    
    return {
        "message": "OTP sent successfully to your email.",
        # "debug_otp": otp_code  # Uncomment only during local testing if needed
    }

@router.put("/set_password", status_code=status.HTTP_200_OK)
def resetPassword(body: ReSetPassword, db: Session = Depends(get_db)):
    print(body , "22222222222222222222222222222222222222222222222222222222222222222")
    try:
        # Call the emailService function we just completed
        emailService.setPassword(db, body)
        return {"message": "Password has been successfully set. You can now log in."}
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(err)
        )
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(err)}"
        )