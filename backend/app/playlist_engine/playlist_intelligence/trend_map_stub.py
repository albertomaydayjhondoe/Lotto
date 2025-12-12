"""
Playlist Intelligence — Trend Map STUB

Tracks current playlist trends and genre popularity.
STUB MODE: Returns mock trend data.
"""

from typing import Dict, List, Any
from dataclasses import dataclass
from datetime import datetime


@dataclass
class GenreTrend:
    """Genre trend information"""
    genre: str
    popularity_score: float  # 0-1
    trending: str  # "up", "stable", "down"
    avg_bpm: int
    avg_energy: float
    dominant_moods: List[str]
    hot_subgenres: List[str]


class TrendMapStub:
    """
    STUB: Provides trend analysis for playlists and genres.
    
    In LIVE mode, this would use:
    - Spotify Charts API
    - TikTok trending sounds
    - YouTube Music trends
    - Social media sentiment analysis
    - Historical streaming data
    
    Phase 3: Returns mock trend data.
    """
    
    def __init__(self):
        self.stub_mode = True
        self._trends = self._generate_mock_trends()
        
    def _generate_mock_trends(self) -> Dict[str, GenreTrend]:
        """Generate mock trend data for major genres"""
        return {
            "Deep House": GenreTrend(
                genre="Deep House",
                popularity_score=0.85,
                trending="up",
                avg_bpm=124,
                avg_energy=0.72,
                dominant_moods=["Chill", "Euphoric", "Atmospheric"],
                hot_subgenres=["Organic House", "Afro House", "Melodic House"]
            ),
            "Tech House": GenreTrend(
                genre="Tech House",
                popularity_score=0.92,
                trending="up",
                avg_bpm=128,
                avg_energy=0.85,
                dominant_moods=["Groovy", "Energetic", "Peak Hour"],
                hot_subgenres=["Minimal Tech", "Vocal Tech House", "Bass House"]
            ),
            "Melodic Techno": GenreTrend(
                genre="Melodic Techno",
                popularity_score=0.88,
                trending="stable",
                avg_bpm=124,
                avg_energy=0.78,
                dominant_moods=["Atmospheric", "Emotional", "Progressive"],
                hot_subgenres=["Progressive House", "Organic Techno", "Ambient Techno"]
            ),
            "Future Bass": GenreTrend(
                genre="Future Bass",
                popularity_score=0.75,
                trending="down",
                avg_bpm=150,
                avg_energy=0.90,
                dominant_moods=["Uplifting", "Energetic", "Melodic"],
                hot_subgenres=["Chill Trap", "Melodic Dubstep", "Wave"]
            ),
            "Lo-Fi House": GenreTrend(
                genre="Lo-Fi House",
                popularity_score=0.80,
                trending="up",
                avg_bpm=120,
                avg_energy=0.60,
                dominant_moods=["Chill", "Nostalgic", "Warm"],
                hot_subgenres=["Minimal House", "Microhouse", "Dub Techno"]
            ),
            "Indie Dance": GenreTrend(
                genre="Indie Dance",
                popularity_score=0.78,
                trending="stable",
                avg_bpm=118,
                avg_energy=0.75,
                dominant_moods=["Uplifting", "Feel-Good", "Nostalgic"],
                hot_subgenres=["Nu Disco", "Electro Funk", "Synth Pop"]
            ),
            "Progressive House": GenreTrend(
                genre="Progressive House",
                popularity_score=0.82,
                trending="stable",
                avg_bpm=128,
                avg_energy=0.80,
                dominant_moods=["Euphoric", "Uplifting", "Progressive"],
                hot_subgenres=["Melodic Progressive", "Festival Progressive", "Deep Progressive"]
            ),
            "Ambient": GenreTrend(
                genre="Ambient",
                popularity_score=0.70,
                trending="up",
                avg_bpm=90,
                avg_energy=0.35,
                dominant_moods=["Meditative", "Atmospheric", "Peaceful"],
                hot_subgenres=["Dark Ambient", "Organic Ambient", "Cinematic Ambient"]
            ),
            "Synthwave": GenreTrend(
                genre="Synthwave",
                popularity_score=0.72,
                trending="stable",
                avg_bpm=115,
                avg_energy=0.68,
                dominant_moods=["Nostalgic", "Cinematic", "Retro"],
                hot_subgenres=["Darksynth", "Outrun", "Cyberpunk"]
            ),
            "Electronica": GenreTrend(
                genre="Electronica",
                popularity_score=0.68,
                trending="stable",
                avg_bpm=120,
                avg_energy=0.70,
                dominant_moods=["Creative", "Experimental", "Abstract"],
                hot_subgenres=["IDM", "Glitch", "Leftfield"]
            )
        }
    
    def get_genre_trend(self, genre: str) -> GenreTrend:
        """Get trend data for specific genre"""
        return self._trends.get(genre, self._get_default_trend(genre))
    
    def _get_default_trend(self, genre: str) -> GenreTrend:
        """Return default trend for unknown genres"""
        return GenreTrend(
            genre=genre,
            popularity_score=0.50,
            trending="stable",
            avg_bpm=120,
            avg_energy=0.65,
            dominant_moods=["Neutral"],
            hot_subgenres=[]
        )
    
    def get_trending_genres(self, limit: int = 10) -> List[GenreTrend]:
        """Get top trending genres"""
        trends = list(self._trends.values())
        trends.sort(key=lambda t: t.popularity_score, reverse=True)
        return trends[:limit]
    
    def get_genres_by_bpm(self, bpm: int, tolerance: int = 5) -> List[GenreTrend]:
        """Find genres compatible with given BPM"""
        compatible = []
        for trend in self._trends.values():
            if abs(trend.avg_bpm - bpm) <= tolerance:
                compatible.append(trend)
        return compatible
    
    def get_hot_subgenres(self) -> Dict[str, List[str]]:
        """Get all hot subgenres by main genre"""
        return {
            trend.genre: trend.hot_subgenres
            for trend in self._trends.values()
        }
    
    def predict_playlist_demand(
        self,
        genre: str,
        mood: str,
        bpm: int
    ) -> Dict[str, Any]:
        """
        STUB: Predict demand for playlists matching criteria.
        
        Args:
            genre: Main genre
            mood: Track mood
            bpm: Track BPM
            
        Returns:
            Demand prediction dict
        """
        trend = self.get_genre_trend(genre)
        
        # Calculate demand score
        demand_score = trend.popularity_score
        
        # Adjust for mood
        if mood in trend.dominant_moods:
            demand_score *= 1.15
        
        # Adjust for BPM match
        if abs(trend.avg_bpm - bpm) <= 3:
            demand_score *= 1.10
        elif abs(trend.avg_bpm - bpm) <= 8:
            demand_score *= 1.05
        
        demand_score = min(demand_score, 1.0)
        
        return {
            "genre": genre,
            "mood": mood,
            "bpm": bpm,
            "demand_score": demand_score,
            "trend_direction": trend.trending,
            "recommendation": self._get_demand_recommendation(demand_score, trend.trending)
        }
    
    def _get_demand_recommendation(self, score: float, trending: str) -> str:
        """Generate recommendation based on demand score"""
        if score >= 0.85 and trending == "up":
            return "High demand - submit to multiple playlists immediately"
        elif score >= 0.75:
            return "Good demand - target top playlists in genre"
        elif score >= 0.60:
            return "Moderate demand - focus on niche playlists"
        elif trending == "up":
            return "Growing trend - consider early positioning"
        else:
            return "Low demand - consider alternative genres or wait for trend shift"
    
    def get_playlist_saturation(self, genre: str) -> Dict[str, Any]:
        """
        STUB: Analyze playlist saturation for genre.
        
        Returns:
            Saturation analysis
        """
        trend = self.get_genre_trend(genre)
        
        # Mock saturation calculation
        saturation = 0.65 if trend.popularity_score > 0.80 else 0.45
        
        return {
            "genre": genre,
            "saturation_level": saturation,
            "competition": "high" if saturation > 0.70 else "medium" if saturation > 0.50 else "low",
            "opportunity_score": 1.0 - saturation,
            "recommendation": self._get_saturation_recommendation(saturation)
        }
    
    def _get_saturation_recommendation(self, saturation: float) -> str:
        """Generate recommendation based on saturation"""
        if saturation < 0.40:
            return "Low competition - good opportunity for placement"
        elif saturation < 0.65:
            return "Moderate competition - quality matters"
        else:
            return "High competition - need exceptional quality or unique angle"
