from pydantic import BaseModel, EmailStr

class ReSetPassword(BaseModel):
    email: str
    otp:str
    password:str