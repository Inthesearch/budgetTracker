"""
Script to decrypt a user's password from the database
Usage: python decrypt_user_password.py <user_id>
"""
import sys
import os
import asyncio

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.auth import decrypt_password
from app.database import AsyncSessionLocal
from app.models import User
from sqlalchemy import select

async def decrypt_user_password(user_id: int):
    """Decrypt a user's password from the database."""
    async with AsyncSessionLocal() as db:
        # Get user from database
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalars().first()
        
        if not user:
            print(f"User with ID {user_id} not found")
            return None
        
        try:
            # Decrypt the password
            decrypted = decrypt_password(user.hashed_password)
            print(f"User: {user.email}")
            print(f"Decrypted Password: {decrypted}")
            return decrypted
        except Exception as e:
            print(f"Error decrypting password: {e}")
            return None

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python decrypt_user_password.py <user_id>")
        sys.exit(1)
    
    user_id = int(sys.argv[1])
    asyncio.run(decrypt_user_password(user_id))

