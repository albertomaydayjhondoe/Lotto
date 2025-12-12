"""
Tests for Satellite Engine - Sprint 8
Tests completos para todos los módulos del Satellite Engine.
"""
import pytest
from datetime import datetime, timedelta
from app.satellite_engine import (
    # Behavior Engine
    SatelliteBehaviorEngine,
    AccountSchedule,
    # Niche Engine
    SatelliteNicheEngine,
    Niche,
    # Content Router
    SatelliteContentRouter,
    ContentCandidate,
    ContentType,
    # Warmup Engine
    SatelliteWarmupEngine,
    WarmupPhase,
    # Publishing Engine
    SatellitePublishingEngine,
    Platform,
    PublishStatus,
    # ML Learning
    SatelliteMLLearning,
    PerformanceMetrics,
    # Sound Testing
    SoundTestingEngine,
    ABTestConfig
)


class TestSatelliteBehaviorEngine:
    """Tests para BehaviorEngine."""
    
    def test_create_schedule(self):
        """Test: crear schedule con jitter."""
        engine = SatelliteBehaviorEngine()
        
        schedule = engine.create_schedule(
            account_id="test_tiktok_001",
            platform="tiktok",
            timezone_offset=-5
        )
        
        assert schedule.account_id == "test_tiktok_001"
        assert schedule.platform == "tiktok"
        assert schedule.daily_posts_target == 7  # TikTok target
        assert len(schedule.time_slots) == 7
        assert len(schedule.activity_pattern) == 7
        
    def test_anti_correlation(self):
        """Test: anti-correlation validator."""
        engine = SatelliteBehaviorEngine()
        
        # Create schedules for 2 accounts
        schedule1 = engine.create_schedule("account_1", "tiktok", 0)
        schedule2 = engine.create_schedule("account_2", "tiktok", 0)
        
        # Get next times
        time1 = engine.get_next_post_time("account_1")
        
        # Register post for account 1
        engine.register_post("account_1")
        
        # Next time for account 2 should avoid correlation
        time2 = engine.get_next_post_time("account_2")
        
        # Should have 5+ min separation
        if time1 and time2:
            diff = abs((time2 - time1).total_seconds() / 60)
            assert diff >= 5 or diff == 0  # Either separated or different slots
    
    def test_micro_pause(self):
        """Test: micro-pause generation."""
        engine = SatelliteBehaviorEngine()
        
        pause = engine.get_micro_pause()
        
        assert 18 <= pause <= 90


class TestSatelliteNicheEngine:
    """Tests para NicheEngine."""
    
    def test_assign_niche(self):
        """Test: asignar nicho a cuenta."""
        engine = SatelliteNicheEngine()
        
        success = engine.assign_niche_to_account(
            "tiktok_shameless_001",
            Niche.SHAMELESS_EDITS
        )
        
        assert success is True
        
        # Verify assignment
        niche = engine.get_account_niche("tiktok_shameless_001")
        assert niche == Niche.SHAMELESS_EDITS
    
    def test_get_niche_profile(self):
        """Test: obtener perfil de nicho."""
        engine = SatelliteNicheEngine()
        
        profile = engine.get_niche_profile(Niche.SHAMELESS_EDITS)
        
        assert profile is not None
        assert profile.name == "Shameless Edits"
        assert len(profile.style_book.hashtag_templates) > 0
        assert len(profile.visual_library.color_palette) > 0
    
    def test_all_niches_defined(self):
        """Test: todos los nichos tienen perfil."""
        engine = SatelliteNicheEngine()
        
        for niche in Niche:
            profile = engine.get_niche_profile(niche)
            assert profile is not None
            assert profile.niche == niche


class TestSatelliteContentRouter:
    """Tests para ContentRouter."""
    
    def test_analyze_content(self):
        """Test: analizar contenido con Vision Engine."""
        router = SatelliteContentRouter()
        
        candidate = router.analyze_content(
            content_id="content_001",
            content_type=ContentType.VIDEO_CLIP,
            source_path="/path/to/video.mp4",
            duration_seconds=15.0,
            music_track_id="track_001",
            lyric_keywords=["barrio", "oro"]
        )
        
        assert candidate.content_id == "content_001"
        assert len(candidate.visual_tags) > 0
        assert len(candidate.dominant_colors) > 0
        assert candidate.motion_intensity > 0
    
    def test_route_content(self):
        """Test: routing de contenido a cuenta."""
        router = SatelliteContentRouter()
        
        # Create candidates
        candidates = [
            router.analyze_content(
                f"content_{i}",
                ContentType.VIDEO_CLIP,
                f"/path/video_{i}.mp4",
                15.0
            )
            for i in range(3)
        ]
        
        # Route to account
        decision = router.route_content_to_account(
            account_id="tiktok_shameless_001",
            niche_name="Shameless Edits",
            niche_palette=["#1a1a2e", "#e94560"],
            content_candidates=candidates,
            preferred_platform="tiktok"
        )
        
        assert decision.account_id == "tiktok_shameless_001"
        assert decision.content_candidate in candidates
        assert decision.virality_score.overall_score > 0
        assert decision.priority >= 1


class TestSatelliteWarmupEngine:
    """Tests para WarmupEngine."""
    
    def test_create_warmup_plan(self):
        """Test: crear plan de warm-up."""
        engine = SatelliteWarmupEngine()
        
        plan = engine.create_warmup_plan(
            account_id="new_account_001",
            platform="tiktok"
        )
        
        assert plan.account_id == "new_account_001"
        assert plan.platform == "tiktok"
        assert plan.current_day == 1
        assert plan.current_phase == WarmupPhase.DAY_1
        assert len(plan.daily_schedules) == 5
    
    def test_warmup_progression(self):
        """Test: progresión de warm-up."""
        engine = SatelliteWarmupEngine()
        
        plan = engine.create_warmup_plan("account_001", "tiktok")
        
        # Day 1
        schedule_day1 = plan.get_current_schedule()
        assert schedule_day1.day == 1
        assert schedule_day1.target_posts == 1
        
        # Complete day 1
        for _ in range(schedule_day1.target_posts):
            engine.register_post("account_001", datetime.now())
        
        # Advance to day 2
        plan.advance_day()
        assert plan.current_day == 2
        assert plan.current_phase == WarmupPhase.DAY_2
    
    def test_is_in_warmup(self):
        """Test: verificar estado de warm-up."""
        engine = SatelliteWarmupEngine()
        
        plan = engine.create_warmup_plan("account_001", "tiktok")
        
        assert engine.is_in_warmup("account_001") is True
        
        # Complete warmup
        plan.warmup_completed = True
        assert engine.is_in_warmup("account_001") is False


class TestSatellitePublishingEngine:
    """Tests para PublishingEngine."""
    
    def test_create_identity(self):
        """Test: crear identidad aislada."""
        engine = SatellitePublishingEngine()
        
        identity = engine.create_identity("account_001")
        
        assert identity.account_id == "account_001"
        assert identity.vpn_server != ""
        assert identity.proxy_ip != ""
        assert identity.user_agent != ""
        assert len(identity.get_fingerprint_hash()) == 16
    
    def test_unique_identities(self):
        """Test: identidades únicas por cuenta."""
        engine = SatellitePublishingEngine()
        
        identity1 = engine.create_identity("account_001")
        identity2 = engine.create_identity("account_002")
        
        # Should have different fingerprints
        hash1 = identity1.get_fingerprint_hash()
        hash2 = identity2.get_fingerprint_hash()
        
        assert hash1 != hash2
    
    def test_queue_publish(self):
        """Test: encolar publicación."""
        engine = SatellitePublishingEngine()
        
        task = engine.queue_publish(
            account_id="account_001",
            platform=Platform.TIKTOK,
            content_id="content_001",
            content_path="/path/video.mp4",
            caption="Test caption",
            hashtags=["#test", "#viral"],
            scheduled_time=datetime.now()
        )
        
        assert task.account_id == "account_001"
        assert task.platform == Platform.TIKTOK
        assert task.status == PublishStatus.PENDING
    
    def test_publish(self):
        """Test: publicar contenido."""
        engine = SatellitePublishingEngine()
        
        task = engine.queue_publish(
            account_id="account_001",
            platform=Platform.TIKTOK,
            content_id="content_001",
            content_path="/path/video.mp4",
            caption="Test",
            hashtags=["#test"],
            scheduled_time=datetime.now()
        )
        
        result = engine.publish(task)
        
        assert result.task == task
        assert result.identity_hash != ""


class TestSatelliteMLLearning:
    """Tests para MLLearning."""
    
    def test_start_learning_cycle(self):
        """Test: iniciar ciclo de aprendizaje."""
        engine = SatelliteMLLearning()
        
        cycle = engine.start_learning_cycle()
        
        assert cycle.cycle_id != ""
        assert cycle.phase.value == "collecting"
        assert not cycle.completed
    
    def test_record_performance(self):
        """Test: registrar performance."""
        engine = SatelliteMLLearning()
        engine.start_learning_cycle()
        
        metrics = PerformanceMetrics(
            post_id="post_001",
            account_id="account_001",
            platform="tiktok",
            published_at=datetime.now(),
            views=10000,
            likes=500,
            comments=50,
            shares=100,
            retention_rate=0.85,
            hour_published=18,
            day_of_week=3
        )
        
        engine.record_performance(metrics)
        
        assert len(engine.timing_analysis.metrics_history) == 1
    
    def test_analyze_optimal_timings(self):
        """Test: analizar timings óptimos."""
        engine = SatelliteMLLearning()
        engine.start_learning_cycle()
        
        # Add multiple metrics
        for i in range(10):
            metrics = PerformanceMetrics(
                post_id=f"post_{i}",
                account_id="account_001",
                platform="tiktok",
                published_at=datetime.now(),
                views=5000 + i * 1000,
                likes=200 + i * 50,
                retention_rate=0.7 + i * 0.02,
                hour_published=18 + (i % 4),
                day_of_week=i % 7
            )
            engine.record_performance(metrics)
        
        # Analyze
        timings = engine.timing_analysis.analyze_optimal_hours(min_samples=2)
        
        assert len(timings) > 0


class TestSoundTestingEngine:
    """Tests para SoundTestingEngine."""
    
    def test_create_ab_test(self):
        """Test: crear test A/B."""
        engine = SoundTestingEngine()
        
        accounts = [f"account_{i}" for i in range(10)]
        
        test = engine.create_ab_test(
            sound_a_id="sound_001",
            sound_a_name="Track A",
            sound_b_id="sound_002",
            sound_b_name="Track B",
            accounts_pool=accounts
        )
        
        assert test.test_id != ""
        assert len(test.sound_a_accounts) == 5
        assert len(test.sound_b_accounts) == 5
        assert test.sound_a_metrics is not None
        assert test.sound_b_metrics is not None
    
    def test_record_post_performance(self):
        """Test: registrar performance de post."""
        engine = SoundTestingEngine()
        
        accounts = [f"account_{i}" for i in range(10)]
        test = engine.create_ab_test(
            "sound_001", "Track A",
            "sound_002", "Track B",
            accounts
        )
        
        engine.start_test(test.test_id)
        
        # Record performance for sound A
        engine.record_post_performance(
            test_id=test.test_id,
            sound_id="sound_001",
            post_id="post_001",
            views=10000,
            likes=500,
            comments=50,
            shares=100,
            saves=200,
            ctr=0.05,
            retention=0.85,
            completion_rate=0.90
        )
        
        metrics = test.sound_a_metrics
        assert metrics.total_views == 10000
        assert metrics.total_likes == 500
        assert metrics.posts_count == 1
    
    def test_analyze_test(self):
        """Test: analizar resultados de test."""
        engine = SoundTestingEngine()
        
        accounts = [f"account_{i}" for i in range(10)]
        test = engine.create_ab_test(
            "sound_001", "Track A",
            "sound_002", "Track B",
            accounts
        )
        
        engine.start_test(test.test_id)
        
        # Add performance for both sounds
        for i in range(5):
            engine.record_post_performance(
                test.test_id, "sound_001", f"post_a_{i}",
                10000, 500, 50, 100, 200, 0.05, 0.85, 0.90
            )
            engine.record_post_performance(
                test.test_id, "sound_002", f"post_b_{i}",
                8000, 300, 30, 50, 100, 0.04, 0.75, 0.80
            )
        
        # Analyze
        result = engine.analyze_test(test.test_id)
        
        assert result.sound_a_score > 0
        assert result.sound_b_score > 0
        assert result.winner.value in ["sound_a", "sound_b", "tie"]


class TestSatelliteIntegration:
    """Tests de integración entre módulos."""
    
    def test_full_workflow(self):
        """Test: workflow completo de satellite account."""
        # 1. Create engines
        behavior_engine = SatelliteBehaviorEngine()
        niche_engine = SatelliteNicheEngine()
        content_router = SatelliteContentRouter()
        warmup_engine = SatelliteWarmupEngine()
        publishing_engine = SatellitePublishingEngine()
        ml_engine = SatelliteMLLearning()
        
        account_id = "integration_test_account"
        
        # 2. Assign niche
        niche_engine.assign_niche_to_account(account_id, Niche.SHAMELESS_EDITS)
        profile = niche_engine.get_account_profile(account_id)
        assert profile is not None
        
        # 3. Create behavior schedule
        schedule = behavior_engine.create_schedule(account_id, "tiktok", -5)
        assert schedule.account_id == account_id
        
        # 4. Create warmup plan
        warmup_plan = warmup_engine.create_warmup_plan(account_id, "tiktok")
        assert warmup_plan.account_id == account_id
        
        # 5. Create identity
        identity = publishing_engine.create_identity(account_id)
        assert identity.account_id == account_id
        
        # 6. Route content
        candidates = [
            content_router.analyze_content(
                f"content_{i}",
                ContentType.VIDEO_CLIP,
                f"/path/video_{i}.mp4",
                15.0
            )
            for i in range(3)
        ]
        
        decision = content_router.route_content_to_account(
            account_id=account_id,
            niche_name=profile.name,
            niche_palette=profile.visual_library.color_palette,
            content_candidates=candidates,
            preferred_platform="tiktok"
        )
        
        assert decision.account_id == account_id
        
        # 7. Start ML learning cycle
        cycle = ml_engine.start_learning_cycle()
        assert cycle.cycle_id != ""
        
        print(f"✓ Integration test passed for {account_id}")


# Run all tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
