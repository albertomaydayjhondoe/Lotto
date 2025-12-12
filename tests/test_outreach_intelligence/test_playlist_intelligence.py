"""
Tests for Playlist Intelligence subsystem
"""

import pytest
from backend.app.outreach_intelligence.playlist_intelligence import (
    PlaylistAnalyzerStub,
    GPTPromptBuilder,
    PlaylistClassifier,
    PlaylistRecommendationEngine,
    ReleasePhase
)


def test_analyzer_track_analysis(sample_track_metadata):
    """Test track analysis"""
    analyzer = PlaylistAnalyzerStub()
    
    profile = analyzer.analyze_track(
        track_id=sample_track_metadata["track_id"],
        audio_file_path=None,
        lyrics="Sample lyrics",
        artist_metadata={}
    )
    
    assert profile.track_id == sample_track_metadata["track_id"]
    assert "audio_features" in profile.__dict__
    assert "gpt_insights" in profile.__dict__
    assert profile.gpt_insights["stub_note"] == "STUB MODE - Replace with real GPT-5 in Phase 5"


def test_gpt_prompt_builder():
    """Test GPT prompt generation"""
    builder = GPTPromptBuilder()
    
    prompt = builder.build_playlist_analysis_prompt({
        "genre": "Deep House",
        "mood": "Chill",
        "bpm": 124,
        "energy": 0.75,
        "features": ["atmospheric", "melodic"],
        "themes": ["night", "emotion"],
        "aesthetic": "minimalist"
    })
    
    assert "system" in prompt
    assert "user" in prompt