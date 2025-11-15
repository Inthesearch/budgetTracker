from datetime import datetime, timedelta
from typing import Optional
import sys
import warnings

# Fix for passlib/bcrypt bug detection issue on Windows
# Must be done BEFORE importing passlib.context
if sys.platform == 'win32':
    warnings.filterwarnings('ignore', category=UserWarning, module='passlib')
    # Import and patch bcrypt handler before it initializes
    try:
        import passlib.handlers.bcrypt as _bcrypt_module
        import bcrypt as _bcrypt_lib
        
        # Patch the actual bcrypt.hashpw function to auto-truncate passwords > 72 bytes
        # This will fix the bug detection issue
        _original_hashpw = _bcrypt_lib.hashpw
        def _safe_hashpw(password, salt):
            # Truncate password to 72 bytes if necessary
            if isinstance(password, bytes):
                if len(password) > 72:
                    password = password[:72]
            elif isinstance(password, str):
                password_bytes = password.encode('utf-8')
                if len(password_bytes) > 72:
                    password_bytes = password_bytes[:72]
                    password = password_bytes.decode('utf-8', errors='ignore').encode('utf-8')
                else:
                    password = password_bytes
            return _original_hashpw(password, salt)
        
        # Replace bcrypt.hashpw with our safe version
        _bcrypt_lib.hashpw = _safe_hashpw
        # Also patch it in the passlib module
        _bcrypt_module._bcrypt = _bcrypt_lib
        
        # Patch _finalize_backend_mixin to skip bug detection
        bcrypt_class = _bcrypt_module.bcrypt
        if hasattr(bcrypt_class, '_finalize_backend_mixin'):
            try:
                _original_finalize = bcrypt_class._finalize_backend_mixin.__func__
            except AttributeError:
                _original_finalize = bcrypt_class._finalize_backend_mixin
            
            @classmethod
            def _safe_finalize(cls, name, dryrun=False):
                try:
                    return _original_finalize(cls, name, dryrun)
                except ValueError as e:
                    error_str = str(e).lower()
                    if "72 bytes" in error_str or "cannot be longer than 72" in error_str:
                        # Bug detection failed - mark backend as loaded anyway
                        try:
                            if hasattr(cls, '_backend_loaded'):
                                cls._backend_loaded = True
                            if hasattr(cls, '_backend'):
                                cls._backend = name
                        except:
                            pass
                        return True
                    raise
            
            bcrypt_class._finalize_backend_mixin = _safe_finalize
        
        # Patch detect_wrap_bug as backup
        _original_detect = getattr(_bcrypt_module.bcrypt, 'detect_wrap_bug', None)
        if _original_detect:
            def _safe_detect_wrap_bug(ident):
                try:
                    return _original_detect(ident)
                except ValueError as e:
                    if "72 bytes" in str(e) or "cannot be longer than 72" in str(e):
                        return False
                    raise
            _bcrypt_module.bcrypt.detect_wrap_bug = _safe_detect_wrap_bug
            
    except Exception as e:
        print(f"Warning: Could not patch bcrypt: {e}")
        import traceback
        traceback.print_exc()

from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from .config import settings
from .database import get_db
from .models import User
from .schemas import TokenData
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# Create password context (bug detection should be patched by now)
# Pre-initialize the backend to avoid lazy initialization errors
try:
    # Force backend initialization now (before first use) to catch errors early
    from passlib.handlers.bcrypt import bcrypt
    # Try to set backend explicitly - our patches should catch the error
    try:
        bcrypt.set_backend("bcrypt")
    except ValueError as e:
        if "72 bytes" in str(e) or "cannot be longer than 72" in str(e):
            # Bug detection failed - mark backend as loaded manually
            print(f"Warning: bcrypt bug detection failed, marking backend as loaded: {e}")
            # Manually mark backend as loaded to skip bug detection
            if hasattr(bcrypt, '_backend'):
                bcrypt._backend = 'bcrypt'
            if hasattr(bcrypt, '_backend_loaded'):
                bcrypt._backend_loaded = True
        else:
            raise
except Exception as e:
    print(f"Warning: Error pre-initializing bcrypt backend: {e}")

# Now create the context
try:
    pwd_context = CryptContext(
        schemes=["bcrypt"],
        deprecated="auto",
    )
except Exception as e:
    print(f"Warning: Error creating password context: {e}")
    # Fallback: create context anyway
    pwd_context = CryptContext(
        schemes=["bcrypt"],
        deprecated="auto",
    )

# JWT token security
security = HTTPBearer()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    try:
        # Truncate password to 72 bytes if necessary (bcrypt limitation)
        password_bytes = plain_password.encode('utf-8')
        if len(password_bytes) > 72:
            password_bytes = password_bytes[:72]
            plain_password = password_bytes.decode('utf-8', errors='ignore')
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        print(f"Password verification error: {e}")
        return False

def get_password_hash(password: str) -> str:
    """Hash a password."""
    # Truncate password to 72 bytes if necessary (bcrypt limitation)
    password_bytes = password.encode('utf-8')
    if len(password_bytes) > 72:
        password_bytes = password_bytes[:72]
        password = password_bytes.decode('utf-8', errors='ignore')
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt

def verify_token(token: str) -> Optional[TokenData]:
    """Verify and decode a JWT token."""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        user_id: int = payload.get("sub")
        email: str = payload.get("email")
        if user_id is None or email is None:
            return None
        return TokenData(user_id=user_id, email=email)
    except JWTError:
        return None

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Get the current authenticated user."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    token_data = verify_token(credentials.credentials)
    if token_data is None:
        raise credentials_exception
    
    result = await db.execute(select(User).where(User.id == token_data.user_id))
    user = result.scalars().first()
    if user is None:
        raise credentials_exception
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    return user

async def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    """Authenticate a user with email and password."""
    print(f"Authenticating user with email: {email}")
    
    # Debug: Check what database we're using
    from .config import settings
    print(f"Current database URL: {settings.database_url}")
    
    # Debug: Check if there are any users in the database
    all_users_result = await db.execute(select(User))
    all_users = all_users_result.scalars().all()
    print(f"Total users in database: {len(all_users)}")
    for u in all_users:
        print(f"  - User ID: {u.id}, Email: {u.email}, Active: {u.is_active}")
    
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalars().first()
    print(f"User found: {user is not None}")
    if not user:
        print("No user found with this email")
        return None
    print(f"Verifying password for user: {user.email}")
    if not verify_password(password, user.hashed_password):
        print("Password verification failed")
        return None
    print("Password verification successful")
    return user 