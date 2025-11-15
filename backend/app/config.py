from pydantic_settings import BaseSettings
from typing import List
import os
from dotenv import load_dotenv

# Debug: Check current working directory and .env file
print(f"Current working directory: {os.getcwd()}")

# Check if we're in production (Render sets RENDER=true)
is_production = os.getenv("RENDER", "false").lower() == "true"
print(f"Running in production: {is_production}")

# Try to load .env file (only in development)
if not is_production:
    print(f"Loading .env file for development...")
    load_dotenv()
    # Also try loading from specific path
    import pathlib
    backend_dir = pathlib.Path(__file__).parent.parent
    env_path = backend_dir / ".env"
    print(f"Looking for .env at: {env_path}")
    if env_path.exists():
        print(f".env file exists at {env_path}")
        load_dotenv(env_path)
    else:
        print(f".env file does not exist at {env_path}")
else:
    print(f"In production - using environment variables from platform")

# Debug: Check if DATABASE_URL is loaded
database_url_from_env = os.getenv("DATABASE_URL")
print(f"DATABASE_URL from environment: {database_url_from_env}")

class Settings(BaseSettings):
    # Database
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./budget_tracker.db")
    
    # JWT
    secret_key: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    algorithm: str = os.getenv("ALGORITHM", "HS256")
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    
    # Password encryption key (for decryptable passwords - SECURITY WARNING: Not recommended!)
    # Generate a new key with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
    password_encryption_key: str = os.getenv("PASSWORD_ENCRYPTION_KEY", "")
    
    # Email
    smtp_server: str = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port: int = int(os.getenv("SMTP_PORT", "587"))
    smtp_username: str = os.getenv("SMTP_USERNAME", "")
    smtp_password: str = os.getenv("SMTP_PASSWORD", "")
    
    # Application
    debug: bool = os.getenv("DEBUG", "True").lower() == "true"
    
    # print(f"CORS Origins: {os.getenv('CORS_ORIGINS')}")

    # CORS Origins - handle both environment variable and default list
    @property
    def cors_origins(self) -> List[str]:
        cors_env = os.getenv("CORS_ORIGINS")
        if cors_env:
            # If CORS_ORIGINS is set, try to parse it as comma-separated values
            origins = [origin.strip() for origin in cors_env.split(",")]
            print(f"CORS Origins from environment: {origins}")
            return origins
        else:
            # Default origins for development
            default_origins = [
                "http://localhost:3000",
                "http://127.0.0.1:3000",
                "http://localhost:5173",
                "http://127.0.0.1:5173",
                "http://localhost:3001",
                "http://127.0.0.1:3001",
                "http://localhost:8080",
                "http://127.0.0.1:8080",
                # Add common production domains
                "https://budget-tracker-frontend.vercel.app",
                "https://budget-tracker-frontend.netlify.app",
                "https://budget-tracker-app.vercel.app",
                "https://budget-tracker-app.netlify.app"
            ]
            print(f"CORS Origins (default): {default_origins}")
            return default_origins
    
    class Config:
        env_file = ".env"

settings = Settings() 