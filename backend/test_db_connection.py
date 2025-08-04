import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

async def test_database_connection():
    print("=== Database Connection Test ===")
    
    # Check environment variables
    database_url = os.getenv("DATABASE_URL")
    print(f"Database URL: {database_url}")
    
    if not database_url:
        print("❌ DATABASE_URL not found in environment variables")
        return
    
    try:
        # Test the database configuration
        from app.database import engine, sync_engine
        
        print("✅ Database engines created successfully")
        
        # Test sync connection
        print("\n=== Testing Sync Connection ===")
        try:
            with sync_engine.connect() as conn:
                result = conn.execute("SELECT 1")
                print("✅ Sync connection successful")
        except Exception as e:
            print(f"❌ Sync connection failed: {e}")
        
        # Test async connection
        print("\n=== Testing Async Connection ===")
        try:
            async with engine.begin() as conn:
                result = await conn.execute("SELECT 1")
                print("✅ Async connection successful")
        except Exception as e:
            print(f"❌ Async connection failed: {e}")
            
    except Exception as e:
        print(f"❌ Database configuration error: {e}")
        print(f"Error type: {type(e).__name__}")

if __name__ == "__main__":
    asyncio.run(test_database_connection()) 