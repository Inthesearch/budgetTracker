from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from .config import settings
import asyncio

# For async operations (PostgreSQL)
if settings.database_url.startswith("postgresql"):

    sync_engine = create_engine(settings.database_url, echo=settings.debug)
    
    # Convert to async URL
    async_database_url = settings.database_url.replace("postgresql://", "postgresql+asyncpg://")
    engine = create_async_engine(async_database_url, echo=settings.debug)
    AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    SessionLocal = None
else:
    # For SQLite (development)
    engine = create_engine(settings.database_url, echo=settings.debug)
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