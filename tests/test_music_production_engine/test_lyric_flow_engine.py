"""Tests for Lyric Flow Engine module."""
import pytest
from backend.app.music_production_engine.lyric_flow_engine import (
    WhisperStub, LyricAnalyzer, FlowAnalyzer, CorrectionEngine
)

@pytest.mark.asyncio
async def test_whisper_transcription():
    transcriber = WhisperStub()
    result = await transcriber.transcribe("https://audio.mp3", word_timestamps=True)
    assert len(result.text) > 0
    assert len(result.segments) > 0
    assert result.language == "en"

@pytest.mark.asyncio
async def test_lyric_analysis():
    analyzer = LyricAnalyzer()
    lyrics = "I'm on my grind every day\nMaking moves in every way"
    result = await analyzer.analyze(lyrics)
    assert 0 <= result.quality_score <= 100
    assert result.metrics.total_lines == 2

@pytest.mark.asyncio
async def test_correction_engine():
    engine = CorrectionEngine()
    lyrics = "Test lyrics"
    report = await engine.generate_corrections(lyrics, {"issues": []}, {})
    assert report.total_suggestions >= 0
