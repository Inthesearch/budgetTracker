"""
Utility functions for the application
"""
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from .models import User
from .auth import decrypt_password

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
