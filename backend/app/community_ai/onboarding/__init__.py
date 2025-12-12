"""
Artist Onboarding System

This module provides automated artist interrogation and configuration generation.

Main Components:
- BrandGenerator: Transform answers → brand_static_rules.json
- SatelliteGenerator: Transform answers → satellite_rules.json
- StrategyGenerator: Transform answers → content_strategy.json
- OnboardingOrchestrator: Master script to run all generators

Usage:
    from backend.app.community_ai.onboarding import OnboardingOrchestrator
    
    orchestrator = OnboardingOrchestrator(
        answers_path="onboarding_answers.json",
        output_dir="../brand/"
    )
    orchestrator.run()
"""

from .brand_generator import BrandGenerator, generate_brand_rules
from .satellite_generator import SatelliteGenerator, generate_satellite_rules
from .strategy_generator import StrategyGenerator, generate_content_strategy
from .onboarding_orchestrator import OnboardingOrchestrator

__all__ = [
    'BrandGenerator',
    'SatelliteGenerator',
    'StrategyGenerator',
    'OnboardingOrchestrator',
    'generate_brand_rules',
    'generate_satellite_rules',
    'generate_content_strategy',
]

__version__ = '1.0.0'
