"""
Playlist Intelligence — Matcher STUB

Matches tracks to compatible playlists.
STUB MODE: Returns mock matching scores.
"""

from typing import List, Dict, Any, Tuple
from dataclasses import dataclass

from .analyzer_stub import TrackAnalysis
from .playlist_database_stub import PlaylistData, PlaylistDatabaseStub


@dataclass
class PlaylistMatch:
    """Playlist match result"""
    playlist: PlaylistData
    compatibility_score: float
    match_reasons: List[str]
    recommended_action: str  # "submit_now", "submit_after_release", "skip"
    priority: str  # "high", "medium", "low"


class PlaylistMatcherStub:
    """
    STUB: Matches tracks to compatible playlists.
    
    In LIVE mode, this would use:
    - ML models for similarity matching
    - Historical success rates
    - Curator behavior patterns
    - Real-time playlist trends
    
    Phase 3: Returns mock matches with scoring logic.
    """
    
    def __init__(self):
        self.stub_mode = True
        self.playlist_db = PlaylistDatabaseStub()
        
    def match_track(
        self,
        track_analysis: TrackAnalysis,
        is_released: bool = False,
        min_score: float = 0.5
    ) -> List[PlaylistMatch]:
        """
        STUB: Find compatible playlists for a track.
        
        Args:
            track_analysis: TrackAnalysis object
            is_released: Whether track has been released
            min_score: Minimum compatibility score threshold
            
        Returns:
            List of PlaylistMatch objects sorted by score
        """
        matches = []
        
        # Get candidate playlists
        if is_released:
            candidates = self.playlist_db.get_all_playlists()
        else:
            candidates = self.playlist_db.filter_by_unreleased_acceptance(True)
        
        # Score each playlist
        for playlist in candidates:
            score, reasons = self._calculate_compatibility_score(
                track_analysis, playlist, is_released
            )
            
            if score >= min_score:
                match = PlaylistMatch(
                    playlist=playlist,
                    compatibility_score=score,
                    match_reasons=reasons,
                    recommended_action=self._get_recommended_action(score, is_released, playlist),
                    priority=self._get_priority(score, playlist.size)
                )
                matches.append(match)
        
        # Sort by score (highest first)
        matches.sort(key=lambda m: m.compatibility_score, reverse=True)
        
        return matches
    
    def _calculate_compatibility_score(
        self,
        track: TrackAnalysis,
        playlist: PlaylistData,
        is_released: bool
    ) -> Tuple[float, List[str]]:
        """
        STUB: Calculate compatibility score between track and playlist.
        
        Returns:
            (score, reasons) tuple
        """
        score = 0.0
        reasons = []
        
        # Genre match (30%)
        if track.genre in playlist.accepted_genres:
            score += 0.3
            reasons.append(f"Genre match: {track.genre}")
        elif track.subgenre in playlist.accepted_genres:
            score += 0.2
            reasons.append(f"Subgenre match: {track.subgenre}")
        
        # BPM compatibility (20%)
        if playlist.bpm_range[0] <= track.bpm <= playlist.bpm_range[1]:
            score += 0.2
            reasons.append(f"BPM in range: {track.bpm}")
        elif abs(track.bpm - playlist.bpm_range[0]) <= 5 or abs(track.bpm - playlist.bpm_range[1]) <= 5:
            score += 0.1
            reasons.append(f"BPM close to range: {track.bpm}")
        
        # Mood match (15%)
        if track.mood.lower() in playlist.mood.lower() or playlist.mood.lower() in track.mood.lower():
            score += 0.15
            reasons.append(f"Mood match: {track.mood}")
        
        # Production quality (15%)
        quality_bonus = track.production_quality * 0.15
        score += quality_bonus
        if track.production_quality >= 0.8:
            reasons.append(f"High production quality: {track.production_quality:.2f}")
        
        # A&R score (10%)
        a_and_r_bonus = (track.a_and_r_score / 10) * 0.1
        score += a_and_r_bonus
        if track.a_and_r_score >= 7.5:
            reasons.append(f"Strong A&R score: {track.a_and_r_score}")
        
        # Release type compatibility (10%)
        if is_released and playlist.release_type in ["released", "both"]:
            score += 0.1
            reasons.append("Release status compatible")
        elif not is_released and playlist.release_type in ["unreleased", "both"]:
            score += 0.1
            reasons.append("Accepts unreleased tracks")
        
        return (min(score, 1.0), reasons)
    
    def _get_recommended_action(
        self,
        score: float,
        is_released: bool,
        playlist: PlaylistData
    ) -> str:
        """Determine recommended action based on score and status"""
        if score >= 0.75:
            return "submit_now"
        elif score >= 0.6 and is_released:
            return "submit_now"
        elif score >= 0.6 and not is_released and playlist.accepts_unreleased:
            return "submit_now"
        elif score >= 0.5 and not is_released:
            return "submit_after_release"
        else:
            return "skip"
    
    def _get_priority(self, score: float, playlist_size: int) -> str:
        """Determine priority based on score and playlist size"""
        if score >= 0.8 and playlist_size >= 50000:
            return "high"
        elif score >= 0.7 or playlist_size >= 100000:
            return "high"
        elif score >= 0.6:
            return "medium"
        else:
            return "low"
    
    def get_top_matches(
        self,
        track_analysis: TrackAnalysis,
        is_released: bool = False,
        limit: int = 20
    ) -> List[PlaylistMatch]:
        """
        STUB: Get top N playlist matches.
        
        Args:
            track_analysis: TrackAnalysis object
            is_released: Whether track has been released
            limit: Maximum number of matches to return
            
        Returns:
            Top N PlaylistMatch objects
        """
        all_matches = self.match_track(track_analysis, is_released)
        return all_matches[:limit]
