#!/usr/bin/env python3
"""
Verify Community Manager AI module imports.
Quick smoke test before running full test suite.
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def test_imports():
    """Test all critical imports."""
    print("🔍 Testing Community Manager AI imports...\n")
    
    errors = []
    
    # Test models
    try:
        from app.community_ai.models import (
            ContentType, Platform, ChannelType, SentimentType,
            DailyPlan, CreativeRecommendation, TrendItem,
            SentimentResult, DailyReport
        )
        print("✅ Models import successful")
    except Exception as e:
        errors.append(f"❌ Models import failed: {e}")
        print(errors[-1])
    
    # Test planner
    try:
        from app.community_ai.planner import DailyPlanner
        print("✅ Planner import successful")
    except Exception as e:
        errors.append(f"❌ Planner import failed: {e}")
        print(errors[-1])
    
    # Test recommender
    try:
        from app.community_ai.content_recommender import ContentRecommender
        print("✅ ContentRecommender import successful")
    except Exception as e:
        errors.append(f"❌ ContentRecommender import failed: {e}")
        print(errors[-1])
    
    # Test trend miner
    try:
        from app.community_ai.trend_miner import TrendMiner
        print("✅ TrendMiner import successful")
    except Exception as e:
        errors.append(f"❌ TrendMiner import failed: {e}")
        print(errors[-1])
    
    # Test sentiment analyzer
    try:
        from app.community_ai.sentiment_analyzer import SentimentAnalyzer
        print("✅ SentimentAnalyzer import successful")
    except Exception as e:
        errors.append(f"❌ SentimentAnalyzer import failed: {e}")
        print(errors[-1])
    
    # Test daily reporter
    try:
        from app.community_ai.daily_reporter import DailyReporter
        print("✅ DailyReporter import successful")
    except Exception as e:
        errors.append(f"❌ DailyReporter import failed: {e}")
        print(errors[-1])
    
    # Test utils
    try:
        from app.community_ai.utils import (
            load_brand_rules,
            calculate_confidence_score,
            validate_brand_compliance
        )
        print("✅ Utils import successful")
    except Exception as e:
        errors.append(f"❌ Utils import failed: {e}")
        print(errors[-1])
    
    # Summary
    print(f"\n{'='*50}")
    if errors:
        print(f"❌ {len(errors)} import errors found:")
        for err in errors:
            print(f"  {err}")
        return False
    else:
        print("✅ All imports successful!")
        print("\n📦 Community Manager AI module ready for testing")
        return True

if __name__ == "__main__":
    success = test_imports()
    sys.exit(0 if success else 1)
