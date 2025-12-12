"""
Sprint 16: Influencer Trend Engine - Comprehensive Tests

Tests:
1. Scraper functionality (multi-platform, caching, rate limiting)
2. Analysis scoring correctness
3. Trend synthesis reproducibility
4. Selector optimization under constraints
5. Campaign planning completeness
6. Orchestration bridge integration
7. Sprint 14 integration (risk simulation)
8. Sprint 15 integration (policy checking)

Target: ≥80% coverage

Author: STAKAZO Project
Date: 2025-12-12
"""

import pytest
from datetime import datetime, timedelta
from pathlib import Path
import tempfile
import shutil

from app.influencer_trend_engine import (
    # Scraper
    InfluencerScraper,
    Platform,
    PostingFrequency,
    
    # Analyzer
    InfluencerAnalyzer,
    
    # Trend Synthesis
    TrendSynthesisEngine,
    TrendVariantType,
    
    # Selector
    InfluencerSelector,
    
    # Campaign Planner
    InfluencerCampaignPlanner,
    PublicationPhase,
    
    # Orchestration Bridge
    OrchestrationBridgeTrends,
    CampaignStatus
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def temp_cache_dir():
    """Temporary cache directory"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def scraper(temp_cache_dir):
    """Influencer scraper with temp cache"""
    return InfluencerScraper(cache_dir=temp_cache_dir, cache_ttl_hours=24)


@pytest.fixture
def analyzer():
    """Influencer analyzer"""
    return InfluencerAnalyzer()


@pytest.fixture
def selector():
    """Influencer selector"""
    return InfluencerSelector(
        risk_threshold=0.45,
        diversity_threshold=0.6
    )


@pytest.fixture
def trend_engine():
    """Trend synthesis engine"""
    return TrendSynthesisEngine()


@pytest.fixture
def planner():
    """Campaign planner"""
    return InfluencerCampaignPlanner()


@pytest.fixture
def bridge():
    """Orchestration bridge"""
    return OrchestrationBridgeTrends()


@pytest.fixture
def sample_profiles(scraper, analyzer):
    """Sample analyzed profiles"""
    urls = [
        "https://www.tiktok.com/@creator1",
        "https://www.tiktok.com/@creator2",
        "https://www.instagram.com/@creator3",
        "https://www.instagram.com/@creator4",
        "https://www.youtube.com/@creator5",
        "https://www.tiktok.com/@creator6",
        "https://www.tiktok.com/@creator7",
        "https://www.instagram.com/@creator8"
    ]
    
    raw_data = scraper.scrape_multiple(urls)
    return analyzer.analyze_batch(raw_data)


# ============================================================================
# SCRAPER TESTS
# ============================================================================

class TestInfluencerScraper:
    """Test influencer scraper functionality"""
    
    def test_scraper_tiktok(self, scraper):
        """Test TikTok profile scraping"""
        url = "https://www.tiktok.com/@test_creator"
        data = scraper.scrape_influencer(url)
        
        assert data is not None
        assert data.platform == Platform.TIKTOK
        assert data.username == "test_creator"
        assert data.metrics.followers > 0
        assert data.metrics.engagement_rate > 0
        assert len(data.narrative_topics) > 0
    
    def test_scraper_instagram(self, scraper):
        """Test Instagram profile scraping"""
        url = "https://www.instagram.com/test_creator"
        data = scraper.scrape_influencer(url)
        
        assert data is not None
        assert data.platform == Platform.INSTAGRAM
        assert data.metrics.avg_likes > 0
    
    def test_scraper_youtube(self, scraper):
        """Test YouTube channel scraping"""
        url = "https://www.youtube.com/@test_channel"
        data = scraper.scrape_influencer(url)
        
        assert data is not None
        assert data.platform == Platform.YOUTUBE
        assert data.metrics.avg_views > 0
    
    def test_scraper_caching(self, scraper):
        """Test caching avoids repeated scraping"""
        url = "https://www.tiktok.com/@cached_creator"
        
        # First scrape
        data1 = scraper.scrape_influencer(url)
        scrape_time1 = data1.scraped_at
        
        # Second scrape (should use cache)
        data2 = scraper.scrape_influencer(url)
        scrape_time2 = data2.scraped_at
        
        # Same scrape time = cache hit
        assert scrape_time1 == scrape_time2
    
    def test_scraper_force_refresh(self, scraper):
        """Test force refresh bypasses cache"""
        url = "https://www.tiktok.com/@refresh_test"
        
        # First scrape
        data1 = scraper.scrape_influencer(url)
        
        # Force refresh
        data2 = scraper.scrape_influencer(url, force_refresh=True)
        
        # Different scrape times
        assert data1.scraped_at != data2.scraped_at
    
    def test_scraper_multiple(self, scraper):
        """Test batch scraping"""
        urls = [
            "https://www.tiktok.com/@creator1",
            "https://www.instagram.com/@creator2",
            "https://www.youtube.com/@creator3"
        ]
        
        results = scraper.scrape_multiple(urls)
        
        assert len(results) == 3
        assert results[0].platform == Platform.TIKTOK
        assert results[1].platform == Platform.INSTAGRAM
        assert results[2].platform == Platform.YOUTUBE
    
    def test_scraper_unknown_platform(self, scraper):
        """Test unknown platform returns None"""
        url = "https://unknown-platform.com/@creator"
        data = scraper.scrape_influencer(url)
        
        assert data is None


# ============================================================================
# ANALYZER TESTS
# ============================================================================

class TestInfluencerAnalyzer:
    """Test influencer analysis and scoring"""
    
    def test_analyzer_basic(self, scraper, analyzer):
        """Test basic analysis"""
        url = "https://www.tiktok.com/@test_analyzer"
        raw_data = scraper.scrape_influencer(url)
        profile = analyzer.analyze(raw_data)
        
        assert profile is not None
        assert 0 <= profile.scores.impact_score <= 1
        assert 0 <= profile.scores.credibility_score <= 1
        assert 0 <= profile.scores.cultural_fit <= 1
        assert 0 <= profile.scores.trend_reactivity <= 1
        assert 0 <= profile.scores.risk_score <= 1
        assert 0 <= profile.scores.price_efficiency <= 1
    
    def test_analyzer_composite_score(self, scraper, analyzer):
        """Test composite score calculation"""
        url = "https://www.tiktok.com/@composite_test"
        raw_data = scraper.scrape_influencer(url)
        profile = analyzer.analyze(raw_data)
        
        composite = profile.scores.composite_score()
        assert 0 <= composite <= 1
    
    def test_analyzer_strengths_weaknesses(self, scraper, analyzer):
        """Test strengths/weaknesses identification"""
        url = "https://www.tiktok.com/@strengths_test"
        raw_data = scraper.scrape_influencer(url)
        profile = analyzer.analyze(raw_data)
        
        assert len(profile.strengths) >= 0
        assert len(profile.weaknesses) >= 0
        assert isinstance(profile.recommended_use_case, str)
    
    def test_analyzer_batch(self, scraper, analyzer):
        """Test batch analysis"""
        urls = [
            "https://www.tiktok.com/@batch1",
            "https://www.tiktok.com/@batch2"
        ]
        
        raw_data = scraper.scrape_multiple(urls)
        profiles = analyzer.analyze_batch(raw_data)
        
        assert len(profiles) == 2
        assert all(p.scores is not None for p in profiles)


# ============================================================================
# TREND SYNTHESIS TESTS
# ============================================================================

class TestTrendSynthesisEngine:
    """Test trend synthesis"""
    
    def test_trend_synthesis_basic(self, trend_engine):
        """Test basic trend generation"""
        blueprint, variants = trend_engine.synthesize_trend(
            song_name="Test Song",
            song_tempo=120,
            song_mood="energetic",
            visual_aesthetic="urban"
        )
        
        assert blueprint is not None
        assert blueprint.song_name == "Test Song"
        assert len(blueprint.hashtags) > 0
        assert 0 <= blueprint.virality_potential <= 1
        assert 0 <= blueprint.risk_score <= 1
        
        assert len(variants) >= 3  # At least influencer, satellite, organic
    
    def test_trend_variants(self, trend_engine):
        """Test trend variant generation"""
        _, variants = trend_engine.synthesize_trend(
            song_name="Variant Test",
            song_tempo=128,
            song_mood="party",
            visual_aesthetic="raw"
        )
        
        # Check variant types
        variant_types = set(v.variant_type for v in variants)
        assert TrendVariantType.INFLUENCER in variant_types
        assert TrendVariantType.SATELLITE in variant_types
        assert TrendVariantType.ORGANIC in variant_types
    
    def test_trend_reproducibility(self, trend_engine):
        """Test trend synthesis is deterministic (given same inputs)"""
        params = {
            "song_name": "Reproducible Song",
            "song_tempo": 130,
            "song_mood": "romantic",
            "visual_aesthetic": "cinematic"
        }
        
        blueprint1, _ = trend_engine.synthesize_trend(**params)
        blueprint2, _ = trend_engine.synthesize_trend(**params)
        
        # Core attributes should match
        assert blueprint1.core_movement == blueprint2.core_movement
        assert blueprint1.visual_style == blueprint2.visual_style
        assert blueprint1.cut_rhythm == blueprint2.cut_rhythm


# ============================================================================
# SELECTOR TESTS
# ============================================================================

class TestInfluencerSelector:
    """Test influencer selection optimization"""
    
    def test_selector_basic(self, sample_profiles, selector):
        """Test basic pack selection"""
        pack = selector.select_optimal_pack(
            candidates=sample_profiles,
            budget_usd=5000.0
        )
        
        assert pack is not None
        assert pack.total_creators >= 5
        assert pack.total_budget_usd <= 5000.0
        assert 0 <= pack.diversity_score <= 1
        assert pack.max_risk_score < selector.risk_threshold
    
    def test_selector_budget_constraint(self, sample_profiles, selector):
        """Test budget constraint is respected"""
        budget = 2000.0
        pack = selector.select_optimal_pack(
            candidates=sample_profiles,
            budget_usd=budget
        )
        
        if pack:
            assert pack.total_budget_usd <= budget
    
    def test_selector_risk_filtering(self, sample_profiles, selector):
        """Test high-risk creators are filtered"""
        pack = selector.select_optimal_pack(
            candidates=sample_profiles,
            budget_usd=5000.0
        )
        
        if pack:
            # All selected creators below risk threshold
            for creator in pack.all_creators:
                assert creator.profile.scores.risk_score < selector.risk_threshold
    
    def test_selector_diversity(self, sample_profiles, selector):
        """Test diversity is enforced"""
        pack = selector.select_optimal_pack(
            candidates=sample_profiles,
            budget_usd=5000.0
        )
        
        if pack:
            assert pack.diversity_score >= selector.diversity_threshold
    
    def test_selector_simulation(self, sample_profiles, selector):
        """Test campaign outcome simulation"""
        pack = selector.select_optimal_pack(
            candidates=sample_profiles,
            budget_usd=5000.0
        )
        
        if pack:
            outcomes = selector.simulate_campaign_outcomes(
                pack=pack,
                virality_factor=1.5
            )
            
            assert outcomes['total_impressions'] > 0
            assert outcomes['total_engagement'] > 0
            assert outcomes['roi'] >= 0


# ============================================================================
# CAMPAIGN PLANNER TESTS
# ============================================================================

class TestInfluencerCampaignPlanner:
    """Test campaign planning"""
    
    def test_planner_basic(self, sample_profiles, selector, trend_engine, planner):
        """Test basic campaign planning"""
        pack = selector.select_optimal_pack(sample_profiles, budget_usd=5000.0)
        blueprint, variants = trend_engine.synthesize_trend(
            song_name="Plan Test",
            song_tempo=120,
            song_mood="energetic",
            visual_aesthetic="urban"
        )
        
        if pack:
            campaign = planner.plan_campaign(
                campaign_name="Test Campaign",
                pack=pack,
                blueprint=blueprint,
                variants=variants
            )
            
            assert campaign is not None
            assert campaign.campaign_name == "Test Campaign"
            assert len(campaign.timeline.schedules) > 0
            assert campaign.expected_outcomes.cumulative_impressions > 0
    
    def test_planner_timeline(self, sample_profiles, selector, trend_engine, planner):
        """Test timeline generation"""
        pack = selector.select_optimal_pack(sample_profiles, budget_usd=5000.0)
        blueprint, variants = trend_engine.synthesize_trend(
            song_name="Timeline Test",
            song_tempo=128,
            song_mood="party",
            visual_aesthetic="raw"
        )
        
        if pack:
            campaign = planner.plan_campaign(
                campaign_name="Timeline Test",
                pack=pack,
                blueprint=blueprint,
                variants=variants
            )
            
            timeline = campaign.timeline
            
            # Check phases exist
            seed_schedules = timeline.get_schedules_by_phase(PublicationPhase.SEED)
            amplify_schedules = timeline.get_schedules_by_phase(PublicationPhase.AMPLIFY)
            
            assert len(seed_schedules) > 0
            assert len(amplify_schedules) > 0
            
            # Primary creators post first (seed)
            assert len(seed_schedules) == len(pack.primary_creators)
    
    def test_planner_risk_mapping(self, sample_profiles, selector, trend_engine, planner):
        """Test risk mapping"""
        pack = selector.select_optimal_pack(sample_profiles, budget_usd=5000.0)
        blueprint, variants = trend_engine.synthesize_trend(
            song_name="Risk Test",
            song_tempo=130,
            song_mood="energetic",
            visual_aesthetic="urban"
        )
        
        if pack:
            campaign = planner.plan_campaign(
                campaign_name="Risk Test",
                pack=pack,
                blueprint=blueprint,
                variants=variants
            )
            
            risk_map = campaign.risk_map
            
            assert 0 <= risk_map.overall_risk_score <= 1
            assert len(risk_map.risk_by_phase) > 0
            assert len(risk_map.mitigation_strategies) > 0


# ============================================================================
# ORCHESTRATION BRIDGE TESTS
# ============================================================================

class TestOrchestrationBridgeTrends:
    """Test orchestration bridge integration"""
    
    def test_bridge_validation(self, sample_profiles, selector, trend_engine, planner, bridge):
        """Test campaign validation"""
        pack = selector.select_optimal_pack(sample_profiles, budget_usd=5000.0)
        blueprint, variants = trend_engine.synthesize_trend(
            song_name="Validation Test",
            song_tempo=120,
            song_mood="energetic",
            visual_aesthetic="urban"
        )
        
        if pack:
            campaign = planner.plan_campaign(
                campaign_name="Validation Test",
                pack=pack,
                blueprint=blueprint,
                variants=variants
            )
            
            validation = bridge.validate_influencer_pack(campaign)
            
            assert validation is not None
            assert isinstance(validation.is_valid, bool)
            assert isinstance(validation.errors, list)
            assert isinstance(validation.warnings, list)
    
    def test_bridge_risk_simulation(self, sample_profiles, selector, trend_engine, planner, bridge):
        """Test risk simulation (Sprint 14 integration)"""
        pack = selector.select_optimal_pack(sample_profiles, budget_usd=5000.0)
        blueprint, variants = trend_engine.synthesize_trend(
            song_name="Risk Sim Test",
            song_tempo=128,
            song_mood="party",
            visual_aesthetic="raw"
        )
        
        if pack:
            campaign = planner.plan_campaign(
                campaign_name="Risk Sim Test",
                pack=pack,
                blueprint=blueprint,
                variants=variants
            )
            
            risk_sim = bridge.simulate_campaign_risk(campaign)
            
            assert risk_sim is not None
            assert 0 <= risk_sim.overall_risk_score <= 1
            assert isinstance(risk_sim.high_risk_factors, list)
            assert isinstance(risk_sim.approval_recommended, bool)
    
    def test_bridge_policy_check(self, sample_profiles, selector, trend_engine, planner, bridge):
        """Test policy checking (Sprint 15 integration)"""
        pack = selector.select_optimal_pack(sample_profiles, budget_usd=5000.0)
        blueprint, variants = trend_engine.synthesize_trend(
            song_name="Policy Test",
            song_tempo=130,
            song_mood="energetic",
            visual_aesthetic="urban"
        )
        
        if pack:
            campaign = planner.plan_campaign(
                campaign_name="Policy Test",
                pack=pack,
                blueprint=blueprint,
                variants=variants
            )
            
            policy_check = bridge.check_policies(campaign)
            
            assert policy_check is not None
            assert isinstance(policy_check.policies_passed, bool)
            assert len(policy_check.policies_checked) > 0
    
    def test_bridge_full_launch(self, sample_profiles, selector, trend_engine, planner, bridge):
        """Test full launch workflow"""
        pack = selector.select_optimal_pack(sample_profiles, budget_usd=5000.0)
        blueprint, variants = trend_engine.synthesize_trend(
            song_name="Launch Test",
            song_tempo=128,
            song_mood="energetic",
            visual_aesthetic="urban"
        )
        
        if pack:
            campaign = planner.plan_campaign(
                campaign_name="Launch Test",
                pack=pack,
                blueprint=blueprint,
                variants=variants
            )
            
            execution = bridge.request_trend_launch(
                campaign=campaign,
                auto_approve=True
            )
            
            assert execution is not None
            assert execution.status in [
                CampaignStatus.IN_PROGRESS,
                CampaignStatus.APPROVED,
                CampaignStatus.FAILED
            ]
            
            if execution.status == CampaignStatus.IN_PROGRESS:
                assert len(execution.orchestrator_job_ids) > 0
                assert execution.ledger_id is not None


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestFullPipeline:
    """Test complete end-to-end pipeline"""
    
    def test_complete_pipeline(self, scraper, analyzer, selector, trend_engine, planner, bridge):
        """Test full pipeline: scrape → analyze → select → synthesize → plan → launch"""
        
        # 1. Scrape
        urls = [f"https://www.tiktok.com/@pipeline_creator{i}" for i in range(1, 10)]
        raw_data = scraper.scrape_multiple(urls)
        assert len(raw_data) > 0
        
        # 2. Analyze
        profiles = analyzer.analyze_batch(raw_data)
        assert len(profiles) == len(raw_data)
        
        # 3. Select
        pack = selector.select_optimal_pack(profiles, budget_usd=5000.0)
        assert pack is not None
        
        # 4. Synthesize
        blueprint, variants = trend_engine.synthesize_trend(
            song_name="Pipeline Song",
            song_tempo=128,
            song_mood="energetic",
            visual_aesthetic="urban"
        )
        assert blueprint is not None
        assert len(variants) >= 3
        
        # 5. Plan
        campaign = planner.plan_campaign(
            campaign_name="Pipeline Campaign",
            pack=pack,
            blueprint=blueprint,
            variants=variants
        )
        assert campaign is not None
        
        # 6. Launch
        execution = bridge.request_trend_launch(campaign, auto_approve=True)
        assert execution is not None
        assert execution.validation_result is not None
        assert execution.risk_simulation is not None
        assert execution.policy_check is not None


# ============================================================================
# EDGE CASES
# ============================================================================

class TestEdgeCases:
    """Test edge cases and error handling"""
    
    def test_empty_candidates(self, selector):
        """Test selector with no candidates"""
        pack = selector.select_optimal_pack(
            candidates=[],
            budget_usd=5000.0
        )
        assert pack is None
    
    def test_zero_budget(self, sample_profiles, selector):
        """Test selector with zero budget"""
        pack = selector.select_optimal_pack(
            candidates=sample_profiles,
            budget_usd=0.0
        )
        assert pack is None
    
    def test_insufficient_safe_candidates(self, scraper, analyzer, selector):
        """Test when not enough low-risk candidates"""
        # Create high-risk profiles (simulated by modifying scraper output)
        # In real scenario, this would be actual high-risk creators
        urls = ["https://www.tiktok.com/@risky1", "https://www.tiktok.com/@risky2"]
        raw_data = scraper.scrape_multiple(urls)
        profiles = analyzer.analyze_batch(raw_data)
        
        # Try to select with very strict risk threshold
        strict_selector = InfluencerSelector(risk_threshold=0.01)
        pack = strict_selector.select_optimal_pack(profiles, budget_usd=5000.0)
        
        # Should fail due to insufficient safe candidates
        assert pack is None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
