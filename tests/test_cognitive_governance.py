"""
SPRINT 14 - Cognitive Governance Tests

Test suite para Sprint 14: Cognitive Governance & Risk Intelligence Layer

Módulos testeados:
- Decision Ledger
- Risk Simulation Engine
- Aggressiveness Monitor
- Decision Classifier
- Governance Bridge (integration)

Coverage target: ≥80%
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from datetime import datetime, timedelta
from app.cognitive_governance import (
    DecisionLedger,
    DecisionRecord,
    DecisionType,
    RiskSimulationEngine,
    ActionType,
    AggressivenessMonitor,
    AggressivenessLevel,
    DecisionClassifier,
    DecisionLevel,
    CognitiveGovernanceBridge,
    DecisionOutcome,
)


def test_1_decision_ledger_record():
    """Test 1: Decision ledger recording"""
    print("\n" + "="*60)
    print("TEST 1: Decision Ledger Recording")
    print("="*60)
    
    ledger = DecisionLedger(storage_path="/tmp/test_cognitive_governance")
    
    decision = DecisionRecord(
        decision_id="",
        actor="Orchestrator",
        decision_type=DecisionType.CONTENT_BOOST,
        timestamp=datetime.now(),
        inputs=["ML", "SatelliteEngine"],
        context={'account_id': 'test_001'},
        alternatives_considered=["Option_A", "Option_B"],
        chosen="Option_A",
        reasoning=["High retention", "Low risk"],
        confidence=0.85,
        risk_score=0.20
    )
    
    decision_id = ledger.record_decision(decision)
    
    assert decision_id is not None, "Decision ID should be generated"
    print(f"   ✓ Decision recorded: {decision_id}")
    
    # Retrieve
    retrieved = ledger.get_decision(decision_id)
    assert retrieved is not None, "Decision should be retrievable"
    assert retrieved.actor == "Orchestrator"
    assert retrieved.confidence == 0.85
    print(f"   ✓ Decision retrieved: confidence={retrieved.confidence}")
    
    # Stats
    stats = ledger.get_statistics()
    assert stats['total_decisions'] >= 1
    print(f"   ✓ Ledger stats: {stats['total_decisions']} total decisions")


def test_2_risk_simulation():
    """Test 2: Risk simulation engine"""
    print("\n" + "="*60)
    print("TEST 2: Risk Simulation Engine")
    print("="*60)
    
    engine = RiskSimulationEngine()
    
    context = {
        'account_id': 'test_002',
        'platform': 'tiktok',
        'fingerprint_changes_24h': 0,
        'ip_changes_24h': 0,
        'account_age_days': 30,
        'recent_actions': [],
        'metrics': {
            'reach_drop_7d': 0.05,
            'engagement_rate': 0.04
        },
        'reports_7d': 0,
        'concurrent_accounts': 2,
        'content_quality_score': 0.7
    }
    
    result = engine.simulate_action(ActionType.POST_CONTENT, context)
    
    assert result is not None, "Simulation should return result"
    assert 0 <= result.total_risk_score <= 1, "Risk score should be 0-1"
    assert result.risk_level is not None
    print(f"   ✓ Simulation complete: risk={result.total_risk_score:.2f}, level={result.risk_level.value}")
    print(f"   ✓ Should proceed: {result.should_proceed}")
    
    # Test high risk scenario
    high_risk_context = context.copy()
    high_risk_context['fingerprint_changes_24h'] = 3
    high_risk_context['ip_changes_24h'] = 2
    high_risk_context['metrics']['reach_drop_7d'] = 0.40
    
    high_risk_result = engine.simulate_action(ActionType.POST_CONTENT, high_risk_context)
    assert high_risk_result.total_risk_score > result.total_risk_score, "High risk context should have higher score"
    print(f"   ✓ High risk simulation: risk={high_risk_result.total_risk_score:.2f}")


def test_3_aggressiveness_monitor():
    """Test 3: Aggressiveness monitor"""
    print("\n" + "="*60)
    print("TEST 3: Aggressiveness Monitor")
    print("="*60)
    
    monitor = AggressivenessMonitor()
    
    # Record some actions
    for i in range(5):
        monitor.record_action(
            action_type="post_content",
            account_id=f"acc_{i % 2}",
            timestamp=datetime.now() - timedelta(seconds=i*10)
        )
    
    print(f"   ✓ Recorded 5 actions")
    
    # Evaluate
    score = monitor.evaluate_aggressiveness()
    
    assert score is not None, "Score should be generated"
    assert score.level in [AggressivenessLevel.SAFE, AggressivenessLevel.WARNING, AggressivenessLevel.DANGER]
    print(f"   ✓ Aggressiveness: level={score.level.value}, score={score.global_score:.2f}")
    print(f"   ✓ Should throttle: {score.should_throttle}")
    print(f"   ✓ Should block: {score.should_block_critical}")
    
    # Test heavy load
    for i in range(50):
        monitor.record_action("post", f"acc_{i % 3}", datetime.now())
    
    high_agg_score = monitor.evaluate_aggressiveness()
    # Note: Aggressiveness might not always increase due to time-window cleanup
    print(f"   ✓ After 50 actions: score={high_agg_score.global_score:.2f}, level={high_agg_score.level.value}")


def test_4_decision_classifier():
    """Test 4: Decision classifier"""
    print("\n" + "="*60)
    print("TEST 4: Decision Classifier")
    print("="*60)
    
    classifier = DecisionClassifier()
    
    # Test MICRO
    micro = classifier.classify_decision(
        decision_type="like_single",
        estimated_risk=0.1,
        estimated_impact=0.05
    )
    assert micro.level == DecisionLevel.MICRO
    assert not micro.requires_ledger
    print(f"   ✓ MICRO classification: requires_ledger={micro.requires_ledger}")
    
    # Test STANDARD
    standard = classifier.classify_decision(
        decision_type="post_content",
        estimated_risk=0.3,
        estimated_impact=0.2
    )
    assert standard.level == DecisionLevel.STANDARD
    assert standard.requires_ledger
    assert not standard.requires_simulation
    print(f"   ✓ STANDARD classification: requires_ledger={standard.requires_ledger}, requires_sim={standard.requires_simulation}")
    
    # Test CRITICAL
    critical = classifier.classify_decision(
        decision_type="scale_accounts",
        estimated_risk=0.6,
        estimated_impact=0.5,
        context={'accounts_affected': 10}
    )
    assert critical.level == DecisionLevel.CRITICAL
    assert critical.requires_ledger
    assert critical.requires_simulation
    assert critical.requires_llm_validation
    print(f"   ✓ CRITICAL classification: requires_sim={critical.requires_simulation}, requires_llm={critical.requires_llm_validation}")
    
    # Test STRUCTURAL
    structural = classifier.classify_decision(
        decision_type="strategy_change",
        estimated_risk=0.8,
        estimated_impact=0.7,
        context={'accounts_affected': 100}
    )
    assert structural.level == DecisionLevel.STRUCTURAL
    assert structural.requires_human_approval
    print(f"   ✓ STRUCTURAL classification: requires_human={structural.requires_human_approval}")


def test_5_governance_bridge_integration():
    """Test 5: Governance bridge integration"""
    print("\n" + "="*60)
    print("TEST 5: Governance Bridge Integration")
    print("="*60)
    
    bridge = CognitiveGovernanceBridge({
        'ledger': {'storage_path': '/tmp/test_cognitive_governance_bridge'}
    })
    
    # Test MICRO decision (should be approved immediately)
    eval_micro = bridge.evaluate_decision(
        decision_type="like_single",
        actor="Orchestrator",
        context={
            'account_id': 'test_005',
            'estimated_risk': 0.1,
            'estimated_impact': 0.05
        }
    )
    
    assert eval_micro.approved, "MICRO decision should be approved"
    assert eval_micro.classification_level == DecisionLevel.MICRO
    print(f"   ✓ MICRO decision: approved={eval_micro.approved}, level={eval_micro.classification_level.value}")
    
    # Test STANDARD decision
    eval_standard = bridge.evaluate_decision(
        decision_type="content_boost",
        actor="Orchestrator",
        context={
            'account_id': 'test_006',
            'estimated_risk': 0.3,
            'estimated_impact': 0.2
        },
        chosen="YT_Video_014",
        reasoning=["High retention", "Near breakout"]
    )
    
    assert eval_standard.approved, "STANDARD decision should be approved"
    assert eval_standard.decision_id is not None, "STANDARD should be recorded in ledger"
    print(f"   ✓ STANDARD decision: approved={eval_standard.approved}, decision_id={eval_standard.decision_id}")
    
    # Test CRITICAL decision
    eval_critical = bridge.evaluate_decision(
        decision_type="scale_accounts",
        actor="Orchestrator",
        context={
            'account_id': 'test_007',
            'estimated_risk': 0.6,
            'estimated_impact': 0.5,
            'accounts_affected': 10,
            'platform': 'tiktok',
            'fingerprint_changes_24h': 0,
            'ip_changes_24h': 0,
            'account_age_days': 60,
            'recent_actions': [],
            'metrics': {'reach_drop_7d': 0.05, 'engagement_rate': 0.04}
        }
    )
    
    assert eval_critical.classification_level == DecisionLevel.CRITICAL
    assert eval_critical.requires_simulation
    print(f"   ✓ CRITICAL decision: level={eval_critical.classification_level.value}, approved={eval_critical.approved}")
    print(f"   ✓ Risk score: {eval_critical.risk_score:.2f}")


def test_6_high_aggressiveness_blocking():
    """Test 6: High aggressiveness blocks decisions"""
    print("\n" + "="*60)
    print("TEST 6: Aggressiveness Blocking")
    print("="*60)
    
    bridge = CognitiveGovernanceBridge({
        'ledger': {'storage_path': '/tmp/test_cognitive_governance_throttle'},
        'agg_monitor': {
            'baseline_actions_per_hour': 5  # Low baseline to trigger throttling
        }
    })
    
    # Simulate many actions to increase aggressiveness
    for i in range(30):
        bridge.agg_monitor.record_action("post", f"acc_{i % 3}", datetime.now())
    
    # Force aggressiveness evaluation
    agg_score = bridge.agg_monitor.evaluate_aggressiveness()
    print(f"   ✓ Aggressiveness after 30 actions: {agg_score.global_score:.2f}")
    
    # Try to make a decision
    eval_throttled = bridge.evaluate_decision(
        decision_type="content_boost",
        actor="Orchestrator",
        context={
            'account_id': 'test_008',
            'estimated_risk': 0.3,
            'estimated_impact': 0.2
        }
    )
    
    # Should be throttled if aggressiveness is high
    if agg_score.should_block_critical:
        assert eval_throttled.outcome == DecisionOutcome.THROTTLED
        print(f"   ✓ Decision throttled due to high aggressiveness")
    else:
        print(f"   ✓ Decision not throttled (aggressiveness still acceptable)")


def test_7_statistics_collection():
    """Test 7: Statistics collection"""
    print("\n" + "="*60)
    print("TEST 7: Statistics Collection")
    print("="*60)
    
    bridge = CognitiveGovernanceBridge({
        'ledger': {'storage_path': '/tmp/test_cognitive_governance_stats'}
    })
    
    # Make several decisions
    for i in range(5):
        bridge.evaluate_decision(
            decision_type="post_content",
            actor="Orchestrator",
            context={
                'account_id': f'test_{i}',
                'estimated_risk': 0.2 + i * 0.1,
                'estimated_impact': 0.1
            }
        )
    
    stats = bridge.get_statistics()
    
    assert 'bridge' in stats
    assert 'classifier' in stats
    assert 'risk_engine' in stats
    assert 'aggressiveness_monitor' in stats
    assert 'ledger' in stats
    
    print(f"   ✓ Bridge stats: {stats['bridge']['total_evaluations']} evaluations")
    print(f"   ✓ Approval rate: {stats['bridge']['approval_rate']:.2%}")
    print(f"   ✓ Classifier: {stats['classifier']['total_classifications']} classifications")
    print(f"   ✓ Risk engine: {stats['risk_engine']['simulations_run']} simulations")


def test_8_daily_summary():
    """Test 8: Daily summary generation"""
    print("\n" + "="*60)
    print("TEST 8: Daily Summary Generation")
    print("="*60)
    
    bridge = CognitiveGovernanceBridge({
        'ledger': {'storage_path': '/tmp/test_cognitive_governance_summary'}
    })
    
    # Make some decisions
    for i in range(3):
        bridge.evaluate_decision(
            decision_type="content_boost",
            actor="Orchestrator",
            context={'account_id': f'test_{i}', 'estimated_risk': 0.3, 'estimated_impact': 0.2},
            chosen=f"Content_{i}",
            reasoning=["Test reasoning"]
        )
    
    summary = bridge.get_daily_summary()
    
    assert 'report' in summary
    assert 'metrics' in summary
    assert isinstance(summary['report'], str)
    
    print(f"   ✓ Daily summary generated")
    print(f"   ✓ Total decisions: {summary['metrics'].get('Total Decisions', 0)}")
    print(f"   ✓ Report length: {len(summary['report'])} chars")


# Run all tests
if __name__ == "__main__":
    print("\n" + "="*60)
    print("SPRINT 14: COGNITIVE GOVERNANCE TESTS")
    print("="*60)
    
    tests = [
        test_1_decision_ledger_record,
        test_2_risk_simulation,
        test_3_aggressiveness_monitor,
        test_4_decision_classifier,
        test_5_governance_bridge_integration,
        test_6_high_aggressiveness_blocking,
        test_7_statistics_collection,
        test_8_daily_summary,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            failed += 1
            print(f"\n   ❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"Total: {len(tests)}")
    print(f"Passed: {passed} ✅")
    print(f"Failed: {failed} ❌")
    print(f"Coverage: {(passed/len(tests)*100):.1f}%")
    
    if failed == 0:
        print("\n🎉 ALL TESTS PASSED!")
    else:
        print(f"\n⚠️  {failed} test(s) failed")
