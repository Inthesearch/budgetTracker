from pydantic_settings import BaseSettings
from typing import List
import os
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    # Database
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./budget_tracker.db")
    
    # JWT
    secret_key: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    algorithm: str = os.getenv("ALGORITHM", "HS256")
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    
    # Email
    smtp_server: str = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port: int = int(os.getenv("SMTP_PORT", "587"))
    smtp_username: str = os.getenv("SMTP_USERNAME", "")
    smtp_password: str = os.getenv("SMTP_PASSWORD", "")
    
    # Application
    debug: bool = os.getenv("DEBUG", "True").lower() == "true"
    
    print(f"CORS Origins: {os.getenv("CORS_ORIGINS")}")

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