from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import uvicorn
from sqlalchemy import inspect
import sys
import asyncio

# Fix for Windows: psycopg3 requires SelectorEventLoop, not ProactorEventLoop
if sys.platform == 'win32':
    # Set the event loop policy to use SelectorEventLoop on Windows
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from .config import settings
from .database import engine, Base
# from .database import sync_engine  # Not needed for async-only codebase
from .routers import auth, category, subcategory, transaction, account

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Checking database tables...")
    try:
        # For SQLite, use a workaround: create tables with sync connection if async fails
        if "sqlite" in settings.database_url.lower():
            # Use synchronous SQLite connection for table creation (workaround for aiosqlite issue)
            from sqlalchemy import create_engine as create_sync_engine
            # Convert async URL to sync URL
            sync_url = settings.database_url.replace("sqlite+aiosqlite://", "sqlite://")
            if sync_url == settings.database_url:  # If no replacement happened, it might already be sqlite://
                sync_url = settings.database_url
            sync_engine = create_sync_engine(sync_url, connect_args={"check_same_thread": False})
            Base.metadata.create_all(bind=sync_engine)
            sync_engine.dispose()
            print("Database tables created successfully using sync connection!")
        else:
            # For PostgreSQL, use async connection
            async with engine.begin() as conn:
                def create_tables(sync_conn):
                    Base.metadata.create_all(bind=sync_conn)
                await conn.run_sync(create_tables)
            print("Database tables created successfully!")
    except Exception as e:
        print(f"Database setup error: {e}")
        import traceback
        traceback.print_exc()
        print("Note: You can create tables manually using: alembic upgrade head")
        print("Continuing with startup...")
    
    yield
    # Shutdown
    await engine.dispose()
    print("Shutting down...")

app = FastAPI(
    title="Budget Tracker API",
    description="A comprehensive budget tracking API with user management, categories, transactions, and analytics",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware with detailed configuration
print(f"Configuring CORS with origins: {settings.cors_origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/v1")
app.include_router(category.router, prefix="/api/v1")
app.include_router(subcategory.router, prefix="/api/v1")
app.include_router(transaction.router, prefix="/api/v1")
app.include_router(account.router, prefix="/api/v1")

@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Budget Tracker API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "message": "API is running"}

@app.get("/cors-test")
async def cors_test():
    """Test endpoint to check CORS configuration."""
    return {
        "message": "CORS test successful",
        "allowed_origins": settings.cors_origins,
        "timestamp": "2024-01-01T00:00:00Z"
    }

# Global exception handler
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "message": exc.detail,
            "error_code": f"HTTP_{exc.status_code}"
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "Internal server error",
            "error_code": "INTERNAL_ERROR"
        }
    )

if __name__ == "__main__":
    # Ensure event loop policy is set for Windows before uvicorn starts
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        loop="asyncio"  # Explicitly use asyncio loop
    ) 