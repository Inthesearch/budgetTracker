from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from .config import settings
import asyncio
from urllib.parse import urlparse, parse_qs, urlencode
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def clean_database_url(url: str) -> str:
    """Clean database URL by removing unsupported parameters for asyncpg."""
    if url.startswith("postgresql://"):
        # Parse the URL
        parsed = urlparse(url)
        query_params = parse_qs(parsed.query)
        
        # Remove unsupported parameters for asyncpg
        unsupported_params = [
            'sslmode', 'sslcert', 'sslkey', 'sslrootcert', 
            'channel_binding', 'application_name', 'client_encoding',
            'connect_timeout', 'options', 'target_session_attrs'
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

def create_database_engines():
    """Create database engines with proper error handling."""
    try:
        if settings.database_url.startswith("postgresql"):
            # Clean the URL for asyncpg
            clean_sync_url = clean_database_url(settings.database_url)
            async_database_url = clean_sync_url.replace("postgresql://", "postgresql+asyncpg://")
            
            logger.info(f"Original database URL: {settings.database_url}")
            logger.info(f"Clean sync URL: {clean_sync_url}")
            logger.info(f"Async database URL: {async_database_url}")
            
            # Create sync engine for migrations and sync operations
            sync_engine = create_engine(
                clean_sync_url, 
                echo=settings.debug,
                pool_pre_ping=True,
                pool_recycle=300
            )
            
            # Create async engine with SSL configuration
            engine = create_async_engine(
                async_database_url, 
                echo=settings.debug,
                pool_pre_ping=True,
                pool_recycle=300,
                # SSL configuration for production
                connect_args={
                    "server_settings": {
                        "application_name": "budget_tracker_app"
                    }
                }
            )
            
            return engine, sync_engine
            
        else:
            # For SQLite (development)
            engine = create_engine(settings.database_url, echo=settings.debug)
            return engine, engine
            
    except Exception as e:
        logger.error(f"Failed to create database engines: {e}")
        raise

# Create engines
try:
    engine, sync_engine = create_database_engines()
    AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)
except Exception as e:
    logger.error(f"Database initialization failed: {e}")
    # Fallback to SQLite for development
    engine = create_engine("sqlite:///./budget_tracker.db", echo=settings.debug)
    sync_engine = engine
    AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Dependency to get database session
async def get_db():
    if settings.database_url.startswith("postgresql"):
        async with AsyncSessionLocal() as session:
            try:
                yield session
            finally:
                await session.close()
    else:
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

# For sync operations (when needed)
def get_sync_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 