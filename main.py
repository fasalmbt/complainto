from fastapi import FastAPI, Depends, HTTPException, status, File, UploadFile, Form, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from typing import Optional, List
import os
import uuid
import secrets
import smtplib
import random
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from jose import jwt
from passlib.context import CryptContext
from dotenv import load_dotenv
import database
import models
import schemas

app = FastAPI(title="Complaint Management System")
load_dotenv()

BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))
RESET_TOKEN_EXPIRE_HOURS = int(os.getenv("RESET_TOKEN_EXPIRE_HOURS", 24))

SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
SMTP_PORT = int(os.getenv("SMTP_PORT", 2525))
FROM_EMAIL = os.getenv("FROM_EMAIL")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

os.makedirs("static/uploads", exist_ok=True)
os.makedirs("static/css", exist_ok=True)
os.makedirs("static/js", exist_ok=True)
os.makedirs("templates", exist_ok=True)

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

models.Base.metadata.create_all(bind=database.engine)

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def generate_otp() -> str:
    return str(random.randint(100000, 999999))

def send_otp_email(email: str, otp: str):
    try:
        msg = MIMEMultipart()
        msg['From'] = FROM_EMAIL
        msg['To'] = email
        msg['Subject'] = "Your OTP for Account Verification"
        
        body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                }}
                .otp {{
                    font-size: 24px;
                    font-weight: bold;
                    color: #4f46e5;
                }}
            </style>
        </head>
        <body>
            <p>Your OTP for account verification is:</p>
            <p class="otp">{otp}</p>
            <p>This OTP is valid for 10 minutes.</p>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(body, 'html'))
        
        with smtplib.SMTP(SMTP_SERVER, int(SMTP_PORT)) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.sendmail(FROM_EMAIL, email, msg.as_string())
        
        return True
    except Exception as e:
        print(f"Failed to send OTP email: {str(e)}")
        return False



def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def generate_reset_token():
    return secrets.token_urlsafe(32)

def send_reset_email(email: str, reset_token: str):
    try:
        msg = MIMEMultipart()
        msg['From'] = FROM_EMAIL
        msg['To'] = email
        msg['Subject'] = "🔑 Password Reset | Complainto" 

        reset_url = f"{BASE_URL}/reset-password?token={reset_token}"
        
        body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{
                    font-family: 'Inter', sans-serif;
                    background: #f9fafb;
                    margin: 0;
                    padding: 20px;
                }}
                .container {{
                    max-width: 500px;
                    margin: 0 auto;
                    background: white;
                    border-radius: 8px;
                    padding: 30px;
                    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
                }}
                .button {{
                    display: inline-block;
                    padding: 12px 24px;
                    background: #4f46e5;
                    color: white;
                    text-decoration: none;
                    border-radius: 6px;
                    font-weight: 600;
                }}
                .url {{
                    word-break: break-all;
                    font-family: monospace;
                    background: #f3f4f6;
                    padding: 10px;
                    border-radius: 4px;
                    font-size: 13px;
                }}
                .warning {{
                    color: #ef4444;
                    font-size: 13px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h2 style="margin-top: 0;">Reset your password</h2>
                <p>Click below to set a new password:</p>
                <p><a href="{reset_url}" class="button">Reset Now</a></p>
                <p>Or copy this link:</p>
                <p class="url">{reset_url}</p>
                <p class="warning">⚠️ Link expires in 1 hour.</p>
            </div>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(body, 'html'))
        
        with smtplib.SMTP(SMTP_SERVER, int(SMTP_PORT)) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.sendmail(FROM_EMAIL, email, msg.as_string())
        
        print(f"[✅] Reset link sent to {email}")
        return True
        
    except Exception as e:
        print(f"[❌] Failed to send email: {str(e)}")
        raise

        
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    
    user = db.query(models.User).filter(models.User.email == email).first()
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.get("/forgot-password", response_class=HTMLResponse)
async def forgot_password_page(request: Request):
    return templates.TemplateResponse("forgot_password.html", {"request": request})

@app.get("/reset-password", response_class=HTMLResponse)
async def reset_password_page(request: Request, token: str = None):
    return templates.TemplateResponse("reset_password.html", {"request": request, "token": token})

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, db: Session = Depends(get_db)):
    complaints = db.query(models.Complaint).all()
    return templates.TemplateResponse("dashboard.html", {"request": request, "complaints": complaints})

@app.get("/admin", response_class=HTMLResponse)
async def admin_dashboard(request: Request):
    return templates.TemplateResponse("admin.html", {"request": request})

@app.post("/api/register")
async def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = get_password_hash(user.password)
    db_user = models.User(
        email=user.email,
        name=user.name,
        hashed_password=hashed_password,
        is_admin=user.is_admin
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer", "user": {"email": db_user.email, "name": db_user.name, "is_admin": db_user.is_admin}}

@app.post("/api/login")
async def login(user: schemas.UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer", "user": {"email": db_user.email, "name": db_user.name, "is_admin": db_user.is_admin}}

@app.post("/api/forgot-password")
async def forgot_password(request: schemas.ForgotPasswordRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == request.email).first()
    if not user:
        return {"message": "If the email exists, a reset link has been sent"}
    
    reset_token = generate_reset_token()
    expires_at = datetime.utcnow() + timedelta(hours=RESET_TOKEN_EXPIRE_HOURS)
    
    db_reset = models.PasswordReset(
        user_id=user.id,
        token=reset_token,
        expires_at=expires_at
    )
    db.add(db_reset)
    db.commit()
    
    email_sent = send_reset_email(user.email, reset_token)
    
    if not email_sent:
        raise HTTPException(status_code=500, detail="Failed to send reset email")
    
    return {"message": "If the email exists, a reset link has been sent"}

@app.post("/api/reset-password")
async def reset_password(request: schemas.ResetPasswordRequest, db: Session = Depends(get_db)):
    reset_record = db.query(models.PasswordReset).filter(
        models.PasswordReset.token == request.token,
        models.PasswordReset.used == False,
        models.PasswordReset.expires_at > datetime.utcnow()
    ).first()
    
    if not reset_record:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")
    
    user = db.query(models.User).filter(models.User.id == reset_record.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.hashed_password = get_password_hash(request.new_password)
    
    reset_record.used = True
    
    db.commit()
    
    return {"message": "Password reset successfully"}

@app.post("/api/complaints")
async def create_complaint(
    title: str = Form(...),
    description: str = Form(...),
    category: str = Form(...),
    screenshot: Optional[UploadFile] = File(None),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    screenshot_path = None
    if screenshot:
        file_extension = screenshot.filename.split(".")[-1]
        filename = f"{uuid.uuid4()}.{file_extension}"
        screenshot_path = f"static/uploads/{filename}"
        
        with open(screenshot_path, "wb") as buffer:
            content = await screenshot.read()
            buffer.write(content)
    
    db_complaint = models.Complaint(
        title=title,
        description=description,
        category=category,
        screenshot_path=screenshot_path,
        user_id=current_user.id,
        status="pending"
    )
    db.add(db_complaint)
    db.commit()
    db.refresh(db_complaint)
    
    return {"message": "Complaint submitted successfully", "complaint_id": db_complaint.id}

@app.get("/api/complaints")
async def get_user_complaints(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    complaints = db.query(models.Complaint).filter(models.Complaint.user_id == current_user.id).all()
    return complaints

@app.get("/api/admin/complaints")
async def get_all_complaints(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    complaints = db.query(models.Complaint).all()
    complaint_list = []
    for complaint in complaints:
        user = db.query(models.User).filter(models.User.id == complaint.user_id).first()
        complaint_dict = {
            "id": complaint.id,
            "title": complaint.title,
            "description": complaint.description,
            "category": complaint.category,
            "status": complaint.status,
            "screenshot_path": complaint.screenshot_path,
            "created_at": complaint.created_at,
            "updated_at": complaint.updated_at,
            "user_name": user.name if user else "Unknown",
            "user_email": user.email if user else "Unknown"
        }
        complaint_list.append(complaint_dict)
    
    return complaint_list

@app.put("/api/admin/complaints/{complaint_id}")
async def update_complaint_status(
    complaint_id: int,
    status_update: schemas.ComplaintStatusUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    complaint = db.query(models.Complaint).filter(models.Complaint.id == complaint_id).first()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")
    
    complaint.status = status_update.status
    complaint.admin_notes = status_update.admin_notes
    complaint.updated_at = datetime.utcnow()
    
    db.commit()
    return {"message": "Complaint updated successfully"}

@app.post("/api/send-otp")
async def send_otp(request: schemas.OTPRequest, db: Session = Depends(get_db)):
    db.query(models.OTP).filter(models.OTP.email == request.email).delete()
    
    otp = generate_otp()
    expires_at = datetime.utcnow() + timedelta(minutes=10)
    
    db_otp = models.OTP(
        email=request.email,
        otp=otp,
        expires_at=expires_at
    )
    db.add(db_otp)
    db.commit()
    
    if not send_otp_email(request.email, otp):
        raise HTTPException(status_code=500, detail="Failed to send OTP")
    
    return {"message": "OTP sent successfully"}

@app.post("/api/verify-otp")
async def verify_otp(request: schemas.VerifyOTPRequest, db: Session = Depends(get_db)):
    otp_record = db.query(models.OTP).filter(
        models.OTP.email == request.email,
        models.OTP.otp == request.otp,
        models.OTP.expires_at > datetime.utcnow(),
        models.OTP.is_used == False
    ).first()
    
    if not otp_record:
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")
    
    otp_record.is_used = True
    db.commit()
    
    return {"message": "OTP verified successfully"}

@app.post("/api/change-password")
async def change_password(
    request: schemas.ChangePasswordRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not verify_password(request.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    
    if request.new_password != request.confirm_password:
        raise HTTPException(status_code=400, detail="New passwords don't match")
    
    current_user.hashed_password = get_password_hash(request.new_password)
    db.commit()
    
    return {"message": "Password changed successfully"}

@app.get("/api/profile")
async def get_profile(current_user: models.User = Depends(get_current_user)):
    return {
        "name": current_user.name,
        "email": current_user.email,
        "is_admin": current_user.is_admin,
        "created_at": current_user.created_at
    }

@app.put("/api/profile")
async def update_profile(
    profile: schemas.ProfileUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if profile.email != current_user.email:
        existing_user = db.query(models.User).filter(
            models.User.email == profile.email,
            models.User.id != current_user.id
        ).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already in use")
    
    current_user.name = profile.name
    current_user.email = profile.email
    db.commit()
    
    return {"message": "Profile updated successfully"}

@app.delete("/api/account")
async def delete_account(
    request: schemas.DeleteAccountRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not verify_password(request.password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect password")
    
    otp_record = db.query(models.OTP).filter(
        models.OTP.email == current_user.email,
        models.OTP.otp == request.otp,
        models.OTP.expires_at > datetime.utcnow(),
        models.OTP.is_used == False
    ).first()
    
    if not otp_record:
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")
    
    otp_record.is_used = True
    
    db.query(models.Complaint).filter(models.Complaint.user_id == current_user.id).delete()
    
    db.delete(current_user)
    db.commit()
    
    return {"message": "Account deleted successfully"}

@app.get("/profile", response_class=HTMLResponse)
async def profile_page(request: Request, db: Session = Depends(get_db)):
    complaints = db.query(models.Complaint).all()
    return templates.TemplateResponse("profile.html", {"request": request, "complaints": complaints })

@app.get("/change-password", response_class=HTMLResponse)
async def change_password_page(request: Request):
    return templates.TemplateResponse("change_password.html", {"request": request})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
