from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, status, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
import shutil
import os
import pyotp
import qrcode
import io
import base64
from sqlalchemy.orm import Session
from app.config import DATA_DIR
from app.ingestion import ingest_file, get_query_engine
from app.database import init_db, get_db, User, Feedback
from app.auth import get_current_active_user, verify_password, get_password_hash, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
from app.utils import validate_password, send_email
from pydantic import BaseModel
from datetime import timedelta, datetime
from typing import Optional, List

# Initialize Database
init_db()

import firebase_admin
from firebase_admin import credentials, auth as firebase_auth

# Initialize Firebase Admin
try:
    cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred)
    print("Firebase Admin Initialized")
except Exception as e:
    print(f"Warning: Firebase Admin failed to initialize: {e}")

app = FastAPI()

# Allow CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryRequest(BaseModel):
    query: str

class UserCreate(BaseModel):
    email: str
    password: str
    role: str = "lawyer"

class Token(BaseModel):
    access_token: str
    token_type: str
    mfa_required: bool = False

class MFAVerify(BaseModel):
    code: str

class EmailVerify(BaseModel):
    token: str

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.post("/auth/register")
def register(user: UserCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    # 1. Check if user exists
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # 2. Validate Password
    if not validate_password(user.password):
        raise HTTPException(
            status_code=400, 
            detail="Password must be at least 8 chars, include upper, lower, digit, and special char."
        )
    
    # 3. Create User (Unverified)
    hashed_password = get_password_hash(user.password)
    new_user = User(
        email=user.email, 
        hashed_password=hashed_password, 
        role=user.role,
        is_verified=False # Default to False
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # 4. Generate Verification Token (JWT)
    verify_token = create_access_token(
        data={"sub": new_user.email, "type": "verification"}, 
        expires_delta=timedelta(hours=24)
    )
    
    # 5. Send Verification Email (Mock)
    verification_link = f"http://localhost:3000/verify-email?token={verify_token}"
    email_body = f"Please verify your email by clicking here: {verification_link}"
    background_tasks.add_task(send_email, new_user.email, "Verify your Legal AI Account", email_body)
    
    return {"message": "Registration successful. Please check your email to verify your account."}

@app.post("/auth/verify-email")
def verify_email_token(verify_data: EmailVerify, db: Session = Depends(get_db)):
    from jose import jwt, JWTError
    from app.auth import SECRET_KEY, ALGORITHM
    
    try:
        payload = jwt.decode(verify_data.token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        token_type: str = payload.get("type")
        
        if not email or token_type != "verification":
            raise HTTPException(status_code=400, detail="Invalid token")
            
        user = db.query(User).filter(User.email == email).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
            
        if user.is_verified:
             return {"message": "Email already verified"}

        user.is_verified = True
        db.commit()
        return {"message": "Email verified successfully"}
        
    except JWTError:
        raise HTTPException(status_code=400, detail="Invalid or expired token")

class ResendVerification(BaseModel):
    email: str

@app.post("/auth/resend-verification")
def resend_verification(resend_data: ResendVerification, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == resend_data.email).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.is_verified:
        return {"message": "Email already verified"}
    
    # Generate new verification token
    verify_token = create_access_token(
        data={"sub": user.email, "type": "verification"}, 
        expires_delta=timedelta(hours=24)
    )
    
    # Send verification email
    verification_link = f"http://localhost:3000/verify-email?token={verify_token}"
    email_body = f"Please verify your email by clicking here: {verification_link}"
    background_tasks.add_task(send_email, user.email, "Verify your Legal AI Account", email_body)
    
    return {"message": "Verification email sent. Please check your inbox."}

class UserResponse(BaseModel):
    id: int
    email: str
    role: str
    is_active: bool
    is_verified: bool
    mfa_enabled: bool
    phone_number: Optional[str] = None

@app.get("/auth/me", response_model=UserResponse)
def read_users_me(current_user: User = Depends(get_current_active_user)):
    return current_user

@app.post("/auth/token", response_model=Token)
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), 
    mfa_code: Optional[str] = None,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_verified:
        raise HTTPException(status_code=400, detail="Please verify your email first.")

    # MFA Check
    if user.mfa_enabled:
        if not mfa_code:
            # Signal frontend that MFA is required
            # We can't return a 200 Token here, so we raise a specific 403 or return a special structure
            # But OAuth2 spec expects 400/401. Let's use 403 Forbidden with detail "MFA_REQUIRED"
            raise HTTPException(status_code=403, detail="MFA_REQUIRED")
        
        totp = pyotp.TOTP(user.mfa_secret)
        if not totp.verify(mfa_code):
             raise HTTPException(status_code=401, detail="Invalid MFA code")

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email, "role": user.role}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer", "mfa_required": False}

@app.get("/auth/mfa/setup")
def setup_mfa(current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    if current_user.mfa_enabled:
        raise HTTPException(status_code=400, detail="MFA is already enabled")
    
    # Generate Secret
    secret = pyotp.random_base32()
    
    # Generate QR Code
    totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(name=current_user.email, issuer_name="Legal AI Tool")
    
    # Save secret temporarily (or permanently but disabled)
    current_user.mfa_secret = secret
    db.commit()
    
    return {"secret": secret, "otpauth_url": totp_uri}

@app.post("/auth/mfa/enable")
def enable_mfa(mfa_data: MFAVerify, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    if not current_user.mfa_secret:
        raise HTTPException(status_code=400, detail="Please setup MFA first")
        
    totp = pyotp.TOTP(current_user.mfa_secret)
    if not totp.verify(mfa_data.code):
        raise HTTPException(status_code=400, detail="Invalid code")
        
    current_user.mfa_enabled = True
    db.commit()
    return {"message": "MFA Enabled Successfully"}

@app.post("/auth/mfa/disable")
def disable_mfa(mfa_data: MFAVerify, background_tasks: BackgroundTasks, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    if not current_user.mfa_enabled:
        raise HTTPException(status_code=400, detail="MFA is not enabled")
    
    # Step 1: Verify MFA code
    totp = pyotp.TOTP(current_user.mfa_secret)
    if not totp.verify(mfa_data.code):
        raise HTTPException(status_code=400, detail="Invalid MFA code")
    
    # Step 2: Generate 6-digit OTP
    import random
    otp = str(random.randint(100000, 999999))
    
    # Step 3: Store OTP with 10-minute expiry
    expiry = (datetime.utcnow() + timedelta(minutes=10)).isoformat()
    current_user.mfa_disable_otp = otp
    current_user.mfa_disable_otp_expiry = expiry
    db.commit()
    
    # Step 4: Send OTP via email
    email_body = f"Your OTP to disable MFA is: {otp}\n\nThis OTP will expire in 10 minutes.\n\nIf you did not request this, please ignore this email."
    background_tasks.add_task(send_email, current_user.email, "Disable MFA - OTP Verification", email_body)
    
    return {"message": "OTP sent to your email", "status": "otp_sent"}

class VerifyOTP(BaseModel):
    otp: str

@app.post("/auth/mfa/disable/verify-otp")
def verify_disable_mfa_otp(otp_data: VerifyOTP, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    if not current_user.mfa_enabled:
        raise HTTPException(status_code=400, detail="MFA is not enabled")
    
    if not current_user.mfa_disable_otp or not current_user.mfa_disable_otp_expiry:
        raise HTTPException(status_code=400, detail="No OTP request found. Please request OTP first.")
    
    # Check if OTP has expired
    expiry_time = datetime.fromisoformat(current_user.mfa_disable_otp_expiry)
    if datetime.utcnow() > expiry_time:
        current_user.mfa_disable_otp = None
        current_user.mfa_disable_otp_expiry = None
        db.commit()
        raise HTTPException(status_code=400, detail="OTP has expired. Please request a new one.")
    
    # Verify OTP
    if current_user.mfa_disable_otp != otp_data.otp:
        raise HTTPException(status_code=400, detail="Invalid OTP")
    
    # Disable MFA
    current_user.mfa_enabled = False
    current_user.mfa_secret = None
    current_user.mfa_disable_otp = None
    current_user.mfa_disable_otp_expiry = None
    db.commit()
    
    return {"message": "MFA Disabled Successfully"}

class VerifyPhone(BaseModel):
    id_token: str

@app.post("/auth/verify-phone")
def verify_phone(data: VerifyPhone, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    try:
        # Verify the ID token
        decoded_token = firebase_auth.verify_id_token(data.id_token)
        phone_number = decoded_token.get('phone_number')
        
        if not phone_number:
            raise HTTPException(status_code=400, detail="No phone number found in token")
            
        # Check if phone number is already used by another user
        existing_user = db.query(User).filter(User.phone_number == phone_number).first()
        if existing_user and existing_user.id != current_user.id:
            raise HTTPException(status_code=400, detail="Phone number already linked to another account")
            
        # Update user's phone number
        current_user.phone_number = phone_number
        db.commit()
        
        return {"message": "Phone number verified and linked successfully", "phone_number": phone_number}
        
    except firebase_auth.InvalidIdTokenError:
        raise HTTPException(status_code=400, detail="Invalid ID token")
    except Exception as e:
        print(f"Error verifying phone: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/auth/login/phone", response_model=Token)
def login_with_phone(data: VerifyPhone, db: Session = Depends(get_db)):
    try:
        # Verify the ID token
        decoded_token = firebase_auth.verify_id_token(data.id_token)
        phone_number = decoded_token.get('phone_number')
        
        if not phone_number:
            raise HTTPException(status_code=400, detail="No phone number found in token")
            
        # Find user by phone number
        user = db.query(User).filter(User.phone_number == phone_number).first()
        if not user:
            raise HTTPException(status_code=404, detail="No account linked to this phone number")
            
        if not user.is_active:
            raise HTTPException(status_code=400, detail="Inactive user")
            
        # Create access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.email, "role": user.role},
            expires_delta=access_token_expires
        )
        
        return {"access_token": access_token, "token_type": "bearer", "mfa_required": False}
        
    except firebase_auth.InvalidIdTokenError:
        raise HTTPException(status_code=400, detail="Invalid ID token")
    except Exception as e:
        print(f"Error logging in with phone: {e}")
        raise HTTPException(status_code=400, detail=str(e))

class DeleteAccount(BaseModel):
    password: str

@app.delete("/auth/account")
def delete_account(delete_data: DeleteAccount, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    # Verify password before deletion
    if not verify_password(delete_data.password, current_user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect password")
    
    # Delete user
    db.delete(current_user)
    db.commit()
    return {"message": "Account deleted successfully"}

@app.post("/upload")
async def upload_file(file: UploadFile = File(...), current_user: User = Depends(get_current_active_user)):
    # Check if user has permission to upload
    if current_user.role not in ["admin", "lawyer"]:
        raise HTTPException(
            status_code=403, 
            detail="Only administrators and lawyers can upload documents"
        )
    
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
    
    file_path = os.path.join(DATA_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    try:
        print(f"Processing upload for: {file.filename}")
        num_docs = ingest_file(file_path)
        print(f"Ingestion complete. Docs: {num_docs}")
        return {"message": "File uploaded and ingested", "filename": file.filename, "chunks": num_docs}
    except Exception as e:
        print(f"Upload failed: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/query")
async def query_index(request: QueryRequest, current_user: User = Depends(get_current_active_user)):
    engine = get_query_engine()
    if not engine:
        raise HTTPException(status_code=404, detail="Index not found. Please upload a file first.")
    
    response = engine.query(request.query)
    return {
        "response": response.response,
        "sources": [
            {
                "file": node.metadata.get("file_name"), 
                "page": node.metadata.get("page_label"),
                "text": node.get_text()[:200] + "..." # Preview text
            }
            for node in response.source_nodes
        ]
    }

class FeedbackCreate(BaseModel):
    query: str
    response: str
    rating: str  # "thumbs_up" or "thumbs_down"
    categories: Optional[List[str]] = None
    comment: Optional[str] = None

@app.post("/feedback")
async def submit_feedback(
    feedback: FeedbackCreate, 
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # Convert categories list to JSON string
    categories_str = ",".join(feedback.categories) if feedback.categories else None
    
    new_feedback = Feedback(
        user_id=current_user.id,
        query=feedback.query,
        response=feedback.response,
        rating=feedback.rating,
        categories=categories_str,
        comment=feedback.comment,
        timestamp=datetime.utcnow().isoformat()
    )
    
    db.add(new_feedback)
    db.commit()
    
    return {"message": "Feedback submitted successfully"}
