"""
Live Configuration Management - STUB Mode

This module manages the transition between STUB and LIVE modes.
In Phase 3, everything remains in STUB mode.
In Phase 4, LIVE_MODE will be activated progressively.

CURRENT STATUS: STUB MODE ONLY
"""

from typing import Dict, Any
from enum import Enum


class ExecutionMode(str, Enum):
    """Execution mode for the system."""
    STUB = "stub"
    LIVE = "live"
    HYBRID = "hybrid"  # Some components STUB, some LIVE


class LiveConfig:
    """
    Configuration manager for STUB/LIVE mode.
    
    Phase 3: All components in STUB mode
    Phase 4: Progressive activation to LIVE mode
    """
    
    # PHASE 3: STUB MODE LOCKED
    LIVE_MODE: bool = False
    STUB_MODE: bool = True
    EXECUTION_MODE: ExecutionMode = ExecutionMode.STUB
    
    # API Activation Flags (all False in Phase 3)
    SUNO_API_ACTIVE: bool = False
    OPENAI_API_ACTIVE: bool = False
    WHISPER_API_ACTIVE: bool = False
    GEMINI_API_ACTIVE: bool = False
    
    # ML Model Loading Flags (all False in Phase 3)
    YOLO_MODEL_LOADED: bool = False
    COCO_MODEL_LOADED: bool = False
    ULTRALYTICS_MODEL_LOADED: bool = False
    ESSENTIA_LOADED: bool = False
    DEMUCS_LOADED: bool = False
    CREPE_LOADED: bool = False
    LIBROSA_LOADED: bool = False
    VGGISH_LOADED: bool = False
    
    # Ad Platform Integration Flags (all False in Phase 3)
    META_ADS_ACTIVE: bool = False
    TIKTOK_ADS_ACTIVE: bool = False
    SPOTIFY_ADS_ACTIVE: bool = False
    YOUTUBE_ADS_ACTIVE: bool = False
    
    # Worker Flags (all False in Phase 3)
    CELERY_WORKERS_ACTIVE: bool = False
    GPU_WORKERS_ACTIVE: bool = False
    
    # Router Registration (False in Phase 3)
    ROUTERS_REGISTERED: bool = False
    
    @classmethod
    def get_status(cls) -> Dict[str, Any]:
        """Get current execution mode status."""
        return {
            "execution_mode": cls.EXECUTION_MODE.value,
            "live_mode": cls.LIVE_MODE,
            "stub_mode": cls.STUB_MODE,
            "apis_active": {
                "suno": cls.SUNO_API_ACTIVE,
                "openai": cls.OPENAI_API_ACTIVE,
                "whisper": cls.WHISPER_API_ACTIVE,
                "gemini": cls.GEMINI_API_ACTIVE,
            },
            "ml_models_loaded": {
                "yolo": cls.YOLO_MODEL_LOADED,
                "coco": cls.COCO_MODEL_LOADED,
                "ultralytics": cls.ULTRALYTICS_MODEL_LOADED,
                "essentia": cls.ESSENTIA_LOADED,
                "demucs": cls.DEMUCS_LOADED,
                "crepe": cls.CREPE_LOADED,
                "librosa": cls.LIBROSA_LOADED,
                "vggish": cls.VGGISH_LOADED,
            },
            "ad_platforms_active": {
                "meta": cls.META_ADS_ACTIVE,
                "tiktok": cls.TIKTOK_ADS_ACTIVE,
                "spotify": cls.SPOTIFY_ADS_ACTIVE,
                "youtube": cls.YOUTUBE_ADS_ACTIVE,
            },
            "workers_active": {
                "celery": cls.CELERY_WORKERS_ACTIVE,
                "gpu": cls.GPU_WORKERS_ACTIVE,
            },
            "routers_registered": cls.ROUTERS_REGISTERED,
        }
    
    @classmethod
    def is_stub_mode(cls) -> bool:
        """Check if system is in STUB mode."""
        return cls.STUB_MODE and not cls.LIVE_MODE
    
    @classmethod
    def is_live_mode(cls) -> bool:
        """Check if system is in LIVE mode."""
        return cls.LIVE_MODE and not cls.STUB_MODE
    
    @classmethod
    def is_hybrid_mode(cls) -> bool:
        """Check if system is in HYBRID mode."""
        return cls.EXECUTION_MODE == ExecutionMode.HYBRID


# Global config instance
config = LiveConfig()


def get_live_config() -> LiveConfig:
    """Get global live configuration instance."""
    return config
