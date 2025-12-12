"""
Safety Engine for Meta Autonomous System

Guardian layer that prevents dangerous operations.
"""

from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
import logging

from .config import AutonomousSettings

logger = logging.getLogger(__name__)


class SafetyEngine:
    """
    Safety engine that prevents dangerous operations.
    
    Responsibilities:
    - Prevent overspending beyond daily limits
    - Enforce embargo periods for new entities
    - Block unapproved creatives
    - Rate limit optimization actions
    - Verify minimum data thresholds
    """
    
    def __init__(self, settings: Optional[AutonomousSettings] = None):
        self.settings = settings or AutonomousSettings()
        logger.info(
            f"SafetyEngine initialized: daily_limit=${self.settings.MAX_DAILY_SPEND_USD}, "
            f"embargo={self.settings.MIN_AGE_HOURS}h"
        )
    
    async def prevent_overspend(
        self,
        spend_today: float,
        proposed_budget: float,
        db: Optional[AsyncSession] = None
    ) -> tuple[bool, Optional[str]]:
        """
        Check if proposed action would cause overspending.
        
        Args:
            spend_today: Amount spent today across all campaigns
            proposed_budget: New budget being proposed
            db: Database session for checking total spend
            
        Returns:
            (blocked, reason) tuple - True means blocked
        """
        # Check daily spend limit
        if spend_today >= self.settings.MAX_DAILY_SPEND_USD:
            reason = (
                f"Daily spend limit reached: ${spend_today:.2f} >= "
                f"${self.settings.MAX_DAILY_SPEND_USD:.2f}"
            )
            logger.warning(reason)
            return True, reason
        
        # Check if adding this budget would exceed limit
        projected_spend = spend_today + proposed_budget
        if projected_spend > self.settings.MAX_DAILY_SPEND_USD:
            reason = (
                f"Proposed budget ${proposed_budget:.2f} would exceed daily limit: "
                f"${projected_spend:.2f} > ${self.settings.MAX_DAILY_SPEND_USD:.2f}"
            )
            logger.warning(reason)
            return True, reason
        
        logger.debug(f"Spend check passed: ${spend_today:.2f} + ${proposed_budget:.2f} < limit")
        return False, None
    
    def enforce_embargo_period(
        self,
        created_at: datetime,
        embargo_hours: Optional[int] = None
    ) -> tuple[bool, Optional[str]]:
        """
        Check if entity is still in embargo period (too new to optimize).
        
        Args:
            created_at: When the entity was created
            embargo_hours: Custom embargo period (uses MIN_AGE_HOURS if None)
            
        Returns:
            (in_embargo, reason) tuple - True means blocked
        """
        embargo = embargo_hours or self.settings.MIN_AGE_HOURS
        
        hours_since_creation = (datetime.utcnow() - created_at).total_seconds() / 3600
        
        if hours_since_creation < embargo:
            reason = (
                f"Entity in embargo: {hours_since_creation:.1f}h < {embargo}h required "
                f"(created: {created_at.isoformat()})"
            )
            logger.info(reason)
            return True, reason
        
        logger.debug(f"Embargo passed: {hours_since_creation:.1f}h >= {embargo}h")
        return False, None
    
    def block_unapproved_creatives(
        self,
        creative: Dict[str, Any]
    ) -> tuple[bool, Optional[str]]:
        """
        Check if creative has required human approval.
        
        Args:
            creative: Creative metadata with approval status
            
        Returns:
            (blocked, reason) tuple - True means blocked
        """
        if not self.settings.REQUIRE_HUMAN_APPROVAL_CREATIVES:
            return False, None
        
        is_approved = creative.get("is_human_approved", False)
        
        if not is_approved:
            creative_id = creative.get("id", "unknown")
            reason = f"Creative {creative_id} requires human approval"
            logger.warning(reason)
            return True, reason
        
        return False, None
    
    def check_minimum_data(
        self,
        impressions: int,
        spend: float
    ) -> tuple[bool, Optional[str]]:
        """
        Verify entity has minimum data for reliable optimization.
        
        Args:
            impressions: Number of impressions
            spend: Amount spent
            
        Returns:
            (insufficient, reason) tuple - True means blocked
        """
        if impressions < self.settings.MIN_IMPRESSIONS:
            reason = (
                f"Insufficient impressions: {impressions} < "
                f"{self.settings.MIN_IMPRESSIONS} required"
            )
            logger.info(reason)
            return True, reason
        
        if spend < self.settings.MIN_SPEND_USD:
            reason = (
                f"Insufficient spend: ${spend:.2f} < "
                f"${self.settings.MIN_SPEND_USD:.2f} required"
            )
            logger.info(reason)
            return True, reason
        
        logger.debug(f"Minimum data check passed: {impressions} impressions, ${spend:.2f} spend")
        return False, None
    
    async def check_action_rate_limit(
        self,
        entity_id: str,
        action_type: str,
        last_action_time: Optional[datetime],
        cooldown_hours: Optional[int] = None
    ) -> tuple[bool, Optional[str]]:
        """
        Check if too many actions have been taken recently (rate limiting).
        
        Args:
            entity_id: ID of the entity being optimized
            action_type: Type of action (scale_up, scale_down, etc.)
            last_action_time: When the last action was taken
            cooldown_hours: Custom cooldown period
            
        Returns:
            (rate_limited, reason) tuple - True means blocked
        """
        if not last_action_time:
            return False, None
        
        cooldown = cooldown_hours or 24  # Default 24h cooldown
        
        hours_since_last = (datetime.utcnow() - last_action_time).total_seconds() / 3600
        
        if hours_since_last < cooldown:
            reason = (
                f"Rate limit: {hours_since_last:.1f}h since last {action_type} "
                f"< {cooldown}h cooldown (entity: {entity_id})"
            )
            logger.info(reason)
            return True, reason
        
        return False, None
    
    def validate_roas_confidence(
        self,
        roas: float,
        confidence: float
    ) -> tuple[bool, Optional[str]]:
        """
        Validate ROAS and confidence meet safety thresholds.
        
        Args:
            roas: Return on ad spend
            confidence: Confidence score (0-1)
            
        Returns:
            (invalid, reason) tuple - True means blocked
        """
        # Very low ROAS with high confidence is dangerous
        if roas < 0.5 and confidence > 0.8:
            reason = f"Dangerously low ROAS {roas:.2f} with high confidence {confidence:.2%}"
            logger.warning(reason)
            return True, reason
        
        # Negative ROAS should always be blocked from scale-up
        if roas < 0:
            reason = f"Negative ROAS {roas:.2f} is invalid"
            logger.error(reason)
            return True, reason
        
        return False, None
    
    async def validate_action(
        self,
        action_type: str,
        action_data: Dict[str, Any],
        context: Dict[str, Any],
        db: Optional[AsyncSession] = None
    ) -> tuple[bool, Optional[str]]:
        """
        Unified safety validation for any action.
        
        Args:
            action_type: Type of action
            action_data: Action-specific data
            context: Additional context (created_at, spend, impressions, etc.)
            db: Database session for checking limits
            
        Returns:
            (blocked, reason) tuple - True means action blocked
        """
        # Check embargo period
        created_at = context.get("created_at")
        if created_at:
            in_embargo, reason = self.enforce_embargo_period(created_at)
            if in_embargo:
                return True, reason
        
        # Check minimum data
        impressions = context.get("impressions", 0)
        spend = context.get("spend", 0)
        insufficient, reason = self.check_minimum_data(impressions, spend)
        if insufficient:
            return True, reason
        
        # Check ROAS confidence for scale-up
        if action_type == "scale_up":
            roas = context.get("roas", 0)
            confidence = context.get("confidence", 0)
            invalid, reason = self.validate_roas_confidence(roas, confidence)
            if invalid:
                return True, reason
        
        # Check rate limit
        entity_id = context.get("entity_id", "unknown")
        last_action = context.get("last_action_time")
        rate_limited, reason = await self.check_action_rate_limit(
            entity_id, action_type, last_action
        )
        if rate_limited:
            return True, reason
        
        # Check overspend for budget increases
        if action_type in ["scale_up", "create_campaign"]:
            spend_today = context.get("spend_today", 0)
            proposed_budget = action_data.get("budget", 0)
            overspend, reason = await self.prevent_overspend(
                spend_today, proposed_budget, db
            )
            if overspend:
                return True, reason
        
        # Check creative approval
        if action_type == "change_creative":
            creative = action_data.get("creative", {})
            blocked, reason = self.block_unapproved_creatives(creative)
            if blocked:
                return True, reason
        
        logger.debug(f"Safety validation passed for {action_type}")
        return False, None
