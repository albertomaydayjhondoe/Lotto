"""
Curator AutoMailer — Curator Database STUB

Mock curator database with 200+ curators.
STUB MODE: Returns mock curator data.
"""

from typing import List, Dict, Any
from dataclasses import dataclass


@dataclass
class CuratorData:
    """Curator information"""
    curator_id: str
    name: str
    email: str
    playlists: List[str]
    total_followers: int
    accepts_unreleased: bool
    language: str
    timezone: str
    response_rate: float
    avg_response_time_days: int
    specialties: List[str]
    preferred_contact_day: str  # "weekday", "weekend", "any"


class CuratorDatabaseStub:
    """
    STUB: Curator database with 200+ mock curators.
    
    In LIVE mode, this would connect to:
    - Curator CRM system
    - Historical email engagement data
    - Curator relationship manager
    
    Phase 3: Returns mock curator profiles only.
    """
    
    def __init__(self):
        self.stub_mode = True
        self._curators = self._generate_mock_curators()
        
    def _generate_mock_curators(self) -> List[CuratorData]:
        """Generate 200+ mock curators"""
        curators = []
        
        # Premium curators (large playlists)
        premium_data = [
            ("Deep House", ["Deep House", "Tech House", "Melodic House"], "en", 150000),
            ("Electronic Vibes", ["Progressive House", "Trance", "Melodic Techno"], "en", 200000),
            ("Chill Electronic", ["Chillout", "Downtempo", "Ambient"], "en", 180000),
            ("Future Bass Central", ["Future Bass", "Trap", "Melodic Dubstep"], "en", 175000),
            ("Indie Dance Movement", ["Indie Dance", "Nu Disco", "Electro"], "en", 160000),
        ]
        
        for i, (name, specialties, lang, followers) in enumerate(premium_data):
            curators.append(CuratorData(
                curator_id=f"premium_{i:03d}",
                name=f"{name} Curator",
                email=f"curator.{name.lower().replace(' ', '.')}@premium.stub",
                playlists=[f"{name} #{j+1}" for j in range(3)],
                total_followers=followers,
                accepts_unreleased=False,
                language=lang,
                timezone="America/Los_Angeles",
                response_rate=0.45,
                avg_response_time_days=7,
                specialties=specialties,
                preferred_contact_day="weekday"
            ))
        
        # Mid-tier curators
        mid_tier_genres = [
            ["Lo-Fi House", "Minimal"],
            ["Synthwave", "Retrowave"],
            ["Organic House", "Afro House"],
            ["Tech House", "Minimal Techno"],
            ["Progressive House", "Big Room"],
        ]
        
        for i, specialties in enumerate(mid_tier_genres * 40):  # 200 mid-tier
            curators.append(CuratorData(
                curator_id=f"midtier_{i:03d}",
                name=f"Curator {specialties[0]} {i}",
                email=f"curator.midtier.{i}@playlist.stub",
                playlists=[f"{specialties[0]} Collection"],
                total_followers=25000 + (i * 500),
                accepts_unreleased=i % 3 == 0,
                language="en" if i % 2 == 0 else "es",
                timezone="America/New_York" if i % 2 == 0 else "Europe/London",
                response_rate=0.60,
                avg_response_time_days=5,
                specialties=specialties,
                preferred_contact_day="weekday" if i % 2 == 0 else "any"
            ))
        
        # Independent curators (smaller, more responsive)
        indie_genres = [
            ["Experimental", "IDM"],
            ["Electronica", "Leftfield"],
            ["Breakbeat", "UK Garage"],
            ["Ambient", "Drone"],
        ]
        
        for i, specialties in enumerate(indie_genres * 50):  # 200 indie
            curators.append(CuratorData(
                curator_id=f"indie_{i:03d}",
                name=f"Indie Curator {i}",
                email=f"curator.indie.{i}@underground.stub",
                playlists=[f"Underground {specialties[0]}"],
                total_followers=5000 + (i * 100),
                accepts_unreleased=i % 2 == 0,
                language="en",
                timezone="America/Los_Angeles",
                response_rate=0.75,
                avg_response_time_days=3,
                specialties=specialties,
                preferred_contact_day="any"
            ))
        
        return curators
    
    def get_all_curators(self) -> List[CuratorData]:
        """Get all curators"""
        return self._curators
    
    def get_curator_by_id(self, curator_id: str) -> CuratorData:
        """Get specific curator"""
        for c in self._curators:
            if c.curator_id == curator_id:
                return c
        return None
    
    def filter_by_specialty(self, genre: str) -> List[CuratorData]:
        """Filter curators by genre specialty"""
        return [
            c for c in self._curators
            if genre in c.specialties
        ]
    
    def filter_by_unreleased_acceptance(self, accepts: bool = True) -> List[CuratorData]:
        """Filter curators who accept unreleased tracks"""
        return [
            c for c in self._curators
            if c.accepts_unreleased == accepts
        ]
    
    def filter_by_followers(self, min_followers: int = 0, max_followers: int = 999999999) -> List[CuratorData]:
        """Filter by follower count"""
        return [
            c for c in self._curators
            if min_followers <= c.total_followers <= max_followers
        ]
    
    def filter_by_response_rate(self, min_rate: float = 0.0) -> List[CuratorData]:
        """Filter by response rate"""
        return [
            c for c in self._curators
            if c.response_rate >= min_rate
        ]
    
    def search_by_email(self, email: str) -> CuratorData:
        """Search curator by email"""
        for c in self._curators:
            if c.email.lower() == email.lower():
                return c
        return None
