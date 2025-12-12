"""
Tests for Trend Map and Genre Analysis
"""

import pytest
from backend.app.playlist_engine.playlist_intelligence import TrendMapStub


def test_get_genre_trend():
    """Test retrieving genre trend data"""
    trend_map = TrendMapStub()
    
    trend = trend_map.get_genre_trend("Deep House")
    
    assert trend.genre == "Deep House"
    assert 0 <= trend.popularity_score <= 1
    assert trend.trending in ["up", "stable", "down"]
    assert isinstance(trend.avg_bpm, int)
    assert isinstance(trend.dominant_moods, list)
    assert len(trend.dominant_moods) > 0


def test_get_trending_genres():
    """Test getting top trending genres"""
    trend_map = TrendMapStub()
    
    trending = trend_map.get_trending_genres(limit=5)
    
    assert isinstance(trending, list)
    assert len(trending) <= 5
    
    # Verify sorted by popularity
    if len(trending) >= 2:
        assert trending[0].popularity_score >= trending[1].popularity_score


def test_get_genres_by_bpm():
    """Test finding genres compatible with BPM"""
    trend_map = TrendMapStub()
    
    compatible = trend_map.get_genres_by_bpm(bpm=124, tolerance=5)
    
    assert isinstance(compatible, list)
    
    # Verify BPM compatibility
    for trend in compatible:
        assert abs(trend.avg_bpm - 124) <= 5


def test_predict_playlist_demand():
    """Test demand prediction"""
    trend_map = TrendMapStub()
    
    prediction = trend_map.predict_playlist_demand(
        genre="Tech House",
        mood="Energetic",
        bpm=128
    )
    
    assert "demand_score" in prediction
    assert "trend_direction" in prediction
    assert "recommendation" in prediction
    assert 0 <= prediction["demand_score"] <= 1


def test_get_playlist_saturation():
    """Test saturation analysis"""
    trend_map = TrendMapStub()
    
    saturation = trend_map.get_playlist_saturation("Deep House")
    
    assert "saturation_level" in saturation
    assert "competition" in saturation
    assert saturation["competition"] in ["low", "medium", "high"]
    assert "opportunity_score" in saturation
    assert "recommendation" in saturation
