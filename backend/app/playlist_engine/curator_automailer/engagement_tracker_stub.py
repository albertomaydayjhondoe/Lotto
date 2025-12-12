"""
Curator AutoMailer — Engagement Tracker STUB

Tracks curator engagement and campaign metrics.
STUB MODE: In-memory tracking.
"""

from typing import Dict, Any, List
from datetime import datetime
from collections import defaultdict


class EngagementTrackerStub:
    """
    STUB: Tracks curator engagement metrics.
    
    Monitors:
    - Emails sent per curator
    - Response rates
    - Acceptance rates
    - Best-performing curators
    - Campaign effectiveness
    
    In LIVE mode, this would use:
    - Database for persistent storage
    - Analytics dashboard
    - Real-time metrics
    
    Phase 3: In-memory tracking only.
    """
    
    def __init__(self):
        self.stub_mode = True
        self._engagement_data = defaultdict(lambda: {
            "emails_sent": 0,
            "responses_received": 0,
            "acceptances": 0,
            "rejections": 0,
            "last_contact": None,
            "successful_placements": []
        })
        self._campaign_data = {}
        
    def track_email_sent(
        self,
        curator_email: str,
        campaign_id: str,
        track_id: str
    ) -> Dict[str, Any]:
        """
        Track email sent to curator.
        
        Args:
            curator_email: Curator's email
            campaign_id: Campaign ID
            track_id: Track ID
            
        Returns:
            Tracking confirmation
        """
        self._engagement_data[curator_email]["emails_sent"] += 1
        self._engagement_data[curator_email]["last_contact"] = datetime.utcnow().isoformat()
        
        # Track campaign
        if campaign_id not in self._campaign_data:
            self._campaign_data[campaign_id] = {
                "emails_sent": 0,
                "responses": 0,
                "acceptances": 0,
                "track_id": track_id
            }
        
        self._campaign_data[campaign_id]["emails_sent"] += 1
        
        return {
            "status": "tracked",
            "curator_email": curator_email,
            "campaign_id": campaign_id,
            "tracked_at": datetime.utcnow().isoformat(),
            "stub_mode": True
        }
    
    def track_response(
        self,
        curator_email: str,
        campaign_id: str,
        response_type: str  # "accepted", "rejected", "other"
    ) -> Dict[str, Any]:
        """
        Track curator response.
        
        Args:
            curator_email: Curator's email
            campaign_id: Campaign ID
            response_type: Type of response
            
        Returns:
            Tracking confirmation
        """
        self._engagement_data[curator_email]["responses_received"] += 1
        
        if response_type == "accepted":
            self._engagement_data[curator_email]["acceptances"] += 1
            if campaign_id in self._campaign_data:
                self._campaign_data[campaign_id]["acceptances"] += 1
        elif response_type == "rejected":
            self._engagement_data[curator_email]["rejections"] += 1
        
        if campaign_id in self._campaign_data:
            self._campaign_data[campaign_id]["responses"] += 1
        
        return {
            "status": "tracked",
            "curator_email": curator_email,
            "response_type": response_type,
            "tracked_at": datetime.utcnow().isoformat(),
            "stub_mode": True
        }
    
    def track_placement(
        self,
        curator_email: str,
        playlist_id: str,
        track_id: str
    ) -> Dict[str, Any]:
        """
        Track successful playlist placement.
        
        Args:
            curator_email: Curator's email
            playlist_id: Playlist ID
            track_id: Track ID
            
        Returns:
            Tracking confirmation
        """
        placement = {
            "playlist_id": playlist_id,
            "track_id": track_id,
            "placed_at": datetime.utcnow().isoformat()
        }
        
        self._engagement_data[curator_email]["successful_placements"].append(placement)
        
        return {
            "status": "tracked",
            "curator_email": curator_email,
            "placement": placement,
            "stub_mode": True
        }
    
    def get_curator_stats(
        self,
        curator_email: str
    ) -> Dict[str, Any]:
        """
        Get engagement statistics for specific curator.
        
        Args:
            curator_email: Curator's email
            
        Returns:
            Curator statistics
        """
        data = self._engagement_data[curator_email]
        
        response_rate = (
            data["responses_received"] / data["emails_sent"]
            if data["emails_sent"] > 0 else 0
        )
        
        acceptance_rate = (
            data["acceptances"] / data["responses_received"]
            if data["responses_received"] > 0 else 0
        )
        
        return {
            "curator_email": curator_email,
            "emails_sent": data["emails_sent"],
            "responses_received": data["responses_received"],
            "acceptances": data["acceptances"],
            "rejections": data["rejections"],
            "response_rate": response_rate,
            "acceptance_rate": acceptance_rate,
            "successful_placements": len(data["successful_placements"]),
            "last_contact": data["last_contact"],
            "stub_mode": True
        }
    
    def get_campaign_stats(
        self,
        campaign_id: str
    ) -> Dict[str, Any]:
        """
        Get statistics for specific campaign.
        
        Args:
            campaign_id: Campaign ID
            
        Returns:
            Campaign statistics
        """
        if campaign_id not in self._campaign_data:
            return {
                "campaign_id": campaign_id,
                "status": "not_found",
                "stub_mode": True
            }
        
        data = self._campaign_data[campaign_id]
        
        response_rate = (
            data["responses"] / data["emails_sent"]
            if data["emails_sent"] > 0 else 0
        )
        
        acceptance_rate = (
            data["acceptances"] / data["responses"]
            if data["responses"] > 0 else 0
        )
        
        return {
            "campaign_id": campaign_id,
            "track_id": data["track_id"],
            "emails_sent": data["emails_sent"],
            "responses": data["responses"],
            "acceptances": data["acceptances"],
            "response_rate": response_rate,
            "acceptance_rate": acceptance_rate,
            "stub_mode": True
        }
    
    def get_top_curators(
        self,
        metric: str = "acceptance_rate",
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get top-performing curators.
        
        Args:
            metric: Metric to sort by ("acceptance_rate", "placements", "response_rate")
            limit: Number of curators to return
            
        Returns:
            List of top curators
        """
        curator_stats = []
        
        for email, data in self._engagement_data.items():
            if data["emails_sent"] == 0:
                continue
            
            response_rate = (
                data["responses_received"] / data["emails_sent"]
                if data["emails_sent"] > 0 else 0
            )
            
            acceptance_rate = (
                data["acceptances"] / data["responses_received"]
                if data["responses_received"] > 0 else 0
            )
            
            curator_stats.append({
                "curator_email": email,
                "acceptance_rate": acceptance_rate,
                "response_rate": response_rate,
                "placements": len(data["successful_placements"]),
                "emails_sent": data["emails_sent"]
            })
        
        # Sort by metric
        if metric == "acceptance_rate":
            curator_stats.sort(key=lambda x: x["acceptance_rate"], reverse=True)
        elif metric == "placements":
            curator_stats.sort(key=lambda x: x["placements"], reverse=True)
        elif metric == "response_rate":
            curator_stats.sort(key=lambda x: x["response_rate"], reverse=True)
        
        return curator_stats[:limit]
    
    def get_overall_stats(self) -> Dict[str, Any]:
        """Get overall engagement statistics"""
        total_emails = sum(data["emails_sent"] for data in self._engagement_data.values())
        total_responses = sum(data["responses_received"] for data in self._engagement_data.values())
        total_acceptances = sum(data["acceptances"] for data in self._engagement_data.values())
        total_placements = sum(len(data["successful_placements"]) for data in self._engagement_data.values())
        
        overall_response_rate = (
            total_responses / total_emails if total_emails > 0 else 0
        )
        
        overall_acceptance_rate = (
            total_acceptances / total_responses if total_responses > 0 else 0
        )
        
        return {
            "total_curators_contacted": len(self._engagement_data),
            "total_emails_sent": total_emails,
            "total_responses": total_responses,
            "total_acceptances": total_acceptances,
            "total_placements": total_placements,
            "overall_response_rate": overall_response_rate,
            "overall_acceptance_rate": overall_acceptance_rate,
            "total_campaigns": len(self._campaign_data),
            "stub_mode": True
        }
