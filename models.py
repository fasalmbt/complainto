from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    name = Column(String)
    hashed_password = Column(String)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    complaints = relationship("Complaint", back_populates="user")
    password_resets = relationship("PasswordReset", back_populates="user")

class Complaint(Base):
    __tablename__ = "complaints"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(Text)
    category = Column(String)
    status = Column(String, default="pending")  # pending, in_progress, resolved, rejected
    screenshot_path = Column(String, nullable=True)
    admin_notes = Column(Text, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="complaints")

class PasswordReset(Base):
    __tablename__ = "password_resets"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    token = Column(String, unique=True, index=True)
    expires_at = Column(DateTime)
    used = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="password_resets")

class OTP(Base):
    __tablename__ = "otps"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, index=True)
    otp = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)
    is_used = Column(Boolean, default=False)