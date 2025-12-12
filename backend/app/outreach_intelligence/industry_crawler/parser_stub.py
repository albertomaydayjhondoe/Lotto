"""
Industry Crawler — Parser STUB

Parses crawled data from various sources and extracts relevant contact information.

STUB MODE: Returns mock parsed data.
"""

from typing import Dict, Any, List
import re


class ParserStub:
    """
    STUB: Parses HTML, JSON, and text data from crawled sources.
    
    In LIVE mode:
    - BeautifulSoup for HTML parsing
    - JSON extraction from APIs
    - Email pattern recognition
    - Contact form detection
    
    Phase 4: Mock parsing.
    """
    
    def __init__(self):
        self.stub_mode = True
        
    def parse_html_page(self, html_content: str) -> Dict[str, Any]:
        """STUB: Parse HTML for contact info"""
        return {
            "emails_found": ["curator@example.com"],
            "social_links": {"instagram": "@curator", "twitter": "@curator"},
            "submission_forms": ["https://example.com/submit"],
            "genres_mentioned": ["Deep House", "Techno"],
            "stub_note": "STUB MODE"
        }
    
    def extract_email_from_text(self, text: str) -> List[str]:
        """STUB: Extract emails using regex"""
        # Simple regex pattern
        pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        return re.findall(pattern, text) if not self.stub_mode else ["extracted@example.com"]
    
    def parse_spotify_api_response(self, api_response: Dict[str, Any]) -> Dict[str, Any]:
        """STUB: Parse Spotify API data"""
        return {
            "playlist_id": "mock_playlist_001",
            "name": "Mock Playlist",
            "followers": 50000,
            "owner": "Mock Curator",
            "stub_note": "STUB MODE"
        }
    
    def parse_youtube_api_response(self, api_response: Dict[str, Any]) -> Dict[str, Any]:
        """STUB: Parse YouTube API data"""
        return {
            "channel_id": "mock_channel_001",
            "channel_name": "Mock Channel",
            "subscribers": 100000,
            "stub_note": "STUB MODE"
        }
