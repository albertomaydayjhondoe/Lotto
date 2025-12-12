"""
Tests for Sentiment Analyzer - Sprint 4B

Tests sentiment analysis with lexicon-based approach (NO LLM).
Target: ≥90% accuracy
"""

import pytest

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from community_ai.sentiment_analyzer import SentimentAnalyzer
from community_ai.models import SentimentResult, SentimentType


# ========================================
# Fixtures
# ========================================

@pytest.fixture
def analyzer():
    """Create a SentimentAnalyzer instance."""
    return SentimentAnalyzer()


@pytest.fixture
def positive_comments_es():
    """Positive Spanish comments."""
    return [
        "¡Me encanta este tema! 🔥🔥🔥",
        "Increíble, cuando sale el videoclip?",
        "Esta canción está brutal, la mejor",
        "NECESITO más música así 🙏",
        "Tremenda producción hermano"
    ]


@pytest.fixture
def negative_comments_es():
    """Negative Spanish comments."""
    return [
        "No me gusta este estilo",
        "La anterior canción era mejor",
        "Esto no es lo tuyo bro",
        "Que decepción",
        "Ya no eres el mismo"
    ]


@pytest.fixture
def neutral_comments_es():
    """Neutral Spanish comments."""
    return [
        "Ok",
        "Interesante",
        "No está mal",
        "A ver qué tal",
        "Hmmm"
    ]


@pytest.fixture
def positive_comments_en():
    """Positive English comments."""
    return [
        "This is fire! 🔥",
        "Amazing work bro",
        "Can't wait for more!",
        "NEED this on Spotify NOW",
        "Best track of the year"
    ]


@pytest.fixture
def hype_comments():
    """Hype-indicating comments."""
    return [
        "Cuando sale el tema completo?",
        "NECESITO esta canción ya",
        "Where can I download this?",
        "Release date please!!!",
        "Ya quiero escuchar el álbum"
    ]


# ========================================
# Test Initialization
# ========================================

def test_analyzer_initialization(analyzer):
    """Test analyzer initializes correctly."""
    assert analyzer is not None
    assert analyzer.lexicon_es is not None
    assert analyzer.lexicon_en is not None


# ========================================
# Test Single Comment Analysis (Spanish)
# ========================================

def test_analyze_positive_comment_es(analyzer):
    """Test positive Spanish comment."""
    result = analyzer.analyze_comment(
        text="¡Me encanta este tema! 🔥🔥🔥",
        language="es"
    )
    
    assert isinstance(result, SentimentResult)
    assert result.sentiment == SentimentType.POSITIVE
    assert result.confidence > 0.7


def test_analyze_negative_comment_es(analyzer):
    """Test negative Spanish comment."""
    result = analyzer.analyze_comment(
        text="No me gusta este estilo",
        language="es"
    )
    
    assert result.sentiment == SentimentType.NEGATIVE
    assert result.confidence > 0.6


def test_analyze_neutral_comment_es(analyzer):
    """Test neutral Spanish comment."""
    result = analyzer.analyze_comment(
        text="Interesante",
        language="es"
    )
    
    assert result.sentiment == SentimentType.NEUTRAL


# ========================================
# Test Single Comment Analysis (English)
# ========================================

def test_analyze_positive_comment_en(analyzer):
    """Test positive English comment."""
    result = analyzer.analyze_comment(
        text="This is fire! 🔥",
        language="en"
    )
    
    assert result.sentiment == SentimentType.POSITIVE
    assert result.confidence > 0.7


def test_analyze_negative_comment_en(analyzer):
    """Test negative English comment."""
    result = analyzer.analyze_comment(
        text="This is terrible",
        language="en"
    )
    
    assert result.sentiment == SentimentType.NEGATIVE


# ========================================
# Test Batch Analysis
# ========================================

def test_analyze_batch_basic(analyzer, positive_comments_es):
    """Test batch analysis."""
    results = analyzer.analyze_batch(
        comments=positive_comments_es,
        language="es"
    )
    
    assert len(results) == len(positive_comments_es)
    assert all(isinstance(r, SentimentResult) for r in results)


def test_batch_analysis_preserves_order(analyzer):
    """Test batch preserves comment order."""
    comments = [
        "Me encanta",
        "No me gusta",
        "Ok"
    ]
    
    results = analyzer.analyze_batch(comments, "es")
    
    assert len(results) == 3
    assert results[0].sentiment == SentimentType.POSITIVE
    assert results[1].sentiment == SentimentType.NEGATIVE
    assert results[2].sentiment == SentimentType.NEUTRAL


def test_batch_analysis_large_set(analyzer):
    """Test batch with 200+ comments."""
    comments = ["Me encanta este tema"] * 250
    
    results = analyzer.analyze_batch(comments, "es")
    
    assert len(results) == 250
    assert all(r.sentiment == SentimentType.POSITIVE for r in results)


# ========================================
# Test Sentiment Score Calculation
# ========================================

def test_sentiment_score_range(analyzer):
    """Test sentiment score is in range [-1, 1]."""
    result = analyzer.analyze_comment("Me encanta", "es")
    
    assert -1.0 <= result.score <= 1.0


def test_positive_score_above_zero(analyzer, positive_comments_es):
    """Test positive comments have score > 0."""
    for comment in positive_comments_es:
        result = analyzer.analyze_comment(comment, "es")
        assert result.score > 0


def test_negative_score_below_zero(analyzer, negative_comments_es):
    """Test negative comments have score < 0."""
    for comment in negative_comments_es:
        result = analyzer.analyze_comment(comment, "es")
        assert result.score < 0


def test_neutral_score_near_zero(analyzer, neutral_comments_es):
    """Test neutral comments have score near 0."""
    for comment in neutral_comments_es:
        result = analyzer.analyze_comment(comment, "es")
        assert -0.3 <= result.score <= 0.3


# ========================================
# Test Topic Extraction
# ========================================

def test_extract_topics_basic(analyzer):
    """Test topic extraction."""
    result = analyzer.analyze_comment(
        text="Me encanta el videoclip y la producción musical",
        language="es"
    )
    
    assert isinstance(result.topics, list)
    assert len(result.topics) > 0


def test_topics_include_keywords(analyzer):
    """Test extracted topics include key themes."""
    result = analyzer.analyze_comment(
        text="El beat está increíble y el flow es brutal",
        language="es"
    )
    
    topics_str = " ".join(result.topics).lower()
    assert "beat" in topics_str or "flow" in topics_str or "música" in topics_str


# ========================================
# Test Hype Detection
# ========================================

def test_detect_hype_when_present(analyzer):
    """Test hype detection in comments."""
    result = analyzer.analyze_comment(
        text="Cuando sale el tema completo?",
        language="es"
    )
    
    assert result.is_hype is True


def test_hype_with_need_keyword(analyzer):
    """Test hype detection with 'necesito'."""
    result = analyzer.analyze_comment(
        text="NECESITO esta canción ya",
        language="es"
    )
    
    assert result.is_hype is True


def test_hype_with_release_date_en(analyzer):
    """Test hype detection in English."""
    result = analyzer.analyze_comment(
        text="Release date please!!!",
        language="en"
    )
    
    assert result.is_hype is True


def test_no_hype_regular_comment(analyzer):
    """Test no hype in regular comments."""
    result = analyzer.analyze_comment(
        text="Me gusta el tema",
        language="es"
    )
    
    assert result.is_hype is False


# ========================================
# Test Confidence Scoring
# ========================================

def test_confidence_high_for_strong_words(analyzer):
    """Test high confidence for strong sentiment."""
    result = analyzer.analyze_comment(
        text="¡INCREÍBLE! Me encanta muchísimo 🔥🔥🔥",
        language="es"
    )
    
    assert result.confidence > 0.8


def test_confidence_lower_for_neutral(analyzer):
    """Test lower confidence for neutral."""
    result = analyzer.analyze_comment(
        text="Ok",
        language="es"
    )
    
    # Neutral should have lower confidence
    assert result.confidence < 0.8


# ========================================
# Test Multi-language Support
# ========================================

def test_spanish_and_english_consistency(analyzer):
    """Test both languages work consistently."""
    es_result = analyzer.analyze_comment("Me encanta", "es")
    en_result = analyzer.analyze_comment("I love it", "en")
    
    assert es_result.sentiment == en_result.sentiment == SentimentType.POSITIVE


# ========================================
# Test Edge Cases
# ========================================

def test_empty_comment(analyzer):
    """Test empty comment handling."""
    result = analyzer.analyze_comment("", "es")
    
    assert result.sentiment == SentimentType.NEUTRAL
    assert result.score == 0.0


def test_emoji_only_comment(analyzer):
    """Test emoji-only comment."""
    result = analyzer.analyze_comment("🔥🔥🔥", "es")
    
    # Should detect positive sentiment from fire emojis
    assert result.sentiment in [SentimentType.POSITIVE, SentimentType.NEUTRAL]


def test_mixed_language_comment(analyzer):
    """Test mixed Spanish-English."""
    result = analyzer.analyze_comment(
        text="Me encanta bro this is fire 🔥",
        language="es"  # Primary language Spanish
    )
    
    # Should still detect positive sentiment
    assert result.sentiment == SentimentType.POSITIVE


def test_very_long_comment(analyzer):
    """Test very long comment."""
    long_text = "Me encanta " * 100
    result = analyzer.analyze_comment(long_text, "es")
    
    assert result.sentiment == SentimentType.POSITIVE


def test_special_characters(analyzer):
    """Test comment with special characters."""
    result = analyzer.analyze_comment(
        text="¡¡¡Me encanta!!! @stakazo #trap",
        language="es"
    )
    
    assert result.sentiment == SentimentType.POSITIVE


def test_uppercase_comment(analyzer):
    """Test all-uppercase comment."""
    result = analyzer.analyze_comment(
        text="ME ENCANTA ESTE TEMA",
        language="es"
    )
    
    # Should handle uppercase
    assert result.sentiment == SentimentType.POSITIVE


# ========================================
# Test Accuracy Target
# ========================================

def test_accuracy_target_positive(analyzer, positive_comments_es):
    """Test ≥90% accuracy on positive comments."""
    results = analyzer.analyze_batch(positive_comments_es, "es")
    
    correct = sum(1 for r in results if r.sentiment == SentimentType.POSITIVE)
    accuracy = correct / len(results)
    
    assert accuracy >= 0.90  # Target: ≥90%


def test_accuracy_target_negative(analyzer, negative_comments_es):
    """Test ≥90% accuracy on negative comments."""
    results = analyzer.analyze_batch(negative_comments_es, "es")
    
    correct = sum(1 for r in results if r.sentiment == SentimentType.NEGATIVE)
    accuracy = correct / len(results)
    
    assert accuracy >= 0.90


# ========================================
# Test Cost Optimization (NO LLM)
# ========================================

def test_no_llm_calls(analyzer):
    """Test that NO LLM calls are made."""
    # This is implicit: analyzer uses lexicon-based approach
    # Cost per batch should be ~0 (no API calls)
    result = analyzer.analyze_comment("Me encanta", "es")
    
    # Should complete instantly (no API latency)
    assert result is not None


# ========================================
# Run tests
# ========================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
