"""
Tests for Brand Interrogator - Sprint 4

Tests the dynamic Q&A system that learns artist identity.
"""

import pytest
from datetime import datetime

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from brand_engine.brand_interrogator import BrandInterrogator
from brand_engine.models import (
    InterrogationQuestion,
    InterrogationResponse,
    BrandProfile,
    QuestionCategory
)


# ========================================
# Fixtures
# ========================================

@pytest.fixture
def interrogator():
    """Create a BrandInterrogator instance."""
    return BrandInterrogator()


@pytest.fixture
def sample_responses():
    """Sample responses for testing."""
    return {
        "aesthetic_primary_colors": "Purple and dark blue with neon accents",
        "aesthetic_mood": "Dark, mysterious, futuristic, cyberpunk",
        "aesthetic_references": "Blade Runner, cyberpunk art, neon Tokyo nights",
        "narrative_core_message": "Perseverance through darkness, finding light in struggle",
        "narrative_tone": "Raw, honest, introspective but hopeful",
        "narrative_themes": "Street life, dreams, resilience, authenticity",
        "cultural_galicia": "Proud Galician roots, references to coast and fog",
        "cultural_urban": "Street culture, trap lifestyle, urban authenticity",
        "restrictions_forbidden": "No violence, no drugs glorification, no disrespect",
        "restrictions_required": "Always genuine, always respectful, keep it real",
        "coherence_visual": "Every video must have consistent purple aesthetic",
        "coherence_narrative": "All content must align with core message",
        "vision_longterm": "Build authentic brand recognized for quality and message",
        "vision_evolution": "Allow natural evolution but maintain core identity"
    }


# ========================================
# Test Question Generation
# ========================================

def test_interrogator_initialization(interrogator):
    """Test interrogator initializes correctly."""
    assert interrogator is not None
    assert len(interrogator.questions) > 0


def test_get_next_question_aesthetic(interrogator):
    """Test getting aesthetic questions."""
    question = interrogator.get_next_question(QuestionCategory.AESTHETIC)
    
    assert question is not None
    assert question.category == QuestionCategory.AESTHETIC
    assert len(question.question_text) > 0


def test_get_next_question_narrative(interrogator):
    """Test getting narrative questions."""
    question = interrogator.get_next_question(QuestionCategory.NARRATIVE)
    
    assert question is not None
    assert question.category == QuestionCategory.NARRATIVE


def test_get_next_question_cultural(interrogator):
    """Test getting cultural questions."""
    question = interrogator.get_next_question(QuestionCategory.CULTURAL)
    
    assert question is not None
    assert question.category == QuestionCategory.CULTURAL


def test_all_questions_have_ids(interrogator):
    """Test all questions have unique IDs."""
    question_ids = set()
    
    for question in interrogator.questions:
        assert question.question_id not in question_ids
        question_ids.add(question.question_id)


def test_questions_cover_all_categories(interrogator):
    """Test questions exist for all categories."""
    categories = set(q.category for q in interrogator.questions)
    
    assert QuestionCategory.AESTHETIC in categories
    assert QuestionCategory.NARRATIVE in categories
    assert QuestionCategory.CULTURAL in categories
    assert QuestionCategory.RESTRICTIONS in categories
    assert QuestionCategory.COHERENCE in categories
    assert QuestionCategory.VISION in categories


# ========================================
# Test Response Recording
# ========================================

def test_record_response(interrogator):
    """Test recording a response."""
    question = interrogator.get_next_question(QuestionCategory.AESTHETIC)
    
    response = InterrogationResponse(
        question_id=question.question_id,
        answer="Purple and dark blue",
        timestamp=datetime.utcnow()
    )
    
    interrogator.record_response(response)
    
    assert len(interrogator.responses) == 1
    assert interrogator.responses[0].question_id == question.question_id


def test_record_multiple_responses(interrogator):
    """Test recording multiple responses."""
    for _ in range(3):
        question = interrogator.get_next_question()
        response = InterrogationResponse(
            question_id=question.question_id,
            answer="Test answer",
            timestamp=datetime.utcnow()
        )
        interrogator.record_response(response)
    
    assert len(interrogator.responses) == 3


def test_get_unanswered_questions(interrogator):
    """Test getting unanswered questions."""
    # Answer first question
    question = interrogator.get_next_question()
    response = InterrogationResponse(
        question_id=question.question_id,
        answer="Test",
        timestamp=datetime.utcnow()
    )
    interrogator.record_response(response)
    
    # Get unanswered
    unanswered = interrogator.get_unanswered_questions()
    
    assert len(unanswered) == len(interrogator.questions) - 1
    assert question.question_id not in [q.question_id for q in unanswered]


def test_is_complete(interrogator):
    """Test completion check."""
    assert not interrogator.is_complete()
    
    # Answer all questions
    for question in interrogator.questions:
        response = InterrogationResponse(
            question_id=question.question_id,
            answer="Test answer",
            timestamp=datetime.utcnow()
        )
        interrogator.record_response(response)
    
    assert interrogator.is_complete()


# ========================================
# Test Profile Building
# ========================================

def test_build_profile_incomplete(interrogator):
    """Test building profile with incomplete responses."""
    # Only answer one question
    question = interrogator.get_next_question()
    response = InterrogationResponse(
        question_id=question.question_id,
        answer="Test",
        timestamp=datetime.utcnow()
    )
    interrogator.record_response(response)
    
    with pytest.raises(ValueError, match="interrogation not complete"):
        interrogator.build_profile()


def test_build_profile_complete(interrogator):
    """Test building complete profile."""
    # Answer all questions
    for question in interrogator.questions:
        response = InterrogationResponse(
            question_id=question.question_id,
            answer="Test answer for " + question.question_id,
            timestamp=datetime.utcnow()
        )
        interrogator.record_response(response)
    
    profile = interrogator.build_profile()
    
    assert isinstance(profile, BrandProfile)
    assert profile.artist_name is not None
    assert len(profile.aesthetic.primary_colors) > 0
    assert len(profile.narrative.core_message) > 0


def test_build_profile_with_real_responses(interrogator, sample_responses):
    """Test building profile with realistic responses."""
    # Map sample responses to questions
    for question in interrogator.questions:
        # Find matching response
        answer = "Generic answer"
        for key, value in sample_responses.items():
            if key in question.question_id:
                answer = value
                break
        
        response = InterrogationResponse(
            question_id=question.question_id,
            answer=answer,
            timestamp=datetime.utcnow()
        )
        interrogator.record_response(response)
    
    profile = interrogator.build_profile()
    
    assert "purple" in profile.aesthetic.primary_colors.lower()
    assert len(profile.narrative.themes) > 0
    assert len(profile.restrictions.forbidden_elements) > 0


# ========================================
# Test Progress Tracking
# ========================================

def test_get_progress(interrogator):
    """Test progress tracking."""
    progress = interrogator.get_progress()
    
    assert progress["total_questions"] == len(interrogator.questions)
    assert progress["answered"] == 0
    assert progress["progress_percent"] == 0.0
    
    # Answer half the questions
    half = len(interrogator.questions) // 2
    for question in interrogator.questions[:half]:
        response = InterrogationResponse(
            question_id=question.question_id,
            answer="Test",
            timestamp=datetime.utcnow()
        )
        interrogator.record_response(response)
    
    progress = interrogator.get_progress()
    assert progress["answered"] == half
    assert 40 <= progress["progress_percent"] <= 60


def test_get_responses_by_category(interrogator):
    """Test getting responses grouped by category."""
    # Answer some questions
    for question in interrogator.questions[:5]:
        response = InterrogationResponse(
            question_id=question.question_id,
            answer="Test",
            timestamp=datetime.utcnow()
        )
        interrogator.record_response(response)
    
    by_category = interrogator.get_responses_by_category()
    
    assert isinstance(by_category, dict)
    assert len(by_category) > 0


# ========================================
# Test Follow-up Questions
# ========================================

def test_generate_followup_aesthetic(interrogator):
    """Test generating follow-up question for aesthetic."""
    initial_answer = "I like purple and dark colors"
    
    followup = interrogator.generate_followup(
        QuestionCategory.AESTHETIC,
        initial_answer
    )
    
    assert followup is not None
    assert "purple" in followup.question_text.lower() or "dark" in followup.question_text.lower()


def test_generate_followup_narrative(interrogator):
    """Test generating follow-up for narrative."""
    initial_answer = "My music is about struggle and perseverance"
    
    followup = interrogator.generate_followup(
        QuestionCategory.NARRATIVE,
        initial_answer
    )
    
    assert followup is not None
    assert len(followup.question_text) > 0


# ========================================
# Test Validation
# ========================================

def test_validate_response_empty(interrogator):
    """Test validation rejects empty responses."""
    question = interrogator.get_next_question()
    
    is_valid, message = interrogator.validate_response(question, "")
    
    assert not is_valid
    assert "empty" in message.lower() or "required" in message.lower()


def test_validate_response_too_short(interrogator):
    """Test validation rejects very short responses."""
    question = interrogator.get_next_question()
    
    is_valid, message = interrogator.validate_response(question, "yes")
    
    assert not is_valid


def test_validate_response_valid(interrogator):
    """Test validation accepts good responses."""
    question = interrogator.get_next_question()
    
    is_valid, message = interrogator.validate_response(
        question,
        "This is a detailed and thoughtful response that provides real information"
    )
    
    assert is_valid


# ========================================
# Test Export/Import
# ========================================

def test_export_responses(interrogator, tmp_path):
    """Test exporting responses to JSON."""
    # Answer some questions
    for question in interrogator.questions[:3]:
        response = InterrogationResponse(
            question_id=question.question_id,
            answer="Test answer",
            timestamp=datetime.utcnow()
        )
        interrogator.record_response(response)
    
    # Export
    export_path = tmp_path / "responses.json"
    interrogator.export_responses(str(export_path))
    
    assert export_path.exists()


def test_import_responses(interrogator, tmp_path):
    """Test importing responses from JSON."""
    # Create and export
    for question in interrogator.questions[:3]:
        response = InterrogationResponse(
            question_id=question.question_id,
            answer="Test answer",
            timestamp=datetime.utcnow()
        )
        interrogator.record_response(response)
    
    export_path = tmp_path / "responses.json"
    interrogator.export_responses(str(export_path))
    
    # Create new interrogator and import
    new_interrogator = BrandInterrogator()
    new_interrogator.import_responses(str(export_path))
    
    assert len(new_interrogator.responses) == 3


# ========================================
# Run tests
# ========================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
