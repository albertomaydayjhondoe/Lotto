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
    
    # Orchestrator Configuration
    ORCHESTRATOR_ENABLED: bool = False  # enable autonomous orchestrator loop
    ORCHESTRATOR_INTERVAL_SECONDS: int = 2  # seconds between orchestrator cycles
    
    # Live Telemetry Configuration (PASO 6.4)
    TELEMETRY_INTERVAL_SECONDS: int = 3  # seconds between telemetry broadcasts
    
    # AI Global Worker Configuration (PASO 7.0)
    AI_WORKER_ENABLED: bool = True  # enable AI global worker
    AI_WORKER_INTERVAL_SECONDS: int = 30  # seconds between AI reasoning cycles
    
    # Meta Autonomous System Configuration (PASO 10.7)
    META_AUTO_ENABLED: bool = True  # enable Meta autonomous worker
    META_AUTO_INTERVAL_SECONDS: int = 1800  # seconds between optimization cycles (30 min)
    META_AUTO_MODE: str = "suggest"  # "suggest" or "auto" - controls execution mode
    
    # AI History Configuration (PASO 8.1)
    AI_HISTORY_MAX_LIMIT: int = 100  # max items per history query
    
    # LLM Provider Configuration (PASO 7.2 - PASO 7.3)
    # Operation Mode
    AI_LLM_MODE: str = "stub"  # "stub" or "live" - controls whether to use real API calls
    
    # OpenAI GPT-5 Configuration
    OPENAI_API_KEY: str | None = None  # OpenAI API key (env: OPENAI_API_KEY)
    AI_OPENAI_MODEL_NAME: str = "gpt-4"  # OpenAI model (use gpt-4 until gpt-5 is available)
    
    # Google Gemini 2.0 Configuration
    GEMINI_API_KEY: str | None = None  # Google Gemini API key (env: GEMINI_API_KEY)
    AI_GEMINI_MODEL_NAME: str = "gemini-2.0-flash-exp"  # Gemini model identifier
    
    # Note: PASO 7.3 activates real LLM integration
    #       - If AI_LLM_MODE="stub" or API keys are missing → stub mode (safe default)
    #       - If AI_LLM_MODE="live" and API keys present → real API calls with fallback
    
    # Security / Credentials Encryption (PASO 5.1)
    CREDENTIALS_ENCRYPTION_KEY: str | None = None  # Fernet key for encrypting social account credentials
    
    # Meta Insights Collector Configuration (PASO 10.7)
    META_INSIGHTS_MODE: str = "stub"  # "stub" or "live" - controls Meta API integration
    META_INSIGHTS_SYNC_INTERVAL_MINUTES: int = 30  # minutes between automatic syncs
    
    class Config:
        case_sensitive = True
        env_file = ".env"
        extra = "ignore"  # Ignore extra fields from .env


settings = Settings()
