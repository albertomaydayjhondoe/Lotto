"""
Application configuration settings.
"""
from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""
    
    PROJECT_NAME: str = "Orquestador API"
    VERSION: str = "0.1.0"
    DESCRIPTION: str = "API para el Orquestador del Sistema Maestro de IA"
    
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@postgres:5432/stakazo_db"
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = ["*"]
    
    # API
    API_V1_STR: str = ""
    
    # File Upload
    MAX_UPLOAD_SIZE: int = 500 * 1024 * 1024  # 500MB
    UPLOAD_DIR: str = "/tmp/uploads"  # Deprecated, use VIDEO_STORAGE_DIR
    VIDEO_STORAGE_DIR: str = "storage/videos"  # Base directory for video storage
    
    # JWT
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    class Config:
        case_sensitive = True
        env_file = ".env"


settings = Settings()
