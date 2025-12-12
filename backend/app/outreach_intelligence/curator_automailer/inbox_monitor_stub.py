"""
Curator AutoMailer — Inbox Monitor STUB

Monitors incoming responses from curators, parses feedback,
and triggers appropriate actions (thank you emails, blacklist updates, etc.).

STUB MODE: Simulates inbox monitoring and response parsing.
"""

from typing import Dict, Any, List
from datetime import datetime
from enum import Enum


class ResponseType(Enum):
    """Type of curator response"""
    POSITIVE = "positive"  # Added to playlist
    INTERESTED = "interested"  # Interested, needs more info
    NOT_A_FIT = "not_a_fit"  # Not right for playlist
    UNSUBSCRIBE = "unsubscribe"  # Don't contact again
    AUTO_REPLY = "auto_reply"  # Out of office, etc.
    SPAM_COMPLAINT = "spam_complaint"  # Reported as spam
    QUESTION = "question"  # Has questions
    NO_RESPONSE = "no_response"  # No reply


class InboxMonitorStub:
    """
    STUB: Monitors curator responses and parses intent.
    
    In LIVE mode:
    - Connects to email inbox (IMAP/Gmail API)
    - Uses NLP to classify responses
    - Extracts action items
    - Triggers automated workflows
    - Learns from response patterns
    
    Phase 4: Simulates response monitoring.
    """
    
    def __init__(self):
        self.stub_mode = True
        self.monitored_responses = []
        
    def check_inbox(
        self,
        since_datetime: str = None
    ) -> List[Dict[str, Any]]:
        """
        STUB: Check inbox for new responses.
        
        Args:
            since_datetime: Only check emails after this time
            
        Returns:
            List of new responses
        """
        # STUB: Return mock responses
        mock_responses = [
            {
                "email_id": "response_001",
                "from": "curator1@spotify.com",
                "subject": "Re: Track Submission for Deep Electronic Vibes",
                "body": "Thanks for the submission! Added to my playlist. Great track!",
                "received_at": datetime.now().isoformat(),
                "original_campaign_id": "campaign_001",
                "stub_note": "STUB MODE - Mock positive response"
            },
            {
                "email_id": "response_002",
                "from": "curator2@playlist.com",
                "subject": "Re: Track Submission",
                "body": "Not quite the right fit for my playlist, but keep sending!",
                "received_at": datetime.now().isoformat(),
                "original_campaign_id": "campaign_002",
                "stub_note": "STUB MODE - Mock negative response"
            },
            {
                "email_id": "response_003",
                "from": "curator3@music.com",
                "subject": "Re: Track Submission",
                "body": "Please remove me from your list. I don't accept unsolicited submissions.",
                "received_at": datetime.now().isoformat(),
                "original_campaign_id": "campaign_003",
                "stub_note": "STUB MODE - Mock unsubscribe"
            }
        ]
        
        return mock_responses
    
    def parse_response(
        self,
        response: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        STUB: Parse curator response and classify intent.
        
        Args:
            response: Raw response data
            
        Returns:
            Parsed response with classification
        """
        body_lower = response.get("body", "").lower()
        
        # STUB: Simple keyword-based classification
        response_type = ResponseType.NO_RESPONSE
        action_needed = None
        blacklist_action = None
        
        # Positive indicators
        if any(word in body_lower for word in ["added", "great", "love", "playlist"]):
            response_type = ResponseType.POSITIVE
            action_needed = "send_thank_you"
        
        # Negative but polite
        elif any(word in body_lower for word in ["not a fit", "not right", "pass"]):
            response_type = ResponseType.NOT_A_FIT
            action_needed = "note_preference"
        
        # Unsubscribe
        elif any(word in body_lower for word in ["unsubscribe", "remove", "stop", "don't contact"]):
            response_type = ResponseType.UNSUBSCRIBE
            action_needed = "blacklist_permanent"
            blacklist_action = "permanent"
        
        # Spam complaint
        elif any(word in body_lower for word in ["spam", "report", "unsolicited"]):
            response_type = ResponseType.SPAM_COMPLAINT
            action_needed = "blacklist_permanent"
            blacklist_action = "permanent"
        
        # Question
        elif any(word in body_lower for word in ["?", "question", "how", "what", "when"]):
            response_type = ResponseType.QUESTION
            action_needed = "manual_review"
        
        # Auto-reply
        elif any(word in body_lower for word in ["out of office", "automatic reply", "away"]):
            response_type = ResponseType.AUTO_REPLY
            action_needed = "reschedule_follow_up"
        
        # Interested
        elif any(word in body_lower for word in ["interested", "send more", "maybe", "consider"]):
            response_type = ResponseType.INTERESTED
            action_needed = "send_more_info"
        
        return {
            "response_id": response.get("email_id"),
            "type": response_type.value,
            "action_needed": action_needed,
            "blacklist_action": blacklist_action,
            "sentiment_score": self._calculate_sentiment(body_lower),
            "key_phrases": self._extract_key_phrases(body_lower),
            "requires_manual_review": response_type in [
                ResponseType.QUESTION,
                ResponseType.SPAM_COMPLAINT
            ],
            "parsed_at": datetime.now().isoformat(),
            "stub_note": "STUB MODE - Simple keyword classification"
        }
    
    def _calculate_sentiment(self, text: str) -> float:
        """
        STUB: Calculate sentiment score.
        
        In LIVE mode: Uses NLP model.
        """
        # STUB: Simple keyword-based sentiment
        positive_words = ["great", "love", "excellent", "perfect", "awesome"]
        negative_words = ["not", "don't", "stop", "spam", "remove"]
        
        positive_count = sum(1 for word in positive_words if word in text)
        negative_count = sum(1 for word in negative_words if word in text)
        
        if positive_count > negative_count:
            return 0.75
        elif negative_count > positive_count:
            return 0.25
        else:
            return 0.50
    
    def _extract_key_phrases(self, text: str) -> List[str]:
        """
        STUB: Extract key phrases from response.
        
        In LIVE mode: Uses NLP extraction.
        """
        # STUB: Return common phrases
        phrases = []
        
        if "added" in text:
            phrases.append("playlist_add")
        if "not a fit" in text or "not right" in text:
            phrases.append("rejection_polite")
        if "unsubscribe" in text or "remove" in text:
            phrases.append("unsubscribe_request")
        if "?" in text:
            phrases.append("has_question")
        
        return phrases
    
    def trigger_automated_actions(
        self,
        parsed_response: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        STUB: Trigger automated actions based on response.
        
        Args:
            parsed_response: Parsed response data
            
        Returns:
            Actions triggered
        """
        actions_triggered = []
        
        action = parsed_response.get("action_needed")
        
        if action == "send_thank_you":
            actions_triggered.append({
                "action": "send_thank_you_email",
                "status": "queued",
                "note": "STUB MODE - Would send thank you email"
            })
        
        elif action == "blacklist_permanent":
            actions_triggered.append({
                "action": "add_to_blacklist",
                "blacklist_type": "permanent",
                "status": "completed",
                "note": "STUB MODE - Would add to blacklist"
            })
            
            # Cancel any scheduled follow-ups
            actions_triggered.append({
                "action": "cancel_follow_ups",
                "status": "completed",
                "note": "STUB MODE - Would cancel follow-ups"
            })
        
        elif action == "note_preference":
            actions_triggered.append({
                "action": "update_curator_preferences",
                "preference": "not_interested_in_genre",
                "status": "completed",
                "note": "STUB MODE - Would update preferences"
            })
        
        elif action == "manual_review":
            actions_triggered.append({
                "action": "flag_for_manual_review",
                "status": "pending",
                "note": "STUB MODE - Would notify team"
            })
        
        elif action == "send_more_info":
            actions_triggered.append({
                "action": "send_additional_info",
                "status": "queued",
                "note": "STUB MODE - Would send press kit"
            })
        
        return {
            "response_id": parsed_response.get("response_id"),
            "actions": actions_triggered,
            "triggered_at": datetime.now().isoformat(),
            "stub_note": "STUB MODE - Actions simulated"
        }
    
    def get_response_statistics(
        self,
        campaign_id: str = None
    ) -> Dict[str, Any]:
        """
        STUB: Get response statistics.
        
        Args:
            campaign_id: Optional campaign to filter by
            
        Returns:
            Statistics summary
        """
        # STUB: Return mock statistics
        return {
            "total_responses": 156,
            "response_rate": 0.23,  # 23% response rate
            "response_breakdown": {
                "positive": 45,  # 29%
                "interested": 23,  # 15%
                "not_a_fit": 65,  # 42%
                "unsubscribe": 12,  # 8%
                "spam_complaint": 3,  # 2%
                "questions": 8  # 5%
            },
            "avg_response_time_hours": 48,
            "playlist_add_rate": 0.29,  # 29% of responses are adds
            "campaign_id": campaign_id,
            "stub_note": "STUB MODE - Mock statistics"
        }
    
    def get_pending_manual_reviews(self) -> List[Dict[str, Any]]:
        """
        STUB: Get responses requiring manual review.
        
        Returns:
            List of responses needing human attention
        """
        # STUB: Return mock pending reviews
        return [
            {
                "response_id": "response_004",
                "from": "curator4@music.com",
                "reason": "Has question about licensing",
                "priority": "medium",
                "received_at": datetime.now().isoformat(),
                "stub_note": "STUB MODE - Mock review item"
            },
            {
                "response_id": "response_005",
                "from": "curator5@radio.com",
                "reason": "Possible spam complaint",
                "priority": "high",
                "received_at": datetime.now().isoformat(),
                "stub_note": "STUB MODE - Mock review item"
            }
        ]
