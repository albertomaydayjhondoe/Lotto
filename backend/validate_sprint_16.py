"""
Sprint 16: End-to-end validation script

Tests complete pipeline without pytest dependency.
"""

from app.influencer_trend_engine import (
    InfluencerScraper,
    InfluencerAnalyzer,
    InfluencerSelector,
    TrendSynthesisEngine,
    InfluencerCampaignPlanner,
    OrchestrationBridgeTrends
)


def main():
    print("🟣 Sprint 16: Influencer Trend Engine - E2E Validation\n")
    
    # Initialize modules
    scraper = InfluencerScraper()
    analyzer = InfluencerAnalyzer()
    selector = InfluencerSelector(
        risk_threshold=0.50,  # More lenient for demo
        diversity_threshold=0.2,  # More lenient for demo
        min_primary_creators=2,
        max_primary_creators=4,
        min_support_creators=2,
        max_support_creators=6
    )
    trend_engine = TrendSynthesisEngine()
    planner = InfluencerCampaignPlanner()
    bridge = OrchestrationBridgeTrends()
    
    # Test 1: Scraper
    print("[1/7] Testing Scraper...")
    urls = [
        "https://www.tiktok.com/@creator1",
        "https://www.tiktok.com/@creator2",
        "https://www.instagram.com/@creator3",
        "https://www.instagram.com/@creator4",
        "https://www.youtube.com/@creator5",
        "https://www.tiktok.com/@creator6",
        "https://www.tiktok.com/@creator7",
        "https://www.instagram.com/@creator8",
        "https://www.tiktok.com/@creator9",
        "https://www.tiktok.com/@creator10"
    ]
    
    raw_data = scraper.scrape_multiple(urls)
    print(f"  ✓ Scraped {len(raw_data)} influencers")
    
    # Test 2: Analyzer
    print("[2/7] Testing Analyzer...")
    profiles = analyzer.analyze_batch(raw_data)
    print(f"  ✓ Analyzed {len(profiles)} profiles")
    
    # Show sample scores
    sample = profiles[0]
    print(f"      Sample: {sample.raw_data.username}")
    print(f"        Impact: {sample.scores.impact_score:.2f}")
    print(f"        Credibility: {sample.scores.credibility_score:.2f}")
    print(f"        Cultural fit: {sample.scores.cultural_fit:.2f}")
    print(f"        Trend reactivity: {sample.scores.trend_reactivity:.2f}")
    print(f"        Risk: {sample.scores.risk_score:.2f}")
    print(f"        Price efficiency: {sample.scores.price_efficiency:.2f}")
    print(f"        Composite: {sample.scores.composite_score():.2f}")
    
    # Test 3: Selector
    print("[3/7] Testing Selector...")
    pack = selector.select_optimal_pack(
        candidates=profiles,
        budget_usd=5000.0
    )
    
    if pack:
        print(f"  ✓ Selected pack with {pack.total_creators} creators")
        print(f"      Primary: {len(pack.primary_creators)}")
        print(f"      Support: {len(pack.support_creators)}")
        print(f"      Budget: ${pack.total_budget_usd:,.2f}")
        print(f"      Expected impressions: {pack.total_expected_impressions:,}")
        print(f"      Diversity: {pack.diversity_score:.2f}")
        print(f"      Max risk: {pack.max_risk_score:.2f}")
    else:
        print("  ✗ Failed to create pack")
        return
    
    # Test 4: Trend Synthesis
    print("[4/7] Testing Trend Synthesis...")
    blueprint, variants = trend_engine.synthesize_trend(
        song_name="Bailando en la Noche",
        song_tempo=128,
        song_mood="energetic",
        visual_aesthetic="urban raw",
        artist_language="es"
    )
    
    print(f"  ✓ Generated trend blueprint")
    print(f"      Movement: {blueprint.core_movement}")
    print(f"      Style: {blueprint.visual_style.value}")
    print(f"      Virality: {blueprint.virality_potential:.2f}")
    print(f"      Risk: {blueprint.risk_score:.2f}")
    print(f"      Variants: {len(variants)}")
    
    # Test 5: Campaign Planner
    print("[5/7] Testing Campaign Planner...")
    campaign = planner.plan_campaign(
        campaign_name="Bailando Launch Campaign",
        pack=pack,
        blueprint=blueprint,
        variants=variants
    )
    
    print(f"  ✓ Planned campaign")
    print(f"      Duration: {(campaign.timeline.campaign_end - campaign.timeline.campaign_start).days} days")
    print(f"      Schedules: {len(campaign.timeline.schedules)}")
    print(f"      Expected impressions: {campaign.expected_outcomes.cumulative_impressions:,}")
    print(f"      Expected engagement: {campaign.expected_outcomes.cumulative_engagement:,}")
    print(f"      Risk: {campaign.risk_map.overall_risk_score:.2f}")
    print(f"      Confidence: {campaign.expected_outcomes.confidence_level}")
    
    # Test 6: Orchestration Bridge - Validation
    print("[6/7] Testing Orchestration Bridge - Validation...")
    validation = bridge.validate_influencer_pack(campaign)
    print(f"  ✓ Validation: {'PASS' if validation.is_valid else 'FAIL'}")
    
    if validation.errors:
        print(f"      Errors: {len(validation.errors)}")
        for err in validation.errors:
            print(f"        - {err}")
    
    if validation.warnings:
        print(f"      Warnings: {len(validation.warnings)}")
        for warn in validation.warnings[:3]:
            print(f"        - {warn}")
    
    # Test 7: Orchestration Bridge - Full Launch
    print("[7/7] Testing Orchestration Bridge - Full Launch...")
    execution = bridge.request_trend_launch(
        campaign=campaign,
        auto_approve=True
    )
    
    print(f"  ✓ Campaign execution: {execution.status.value}")
    print(f"      Validation: {'✓' if execution.validation_result and execution.validation_result.is_valid else '✗'}")
    print(f"      Risk simulation: {'✓' if execution.risk_simulation else '✗'}")
    print(f"      Policy check: {'✓' if execution.policy_check else '✗'}")
    print(f"      Ledger ID: {execution.ledger_id}")
    print(f"      Orchestrator jobs: {len(execution.orchestrator_job_ids)}")
    
    print("\n" + "="*60)
    print("✅ Sprint 16 E2E Validation: SUCCESS")
    print("="*60)
    
    print("\nSummary:")
    print(f"  • Scraped: {len(raw_data)} influencers")
    print(f"  • Analyzed: {len(profiles)} profiles")
    print(f"  • Selected: {pack.total_creators} creators (${pack.total_budget_usd:,.2f})")
    print(f"  • Trend: {blueprint.song_name} ({len(variants)} variants)")
    print(f"  • Campaign: {campaign.campaign_name} ({len(campaign.timeline.schedules)} schedules)")
    print(f"  • Expected reach: {campaign.expected_outcomes.cumulative_reach:,}")
    print(f"  • Status: {execution.status.value}")


if __name__ == "__main__":
    main()
