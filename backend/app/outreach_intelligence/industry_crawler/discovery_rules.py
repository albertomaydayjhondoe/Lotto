"""
Industry Crawler — Discovery Rules

Defines rules for discovering and filtering relevant industry contacts.

STUB MODE: Returns mock rules and filters.
"""

from typing import Dict, Any, List
from enum import Enum


class DiscoveryPriority(Enum):
    """Priority levels for discovery"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class DiscoveryRules:
    """
    Rules engine for contact discovery and filtering.
    
    Phase 4: STUB implementation.
    """
    
    def __init__(self):
        self.stub_mode = True
        self.rules = self._load_rules()
        
    def _load_rules(self) -> Dict[str, Any]:
        """Load discovery rules"""
        return {
            "min_playlist_followers": 1000,
            "min_blog_monthly_visitors": 5000,
            "min_youtube_subscribers": 10000,
            "min_radio_listeners": 5000,
            "required_genres": ["Electronic", "House", "Techno"],
            "blacklisted_domains": ["spam.com"],
            "preferred_countries": ["US", "UK", "DE", "FR", "NL"],
            "min_confidence_score": 0.65
        }
    
    def should_contact(self, opportunity: Dict[str, Any]) -> bool:
        """STUB: Determine if opportunity should be contacted"""
        confidence = opportunity.get("confidence_score", 0)
        return confidence >= self.rules["min_confidence_score"]
    
    def calculate_priority(self, opportunity: Dict[str, Any]) -> DiscoveryPriority:
        """STUB: Calculate contact priority"""
        confidence = opportunity.get("confidence_score", 0)
        if confidence >= 0.80:
            return DiscoveryPriority.HIGH
        elif confidence >= 0.65:
            return DiscoveryPriority.MEDIUM
        return DiscoveryPriority.LOW
