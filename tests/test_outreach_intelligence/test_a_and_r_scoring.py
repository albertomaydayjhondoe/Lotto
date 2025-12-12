"""
Tests for A&R Scoring subsystem
"""

import pytest
from backend.app.outreach_intelligence.a_and_r_scoring import (
    HitScoreAlignment,
    HitPotential,
    IndustryFitAnalyzer,
    OpportunityClassifier,
    DecisionMatrix
)


def test_hit_score_calculation(sample_track_metadata):
    """Test hit score calculation"""
    alignment = HitScoreAlignment()
    
    hit_score = alignment.calculate_hit_score(sample_track_metadata)
    
    assert "overall_hit_score" in hit_score
    assert 0 <= hit_score["overall_hit_score"] <= 100
    assert "hit_potential" in hit_score
    assert "breakdown" in hit_score
    assert "recommended_strategy" in hit_score


def test_hit_potential_classification(sample_track_metadata):
    """Test hit potential classification"""
    alignment = HitScoreAlignment()
    
    hit_score = alignment.calculate_hit_score(sample_track_metadata)
    potential = HitPotential(hit_score["hit_potential"])
    
    assert potential in [
        HitPotential.COMMERCIAL_HIT,
        HitPotential.STRONG_POTENTIAL,
        HitPotential.MODERATE_POTENTIAL,
        HitPotential.NICHE_APPEAL,
        HitPotential.UNDERGROUND_ONLY
    ]


def test_industry_fit_analysis(sample_track_metadata):
    """Test market fit analysis"""