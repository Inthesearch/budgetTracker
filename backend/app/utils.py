"""
Utility functions for the application
"""
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from .models import User
from .auth import decrypt_password

def _normalize_whitespace(value: str) -> str:
    """Collapse multiple spaces and trim."""
    return " ".join((value or "").strip().split())

def format_category_name(name: str) -> str:
    """Format category names for display consistently."""
    normalized = _normalize_whitespace(name)
    return normalized.title()

def format_subcategory_name(name: str) -> str:
    """Format sub-category names for display consistently."""
    normalized = _normalize_whitespace(name)
    return normalized.title()

def format_account_name(name: str) -> str:
    """Format account names for display consistently."""
    normalized = _normalize_whitespace(name)
    return normalized.title()

async def get_user_decrypted_password(user_id: int, db: AsyncSession) -> Optional[str]:
    """
    Utility function to get a user's decrypted password.
    Use this in your routers or other parts of the application.
    
    Example usage in a router:
        from app.utils import get_user_decrypted_password
        password = await get_user_decrypted_password(user_id, db)
    """
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()
    
    if not user:
        return None
    
    try:
        return decrypt_password(user.hashed_password)
    except Exception as e:
        print(f"Error decrypting password: {e}")
        return None
