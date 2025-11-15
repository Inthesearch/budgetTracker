"""
Example: How to use decrypt_password function

This file shows different ways to call the decrypt_password function.
"""

# Method 1: Import and use directly in Python code
from app.auth import decrypt_password

# Example: Decrypt a password from database
def example_decrypt_from_db():
    # Assuming you have an encrypted password from the database
    encrypted_password = "gAAAAABl..."  # This would come from user.hashed_password
    
    try:
        decrypted = decrypt_password(encrypted_password)
        print(f"Decrypted password: {decrypted}")
        return decrypted
    except Exception as e:
        print(f"Error decrypting: {e}")
        return None

# Method 2: Use in an async function (like in routers)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models import User

async def example_decrypt_user_password(user_id: int, db: AsyncSession):
    """Example of decrypting a user's password from database."""
    # Get user from database
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()
    
    if not user:
        return None
    
    # Decrypt the password
    try:
        decrypted = decrypt_password(user.hashed_password)
        return decrypted
    except Exception as e:
        print(f"Error decrypting password: {e}")
        return None

# Method 3: Use in a script/CLI tool
if __name__ == "__main__":
    # Example usage
    encrypted = input("Enter encrypted password: ")
    try:
        decrypted = decrypt_password(encrypted)
        print(f"Decrypted: {decrypted}")
    except Exception as e:
        print(f"Error: {e}")

