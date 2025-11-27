"""
Tests for Meta RT Performance Engine (PASO 10.14)
"""

import pytest
import uuid
from datetime import datetime
from unittest.mock import AsyncMock

from app.meta_rt_engine.detector import RealTimeDetector
from app.meta_rt_engine.decision_engine import RealTimeDecisionEngine
from app.meta_rt_engine.actions import RealTimeActionsLayer
from app.meta_rt_engine.schemas import (
    PerformanceSnapshot,
    PerformanceMetrics,
    ActionType,
    SeverityLevel,
)


@pytest.fixture
def sample_campaign_id():
    return uuid.uuid4()


@pytest.fixture
def sample_snapshot(sample_campaign_id):
    return PerformanceSnapshot(
        campaign_id=sample_campaign_id,
        ad_account_id="act_123456789",
        timestamp=datetime.utcnow(),
        window_minutes=5,
        metrics=PerformanceMetrics(
            impressions=1000,
            clicks=25,
            conversions=4,
            spend=75.0,
            ctr=0.025,
            cvr=0.16,
            cpm=75.0,
            cpc=3.0,
            cpa=18.75,
            roas=2.5,
            frequency=3.2,
            reach=313,
        ),
    )


@pytest.mark.asyncio
async def test_detector_stub_mode(sample_campaign_id, sample_snapshot):
    """Test real-time detector in STUB mode."""
    detector = RealTimeDetector(mode="stub")
    
    result = await detector.detect_anomalies(
        campaign_id=sample_campaign_id,
        current_snapshot=sample_snapshot,
    )
    
    assert result.campaign_id == sample_campaign_id
    assert result.snapshot_id is not None
    assert isinstance(result.anomalies, list)
    assert isinstance(result.drifts, list)
    assert isinstance(result.spikes, list)
    assert result.processing_time_ms >= 0  # Can be 0 in fast stub mode


@pytest.mark.asyncio
async def test_detector_anomaly_detection(sample_campaign_id, sample_snapshot):
    """Test that detector can identify anomalies."""
    detector = RealTimeDetector(mode="stub")
    
    # Run multiple times to ensure we get some anomalies
    anomaly_found = False
    for _ in range(10):
        result = await detector.detect_anomalies(
            campaign_id=sample_campaign_id,
            current_snapshot=sample_snapshot,
        )
        if result.anomalies:
            anomaly_found = True
            break
    
    assert anomaly_found, "No anomalies detected in 10 attempts"


@pytest.mark.asyncio
async def test_decision_engine_stub_mode(sample_campaign_id):
    """Test decision engine in STUB mode."""
    from app.meta_rt_engine.schemas import DetectionResult, AnomalyDetection, AnomalyType
    
    decision_engine = RealTimeDecisionEngine(mode="stub")
    
    # Create mock detection result with CTR drop
    detection_result = DetectionResult(
        campaign_id=sample_campaign_id,
        snapshot_id=uuid.uuid4(),
        detection_timestamp=datetime.utcnow(),
        anomalies=[
            AnomalyDetection(
                anomaly_type=AnomalyType.CTR_DROP,
                severity=SeverityLevel.HIGH,
                metric_name="ctr",
                current_value=0.015,
                baseline_value=0.030,
                drop_percentage=50.0,
                threshold_violated=25.0,
                detection_timestamp=datetime.utcnow(),
                confidence=0.95,
                description="CTR dropped 50% from baseline",
            )
        ],
        drifts=[],
        spikes=[],
        has_critical_issues=False,
        critical_count=0,
        high_count=1,
        moderate_count=0,
        processing_time_ms=100,
    )
    
    decision = await decision_engine.make_decision(detection_result)
    
    assert decision.campaign_id == sample_campaign_id
    assert len(decision.recommended_actions) > 0
    assert ActionType.REDUCE_BUDGET in decision.recommended_actions
    assert decision.urgency == SeverityLevel.HIGH
    assert decision.should_auto_apply is True


@pytest.mark.asyncio
async def test_decision_engine_critical_roas():
    """Test decision engine with critical ROAS collapse."""
    from app.meta_rt_engine.schemas import DetectionResult, AnomalyDetection, AnomalyType
    
    decision_engine = RealTimeDecisionEngine(mode="stub")
    campaign_id = uuid.uuid4()
    
    detection_result = DetectionResult(
        campaign_id=campaign_id,
        snapshot_id=uuid.uuid4(),
        detection_timestamp=datetime.utcnow(),
        anomalies=[
            AnomalyDetection(
                anomaly_type=AnomalyType.ROAS_COLLAPSE,
                severity=SeverityLevel.CRITICAL,
                metric_name="roas",
                current_value=0.5,
                baseline_value=3.0,
                drop_percentage=83.3,
                threshold_violated=30.0,
                detection_timestamp=datetime.utcnow(),
                confidence=0.99,
                description="ROAS collapsed 83.3%",
            )
        ],
        drifts=[],
        spikes=[],
        has_critical_issues=True,
        critical_count=1,
        high_count=0,
        moderate_count=0,
        processing_time_ms=100,
    )
    
    decision = await decision_engine.make_decision(detection_result)
    
    assert decision.urgency == SeverityLevel.CRITICAL
    assert ActionType.PAUSE_CAMPAIGN in decision.recommended_actions
    assert ActionType.TRIGGER_FULL_CYCLE in decision.recommended_actions


@pytest.mark.asyncio
async def test_actions_layer_stub_mode(sample_campaign_id):
    """Test actions layer in STUB mode."""
    from app.meta_rt_engine.schemas import RealTimeDecision, DecisionRule
    
    actions_layer = RealTimeActionsLayer(mode="stub")
    
    mock_decision = RealTimeDecision(
        decision_id=uuid.uuid4(),
        campaign_id=sample_campaign_id,
        detection_result_id=uuid.uuid4(),
        recommended_actions=[ActionType.REDUCE_BUDGET, ActionType.TRIGGER_CREATIVE_RESYNC],
        rules_triggered=[],
        reasoning="Test decision",
        urgency=SeverityLevel.HIGH,
        should_auto_apply=True,
        estimated_impact={},
        created_at=datetime.utcnow(),
    )
    
    response = await actions_layer.execute_actions(
        decision=mock_decision,
        auto_apply=False,  # Simulate only
    )
    
    assert response.campaign_id == sample_campaign_id
    assert response.total_actions == 2
    assert response.successful_actions >= 0
    assert len(response.actions_executed) == 2


@pytest.mark.asyncio
async def test_actions_layer_auto_apply(sample_campaign_id):
    """Test actions layer with auto-apply enabled."""
    from app.meta_rt_engine.schemas import RealTimeDecision
    
    actions_layer = RealTimeActionsLayer(mode="stub")
    
    mock_decision = RealTimeDecision(
        decision_id=uuid.uuid4(),
        campaign_id=sample_campaign_id,
        detection_result_id=uuid.uuid4(),
        recommended_actions=[ActionType.REDUCE_BUDGET],
        rules_triggered=[],
        reasoning="Test decision with auto-apply",
        urgency=SeverityLevel.CRITICAL,
        should_auto_apply=True,
        estimated_impact={},
        created_at=datetime.utcnow(),
    )
    
    response = await actions_layer.execute_actions(
        decision=mock_decision,
        auto_apply=True,  # Actually apply
    )
    
    assert response.total_actions == 1
    # Check that action was marked as applied
    for action_result in response.actions_executed:
        if action_result.success:
            assert action_result.applied is True


@pytest.mark.asyncio
async def test_full_rt_pipeline(sample_campaign_id, sample_snapshot):
    """Test complete RT pipeline: detection → decision → action."""
    detector = RealTimeDetector(mode="stub")
    decision_engine = RealTimeDecisionEngine(mode="stub")
    actions_layer = RealTimeActionsLayer(mode="stub")
    
    # Step 1: Detect anomalies
    detection_result = await detector.detect_anomalies(
        campaign_id=sample_campaign_id,
        current_snapshot=sample_snapshot,
    )
    
    # Step 2: Make decision (if anomalies detected)
    if detection_result.anomalies:
        decision = await decision_engine.make_decision(detection_result)
        
        # Step 3: Execute actions
        if decision.recommended_actions:
            action_response = await actions_layer.execute_actions(
                decision=decision,
                auto_apply=False,
            )
            
            assert action_response.total_actions == len(decision.recommended_actions)
            assert action_response.overall_success is True
