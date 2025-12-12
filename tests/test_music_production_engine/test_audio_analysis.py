"""Tests for Audio Analysis module."""
import pytest
from backend.app.music_production_engine.audio_analysis import (
    EssentiaAnalyzerStub, DemucsStub, CrepeStub, LibrosaStub, VGGishStub, StructureAnalyzer, ScoringEngine
)

@pytest.mark.asyncio
async def test_essentia_analysis():
    analyzer = EssentiaAnalyzerStub()
    result = await analyzer.analyze("https://audio.mp3")
    assert result.rhythm.bpm > 0
    assert 0 <= result.spectral.spectral_flatness <= 1

@pytest.mark.asyncio
async def test_demucs_separation():
    separator = DemucsStub()
    result = await separator.separate("https://audio.mp3")
    assert result.separated.vocals_url.endswith("_vocals.wav")
    assert result.separation_quality > 50

@pytest.mark.asyncio
async def test_scoring_engine():
    scorer = ScoringEngine()
    analyses = {"essentia": {}, "demucs": {}, "crepe": {}, "librosa": {}, "vggish": {}, "structure": {}}
    score = await scorer.score(analyses)
    assert 0 <= score.overall_score <= 100
    assert len(score.component_scores) > 0
