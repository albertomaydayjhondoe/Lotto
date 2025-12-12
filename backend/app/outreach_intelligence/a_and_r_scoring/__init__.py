"""
A&R Scoring subsystem initialization

Exports components for A&R intelligence and scoring.
"""

from .hit_score_alignment import HitScoreAlignment, HitPotential
from .industry_fit_analyzer import IndustryFitAnalyzer
from .opportunity_classifier import OpportunityClassifier, OpportunityTier
from .decision_matrix import DecisionMatrix

__all__ = [
    "HitScoreAlignment",
    "HitPotential",
    "IndustryFitAnalyzer",
    "OpportunityClassifier",
    "OpportunityTier",
    "DecisionMatrix"
]
