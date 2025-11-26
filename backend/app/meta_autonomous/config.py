"""
Configuration for Meta Autonomous System Layer
"""

from pydantic_settings import BaseSettings


class AutonomousSettings(BaseSettings):
    """Settings for the autonomous meta ads system."""
    
    # System control
    META_AUTO_ENABLED: bool = True
    META_AUTO_INTERVAL_SECONDS: int = 1800  # 30 minutes
    META_AUTO_MODE: str = "suggest"  # suggest | auto
    
    # Policy thresholds
    MAX_DAILY_CHANGE_PCT: float = 0.20  # Max 20% budget change per day
    MAX_AUTO_CHANGE_PCT: float = 0.10  # Max 10% for auto mode
    HARD_STOP_ROAS: float = 0.9  # Emergency stop if ROAS below this
    HARD_STOP_CONFIDENCE: float = 0.70  # Only hard stop with high confidence
    
    # Safety limits
    MIN_IMPRESSIONS: int = 1000  # Minimum impressions before optimization
    MIN_SPEND_USD: float = 100.0  # Minimum spend before optimization
    MIN_AGE_HOURS: int = 48  # Embargo period for new entities
    CREATIVE_EMBARGO_HOURS: int = 48  # Cooldown for creative changes
    
    # Geographic distribution requirements
    MIN_SPAIN_PERCENTAGE: float = 0.35  # At least 35% Spain
    MAX_SINGLE_COUNTRY_PCT: float = 0.70  # Max 70% in any country
    
    # Spend limits
    MAX_DAILY_SPEND_USD: float = 10000.0  # Hard daily spend limit
    MAX_CAMPAIGN_BUDGET_USD: float = 5000.0  # Max single campaign budget
    
    # Action limits
    MAX_ACTIONS_PER_TICK: int = 50  # Max actions per worker cycle
    MAX_CAMPAIGNS_PER_TICK: int = 100  # Max campaigns to evaluate per cycle
    
    # Creative approval
    REQUIRE_HUMAN_APPROVAL_CREATIVES: bool = True
    
    class Config:
        extra = "ignore"
        env_file = ".env"


settings = AutonomousSettings()
