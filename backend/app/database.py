from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from .config import settings
import asyncio
from urllib.parse import urlparse, parse_qs, urlencode

def clean_database_url(url: str) -> str:
    """Clean database URL by removing unsupported parameters for asyncpg."""
    if url.startswith("postgresql://"):
        # Parse the URL
        parsed = urlparse(url)
        query_params = parse_qs(parsed.query)
        
        # Remove unsupported parameters for asyncpg and psycopg2
        unsupported_params = [
            'sslmode', 'sslcert', 'sslkey', 'sslrootcert', 'channel_binding',
            'connect_timeout', 'application_name', 'client_encoding', 'timezone',
            'options', 'target_session_attrs', 'gssencmode', 'krbsrvname',
            'service', 'requiressl', 'sslmode', 'sslcert', 'sslkey', 'sslrootcert',
            'sslcrl', 'sslcipher', 'sslcompression', 'prefer_query_mode',
            'target_session_attrs', 'session_authorization', 'tcp_user_timeout',
            'replication', 'fallback_application_name', 'keepalives', 'keepalives_idle',
            'keepalives_interval', 'keepalives_count', 'password_encryption'
        ]
        for param in unsupported_params:
            query_params.pop(param, None)
        
        # Rebuild the URL
        clean_query = urlencode(query_params, doseq=True) if query_params else ""
        clean_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        if clean_query:
            clean_url += f"?{clean_query}"
        
        return clean_url
    return url

# For async operations (PostgreSQL)
if settings.database_url.startswith("postgresql"):
    try:
        print("=== Starting PostgreSQL connection setup ===")
        # Clean the URL for asyncpg
        clean_sync_url = clean_database_url(settings.database_url)
        async_database_url = clean_sync_url.replace("postgresql://", "postgresql+asyncpg://")
        
        print(f"Original database URL: {settings.database_url}")
        print(f"Clean sync URL: {clean_sync_url}")
        print(f"Async database URL: {async_database_url}")
        
        print("Creating async engine only (skipping sync engine)...")
        # Create async engine only - avoid psycopg2 issues
        engine = create_async_engine(
            async_database_url, 
            echo=settings.debug,
            pool_pre_ping=True,
            pool_recycle=300
        )
        print("Async engine created successfully")
        
        AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        
        print("PostgreSQL connection configured successfully")
        print(f"Database URL: {settings.database_url}")
        print(f"Engine type: {type(engine)}")
        print("=== PostgreSQL setup completed ===")
        
    except Exception as e:
        print(f"PostgreSQL connection failed: {e}")
        print(f"Exception type: {type(e).__name__}")
        print("Falling back to SQLite for development")
        print(f"Original database URL: {settings.database_url}")
        
        # Fallback to SQLite - use async engine
        fallback_url = "sqlite+aiosqlite:///./budget_tracker.db"
        print(f"Fallback URL: {fallback_url}")
        engine = create_async_engine(fallback_url, echo=settings.debug)
        AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        settings.database_url = fallback_url
else:
    # For SQLite (development) - use async engine
    async_url = settings.database_url.replace("sqlite://", "sqlite+aiosqlite://")
    engine = create_async_engine(async_url, echo=settings.debug)
    AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

Base = declarative_base()

# Dependency to get database session
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

# Note: Sync database operations removed to avoid psycopg2 compatibility issues
# All operations should use async sessions 