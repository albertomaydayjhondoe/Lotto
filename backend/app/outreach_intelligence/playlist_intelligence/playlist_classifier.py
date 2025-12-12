"""
Playlist Intelligence — Playlist Classifier

Classifies playlists by type, style, and suitability for different tracks.
Uses ML models (STUB) to categorize and score playlist opportunities.

STUB MODE: Returns mock classifications.
"""

from typing import Dict, Any, List
from dataclasses import dataclass
from enum import Enum


class PlaylistTier(Enum):
    """Playlist tier classification"""
    EDITORIAL = "editorial"  # Spotify/Apple editorial
    MAJOR_INDEPENDENT = "major_independent"  # 100k+ followers
    ESTABLISHED = "established"  # 10k-100k followers
    EMERGING = "emerging"  # 1k-10k followers
    MICRO = "micro"  # <1k followers


class PlaylistType(Enum):
    """Playlist type categories"""
    GENRE_FOCUSED = "genre_focused"
    MOOD_BASED = "mood_based"
    ACTIVITY = "activity"
    ALGORITHMIC = "algorithmic"
    ARTIST_CURATED = "artist_curated"
    BRAND = "brand"
    PERSONAL = "personal"


@dataclass
class PlaylistClassification:
    """Complete playlist classification"""
    playlist_id: str
    playlist_name: str
    tier: PlaylistTier
    type: PlaylistType
    primary_genre: str
    subgenres: List[str]
    mood_tags: List[str]
    activity_context: str
    follower_count: int
    engagement_rate: float
    acceptance_likelihood: float
    response_time_days: int
    curator_reputation: float
    last_update: str


class PlaylistClassifier:
    """
    STUB: Classifies playlists using ML models.
    
    In LIVE mode:
    - Trains on historical data
    - Uses NLP for playlist title/description analysis
    - Tracks success rates per playlist type
    - Updates classifications based on performance
    
    Phase 4: Returns mock classifications.
    """
    
    def __init__(self):
        self.stub_mode = True
        self.classification_model = None  # STUB: Would load ML model
        
    def classify_playlist(
        self,
        playlist_data: Dict[str, Any]
    ) -> PlaylistClassification:
        """
        STUB: Classify a single playlist.
        
        Args:
            playlist_data: Raw playlist information
            
        Returns:
            Detailed classification
        """
        # STUB: Return mock classification
        return PlaylistClassification(
            playlist_id=playlist_data.get("id", "playlist_001"),
            playlist_name=playlist_data.get("name", "Deep Electronic Vibes"),
            tier=PlaylistTier.ESTABLISHED,
            type=PlaylistType.GENRE_FOCUSED,
            primary_genre="Melodic House & Techno",
            subgenres=["Progressive House", "Organic House", "Downtempo"],
            mood_tags=["atmospheric", "emotional", "driving", "nocturnal"],
            activity_context="Late night focus, driving, workouts",
            follower_count=45000,
            engagement_rate=0.68,
            acceptance_likelihood=0.72,
            response_time_days=7,
            curator_reputation=0.85,
            last_update="2025-11-28"
        )
    
    def classify_batch(
        self,
        playlists: List[Dict[str, Any]]
    ) -> List[PlaylistClassification]:
        """
        STUB: Classify multiple playlists efficiently.
        
        Args:
            playlists: List of playlist data
            
        Returns:
            List of classifications
        """
        return [self.classify_playlist(p) for p in playlists]
    
    def filter_by_tier(
        self,
        classifications: List[PlaylistClassification],
        tiers: List[PlaylistTier]
    ) -> List[PlaylistClassification]:
        """Filter playlists by tier"""
        return [c for c in classifications if c.tier in tiers]
    
    def filter_by_genre(
        self,
        classifications: List[PlaylistClassification],
        genre: str,
        include_subgenres: bool = True
    ) -> List[PlaylistClassification]:
        """Filter playlists by genre match"""
        results = []
        for c in classifications:
            if genre.lower() in c.primary_genre.lower():
                results.append(c)
            elif include_subgenres:
                if any(genre.lower() in sg.lower() for sg in c.subgenres):
                    results.append(c)
        return results
    
    def rank_by_opportunity(
        self,
        classifications: List[PlaylistClassification],
        track_metadata: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        STUB: Rank playlists by opportunity score.
        
        In LIVE mode: Uses ML model trained on success data.
        
        Args:
            classifications: Playlist classifications
            track_metadata: Track info for matching
            
        Returns:
            Ranked list with opportunity scores
        """
        ranked = []
        
        for c in classifications:
            # STUB: Simple scoring algorithm
            opportunity_score = (
                c.acceptance_likelihood * 0.35 +
                c.engagement_rate * 0.25 +
                c.curator_reputation * 0.20 +
                (min(c.follower_count / 100000, 1.0)) * 0.20
            )
            
            ranked.append({
                "classification": c,
                "opportunity_score": round(opportunity_score, 3),
                "estimated_reach": int(c.follower_count * c.engagement_rate),
                "priority": "high" if opportunity_score >= 0.75 else 
                           "medium" if opportunity_score >= 0.5 else "low",
                "reasoning": self._generate_reasoning(c, track_metadata),
                "stub_note": "STUB MODE - Use trained ML model in Phase 5"
            })
        
        # Sort by opportunity score
        ranked.sort(key=lambda x: x["opportunity_score"], reverse=True)
        
        return ranked
    
    def _generate_reasoning(
        self,
        classification: PlaylistClassification,
        track_metadata: Dict[str, Any]
    ) -> str:
        """Generate reasoning for playlist match"""
        # STUB: Simple rule-based reasoning
        reasons = []
        
        if classification.follower_count > 50000:
            reasons.append("High reach potential")
        
        if classification.engagement_rate > 0.65:
            reasons.append("Strong engagement")
        
        if classification.acceptance_likelihood > 0.70:
            reasons.append("High acceptance probability")
        
        if classification.curator_reputation > 0.80:
            reasons.append("Reputable curator")
        
        return ", ".join(reasons) if reasons else "Good general fit"
    
    def get_editorial_targets(
        self,
        track_metadata: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        STUB: Get Spotify/Apple editorial playlist targets.
        
        PRE-RELEASE: Returns editorial targets for manual pitch.
        
        Args:
            track_metadata: Track information
            
        Returns:
            List of editorial opportunities (STUB)
        """
        # STUB: Return mock editorial targets
        return [
            {
                "platform": "Spotify",
                "playlist_name": "Electronic Rising",
                "tier": "Editorial",
                "submission_method": "Spotify for Artists (manual)",
                "lead_time_weeks": 4,
                "success_probability": 0.15,
                "note": "Submit 4 weeks before release via Spotify for Artists",
                "stub_mode": True
            },
            {
                "platform": "Spotify",
                "playlist_name": "Night Mode",
                "tier": "Editorial",
                "submission_method": "Spotify for Artists (manual)",
                "lead_time_weeks": 3,
                "success_probability": 0.22,
                "note": "Strong melodic house focus, fits track profile",
                "stub_mode": True
            },
            {
                "platform": "Apple Music",
                "playlist_name": "Deep House Hits",
                "tier": "Editorial",
                "submission_method": "Apple Music for Artists (manual)",
                "lead_time_weeks": 2,
                "success_probability": 0.18,
                "note": "Submit via Apple Music for Artists dashboard",
                "stub_mode": True
            }
        ]
