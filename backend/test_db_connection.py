import asyncio
import os
from dotenv import load_dotenv
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
            print(f"Error type: {type(e).__name__}")
        
        # Test async connection
        print("\n=== Testing Async Connection ===")
        try:
            async with engine.begin() as conn:
                result = await conn.execute("SELECT 1")
                print("✅ Async connection successful")
        except Exception as e:
            print(f"❌ Async connection failed: {e}")
            print(f"Error type: {type(e).__name__}")
            
    except Exception as e:
        print(f"❌ Database configuration error: {e}")
        print(f"Error type: {type(e).__name__}")
        
        # Try to get more details about the error
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")

def test_url_cleaning():
    print("\n=== Testing URL Cleaning ===")
    from app.database import clean_database_url
    
    test_urls = [
        "postgresql://user:pass@host:port/db?sslmode=require&channel_binding=prefer",
        "postgresql://user:pass@host:port/db?application_name=test&sslmode=require",
        "sqlite:///./test.db"
    ]
    
    for url in test_urls:
        cleaned = clean_database_url(url)
        print(f"Original: {url}")
        print(f"Cleaned:  {cleaned}")
        print()

if __name__ == "__main__":
    test_url_cleaning()
    asyncio.run(test_database_connection()) 