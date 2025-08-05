from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import uvicorn
from sqlalchemy import inspect

from .config import settings
from .database import engine, Base
# from .database import sync_engine  # Not needed for async-only codebase
from .routers import auth, category, subcategory, transaction, account

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Checking database tables...")
    try:
        # For now, just create all tables
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("Database tables created successfully!")
    except Exception as e:
        print(f"Database setup error: {e}")
        print("Continuing with startup...")
    
    yield
    # Shutdown
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
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug
    ) 