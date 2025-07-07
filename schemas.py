from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    email: str
    name: str

class UserCreate(UserBase):
    password: str
    is_admin: bool = False

class UserLogin(BaseModel):
    email: str
    password: str

class ForgotPasswordRequest(BaseModel):
    email: str

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str
    confirm_password: str

class ProfileUpdate(BaseModel):
    name: str
    email: str

class DeleteAccountRequest(BaseModel):
    password: str
    otp: str

class OTPRequest(BaseModel):
    email: str

class VerifyOTPRequest(BaseModel):
    email: str
    otp: str

class User(UserBase):
    id: int
    is_admin: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class ComplaintBase(BaseModel):
    title: str
    description: str
    category: str

class ComplaintCreate(ComplaintBase):
    pass

class ComplaintStatusUpdate(BaseModel):
    status: str
    admin_notes: Optional[str] = None

class Complaint(ComplaintBase):
    id: int
    status: str
    screenshot_path: Optional[str] = None
    admin_notes: Optional[str] = None
    user_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
