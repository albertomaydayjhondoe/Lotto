"""
Optimization Loop Configuration

Environment variables (add to .env):
- OPTIMIZER_ENABLED: Enable/disable the optimization loop
- OPTIMIZER_MODE: "suggest" (default) or "auto" (automatic execution)
- OPTIMIZER_INTERVAL_SECONDS: How often to run optimization checks
- OPTIMIZER_SCALE_UP_MIN_ROAS: Minimum ROAS to trigger scale-up
- OPTIMIZER_SCALE_DOWN_MAX_ROAS: Maximum ROAS before scale-down
- OPTIMIZER_MIN_CONFIDENCE: Minimum confidence score for actions
- OPTIMIZER_MAX_DAILY_CHANGE_PCT: Maximum budget change per day (0.0-1.0)
- OPTIMIZER_EMBARGO_HOURS: Hours to wait before optimizing new campaigns
"""

from pydantic_settings import BaseSettings
from typing import Literal


class OptimizationSettings(BaseSettings):
    """Settings for the Meta Optimization Loop."""
    
    # Core settings
    OPTIMIZER_ENABLED: bool = True
    OPTIMIZER_MODE: Literal["suggest", "auto"] = "suggest"
    OPTIMIZER_INTERVAL_SECONDS: int = 3600  # 1 hour
    
    # ROAS thresholds
    OPTIMIZER_SCALE_UP_MIN_ROAS: float = 2.0
    OPTIMIZER_SCALE_DOWN_MAX_ROAS: float = 1.5
    OPTIMIZER_PAUSE_ROAS: float = 0.8
    
    # Safety limits (guard rails)
    OPTIMIZER_MIN_CONFIDENCE: float = 0.65
    OPTIMIZER_MAX_DAILY_CHANGE_PCT: float = 0.20  # Max 20% daily change
    OPTIMIZER_EMBARGO_HOURS: int = 48  # Wait 48h before optimizing new campaigns
    OPTIMIZER_MIN_SPEND_USD: float = 100.0  # Minimum spend before optimization
    OPTIMIZER_MIN_IMPRESSIONS: int = 1000  # Minimum impressions for statistical validity
    
    # Budget reallocation
    OPTIMIZER_REALLOCATE_THRESHOLD_DIFF: float = 1.5  # Reallocate if ROAS differs by 1.5x
    OPTIMIZER_REALLOCATE_MIN_ADS: int = 3  # Need at least 3 ads to reallocate
    
    # Execution limits
    OPTIMIZER_MAX_ACTIONS_PER_CAMPAIGN: int = 5
    OPTIMIZER_MAX_ACTIONS_PER_RUN: int = 50
    OPTIMIZER_COOLDOWN_HOURS: int = 24  # Wait 24h between optimizations for same ad
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Ignore extra environment variables


settings = OptimizationSettings()
