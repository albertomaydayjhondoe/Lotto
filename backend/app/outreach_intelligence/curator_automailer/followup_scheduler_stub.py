"""
Curator AutoMailer — Follow-up Scheduler STUB

Automatically schedules follow-up emails based on response patterns,
curator behavior, and optimal timing strategies.

STUB MODE: Simulates scheduling logic.
"""

from typing import Dict, Any, List
from datetime import datetime, timedelta
from enum import Enum


class FollowUpReason(Enum):
    """Reason for follow-up"""
    NO_RESPONSE = "no_response"
    OPENED_NOT_CLICKED = "opened_not_clicked"
    CLICKED_NOT_RESPONDED = "clicked_not_responded"
    PREVIOUS_SUCCESS = "previous_success"
    HIGH_PRIORITY = "high_priority"


class FollowUpSchedulerStub:
    """
    STUB: Schedules intelligent follow-up emails.
    
    In LIVE mode:
    - Analyzes open/click patterns
    - Learns optimal follow-up timing per curator
    - Adjusts based on response rates
    - Avoids over-contacting
    
    Phase 4: Returns mock schedules.
    """
    
    def __init__(self):
        self.stub_mode = True
        self.default_follow_up_days = 7  # Default: 7 days after initial
        self.max_follow_ups = 1  # Max 1 follow-up per campaign
        self.scheduled_follow_ups = []
        
    def schedule_follow_up(
        self,
        original_email_id: str,
        curator_info: Dict[str, Any],
        track_info: Dict[str, Any],
        send_date: str,
        reason: FollowUpReason = FollowUpReason.NO_RESPONSE
    ) -> Dict[str, Any]:
        """
        STUB: Schedule a follow-up email.
        
        Args:
            original_email_id: ID of original email
            curator_info: Curator details
            track_info: Track information
            send_date: When original was sent (ISO format)
            reason: Why follow-up is needed
            
        Returns:
            Follow-up schedule details
        """
        sent_dt = datetime.fromisoformat(send_date.split("T")[0])
        follow_up_date = sent_dt + timedelta(days=self.default_follow_up_days)
        
        # Adjust timing based on curator behavior (STUB)
        if curator_info.get("avg_response_time_days"):
            follow_up_date = sent_dt + timedelta(
                days=curator_info["avg_response_time_days"] + 2
            )
        
        schedule = {
            "follow_up_id": f"followup_{len(self.scheduled_follow_ups):06d}",
            "original_email_id": original_email_id,
            "curator_email": curator_info.get("email"),
            "curator_name": curator_info.get("name"),
            "track_title": track_info.get("title"),
            "scheduled_for": follow_up_date.isoformat(),
            "reason": reason.value,
            "follow_up_number": 1,
            "max_follow_ups": self.max_follow_ups,
            "can_send": True,
            "stub_note": "STUB MODE - Would schedule in email service"
        }
        
        self.scheduled_follow_ups.append(schedule)
        
        return schedule
    
    def schedule_batch_follow_ups(
        self,
        campaigns: List[Dict[str, Any]],
        days_since_send: int = 7
    ) -> Dict[str, Any]:
        """
        STUB: Schedule follow-ups for multiple campaigns.
        
        Args:
            campaigns: List of campaign data
            days_since_send: Days to wait before follow-up
            
        Returns:
            Batch schedule summary
        """
        results = {
            "total_campaigns": len(campaigns),
            "follow_ups_scheduled": 0,
            "skipped": 0,
            "reasons_skipped": []
        }
        
        for campaign in campaigns:
            # Check if already responded
            if campaign.get("response_received", False):
                results["skipped"] += 1
                results["reasons_skipped"].append({
                    "campaign_id": campaign.get("campaign_id"),
                    "reason": "Already responded"
                })
                continue
            
            # Check if already followed up
            if campaign.get("follow_up_sent", False):
                results["skipped"] += 1
                results["reasons_skipped"].append({
                    "campaign_id": campaign.get("campaign_id"),
                    "reason": "Already followed up"
                })
                continue
            
            # Schedule follow-up
            schedule = self.schedule_follow_up(
                original_email_id=campaign.get("email_id"),
                curator_info=campaign.get("curator_info", {}),
                track_info=campaign.get("track_info", {}),
                send_date=campaign.get("sent_at"),
                reason=FollowUpReason.NO_RESPONSE
            )
            
            results["follow_ups_scheduled"] += 1
        
        results["stub_note"] = "STUB MODE - Batch scheduling simulation"
        
        return results
    
    def adjust_timing_based_on_engagement(
        self,
        email_id: str,
        engagement_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        STUB: Adjust follow-up timing based on engagement.
        
        If curator opened but didn't click, follow up sooner.
        If curator clicked, wait longer.
        
        Args:
            email_id: Original email ID
            engagement_data: Open/click tracking data
            
        Returns:
            Adjusted schedule
        """
        # Find scheduled follow-up
        follow_up = next(
            (f for f in self.scheduled_follow_ups if f["original_email_id"] == email_id),
            None
        )
        
        if not follow_up:
            return {
                "error": "Follow-up not found",
                "email_id": email_id
            }
        
        original_date = datetime.fromisoformat(follow_up["scheduled_for"])
        adjusted_date = original_date
        
        # Adjust based on engagement
        if engagement_data.get("opened") and not engagement_data.get("clicked"):
            # Opened but not clicked - follow up sooner
            adjusted_date = original_date - timedelta(days=2)
            reason = "Opened but no click - interest shown"
        elif engagement_data.get("clicked") and not engagement_data.get("responded"):
            # Clicked but no response - wait longer
            adjusted_date = original_date + timedelta(days=3)
            reason = "Clicked - give more time"
        else:
            reason = "No engagement - standard timing"
        
        follow_up["scheduled_for"] = adjusted_date.isoformat()
        follow_up["adjustment_reason"] = reason
        follow_up["adjusted"] = True
        
        return follow_up
    
    def cancel_follow_up(
        self,
        email_id: str,
        reason: str = "Response received"
    ) -> Dict[str, Any]:
        """
        STUB: Cancel scheduled follow-up.
        
        Called when curator responds before follow-up is sent.
        
        Args:
            email_id: Original email ID
            reason: Why cancelling
            
        Returns:
            Cancellation confirmation
        """
        # Find and remove follow-up
        follow_up = next(
            (f for f in self.scheduled_follow_ups if f["original_email_id"] == email_id),
            None
        )
        
        if follow_up:
            self.scheduled_follow_ups.remove(follow_up)
            return {
                "cancelled": True,
                "follow_up_id": follow_up["follow_up_id"],
                "reason": reason,
                "cancelled_at": datetime.now().isoformat(),
                "stub_note": "STUB MODE - Would cancel in email service"
            }
        
        return {
            "cancelled": False,
            "error": "Follow-up not found",
            "email_id": email_id
        }
    
    def get_pending_follow_ups(
        self,
        days_ahead: int = 7
    ) -> List[Dict[str, Any]]:
        """
        STUB: Get follow-ups scheduled in next N days.
        
        Args:
            days_ahead: Number of days to look ahead
            
        Returns:
            List of pending follow-ups
        """
        cutoff_date = datetime.now() + timedelta(days=days_ahead)
        
        pending = [
            f for f in self.scheduled_follow_ups
            if datetime.fromisoformat(f["scheduled_for"]) <= cutoff_date
        ]
        
        return pending
    
    def get_follow_up_statistics(self) -> Dict[str, Any]:
        """
        STUB: Get follow-up statistics.
        
        Returns:
            Statistics summary
        """
        return {
            "total_scheduled": len(self.scheduled_follow_ups),
            "pending": len(self.get_pending_follow_ups(30)),
            "avg_days_to_follow_up": self.default_follow_up_days,
            "max_follow_ups_per_campaign": self.max_follow_ups,
            "response_rate_after_follow_up": 0.28,  # STUB
            "conversion_lift": 0.15,  # STUB: 15% lift from follow-ups
            "stub_note": "STUB MODE - Mock statistics"
        }
