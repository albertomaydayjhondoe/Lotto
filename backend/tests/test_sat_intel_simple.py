"""
SPRINT 11 - Satellite Intelligence Optimization
Simple Tests

Tests básicos para verificar que todos los módulos se importan
y funcionan correctamente.
"""

import sys
import os
from datetime import datetime

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


def test_imports():
    """Test 1: Verificar que todos los imports funcionan"""
    print("TEST 1: Checking imports...")
    print("-" * 80)
    
    try:
        # Contracts
        from app.sat_intelligence import (
            ProposalStatus,
            ProposalPriority,
            ContentType,
            RiskLevel,
            ContentMetadata,
            ClipScore,
            ContentVariant,
            TimingWindow,
            ContentProposal,
            AccountProfile,
        )
        print("✅ Contracts imported successfully")
        
        # Core modules
        from app.sat_intelligence import (
            IdentityAwareClipScorer,
            TimingOptimizer,
            UniverseProfileManager,
            SoundTestRecommender,
            VariantGeneratorBridge,
            ProposalEvaluator,
        )
        print("✅ Core modules imported successfully")
        
        # Main API
        from app.sat_intelligence import (
            SatelliteIntelligenceAPI,
            SatIntelConfig,
        )
        print("✅ Main API imported successfully")
        
        print()
        return True
        
    except Exception as e:
        print(f"❌ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_instantiation():
    """Test 2: Verificar que se pueden instanciar los módulos"""
    print("TEST 2: Checking instantiation...")
    print("-" * 80)
    
    try:
        from app.sat_intelligence import (
            IdentityAwareClipScorer,
            TimingOptimizer,
            UniverseProfileManager,
            SoundTestRecommender,
            VariantGeneratorBridge,
            ProposalEvaluator,
            SatelliteIntelligenceAPI,
        )
        
        # Instantiate all modules
        scorer = IdentityAwareClipScorer()
        print(f"✅ IdentityAwareClipScorer: {scorer}")
        
        optimizer = TimingOptimizer()
        print(f"✅ TimingOptimizer: {optimizer}")
        
        manager = UniverseProfileManager()
        print(f"✅ UniverseProfileManager: {manager}")
        
        recommender = SoundTestRecommender()
        print(f"✅ SoundTestRecommender: {recommender}")
        
        generator = VariantGeneratorBridge()
        print(f"✅ VariantGeneratorBridge: {generator}")
        
        evaluator = ProposalEvaluator()
        print(f"✅ ProposalEvaluator: {evaluator}")
        
        api = SatelliteIntelligenceAPI()
        print(f"✅ SatelliteIntelligenceAPI: {api}")
        
        print()
        return True
        
    except Exception as e:
        print(f"❌ Instantiation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_profile_management():
    """Test 3: Verificar Profile Manager"""
    print("TEST 3: Testing Profile Manager...")
    print("-" * 80)
    
    try:
        from app.sat_intelligence import UniverseProfileManager
        
        manager = UniverseProfileManager()
        
        # Create profile
        profile = manager.create_profile(
            account_id="test_acc_001",
            niche_id="music",
            niche_name="Music Test",
            start_warmup=True
        )
        
        print(f"✅ Created profile: {profile.account_id}")
        print(f"   Niche: {profile.niche_id}")
        print(f"   Warmup day: {profile.warmup_day}")
        print(f"   Active: {profile.is_active}")
        
        # Get profile
        retrieved = manager.get_profile("test_acc_001")
        assert retrieved is not None
        assert retrieved.account_id == "test_acc_001"
        print(f"✅ Retrieved profile successfully")
        
        # Update profile
        updated = manager.update_profile("test_acc_001", total_posts=10)
        assert updated.total_posts == 10
        print(f"✅ Updated profile successfully")
        
        # Stats
        stats = manager.get_universe_stats()
        print(f"✅ Universe stats: {stats['total_accounts']} accounts")
        
        print()
        return True
        
    except Exception as e:
        print(f"❌ Profile management test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_clip_scoring():
    """Test 4: Verificar Clip Scoring"""
    print("TEST 4: Testing Clip Scoring...")
    print("-" * 80)
    
    try:
        from app.sat_intelligence import (
            IdentityAwareClipScorer,
            ContentMetadata,
            ContentType,
            AccountProfile,
        )
        
        scorer = IdentityAwareClipScorer()
        
        # Mock content
        content = ContentMetadata(
            content_id="clip_test_001",
            content_type=ContentType.VIDEO_CLIP,
            duration_seconds=12.0,
            visual_tags=["music", "performance"],
            energy=0.8,
            valence=0.7,
        )
        
        # Mock account
        account = AccountProfile(
            account_id="acc_test_001",
            niche_id="music",
            niche_name="Music",
            is_active=True,
            total_posts=50,
            optimal_hours=[10, 14, 18],
        )
        
        # Score
        score = scorer.score_clip(content, account)
        
        print(f"✅ Scored clip: {score.content_id}")
        print(f"   Total score: {score.total_score:.2f}")
        print(f"   Niche match: {score.niche_match_score:.2f}")
        print(f"   Virality: {score.virality_score:.2f}")
        print(f"   Timing: {score.timing_score:.2f}")
        print(f"   Uniqueness: {score.uniqueness_score:.2f}")
        print(f"   Reasoning: {score.reasoning}")
        
        assert 0.0 <= score.total_score <= 1.0
        print(f"✅ Score in valid range")
        
        print()
        return True
        
    except Exception as e:
        print(f"❌ Clip scoring test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_timing_optimizer():
    """Test 5: Verificar Timing Optimizer"""
    print("TEST 5: Testing Timing Optimizer...")
    print("-" * 80)
    
    try:
        from app.sat_intelligence import (
            TimingOptimizer,
            AccountProfile,
        )
        
        optimizer = TimingOptimizer()
        
        # Mock account
        account = AccountProfile(
            account_id="acc_test_002",
            niche_id="music",
            niche_name="Music",
            is_active=True,
            optimal_hours=[10, 14, 18, 21],
            optimal_days=[0, 1, 2, 3, 4],
        )
        
        # Find optimal window
        window = optimizer.find_optimal_window(
            account=account,
            target_time=datetime.now(),
            duration_hours=24
        )
        
        print(f"✅ Generated timing window:")
        print(f"   Start time: {window.start_time.strftime('%Y-%m-%d %H:%M')}")
        print(f"   Optimal score: {window.optimal_score:.2f}")
        print(f"   Jitter: {window.jitter_minutes:+.1f} min")
        print(f"   Reasoning: {window.reasoning}")
        
        assert 0.0 <= window.optimal_score <= 1.0
        print(f"✅ Window score in valid range")
        
        print()
        return True
        
    except Exception as e:
        print(f"❌ Timing optimizer test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_variant_generation():
    """Test 6: Verificar Variant Generation"""
    print("TEST 6: Testing Variant Generation...")
    print("-" * 80)
    
    try:
        from app.sat_intelligence import (
            VariantGeneratorBridge,
            AccountProfile,
        )
        
        generator = VariantGeneratorBridge()
        
        # Mock account
        account = AccountProfile(
            account_id="acc_test_003",
            niche_id="music",
            niche_name="Music",
            is_active=True,
        )
        
        # Generate variant
        variant = generator.generate_variant(
            content_id="clip_test_002",
            account=account,
            audio_track_id="audio_test_001"
        )
        
        print(f"✅ Generated variant: {variant.variant_id}")
        print(f"   Caption: {variant.caption}")
        print(f"   Hashtags: {', '.join(variant.hashtags)}")
        print(f"   Thumbnail: {variant.thumbnail_index}")
        print(f"   Audio offset: {variant.audio_start_offset:.2f}s")
        
        assert len(variant.caption) > 0
        assert len(variant.hashtags) >= 3
        print(f"✅ Variant has valid content")
        
        print()
        return True
        
    except Exception as e:
        print(f"❌ Variant generation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_main_api():
    """Test 7: Verificar Main API"""
    print("TEST 7: Testing Main API (basic)...")
    print("-" * 80)
    
    try:
        from app.sat_intelligence import (
            SatelliteIntelligenceAPI,
            SatIntelConfig,
        )
        
        # Initialize API
        config = SatIntelConfig(
            max_proposals_per_batch=20,
            simulate_only=True
        )
        
        api = SatelliteIntelligenceAPI(config)
        
        print(f"✅ API initialized")
        print(f"   Config: {config}")
        print(f"   Scorer: {api.clip_scorer}")
        print(f"   Optimizer: {api.timing_optimizer}")
        print(f"   Manager: {api.profile_manager}")
        print(f"   Generator: {api.variant_generator}")
        print(f"   Evaluator: {api.proposal_evaluator}")
        
        # Create a test profile
        api.profile_manager.create_profile(
            account_id="api_test_acc_001",
            niche_id="music",
            niche_name="Music API Test",
            start_warmup=False
        )
        
        print(f"✅ Created test profile")
        
        print()
        return True
        
    except Exception as e:
        print(f"❌ Main API test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("=" * 80)
    print("SPRINT 11 - SATELLITE INTELLIGENCE OPTIMIZATION")
    print("Simple Tests")
    print("=" * 80)
    print()
    
    tests = [
        test_imports,
        test_instantiation,
        test_profile_management,
        test_clip_scoring,
        test_timing_optimizer,
        test_variant_generation,
        test_main_api,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            result = test()
            if result:
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Test crashed: {e}")
            failed += 1
    
    print("=" * 80)
    print(f"RESULTS: {passed}/{len(tests)} tests passed")
    if failed > 0:
        print(f"❌ {failed} tests failed")
    else:
        print("✅ ALL TESTS PASSED")
    print("=" * 80)
    
    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
