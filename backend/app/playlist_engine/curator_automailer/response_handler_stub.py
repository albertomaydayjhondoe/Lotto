"""
Curator AutoMailer — Response Handler STUB

Handles curator responses and classifications.
STUB MODE: Simulates response processing.
"""

from typing import Dict, Any, List
from datetime import datetime
from enum import Enum


class ResponseType(Enum):
    """Curator response types"""
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    NO_SUBMIT = "no_submit"
    TRY_LATER = "try_later"
    REQUEST_INFO = "request_info"
    BLACKLIST_REQUEST = "blacklist_request"
    NO_RESPONSE = "no_response"
    OUT_OF_OFFICE = "out_of_office"


class ResponseHandlerStub:
    """
    STUB: Processes curator email responses.
    
    In LIVE mode, this would use:
    - Gmail/Email API for inbox monitoring
    - NLP for sentiment analysis
    - Intent classification models
    - Automated response routing
    
    Phase 3: Simulates response classification.
    """
    
    def __init__(self):
        self.stub_mode = True
        self._responses = []
        
    def classify_response(
        self,
        email_body: str,
        curator_email: str
    ) -> Dict[str, Any]:
        """
        STUB: Classify curator response type.
        
        Args:
            email_body: Response email body
            curator_email: Curator's email
            
        Returns:
            Classification result
        """
        # STUB: Simple keyword matching
        body_lower = email_body.lower()
        
        if any(word in body_lower for word in ["yes", "accepted", "added", "love it", "great track"]):
            response_type = ResponseType.ACCEPTED
            sentiment = "positive"
        elif any(word in body_lower for word in ["no", "pass", "not fit", "don't accept"]):
            response_type = ResponseType.REJECTED
            sentiment = "negative"
        elif any(word in body_lower for word in ["don't send", "unsubscribe", "remove me", "stop"]):
            response_type = ResponseType.BLACKLIST_REQUEST
            sentiment = "negative"
        elif any(word in body_lower for word in ["try later", "full right now", "maybe next time"]):
            response_type = ResponseType.TRY_LATER
            sentiment = "neutral"
        elif any(word in body_lower for word in ["more info", "tell me more", "send me"]):
            response_type = ResponseType.REQUEST_INFO
            sentiment = "positive"
        elif any(word in body_lower for word in ["out of office", "on vacation", "away"]):
            response_type = ResponseType.OUT_OF_OFFICE
            sentiment = "neutral"
        else:
            response_type = ResponseType.NO_RESPONSE
            sentiment = "neutral"
        
        classification = {
            "curator_email": curator_email,
            "response_type": response_type.value,
            "sentiment": sentiment,
            "confidence": 0.85,  # STUB confidence
            "classified_at": datetime.utcnow().isoformat(),
            "stub_mode": True
        }
        
        self._responses.append(classification)
        
        return classification
    
    def process_acceptance(
        self,
        curator_email: str,
        playlist_id: str,
        track_id: str
    ) -> Dict[str, Any]:
        """
        STUB: Process playlist acceptance.
        
        Args:
            curator_email: Curator's email
            playlist_id: Playlist ID
            track_id: Track ID
            
        Returns:
            Processing result
        """
        return {
            "status": "accepted",
            "curator_email": curator_email,
            "playlist_id": playlist_id,
            "track_id": track_id,
            "processed_at": datetime.utcnow().isoformat(),
            "actions_taken": [
                "Marked curator as positive contact",
                "Updated engagement tracker",
                "Scheduled thank you email",
                "Added to success metrics"
            ],
            "stub_mode": True
        }
    
    def process_rejection(
        self,
        curator_email: str,
        track_id: str,
        reason: str = None
    ) -> Dict[str, Any]:
        """
        STUB: Process playlist rejection.
        
        Args:
            curator_email: Curator's email
            track_id: Track ID
            reason: Optional rejection reason
            
        Returns:
            Processing result
        """
        return {
            "status": "rejected",
            "curator_email": curator_email,
            "track_id": track_id,
            "reason": reason,
            "processed_at": datetime.utcnow().isoformat(),
            "actions_taken": [
                "Updated engagement tracker",
                "Marked for future analysis",
                "No further action required"
            ],
            "stub_mode": True
        }
    
    def process_blacklist_request(
        self,
        curator_email: str
    ) -> Dict[str, Any]:
        """
        STUB: Process blacklist request.
        
        Args:
            curator_email: Curator's email
            
        Returns:
            Processing result
        """
        return {
            "status": "blacklisted",
            "curator_email": curator_email,
            "processed_at": datetime.utcnow().isoformat(),
            "actions_taken": [
                "Added to permanent blacklist",
                "Removed from all future campaigns",
                "Logged unsubscribe request"
            ],
            "stub_mode": True
        }
    
    def get_response_stats(
        self,
        campaign_id: str = None
    ) -> Dict[str, Any]:
        """
        STUB: Get response statistics.
        
        Args:
            campaign_id: Optional campaign filter
            
        Returns:
            Statistics dict
        """
        # STUB: Mock statistics
        total_responses = len(self._responses)
        
        if total_responses == 0:
            return {
                "total_responses": 0,
                "stub_mode": True
            }
        
        accepted = len([r for r in self._responses if r["response_type"] == ResponseType.ACCEPTED.value])
        rejected = len([r for r in self._responses if r["response_type"] == ResponseType.REJECTED.value])
        
        return {
            "campaign_id": campaign_id,
            "total_responses": total_responses,
            "accepted": accepted,
            "rejected": rejected,
            "acceptance_rate": accepted / total_responses if total_responses > 0 else 0,
            "response_breakdown": {
                rt.value: len([r for r in self._responses if r["response_type"] == rt.value])
                for rt in ResponseType
            },
            "stub_mode": True
        }
