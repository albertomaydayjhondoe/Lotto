"""
Main Rule Engine interface.
"""
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.rules_engine.models import AdaptiveRuleSet
from app.rules_engine.loader import load_rules
from app.rules_engine.heuristics import apply_platform_heuristics
from app.rules_engine.evaluator import evaluate_clip_by_id
from app.rules_engine.trainer import train_rules


class RuleEngine:
    """
    Main interface for the Rule Engine.
    
    Provides high-level methods for:
    - Getting rules for a platform
    - Evaluating clips
    - Training adaptive weights
    """
    
    async def get_rules(
        self,
        db: AsyncSession,
        platform: str
    ) -> AdaptiveRuleSet:
        """
        Get rule set for a platform.
        
        Loads from database and applies platform-specific heuristics.
        
        Args:
            db: Database session
            platform: Target platform (tiktok|instagram|youtube)
            
        Returns:
            AdaptiveRuleSet with weights
        """
        # Load base rules from database
        rules = await load_rules(db, platform)
        
        # Apply platform heuristics
        rules = apply_platform_heuristics(rules, platform)
        
        return rules
    
    async def evaluate_clip(
        self,
        db: AsyncSession,
        clip_id: UUID,
        platform: str
    ) -> float:
        """
        Evaluate a clip for a specific platform.
        
        Args:
            db: Database session
            clip_id: ID of clip to evaluate
            platform: Target platform
            
        Returns:
            Score between 0.0 and 1.0
        """
        # Get rules for platform
        rules = await self.get_rules(db, platform)
        
        # Evaluate clip
        score = await evaluate_clip_by_id(db, clip_id, rules, platform)
        
        return score
    
    async def train(
        self,
        db: AsyncSession,
        platform: str
    ) -> AdaptiveRuleSet:
        """
        Train rule weights based on performance data.
        
        Args:
            db: Database session
            platform: Platform to train for
            
        Returns:
            Updated AdaptiveRuleSet
        """
        updated_rules = await train_rules(db, platform)
        return updated_rules
