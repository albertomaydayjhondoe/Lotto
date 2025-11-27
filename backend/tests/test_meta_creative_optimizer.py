"""Tests for Meta Creative Optimizer (PASO 10.16)"""
import pytest
from uuid import UUID, uuid4
from datetime import datetime

from app.meta_creative_optimizer.data_collector import UnifiedDataCollector
from app.meta_creative_optimizer.winner_selector import WinnerSelector
from app.meta_creative_optimizer.decision_engine import CreativeDecisionEngine
from app.meta_creative_optimizer.orchestrator_integration import OrchestrationClient
from app.meta_creative_optimizer import schemas


@pytest.mark.asyncio
async def test_data_collection():
    """Test unified data collection"""
    collector = UnifiedDataCollector(mode="stub")
    
    creative_id = uuid4()
    campaign_id = uuid4()
    
    data = await collector.collect_creative_data(creative_id, campaign_id)
    
    assert data.creative_id == creative_id
    assert data.campaign_id == campaign_id
    assert 0 <= data.overall_score <= 100
    assert data.ctr >= 0
    assert data.roas >= 0
    assert isinstance(data.is_fatigued, bool)


@pytest.mark.asyncio
async def test_collect_all_creatives():
    """Test collecting multiple creatives"""
    collector = UnifiedDataCollector(mode="stub")
    
    campaign_ids = [uuid4(), uuid4()]
    creatives = await collector.collect_all_creatives(campaign_ids)
    
    assert len(creatives) >= 6  # Minimum 3 per campaign
    assert all(isinstance(c, schemas.UnifiedCreativeData) for c in creatives)


@pytest.mark.asyncio
async def test_winner_selection():
    """Test winner selection algorithm"""
    collector = UnifiedDataCollector(mode="stub")
    creatives = await collector.collect_all_creatives([uuid4()])
    
    selector = WinnerSelector(mode="stub")
    result = await selector.select_winner(creatives)
    
    assert result.winner_creative_id in [c.creative_id for c in creatives]
    assert 0 <= result.winner_score <= 100
    assert result.candidates_evaluated <= len(creatives)  # May filter fatigued
    assert result.confidence in schemas.DecisionConfidence


@pytest.mark.asyncio
async def test_winner_selection_filters_fatigued():
    """Test that winner selector filters out fatigued creatives"""
    collector = UnifiedDataCollector(mode="stub")
    creatives = await collector.collect_all_creatives([uuid4()])
    
    # Force all but one to be fatigued
    for i, c in enumerate(creatives[:-1]):
        c.is_fatigued = True
        c.overall_score = 40
    
    creatives[-1].is_fatigued = False
    creatives[-1].overall_score = 85
    
    selector = WinnerSelector(mode="stub")
    result = await selector.select_winner(creatives)
    
    assert result.winner_creative_id == creatives[-1].creative_id


@pytest.mark.asyncio
async def test_decision_engine_role_assignment():
    """Test creative role assignment"""
    collector = UnifiedDataCollector(mode="stub")
    creatives = await collector.collect_all_creatives([uuid4()])
    
    selector = WinnerSelector(mode="stub")
    winner = await selector.select_winner(creatives)
    
    engine = CreativeDecisionEngine(mode="stub")
    decisions = await engine.make_decisions(creatives, winner)
    
    assert len(decisions) == len(creatives)
    
    # Check winner is assigned WINNER role
    winner_decision = next(d for d in decisions if d.creative_id == winner.winner_creative_id)
    assert winner_decision.assigned_role == schemas.CreativeRole.WINNER
    
    # Check all decisions have required fields
    for decision in decisions:
        assert decision.assigned_role in schemas.CreativeRole
        assert len(decision.recommended_actions) > 0
        assert 1 <= decision.priority <= 5
        assert decision.confidence in schemas.DecisionConfidence


@pytest.mark.asyncio
async def test_decision_engine_fatigued_handling():
    """Test handling of fatigued creatives"""
    collector = UnifiedDataCollector(mode="stub")
    creative_id = uuid4()
    campaign_id = uuid4()
    
    creative = await collector.collect_creative_data(creative_id, campaign_id)
    creative.is_fatigued = True
    creative.fatigue_score = 75
    creative.overall_score = 55
    
    # Create dummy winner
    winner = schemas.WinnerSelectionResult(
        winner_creative_id=uuid4(),
        winner_score=85.0,
        candidates_evaluated=2,
        confidence=schemas.DecisionConfidence.HIGH,
        reasoning="Test winner",
        selected_at=datetime.utcnow()
    )
    
    engine = CreativeDecisionEngine(mode="stub")
    decision = await engine._decide_for_creative(creative, is_winner=False)
    
    assert decision.assigned_role == schemas.CreativeRole.FATIGUE
    assert schemas.OptimizationAction.GENERATE_VARIANTS in decision.recommended_actions or \
           schemas.OptimizationAction.PAUSE in decision.recommended_actions


@pytest.mark.asyncio
async def test_decision_engine_budget_scaling():
    """Test budget scaling decisions"""
    collector = UnifiedDataCollector(mode="stub")
    creative_id = uuid4()
    campaign_id = uuid4()
    
    creative = await collector.collect_creative_data(creative_id, campaign_id)
    creative.overall_score = 85
    creative.roas = 4.5
    creative.is_fatigued = False
    
    winner = schemas.WinnerSelectionResult(
        winner_creative_id=creative_id,
        winner_score=85.0,
        candidates_evaluated=1,
        confidence=schemas.DecisionConfidence.HIGH,
        reasoning="Test winner",
        selected_at=datetime.utcnow()
    )
    
    engine = CreativeDecisionEngine(mode="stub")
    decision = await engine._decide_for_creative(creative, is_winner=True)
    
    assert decision.assigned_role == schemas.CreativeRole.WINNER
    assert schemas.OptimizationAction.SCALE_BUDGET in decision.recommended_actions
    assert decision.budget_change_pct > 0


@pytest.mark.asyncio
async def test_orchestrator_publish_winner():
    """Test orchestrator publish winner"""
    orchestrator = OrchestrationClient(mode="stub")
    
    creative_id = uuid4()
    campaign_id = uuid4()
    
    result = await orchestrator.publish_winner(creative_id, campaign_id)
    
    assert result.success is True
    assert result.creative_id == creative_id
    assert result.action == "publish"
    assert result.message is not None


@pytest.mark.asyncio
async def test_orchestrator_update_budget():
    """Test orchestrator budget update"""
    orchestrator = OrchestrationClient(mode="stub")
    
    creative_id = uuid4()
    new_budget = 5000.0
    
    result = await orchestrator.update_budget(creative_id, new_budget)
    
    assert result.success is True
    assert result.creative_id == creative_id
    assert result.action == "update_budget"


@pytest.mark.asyncio
async def test_orchestrator_ab_test():
    """Test orchestrator A/B test creation"""
    orchestrator = OrchestrationClient(mode="stub")
    
    creative_ids = [uuid4(), uuid4()]
    campaign_id = uuid4()
    
    result = await orchestrator.create_ab_test(creative_ids, campaign_id)
    
    assert result.success is True
    assert result.action == "create_ab_test"


@pytest.mark.asyncio
async def test_full_optimization_pipeline():
    """Test complete optimization pipeline"""
    # Collect data
    collector = UnifiedDataCollector(mode="stub")
    creatives = await collector.collect_all_creatives([uuid4()])
    
    # Select winner
    selector = WinnerSelector(mode="stub")
    winner = await selector.select_winner(creatives)
    
    # Make decisions
    engine = CreativeDecisionEngine(mode="stub")
    decisions = await engine.make_decisions(creatives, winner)
    
    # Execute orchestrations
    orchestrator = OrchestrationClient(mode="stub")
    winner_decision = next(d for d in decisions if d.creative_id == winner.winner_creative_id)
    
    if schemas.OptimizationAction.PROMOTE in winner_decision.recommended_actions:
        result = await orchestrator.publish_winner(
            winner.winner_creative_id,
            creatives[0].campaign_id
        )
        assert result.success is True
    
    # Verify pipeline completeness
    assert len(creatives) > 0
    assert winner.winner_creative_id in [c.creative_id for c in creatives]
    assert len(decisions) == len(creatives)
    
    # Verify winner gets highest priority
    winner_decision = next(d for d in decisions if d.creative_id == winner.winner_creative_id)
    assert winner_decision.priority == 1


@pytest.mark.asyncio
async def test_variant_generation_decision():
    """Test variant generation decision logic"""
    collector = UnifiedDataCollector(mode="stub")
    creative_id = uuid4()
    campaign_id = uuid4()
    
    creative = await collector.collect_creative_data(creative_id, campaign_id)
    creative.is_fatigued = True
    creative.fatigue_score = 65
    creative.overall_score = 60
    
    winner = schemas.WinnerSelectionResult(
        winner_creative_id=uuid4(),
        winner_score=85.0,
        candidates_evaluated=2,
        confidence=schemas.DecisionConfidence.HIGH,
        reasoning="Test",
        selected_at=datetime.utcnow()
    )
    
    engine = CreativeDecisionEngine(mode="stub")
    decision = await engine._decide_for_creative(creative, is_winner=False)
    
    assert decision.should_generate_variants is True
    assert decision.variant_strategy is not None
    assert decision.should_recombine is True
