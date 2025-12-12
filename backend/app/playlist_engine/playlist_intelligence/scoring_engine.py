"""
Playlist Intelligence — Scoring Engine

Calculates comprehensive playlist fit scores.
STUB MODE: Returns mock weighted scores.
"""

from typing import Dict, List, Any, Tuple
from dataclasses import dataclass

from .analyzer_stub import TrackAnalysis
from .playlist_database_stub import PlaylistData
from .trend_map_stub import TrendMapStub


@dataclass
class PlaylistScore:
    """Detailed playlist scoring breakdown"""
    playlist_id: str
    total_score: float
    component_scores: Dict[str, float]
    weighted_breakdown: Dict[str, Dict[str, Any]]
    confidence_level: str  # "high", "medium", "low"


class ScoringEngine:
    """
    STUB: Advanced scoring engine for playlist compatibility.
    
    Uses weighted multi-factor analysis to determine optimal
    playlist matches with explainable scoring.
    
    Scoring Factors:
    - Genre/Subgenre Match (30%)
    - BPM Compatibility (20%)
    - Mood/Vibe Alignment (15%)
    - Production Quality (15%)
    - Trend Alignment (10%)
    - A&R Score (10%)
    
    Phase 3: STUB scoring logic, no ML models.
    """
    
    def __init__(self):
        self.stub_mode = True
        self.trend_map = TrendMapStub()
        
        # Scoring weights
        self.weights = {
            "genre_match": 0.30,
            "bpm_compatibility": 0.20,
            "mood_alignment": 0.15,
            "production_quality": 0.15,
            "trend_alignment": 0.10,
            "a_and_r_score": 0.10
        }
        
    def calculate_detailed_score(
        self,
        track: TrackAnalysis,
        playlist: PlaylistData
    ) -> PlaylistScore:
        """
        Calculate comprehensive playlist fit score.
        
        Args:
            track: TrackAnalysis object
            playlist: PlaylistData object
            
        Returns:
            PlaylistScore with detailed breakdown
        """
        scores = {}
        breakdown = {}
        
        # 1. Genre Match (30%)
        genre_score, genre_details = self._score_genre_match(track, playlist)
        scores["genre_match"] = genre_score * self.weights["genre_match"]
        breakdown["genre_match"] = genre_details
        
        # 2. BPM Compatibility (20%)
        bpm_score, bpm_details = self._score_bpm_compatibility(track, playlist)
        scores["bpm_compatibility"] = bpm_score * self.weights["bpm_compatibility"]
        breakdown["bpm_compatibility"] = bpm_details
        
        # 3. Mood Alignment (15%)
        mood_score, mood_details = self._score_mood_alignment(track, playlist)
        scores["mood_alignment"] = mood_score * self.weights["mood_alignment"]
        breakdown["mood_alignment"] = mood_details
        
        # 4. Production Quality (15%)
        quality_score, quality_details = self._score_production_quality(track)
        scores["production_quality"] = quality_score * self.weights["production_quality"]
        breakdown["production_quality"] = quality_details
        
        # 5. Trend Alignment (10%)
        trend_score, trend_details = self._score_trend_alignment(track)
        scores["trend_alignment"] = trend_score * self.weights["trend_alignment"]
        breakdown["trend_alignment"] = trend_details
        
        # 6. A&R Score (10%)
        a_and_r_score, a_and_r_details = self._score_a_and_r(track)
        scores["a_and_r_score"] = a_and_r_score * self.weights["a_and_r_score"]
        breakdown["a_and_r_score"] = a_and_r_details
        
        # Calculate total
        total_score = sum(scores.values())
        
        # Determine confidence
        confidence = self._calculate_confidence(scores, breakdown)
        
        return PlaylistScore(
            playlist_id=playlist.playlist_id,
            total_score=total_score,
            component_scores=scores,
            weighted_breakdown=breakdown,
            confidence_level=confidence
        )
    
    def _score_genre_match(
        self,
        track: TrackAnalysis,
        playlist: PlaylistData
    ) -> Tuple[float, Dict[str, Any]]:
        """Score genre compatibility"""
        score = 0.0
        match_type = "none"
        
        if track.genre in playlist.accepted_genres:
            score = 1.0
            match_type = "exact_genre"
        elif track.subgenre in playlist.accepted_genres:
            score = 0.85
            match_type = "subgenre"
        elif any(track.genre.lower() in g.lower() or g.lower() in track.genre.lower() 
                for g in playlist.accepted_genres):
            score = 0.65
            match_type = "related_genre"
        
        return score, {
            "raw_score": score,
            "match_type": match_type,
            "track_genre": track.genre,
            "track_subgenre": track.subgenre,
            "playlist_genres": playlist.accepted_genres,
            "explanation": self._get_genre_explanation(score, match_type)
        }
    
    def _score_bpm_compatibility(
        self,
        track: TrackAnalysis,
        playlist: PlaylistData
    ) -> Tuple[float, Dict[str, Any]]:
        """Score BPM compatibility"""
        bpm_min, bpm_max = playlist.bpm_range
        track_bpm = track.bpm
        
        if bpm_min <= track_bpm <= bpm_max:
            score = 1.0
            fit = "perfect"
        elif abs(track_bpm - bpm_min) <= 3 or abs(track_bpm - bpm_max) <= 3:
            score = 0.85
            fit = "close"
        elif abs(track_bpm - bpm_min) <= 8 or abs(track_bpm - bpm_max) <= 8:
            score = 0.65
            fit = "acceptable"
        else:
            score = 0.3
            fit = "poor"
        
        return score, {
            "raw_score": score,
            "track_bpm": track_bpm,
            "playlist_bpm_range": playlist.bpm_range,
            "fit_level": fit,
            "explanation": self._get_bpm_explanation(score, track_bpm, playlist.bpm_range)
        }
    
    def _score_mood_alignment(
        self,
        track: TrackAnalysis,
        playlist: PlaylistData
    ) -> Tuple[float, Dict[str, Any]]:
        """Score mood/vibe alignment"""
        track_mood = track.mood.lower()
        playlist_mood = playlist.mood.lower()
        
        # Direct match
        if track_mood == playlist_mood:
            score = 1.0
            alignment = "exact"
        # Partial match
        elif track_mood in playlist_mood or playlist_mood in track_mood:
            score = 0.75
            alignment = "similar"
        # Compatible moods (stub logic)
        elif self._moods_are_compatible(track_mood, playlist_mood):
            score = 0.55
            alignment = "compatible"
        else:
            score = 0.3
            alignment = "different"
        
        # Energy factor
        energy_match = 1.0 - abs(track.energy - 0.7) * 0.5  # Assume playlist energy ~0.7
        score = (score * 0.7) + (energy_match * 0.3)
        
        return score, {
            "raw_score": score,
            "track_mood": track.mood,
            "track_energy": track.energy,
            "playlist_mood": playlist.mood,
            "alignment_level": alignment,
            "explanation": f"{alignment.capitalize()} mood match"
        }
    
    def _moods_are_compatible(self, mood1: str, mood2: str) -> bool:
        """Check if moods are compatible (STUB logic)"""
        compatible_groups = [
            {"chill", "relaxed", "calm", "peaceful", "meditative"},
            {"energetic", "uplifting", "euphoric", "peak hour"},
            {"dark", "atmospheric", "deep", "hypnotic"},
            {"happy", "feel-good", "upbeat", "positive"},
            {"emotional", "melancholic", "introspective", "reflective"}
        ]
        
        for group in compatible_groups:
            if mood1 in group and mood2 in group:
                return True
        return False
    
    def _score_production_quality(
        self,
        track: TrackAnalysis
    ) -> Tuple[float, Dict[str, Any]]:
        """Score production quality"""
        quality = track.production_quality
        
        if quality >= 0.85:
            rating = "exceptional"
        elif quality >= 0.75:
            rating = "professional"
        elif quality >= 0.65:
            rating = "good"
        elif quality >= 0.50:
            rating = "acceptable"
        else:
            rating = "needs_improvement"
        
        return quality, {
            "raw_score": quality,
            "rating": rating,
            "explanation": f"{rating.replace('_', ' ').capitalize()} production quality"
        }
    
    def _score_trend_alignment(
        self,
        track: TrackAnalysis
    ) -> Tuple[float, Dict[str, Any]]:
        """Score trend alignment"""
        trend = self.trend_map.get_genre_trend(track.genre)
        
        # Base score from popularity
        score = trend.popularity_score
        
        # Boost for trending up
        if trend.trending == "up":
            score *= 1.15
        elif trend.trending == "down":
            score *= 0.85
        
        score = min(score, 1.0)
        
        return score, {
            "raw_score": score,
            "genre_popularity": trend.popularity_score,
            "trend_direction": trend.trending,
            "explanation": f"Genre {trend.trending} with {trend.popularity_score:.0%} popularity"
        }
    
    def _score_a_and_r(
        self,
        track: TrackAnalysis
    ) -> Tuple[float, Dict[str, Any]]:
        """Score A&R quality"""
        a_and_r = track.a_and_r_score / 10.0  # Normalize to 0-1
        
        if a_and_r >= 0.85:
            tier = "premium"
        elif a_and_r >= 0.70:
            tier = "strong"
        elif a_and_r >= 0.60:
            tier = "good"
        else:
            tier = "developing"
        
        return a_and_r, {
            "raw_score": a_and_r,
            "a_and_r_score": track.a_and_r_score,
            "tier": tier,
            "explanation": f"{tier.capitalize()} A&R rating ({track.a_and_r_score}/10)"
        }
    
    def _calculate_confidence(
        self,
        scores: Dict[str, float],
        breakdown: Dict[str, Dict[str, Any]]
    ) -> str:
        """Calculate confidence level for the score"""
        # High confidence if multiple strong signals
        strong_signals = sum(1 for score in scores.values() if score >= 0.15)
        
        if strong_signals >= 4 and scores["genre_match"] >= 0.20:
            return "high"
        elif strong_signals >= 3:
            return "medium"
        else:
            return "low"
    
    def _get_genre_explanation(self, score: float, match_type: str) -> str:
        """Get human-readable genre match explanation"""
        explanations = {
            "exact_genre": "Perfect genre match",
            "subgenre": "Subgenre matches playlist",
            "related_genre": "Related genre - good fit",
            "none": "Genre mismatch"
        }
        return explanations.get(match_type, "Unknown match type")
    
    def _get_bpm_explanation(
        self,
        score: float,
        track_bpm: int,
        playlist_range: Tuple[int, int]
    ) -> str:
        """Get human-readable BPM explanation"""
        if score >= 0.95:
            return f"BPM {track_bpm} perfectly fits playlist range {playlist_range}"
        elif score >= 0.80:
            return f"BPM {track_bpm} very close to playlist range {playlist_range}"
        elif score >= 0.60:
            return f"BPM {track_bpm} acceptable for playlist range {playlist_range}"
        else:
            return f"BPM {track_bpm} outside optimal range {playlist_range}"
