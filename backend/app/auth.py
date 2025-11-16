from datetime import datetime, timedelta
from typing import Optional
import sys
import warnings
import logging

# Fix for passlib/bcrypt bug detection issue (Windows and Linux/Production)
# Must be done BEFORE importing passlib.context
warnings.filterwarnings('ignore', category=UserWarning, module='passlib')
# Import and patch bcrypt handler before it initializes
try:
    import passlib.handlers.bcrypt as _bcrypt_module
    import bcrypt as _bcrypt_lib
    
    # Patch _load_backend_mixin to handle bcrypt version detection errors
    # This fixes: AttributeError: module 'bcrypt' has no attribute '__about__'
    bcrypt_class = _bcrypt_module.bcrypt
    if hasattr(bcrypt_class, '_load_backend_mixin'):
        try:
            # Get the original method (could be classmethod or regular method)
            _original_load_backend = bcrypt_class._load_backend_mixin
            try:
                _original_load_backend_func = _original_load_backend.__func__
            except AttributeError:
                _original_load_backend_func = _original_load_backend
            
            @classmethod
            def _safe_load_backend(cls, name, dryrun=False):
                try:
                    return _original_load_backend_func(cls, name, dryrun)
                except AttributeError as e:
                    # Handle missing __about__ attribute in bcrypt
                    if '__about__' in str(e) or '__version__' in str(e):
                        print(f"Warning: bcrypt version detection failed, using fallback: {e}")
                        # Mark backend as loaded anyway
                        try:
                            if hasattr(cls, '_backend_loaded'):
                                cls._backend_loaded = True
                            if hasattr(cls, '_backend'):
                                cls._backend = name
                        except:
                            pass
                        return True
                    raise
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
            
            bcrypt_class._load_backend_mixin = _safe_load_backend
        except Exception as e:
            print(f"Warning: Could not patch _load_backend_mixin: {e}")
    
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

# WARNING: Using encryption instead of hashing for passwords is a SECURITY RISK!
# This allows passwords to be decrypted, which is NOT recommended for production.
# Only use this if you have a specific requirement that cannot be solved with password reset.

from cryptography.fernet import Fernet
import base64
import hashlib

# Logger setup for auth module
logger = logging.getLogger("app.auth")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] %(name)s: %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
logger.setLevel(logging.INFO)

# Initialize encryption key
def _get_encryption_key() -> bytes:
    """Get or generate encryption key for passwords."""
    if settings.password_encryption_key:
        # Use provided key
        key = settings.password_encryption_key.encode()
    else:
        # Generate key from secret_key (not ideal, but works)
        key = hashlib.sha256(settings.secret_key.encode()).digest()
    
    # Fernet requires 32-byte key, base64-encoded
    return base64.urlsafe_b64encode(key[:32])

_fernet = None
def _get_fernet() -> Fernet:
    """Get Fernet instance for encryption/decryption."""
    global _fernet
    if _fernet is None:
        encryption_key = _get_encryption_key()
        _fernet = Fernet(encryption_key)
    return _fernet

def encrypt_password(password: str) -> str:
    """
    Encrypt a password (decryptable).
    WARNING: This is a security risk! Passwords should be hashed, not encrypted.
    """
    try:
        fernet = _get_fernet()
        logger.info("Encrypting password (length=%d)", len(password or ""))
        encrypted = fernet.encrypt(password.encode('utf-8'))
        # Log only prefix for safety
        logger.info("Encryption complete (token_prefix=%s...)", encrypted.decode('utf-8')[:16])
        return encrypted.decode('utf-8')
    except Exception as e:
        logger.error("Password encryption error: %s", e)
        raise

def decrypt_password(encrypted_password: str) -> str:
    """
    Decrypt a password.
    WARNING: This is only possible because we're using encryption instead of hashing.
    """
    if not encrypted_password or not encrypted_password.strip():
        raise ValueError("Encrypted password cannot be empty")
    
    # Check if it looks like a bcrypt hash (starts with $2a$, $2b$, or $2y$)
    if encrypted_password.startswith('$2'):
        raise ValueError("This is a bcrypt hash (old system), not an encrypted password. Bcrypt hashes cannot be decrypted - they are one-way hashes. Only passwords encrypted with Fernet (new system) can be decrypted. To decrypt, you need to use a password that was encrypted with the /encrypt endpoint.")
    
    try:
        fernet = _get_fernet()
        logger.info("Attempting decryption (token_prefix=%s...)", encrypted_password[:16])
        decrypted = fernet.decrypt(encrypted_password.encode('utf-8'))
        logger.info("Decryption successful (decrypted_length=%d)", len(decrypted.decode('utf-8')))
        return decrypted.decode('utf-8')
    except Exception as e:
        error_msg = str(e) if str(e) else f"{type(e).__name__}"
        error_type = type(e).__name__
        logger.error("Password decryption error: %s - %s", error_type, error_msg)
        # Provide more helpful error message
        if "InvalidToken" in error_type or "Invalid" in error_msg:
            raise ValueError(f"Invalid encrypted password format. The password may be corrupted, encrypted with a different key, or not a valid Fernet token. Error: {error_msg}")
        raise ValueError(f"Decryption failed ({error_type}): {error_msg}")

def verify_password(plain_password: str, stored_password: str) -> bool:
    """
    Verify a password against stored password.
    Handles both bcrypt hashes (old system) and Fernet encrypted passwords (new system).
    """
    if not stored_password or not plain_password:
        return False
    
    # Check if it's a bcrypt hash (old system - starts with $2a$, $2b$, or $2y$)
    if stored_password.startswith('$2'):
        # Use bcrypt verification for old passwords
        try:
            logger.info("Verifying password using bcrypt")
            return pwd_context.verify(plain_password, stored_password)
        except Exception as e:
            logger.error("Bcrypt password verification error: %s", e)
            return False
    
    # Otherwise, it's a Fernet encrypted password (new system)
    try:
        logger.info("Verifying password using Fernet decryption (stored_prefix=%s...)", (stored_password or "")[:16])
        decrypted = decrypt_password(stored_password)
        return decrypted == plain_password
    except Exception as e:
        logger.error("Password verification error: %s", e)
        return False

def get_password_hash(password: str) -> str:
    """
    Encrypt a password (stored as "hash" but actually encrypted).
    WARNING: This uses encryption, not hashing. Passwords can be decrypted!
    """
    logger.info("Hashing (encrypting) password for storage (length=%d)", len(password or ""))
    token = encrypt_password(password)
    logger.info("Password stored (token_prefix=%s...)", token[:16])
    return token

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