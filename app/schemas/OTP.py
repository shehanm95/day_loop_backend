from pydantic import BaseModel, EmailStr, Field

class OTPRequest(BaseModel):
    email: EmailStr