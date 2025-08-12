from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy.future import select
from datetime import timedelta, datetime
import secrets
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from ..database import get_db
from ..models import User, PasswordReset
from ..schemas import (
    UserCreate, UserLogin, UserResponse, Token, 
    PasswordResetRequest, PasswordResetConfirm, BaseResponse
)
from ..auth import get_password_hash, authenticate_user, create_access_token, get_current_user
from ..config import settings

router = APIRouter(tags=["Authentication"])

@router.post("/register", response_model=BaseResponse)
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    """Register a new user."""
    try:
        # Check if user already exists

        print(user_data.email)
        print(user_data.username)

        result = await db.execute(select(User).where(
            (User.email == user_data.email) | (User.username == user_data.username)
        ))
        existing_user = result.scalars().first()

        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email or username already registered"
            )
        
        # Create new user
        hashed_password = get_password_hash(user_data.password)
        db_user = User(
            email=user_data.email,
            username=user_data.username,
            hashed_password=hashed_password,
            full_name=user_data.full_name
        )
        
        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)
        
        return BaseResponse(
            success=True,
            message="User registered successfully",
            data={"user_id": db_user.id}
        )
        
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email or username already registered"
        )

@router.post("/login", response_model=Token)
async def login(user_credentials: UserLogin, db: AsyncSession = Depends(get_db)):
    """Login user and return access token."""
    user = await authenticate_user(db, user_credentials.email, user_credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email},
        expires_delta=access_token_expires
    )
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.access_token_expire_minutes * 60
    )

@router.post("/forgotPass", response_model=BaseResponse)
async def forgot_password(request: PasswordResetRequest, db: Session = Depends(get_db)):
    """Send password reset email."""
    user = db.query(User).filter(User.email == request.email).first()
    if not user:
        # Don't reveal if email exists or not for security
        return BaseResponse(
            success=True,
            message="If the email exists, a password reset link has been sent"
        )
    
    # Generate reset token
    token = secrets.token_urlsafe(32)
    expires_at = datetime.utcnow() + timedelta(hours=24)
    
    # Save reset token
    reset_record = PasswordReset(
        email=request.email,
        token=token,
        expires_at=expires_at
    )
    db.add(reset_record)
    db.commit()
    
    # Send email (if SMTP is configured)
    if settings.smtp_username and settings.smtp_password:
        try:
            msg = MIMEMultipart()
            msg['From'] = settings.smtp_username
            msg['To'] = request.email
            msg['Subject'] = "Password Reset Request"
            
            reset_url = f"http://localhost:3000/reset-password?token={token}"
            body = f"""
            Hello {user.full_name or user.username},
            
            You have requested a password reset for your Budget Tracker account.
            
            Click the following link to reset your password:
            {reset_url}
            
            This link will expire in 24 hours.
            
            If you didn't request this reset, please ignore this email.
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            server = smtplib.SMTP(settings.smtp_server, settings.smtp_port)
            server.starttls()
            server.login(settings.smtp_username, settings.smtp_password)
            server.send_message(msg)
            server.quit()
            
        except Exception as e:
            # Log error but don't fail the request
            print(f"Email sending failed: {e}")
    
    return BaseResponse(
        success=True,
        message="If the email exists, a password reset link has been sent"
    )

@router.post("/reset-password", response_model=BaseResponse)
async def reset_password(reset_data: PasswordResetConfirm, db: Session = Depends(get_db)):
    """Reset password using token."""
    # Find valid reset record
    reset_record = db.query(PasswordReset).filter(
        PasswordReset.token == reset_data.token,
        PasswordReset.is_used == False,
        PasswordReset.expires_at > datetime.utcnow()
    ).first()
    
    if not reset_record:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
    
    # Find user
    user = db.query(User).filter(User.email == reset_record.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User not found"
        )
    
    # Update password
    user.hashed_password = get_password_hash(reset_data.new_password)
    reset_record.is_used = True
    
    db.commit()
    
    return BaseResponse(
        success=True,
        message="Password reset successfully"
    )

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information."""
    return current_user 