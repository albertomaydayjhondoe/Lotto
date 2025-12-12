"""
Playlist Intelligence — Playlist Database STUB

Contains mock playlist data for matching.
STUB MODE: 200+ mock playlists.
"""

from typing import List, Dict, Any
from dataclasses import dataclass


@dataclass
class PlaylistData:
    """Playlist information"""
    playlist_id: str
    name: str
    size: int
    curator_email: str
    curator_name: str
    accepted_genres: List[str]
    accepts_unreleased: bool
    mood: str
    keywords: List[str]
    bpm_range: tuple
    release_type: str  # "unreleased", "released", "both"
    engagement_rate: float
    avg_streams: int


class PlaylistDatabaseStub:
    """
    STUB: Playlist database with 200+ mock playlists.
    
    In LIVE mode, this would connect to:
    - Real playlist database
    - Spotify API for playlist metadata
    - Curator CRM system
    
    Phase 3: Returns mock playlist data only.
    """
    
    def __init__(self):
        self.stub_mode = True
        self._playlists = self._generate_mock_playlists()
        
    def _generate_mock_playlists(self) -> List[PlaylistData]:
        """Generate 200+ mock playlists"""
        playlists = []
        
        # Large playlists (100k+ followers)
        large_playlists = [
            ("Deep House Vibes", ["Deep House", "Tech House"], "Euphoric", (120, 128)),
            ("Chill Electronic", ["Chillout", "Downtempo"], "Relaxed", (90, 110)),
            ("Indie Electronic Hits", ["Indie Dance", "Nu Disco"], "Uplifting", (115, 125)),
            ("Future Bass Energy", ["Future Bass", "Trap"], "Energetic", (140, 160)),
            ("Melodic Techno Journey", ["Melodic Techno", "Progressive House"], "Atmospheric", (120, 128)),
        ]
        
        for i, (name, genres, mood, bpm_range) in enumerate(large_playlists):
            playlists.append(PlaylistData(
                playlist_id=f"large_{i:03d}",
                name=name,
                size=150000 + (i * 50000),
                curator_email=f"curator.large.{i}@playlist.stub",
                curator_name=f"Curator Large {i}",
                accepted_genres=genres,
                accepts_unreleased=False,
                mood=mood,
                keywords=genres + [mood.lower()],
                bpm_range=bpm_range,
                release_type="released",
                engagement_rate=0.85,
                avg_streams=50000
            ))
        
        # Medium playlists (10k-100k followers)
        medium_genres = [
            (["Synthwave", "Retrowave"], "Nostalgic", (110, 120)),
            (["Lo-Fi House", "Minimal"], "Chill", (118, 124)),
            (["Progressive House", "Trance"], "Uplifting", (128, 138)),
            (["Ambient", "Downtempo"], "Meditative", (80, 100)),
            (["Tech House", "Minimal Techno"], "Groovy", (124, 130)),
        ]
        
        for i, (genres, mood, bpm_range) in enumerate(medium_genres * 20):  # 100 medium
            playlists.append(PlaylistData(
                playlist_id=f"medium_{i:03d}",
                name=f"{genres[0]} Collection #{i}",
                size=25000 + (i * 1000),
                curator_email=f"curator.medium.{i}@playlist.stub",
                curator_name=f"Curator Medium {i}",
                accepted_genres=genres,
                accepts_unreleased=i % 3 == 0,  # 1/3 accept unreleased
                mood=mood,
                keywords=genres + [mood.lower()],
                bpm_range=bpm_range,
                release_type="both" if i % 3 == 0 else "released",
                engagement_rate=0.65,
                avg_streams=8000
            ))
        
        # Small playlists (1k-10k followers) - more accept unreleased
        small_genres = [
            (["Experimental", "IDM"], "Abstract", (90, 140)),
            (["Organic House", "Afro House"], "Warm", (118, 124)),
            (["Breakbeat", "UK Garage"], "Energetic", (130, 140)),
            (["Electronica", "Leftfield"], "Creative", (100, 130)),
        ]
        
        for i, (genres, mood, bpm_range) in enumerate(small_genres * 25):  # 100 small
            playlists.append(PlaylistData(
                playlist_id=f"small_{i:03d}",
                name=f"{genres[0]} Underground #{i}",
                size=3000 + (i * 200),
                curator_email=f"curator.small.{i}@playlist.stub",
                curator_name=f"Curator Small {i}",
                accepted_genres=genres,
                accepts_unreleased=i % 2 == 0,  # 50% accept unreleased
                mood=mood,
                keywords=genres + [mood.lower()],
                bpm_range=bpm_range,
                release_type="both" if i % 2 == 0 else "unreleased",
                engagement_rate=0.45,
                avg_streams=1500
            ))
        
        return playlists
    
    def get_all_playlists(self) -> List[PlaylistData]:
        """Get all playlists"""
        return self._playlists
    
    def filter_by_genre(self, genre: str) -> List[PlaylistData]:
        """Filter playlists by genre"""
        return [
            p for p in self._playlists
            if genre in p.accepted_genres
        ]
    
    def filter_by_unreleased_acceptance(self, accepts_unreleased: bool = True) -> List[PlaylistData]:
        """Filter playlists that accept unreleased tracks"""
        return [
            p for p in self._playlists
            if p.accepts_unreleased == accepts_unreleased
        ]
    
    def filter_by_size(self, min_size: int = 0, max_size: int = 999999999) -> List[PlaylistData]:
        """Filter playlists by size range"""
        return [
            p for p in self._playlists
            if min_size <= p.size <= max_size
        ]
    
    def filter_by_bpm_range(self, track_bpm: int, tolerance: int = 5) -> List[PlaylistData]:
        """Filter playlists compatible with track BPM"""
        return [
            p for p in self._playlists
            if p.bpm_range[0] - tolerance <= track_bpm <= p.bpm_range[1] + tolerance
        ]
    
    def get_playlist_by_id(self, playlist_id: str) -> PlaylistData:
        """Get specific playlist by ID"""
        for p in self._playlists:
            if p.playlist_id == playlist_id:
                return p
        return None
    
    def search_by_keywords(self, keywords: List[str]) -> List[PlaylistData]:
        """Search playlists by keywords"""
        results = []
        for playlist in self._playlists:
            if any(kw.lower() in [pk.lower() for pk in playlist.keywords] for kw in keywords):
                results.append(playlist)
        return results
