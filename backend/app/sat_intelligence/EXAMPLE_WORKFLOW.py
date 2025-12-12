"""
SPRINT 11 - Satellite Intelligence Optimization
Example: Complete Workflow

Demuestra el flujo completo de generación de propuestas inteligentes.
"""

from datetime import datetime
from app.sat_intelligence import (
    # Main API
    SatelliteIntelligenceAPI,
    SatIntelConfig,
    
    # Request/Response
    GenerateProposalRequest,
    
    # Profile Manager
    UniverseProfileManager,
    AccountProfile,
    
    # Helpers
    generate_proposals_simple,
)


def example_full_workflow():
    """
    Ejemplo completo del flujo de Satellite Intelligence.
    
    Flujo:
    1. Inicializar API y Profile Manager
    2. Crear perfiles de cuentas satélite
    3. Generar propuestas de contenido
    4. Revisar resultados
    """
    
    print("=" * 80)
    print("SPRINT 11 - SATELLITE INTELLIGENCE OPTIMIZATION")
    print("Example: Full Workflow")
    print("=" * 80)
    print()
    
    # ========================================================================
    # STEP 1: Initialize API
    # ========================================================================
    
    print("STEP 1: Initializing Satellite Intelligence API...")
    print("-" * 80)
    
    config = SatIntelConfig(
        max_proposals_per_batch=50,
        min_clip_score=0.5,
        max_risk_score=0.7,
        ensure_timing_diversity=True,
        simulate_only=True
    )
    
    api = SatelliteIntelligenceAPI(config)
    print(f"✅ API initialized with config: {config}")
    print()
    
    # ========================================================================
    # STEP 2: Create Account Profiles
    # ========================================================================
    
    print("STEP 2: Creating account profiles...")
    print("-" * 80)
    
    profile_manager = api.profile_manager
    
    # Create 5 accounts across different niches
    accounts = [
        ("acc_music_001", "music", "Music Vibes"),
        ("acc_music_002", "music", "Beat Drop"),
        ("acc_dance_001", "dance", "Dance Moves"),
        ("acc_comedy_001", "comedy", "Funny Moments"),
        ("acc_food_001", "food", "Quick Recipes"),
    ]
    
    for account_id, niche_id, niche_name in accounts:
        profile = profile_manager.create_profile(
            account_id=account_id,
            niche_id=niche_id,
            niche_name=niche_name,
            start_warmup=False  # Already warmed up
        )
        
        # Mark as completed warmup and update optimal hours
        profile_manager.update_profile(
            account_id,
            warmup_completed=True,
            total_posts=25,
            avg_retention=0.75,
            avg_engagement=0.65,
            optimal_hours=[10, 14, 18, 21],
            optimal_days=[0, 1, 2, 3, 4],  # Weekdays
        )
        
        print(f"✅ Created profile: {account_id} ({niche_name} - {niche_id})")
    
    print()
    print(f"✅ Total active accounts: {len(profile_manager.get_active_accounts())}")
    print()
    
    # ========================================================================
    # STEP 3: Generate Proposals
    # ========================================================================
    
    print("STEP 3: Generating proposals...")
    print("-" * 80)
    
    # Content pool (mock IDs)
    content_ids = [
        f"clip_{i:03d}" for i in range(1, 21)  # 20 clips
    ]
    
    request = GenerateProposalRequest(
        content_ids=content_ids,
        account_ids=None,  # All active accounts
        max_proposals=50,
        min_clip_score=0.5,
        max_risk_score=0.7,
        target_timeframe_hours=24,
        include_alternatives=True,
        simulate_only=True
    )
    
    print(f"Request: {len(content_ids)} clips, max {request.max_proposals} proposals")
    print(f"Constraints: min_clip_score={request.min_clip_score}, max_risk_score={request.max_risk_score}")
    print()
    
    response = api.generate_proposals(request)
    
    print(f"✅ Generation complete!")
    print(f"   Batch ID: {response.batch_id}")
    print(f"   Total generated: {response.total_generated}")
    print(f"   Approved: {response.approved_count}")
    print(f"   Rejected: {response.rejected_count}")
    print(f"   High priority: {response.high_priority_count}")
    print(f"   Processing time: {response.processing_time_ms:.0f}ms")
    print()
    
    if response.errors:
        print(f"⚠️  Errors: {', '.join(response.errors)}")
        print()
    
    # ========================================================================
    # STEP 4: Review Top Proposals
    # ========================================================================
    
    print("STEP 4: Reviewing top proposals...")
    print("-" * 80)
    
    # Show top 5 proposals
    top_proposals = response.proposals[:5]
    
    for i, proposal in enumerate(top_proposals, 1):
        print(f"\n📋 Proposal #{i}: {proposal.proposal_id}")
        print(f"   Account: {proposal.account_id} (niche: {proposal.niche_id})")
        print(f"   Content: {proposal.content_id}")
        print(f"   Priority: {proposal.priority.value}")
        print(f"   Risk: {proposal.risk_level.value} ({proposal.risk_score:.2f})")
        print(f"   Clip Score: {proposal.clip_score.total_score:.2f}")
        print(f"      - Niche match: {proposal.clip_score.niche_match_score:.2f}")
        print(f"      - Virality: {proposal.clip_score.virality_score:.2f}")
        print(f"      - Timing: {proposal.clip_score.timing_score:.2f}")
        print(f"      - Uniqueness: {proposal.clip_score.uniqueness_score:.2f}")
        print(f"   Timing: {proposal.timing_window.start_time.strftime('%Y-%m-%d %H:%M')}")
        print(f"      - Optimal score: {proposal.timing_window.optimal_score:.2f}")
        print(f"      - Jitter: {proposal.timing_window.jitter_minutes:+.1f} min")
        print(f"   Caption: {proposal.variant.caption}")
        print(f"   Hashtags: {', '.join(proposal.variant.hashtags[:3])}...")
        print(f"   Rationale: {proposal.rationale}")
    
    print()
    
    # ========================================================================
    # STEP 5: Universe Statistics
    # ========================================================================
    
    print("STEP 5: Universe statistics...")
    print("-" * 80)
    
    stats = profile_manager.get_universe_stats()
    
    print(f"Universe Stats:")
    print(f"   Total accounts: {stats['total_accounts']}")
    print(f"   Active accounts: {stats['active_accounts']}")
    print(f"   Warmup accounts: {stats['warmup_accounts']}")
    print(f"   Suspended accounts: {stats['suspended_accounts']}")
    print(f"   Total posts: {stats['total_posts']}")
    print(f"   Avg retention: {stats['avg_retention']:.2%}")
    print(f"   Avg engagement: {stats['avg_engagement']:.2%}")
    print(f"   Niches: {stats['niches']}")
    print()
    
    # ========================================================================
    # DONE
    # ========================================================================
    
    print("=" * 80)
    print("✅ WORKFLOW COMPLETE")
    print("=" * 80)
    print()
    print("Next steps:")
    print("  1. Send top proposals to Sprint 10 Supervisor for validation")
    print("  2. Schedule approved proposals in Sprint 8 Satellite Engine")
    print("  3. Track performance and update ML models")
    print("  4. Run A/B tests with Sound Test Recommender")
    print()


def example_simple():
    """Ejemplo simplificado usando convenience function"""
    
    print("=" * 80)
    print("SPRINT 11 - SATELLITE INTELLIGENCE OPTIMIZATION")
    print("Example: Simple Usage")
    print("=" * 80)
    print()
    
    # Simple generation
    content_ids = [f"clip_{i:03d}" for i in range(1, 11)]
    
    print(f"Generating proposals for {len(content_ids)} clips...")
    
    response = generate_proposals_simple(content_ids, max_proposals=20)
    
    print(f"✅ Generated {response.approved_count} proposals in {response.processing_time_ms:.0f}ms")
    print()
    
    if response.proposals:
        print("Top proposal:")
        p = response.proposals[0]
        print(f"  Content: {p.content_id} → Account: {p.account_id}")
        print(f"  Priority: {p.priority.value}, Score: {p.clip_score.total_score:.2f}")
        print(f"  Timing: {p.timing_window.start_time.strftime('%Y-%m-%d %H:%M')}")
        print(f"  Caption: {p.variant.caption}")
    
    print()


if __name__ == "__main__":
    # Run full example
    example_full_workflow()
    
    print("\n" + "=" * 80 + "\n")
    
    # Run simple example
    # example_simple()
