"""
Policy Engine for Meta Autonomous System

Enforces business rules and constraints on automated actions.
"""

from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import logging

from .config import AutonomousSettings

logger = logging.getLogger(__name__)


class PolicyEngine:
    """
    Policy engine that validates and enforces business rules.
    
    Responsibilities:
    - Validate campaign creation parameters
    - Enforce budget change limits
    - Implement hard stop rules (emergency brakes)
    - Validate geographic distribution requirements
    - Check creative approval status
    """
    
    def __init__(self, settings: Optional[AutonomousSettings] = None):
        self.settings = settings or AutonomousSettings()
        logger.info(
            f"PolicyEngine initialized: mode={self.settings.META_AUTO_MODE}, "
            f"max_change={self.settings.MAX_DAILY_CHANGE_PCT}"
        )
    
    def can_create_campaign(
        self,
        metadata: Dict[str, Any],
        user_role: str = "manager"
    ) -> tuple[bool, Optional[str]]:
        """
        Validate if a campaign can be created.
        
        Args:
            metadata: Campaign metadata (pixel_id, countries, budget, etc.)
            user_role: Role of requesting user
            
        Returns:
            (allowed, reason) tuple
        """
        # Check budget
        budget = metadata.get("budget_usd", 0)
        if budget <= 0:
            return False, "Budget must be positive"
        
        if budget > self.settings.MAX_CAMPAIGN_BUDGET_USD:
            return False, f"Budget exceeds limit: ${budget} > ${self.settings.MAX_CAMPAIGN_BUDGET_USD}"
        
        # Check pixel
        if not metadata.get("pixel_id"):
            return False, "Pixel ID is required"
        
        # Check countries
        countries = metadata.get("countries", [])
        if not countries:
            return False, "At least one country is required"
        
        # Check geographic distribution if multiple countries
        if len(countries) > 1:
            distribution = metadata.get("budget_distribution", {})
            allowed, reason = self.validate_geo_distribution(distribution, countries)
            if not allowed:
                return False, reason
        
        logger.info(f"Campaign creation approved: budget=${budget}, countries={countries}")
        return True, None
    
    def can_scale_budget(
        self,
        current_budget: float,
        new_budget: float,
        is_auto_mode: bool = False
    ) -> tuple[bool, Optional[str]]:
        """
        Validate if a budget change is allowed.
        
        Args:
            current_budget: Current budget in USD
            new_budget: Proposed new budget in USD
            is_auto_mode: Whether running in automatic mode
            
        Returns:
            (allowed, reason) tuple
        """
        if current_budget <= 0:
            return False, "Current budget must be positive"
        
        # Calculate change percentage
        change = new_budget - current_budget
        amount_pct = abs(change / current_budget)
        
        # Check against limits
        max_change = (
            self.settings.MAX_AUTO_CHANGE_PCT
            if is_auto_mode
            else self.settings.MAX_DAILY_CHANGE_PCT
        )
        
        if amount_pct > max_change:
            return False, (
                f"Change {amount_pct:.1%} exceeds limit {max_change:.1%} "
                f"(${current_budget:.2f} → ${new_budget:.2f})"
            )
        
        # Check absolute budget limit
        if new_budget > self.settings.MAX_CAMPAIGN_BUDGET_USD:
            return False, f"New budget ${new_budget:.2f} exceeds limit ${self.settings.MAX_CAMPAIGN_BUDGET_USD}"
        
        # Pausing (budget to 0) is always allowed
        if new_budget == 0:
            logger.info(f"Pause approved: ${current_budget:.2f} → $0")
            return True, None
        
        direction = "increase" if change > 0 else "decrease"
        logger.info(f"Budget {direction} approved: ${current_budget:.2f} → ${new_budget:.2f} ({amount_pct:.1%})")
        return True, None
    
    def must_halt(
        self,
        roas: float,
        confidence: float,
        spend: float = 0
    ) -> tuple[bool, Optional[str]]:
        """
        Determine if an entity must be immediately halted (hard stop).
        
        This is an emergency brake for poor performance with high confidence.
        
        Args:
            roas: Return on ad spend
            confidence: Confidence score (0-1)
            spend: Amount spent (used for minimum threshold)
            
        Returns:
            (must_halt, reason) tuple
        """
        # Only enforce hard stop if we have enough data
        if spend < self.settings.MIN_SPEND_USD:
            return False, None
        
        # Hard stop rule: ROAS below threshold with high confidence
        if (
            roas < self.settings.HARD_STOP_ROAS
            and confidence >= self.settings.HARD_STOP_CONFIDENCE
        ):
            reason = (
                f"HARD STOP: ROAS {roas:.2f} < {self.settings.HARD_STOP_ROAS:.2f} "
                f"with confidence {confidence:.2%} (spend: ${spend:.2f})"
            )
            logger.warning(reason)
            return True, reason
        
        return False, None
    
    def validate_geo_distribution(
        self,
        distribution: Dict[str, float],
        countries: list[str]
    ) -> tuple[bool, Optional[str]]:
        """
        Validate geographic budget distribution.
        
        Rules:
        - Spain must have at least 35% of budget
        - No single country can exceed 70% (except Spain if alone)
        - All percentages must sum to ~1.0
        
        Args:
            distribution: Country code -> percentage dict (e.g., {"ES": 0.4, "MX": 0.6})
            countries: List of country codes
            
        Returns:
            (valid, reason) tuple
        """
        if not distribution:
            return False, "Distribution dictionary is empty"
        
        # Check Spain percentage
        spain_pct = distribution.get("ES", 0)
        if "ES" in countries and spain_pct < self.settings.MIN_SPAIN_PERCENTAGE:
            return False, (
                f"Spain must have at least {self.settings.MIN_SPAIN_PERCENTAGE:.0%} "
                f"of budget (current: {spain_pct:.0%})"
            )
        
        # Check no single country dominates (except Spain if alone)
        if len(countries) > 1:
            max_country = max(distribution.values())
            if max_country > self.settings.MAX_SINGLE_COUNTRY_PCT:
                return False, (
                    f"No country can exceed {self.settings.MAX_SINGLE_COUNTRY_PCT:.0%} "
                    f"of budget (found: {max_country:.0%})"
                )
        
        # Check sum is approximately 1.0
        total = sum(distribution.values())
        if not (0.99 <= total <= 1.01):
            return False, f"Distribution must sum to 100% (current: {total:.1%})"
        
        logger.info(f"Geographic distribution validated: {distribution}")
        return True, None
    
    def can_change_creative(
        self,
        creative_metadata: Dict[str, Any],
        last_change: Optional[datetime] = None
    ) -> tuple[bool, Optional[str]]:
        """
        Validate if a creative can be changed.
        
        Args:
            creative_metadata: Creative metadata (is_approved, etc.)
            last_change: Timestamp of last change
            
        Returns:
            (allowed, reason) tuple
        """
        # Check human approval requirement
        if self.settings.REQUIRE_HUMAN_APPROVAL_CREATIVES:
            is_approved = creative_metadata.get("is_human_approved", False)
            if not is_approved:
                return False, "Creative requires human approval"
        
        # Check embargo period
        if last_change:
            hours_since_change = (datetime.utcnow() - last_change).total_seconds() / 3600
            if hours_since_change < self.settings.CREATIVE_EMBARGO_HOURS:
                return False, (
                    f"Creative embargo: {hours_since_change:.1f}h < "
                    f"{self.settings.CREATIVE_EMBARGO_HOURS}h required"
                )
        
        return True, None
    
    def validate_action(
        self,
        action_type: str,
        action_data: Dict[str, Any],
        context: Dict[str, Any]
    ) -> tuple[bool, Optional[str]]:
        """
        Unified validation method for any action type.
        
        Args:
            action_type: Type of action (scale_up, scale_down, pause, etc.)
            action_data: Action-specific data
            context: Additional context (current_budget, roas, confidence, etc.)
            
        Returns:
            (allowed, reason) tuple
        """
        is_auto = context.get("is_auto_mode", False)
        
        if action_type == "scale_up":
            current_budget = context.get("current_budget", 0)
            new_budget = action_data.get("new_budget", 0)
            return self.can_scale_budget(current_budget, new_budget, is_auto)
        
        elif action_type == "scale_down":
            current_budget = context.get("current_budget", 0)
            new_budget = action_data.get("new_budget", 0)
            return self.can_scale_budget(current_budget, new_budget, is_auto)
        
        elif action_type == "pause":
            # Pausing is always allowed
            return True, None
        
        elif action_type == "resume":
            # Check if entity should be hard stopped
            roas = context.get("roas", 0)
            confidence = context.get("confidence", 0)
            spend = context.get("spend", 0)
            must_stop, reason = self.must_halt(roas, confidence, spend)
            if must_stop:
                return False, f"Cannot resume: {reason}"
            return True, None
        
        elif action_type == "change_creative":
            creative_metadata = action_data.get("creative_metadata", {})
            last_change = context.get("last_creative_change")
            return self.can_change_creative(creative_metadata, last_change)
        
        else:
            logger.warning(f"Unknown action type: {action_type}")
            return False, f"Unknown action type: {action_type}"
