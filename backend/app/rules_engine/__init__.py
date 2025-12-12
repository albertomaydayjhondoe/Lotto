"""
Rule Engine 2.0 - Dynamic and Adaptive Scoring System

This module provides a comprehensive rule-based system for:
- Scoring clips based on multiple features
- Selecting the best variant for each platform
- Adapting weights based on real-world performance data from the ledger
- Identifying what works and what doesn't
- Automatically improving rules over time

Architecture:
- models.py: Data models for rules and weights
- engine.py: Main RuleEngine interface (public API)
- evaluator.py: Evaluates clips and produces scores
- trainer.py: Learns weights from ledger events
- heuristics.py: Platform-specific hard rules
- loader.py: Loads current rules from database
- persistence.py: Saves adapted rules to database
"""

from app.rules_engine.engine import RuleEngine
from app.rules_engine.models import RuleWeight, AdaptiveRuleSet

__all__ = ["RuleEngine", "RuleWeight", "AdaptiveRuleSet"]
