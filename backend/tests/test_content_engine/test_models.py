"""
Test Models
Tests para modelos Pydantic.
"""

import pytest
from pydantic import ValidationError
from app.content_engine.models import (
    ContentAnalysisRequest,
    VideoAnalysisResult,
    GeneratedHook,
    GeneratedCaption
)


def test_content_analysis_request_valid():
    """Test: Request válido se crea correctamente."""
    request = ContentAnalysisRequest(
        video_id="test_123",
        target_platform="instagram"
    )
    assert request.video_id == "test_123"
    assert request.target_platform == "instagram"
    assert request.generate_hooks is True  # default


def test_content_analysis_request_invalid_platform():
    """Test: Platform inválido lanza ValidationError."""
    with pytest.raises(ValidationError):
        ContentAnalysisRequest(
            video_id="test_123",
            target_platform="invalid_platform"
        )


def test_video_analysis_result():
    """Test: VideoAnalysisResult con valores válidos."""
    result = VideoAnalysisResult(
        video_id="test_video",
        duration_seconds=30.5,
        resolution="1080x1920",
        quality_score=0.85
    )
    assert result.quality_score == 0.85
    assert result.has_audio is True  # default


def test_generated_hook_valid():
    """Test: Hook con campos obligatorios."""
    hook = GeneratedHook(
        text="¿Sabías que este truco funciona?",
        type="question",
        confidence=0.8
    )
    assert hook.text == "¿Sabías que este truco funciona?"
    assert hook.confidence == 0.8


def test_generated_hook_text_too_short():
    """Test: Hook con texto muy corto falla."""
    with pytest.raises(ValidationError):
        GeneratedHook(
            text="Hola",  # < 10 chars
            type="question",
            confidence=0.8
        )


def test_generated_caption_with_hashtags():
    """Test: Caption con hashtags y emojis."""
    caption = GeneratedCaption(
        text="Descubre el secreto 🚀 #viral #contenido",
        hashtags=["viral", "contenido"],
        emojis=["🚀"],
        confidence=0.9
    )
    assert len(caption.hashtags) == 2
    assert caption.character_count > 0


def test_confidence_validation():
    """Test: Confidence fuera de rango falla."""
    with pytest.raises(ValidationError):
        GeneratedHook(
            text="Test hook text here",
            type="question",
            confidence=1.5  # > 1.0
        )
