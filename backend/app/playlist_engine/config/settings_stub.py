"""
Playlist Engine — Configuration STUB

Settings for Playlist Intelligence and Curator AutoMailer.
STUB MODE: All features in stub/simulation mode.
"""

from enum import Enum


class ExecutionMode(Enum):
    """Execution modes"""
    STUB = "stub"
    LIVE = "live"
    HYBRID = "hybrid"


class PlaylistEngineSettings:
    """
    Playlist Engine configuration settings.
    
    Phase 3: All features in STUB mode.
    Phase 4: Activate LIVE mode with real APIs.
    """
    
    # Execution Mode
    EXECUTION_MODE = ExecutionMode.STUB
    LIVE_MODE = False
    STUB_MODE = True
    
    # Feature Flags
    PLAYLIST_ENGINE_ENABLED = True
    EMAIL_AUTOMATION_ENABLED = True
    CURATOR_TRACKING_ENABLED = True
    BLACKLIST_ENABLED = True
    
    # Email Settings (STUB)
    USE_STUB_EMAIL = True
    EMAIL_PROVIDER = "stub"  # "sendgrid", "aws_ses", "gmail"
    EMAIL_FROM_ADDRESS = "noreply@stakazo.stub"
    EMAIL_FROM_NAME = "Stakazo Playlist Team"
    
    # Campaign Settings
    MAX_EMAILS_PER_DAY = 100  # STUB limit
    MAX_FOLLOW_UPS = 2
    FOLLOW_UP_DELAY_DAYS = 7
    AUTO_BLACKLIST_ON_UNSUBSCRIBE = True
    
    # Playlist Intelligence Settings
    MIN_COMPATIBILITY_SCORE = 0.50
    USE_AI_PRIORITIZATION = False  # Activate in Phase 4
    AI_MODEL = "gpt-5-stub"
    
    # Database Settings (STUB)
    USE_MOCK_DATABASE = True
    CURATOR_DATABASE_SIZE = 405  # Mock curators
    PLAYLIST_DATABASE_SIZE = 205  # Mock playlists
    
    # API Keys (ALL STUB - NO REAL KEYS)
    SPOTIFY_API_KEY = None
    SENDGRID_API_KEY = None
    OPENAI_API_KEY = None
    
    # Rate Limiting
    MAX_REQUESTS_PER_MINUTE = 60
    ENABLE_RATE_LIMITING = True
    
    # Logging
    LOG_LEVEL = "INFO"
    LOG_EMAIL_SENDS = True
    LOG_CURATOR_RESPONSES = True
    
    # Testing
    ENABLE_TEST_MODE = True
    TEST_CURATOR_EMAILS = [
        "test.curator1@stub.local",
        "test.curator2@stub.local"
    ]


# Configuration instance
config = PlaylistEngineSettings()


def get_config() -> PlaylistEngineSettings:
    """Get current configuration"""
    return config


def is_live_mode() -> bool:
    """Check if running in LIVE mode"""
    return config.LIVE_MODE and config.EXECUTION_MODE == ExecutionMode.LIVE


def is_stub_mode() -> bool:
    """Check if running in STUB mode"""
    return config.STUB_MODE or config.EXECUTION_MODE == ExecutionMode.STUB
