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
    # Development: SQLite (fallback) or PostgreSQL (recommended)
    # Production: PostgreSQL (via environment variable)
    DATABASE_URL: str = "sqlite+aiosqlite:///./stakazo.db"
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = ["*"]
    
    # API
    API_V1_STR: str = ""
    
    # File Upload
    MAX_UPLOAD_SIZE: int = 500 * 1024 * 1024  # 500MB
    UPLOAD_DIR: str = "/tmp/uploads"  # Deprecated, use VIDEO_STORAGE_DIR
    VIDEO_STORAGE_DIR: str = "storage/videos"  # Base directory for video storage
    
    # JWT
    SECRET_KEY: str = "dev-secret-key-change-in-production"  # Override via env var
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Worker Configuration
    WORKER_POLL_INTERVAL: int = 2  # seconds between job checks
    MAX_JOB_RETRIES: int = 3  # maximum retry attempts per job
    WORKER_ENABLED: bool = False  # enable background worker loop
    
    # Debug Configuration
    DEBUG_ENDPOINTS_ENABLED: bool = True  # enable /debug endpoints (disable in production)
    
    # Publishing Scheduler Configuration
    DEFAULT_TIMEZONE: str = "Europe/Madrid"
    PLATFORM_WINDOWS: dict = {
        "instagram": {"start_hour": 18, "end_hour": 23},
        "tiktok": {"start_hour": 16, "end_hour": 24},
        "youtube": {"start_hour": 17, "end_hour": 22}
    }
    MIN_GAP_MINUTES: dict = {
        "instagram": 60,
        "tiktok": 30,
        "youtube": 90
    }
    
    class Config:
        case_sensitive = True
        env_file = ".env"
        extra = "ignore"  # Ignore extra fields from .env


settings = Settings()
