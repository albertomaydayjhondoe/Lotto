"""
Curator AutoMailer — Routing Logic

Defines campaign routing and retry logic.
STUB MODE: Strategic decision engine.
"""

from typing import Dict, Any, List
from datetime import datetime, timedelta
from enum import Enum


class CampaignPhase(Enum):
    """Campaign phases"""
    WARM_UP = "warm_up"
    CORE_OUTREACH = "core_outreach"
    VOLUME_PUSH = "volume_push"
    FOLLOW_UP = "follow_up"
    LONG_TAIL = "long_tail"
    COMPLETED = "completed"


class RoutingLogic:
    """
    STUB: Campaign routing and retry logic.
    
    Determines:
    - When to send initial emails
    - When to send follow-ups
    - When to stop contacting a curator
    - How to prioritize curators
    - Campaign phase transitions
    
    Phase 3: Strategic logic only, no execution.
    """
    
    def __init__(self):
        self.stub_mode = True
        
        # Routing parameters
        self.params = {
            "initial_delay_days": 0,
            "follow_up_delay_days": 7,
            "max_follow_ups": 2,
            "warm_up_batch_size": 20,
            "core_batch_size": 50,
            "volume_batch_size": 100,
            "phase_transition_days": {
                "warm_up_to_core": 3,
                "core_to_volume": 7,
                "volume_to_follow_up": 14
            }
        }
    
    def should_send_email(
        self,
        curator_email: str,
        last_contact_date: str = None,
        follow_up_count: int = 0,
        curator_response_rate: float = None
    ) -> Dict[str, Any]:
        """
        Determine if email should be sent to curator.
        
        Args:
            curator_email: Curator's email
            last_contact_date: Last contact ISO date
            follow_up_count: Number of follow-ups sent
            curator_response_rate: Historical response rate
            
        Returns:
            Decision dict
        """
        # No previous contact
        if not last_contact_date:
            return {
                "should_send": True,
                "reason": "initial_contact",
                "recommended_timing": "immediate",
                "stub_mode": True
            }
        
        # Check follow-up limits
        if follow_up_count >= self.params["max_follow_ups"]:
            return {
                "should_send": False,
                "reason": "max_follow_ups_reached",
                "recommended_action": "stop_contacting",
                "stub_mode": True
            }
        
        # Calculate days since last contact
        last_contact = datetime.fromisoformat(last_contact_date.replace('Z', '+00:00'))
        days_since = (datetime.utcnow() - last_contact).days
        
        # Determine if follow-up is due
        if days_since >= self.params["follow_up_delay_days"]:
            # Adjust based on response rate
            if curator_response_rate and curator_response_rate < 0.20:
                return {
                    "should_send": False,
                    "reason": "low_historical_response_rate",
                    "recommended_action": "skip_low_performers",
                    "stub_mode": True
                }
            
            return {
                "should_send": True,
                "reason": "follow_up_due",
                "days_since_last": days_since,
                "recommended_timing": "immediate",
                "stub_mode": True
            }
        
        return {
            "should_send": False,
            "reason": "too_soon_for_follow_up",
            "days_until_eligible": self.params["follow_up_delay_days"] - days_since,
            "stub_mode": True
        }
    
    def get_campaign_phase(
        self,
        days_since_start: int,
        emails_sent: int
    ) -> CampaignPhase:
        """
        Determine current campaign phase.
        
        Args:
            days_since_start: Days since campaign start
            emails_sent: Total emails sent
            
        Returns:
            Current campaign phase
        """
        if days_since_start <= self.params["phase_transition_days"]["warm_up_to_core"]:
            return CampaignPhase.WARM_UP
        elif days_since_start <= self.params["phase_transition_days"]["core_to_volume"]:
            return CampaignPhase.CORE_OUTREACH
        elif days_since_start <= self.params["phase_transition_days"]["volume_to_follow_up"]:
            return CampaignPhase.VOLUME_PUSH
        elif days_since_start <= 30:
            return CampaignPhase.FOLLOW_UP
        elif days_since_start <= 45:
            return CampaignPhase.LONG_TAIL
        else:
            return CampaignPhase.COMPLETED
    
    def prioritize_curators(
        self,
        curators: List[Dict[str, Any]],
        compatibility_scores: Dict[str, float]
    ) -> List[Dict[str, Any]]:
        """
        Prioritize curator list for outreach.
        
        Args:
            curators: List of curator dicts
            compatibility_scores: Curator email -> compatibility score
            
        Returns:
            Prioritized curator list
        """
        def priority_score(curator):
            email = curator["email"]
            compat = compatibility_scores.get(email, 0.5)
            response_rate = curator.get("response_rate", 0.5)
            followers = curator.get("total_followers", 10000)
            
            # Weighted score
            score = (
                compat * 0.40 +
                response_rate * 0.30 +
                (min(followers, 200000) / 200000) * 0.30
            )
            
            return score
        
        prioritized = sorted(curators, key=priority_score, reverse=True)
        
        # Add priority tier
        for i, curator in enumerate(prioritized):
            if i < 20:
                curator["priority_tier"] = "premium"
            elif i < 70:
                curator["priority_tier"] = "core"
            else:
                curator["priority_tier"] = "volume"
        
        return prioritized
    
    def get_batch_for_phase(
        self,
        phase: CampaignPhase,
        available_curators: int
    ) -> Dict[str, Any]:
        """
        Get batch size and timing for campaign phase.
        
        Args:
            phase: Current campaign phase
            available_curators: Number of available curators
            
        Returns:
            Batch configuration
        """
        if phase == CampaignPhase.WARM_UP:
            batch_size = min(self.params["warm_up_batch_size"], available_curators)
            timing = "immediate"
        elif phase == CampaignPhase.CORE_OUTREACH:
            batch_size = min(self.params["core_batch_size"], available_curators)
            timing = "staggered_daily"
        elif phase == CampaignPhase.VOLUME_PUSH:
            batch_size = min(self.params["volume_batch_size"], available_curators)
            timing = "staggered_hourly"
        else:
            batch_size = min(20, available_curators)
            timing = "as_needed"
        
        return {
            "phase": phase.value,
            "batch_size": batch_size,
            "timing": timing,
            "recommendation": f"Send {batch_size} emails with {timing} timing",
            "stub_mode": True
        }
    
    def should_retry_curator(
        self,
        curator_email: str,
        previous_attempts: int,
        previous_response: str = None
    ) -> Dict[str, Any]:
        """
        Determine if curator should be retried.
        
        Args:
            curator_email: Curator's email
            previous_attempts: Number of previous attempts
            previous_response: Previous response type
            
        Returns:
            Retry decision
        """
        # Don't retry if received rejection
        if previous_response == "rejected":
            return {
                "should_retry": False,
                "reason": "received_rejection",
                "stub_mode": True
            }
        
        # Don't retry if too many attempts
        if previous_attempts >= 3:
            return {
                "should_retry": False,
                "reason": "max_attempts_exceeded",
                "stub_mode": True
            }
        
        # Retry if no response and attempts < 3
        if not previous_response or previous_response == "no_response":
            return {
                "should_retry": True,
                "reason": "no_response_yet",
                "recommended_delay_days": 14,
                "stub_mode": True
            }
        
        return {
            "should_retry": False,
            "reason": "default_no_retry",
            "stub_mode": True
        }
