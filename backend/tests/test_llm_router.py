"""
Tests for Dual LLM Router (PASO 7.2)

Tests cover:
1. Router selects GPT-5 for critical short tasks
2. Router selects Gemini for long context tasks
3. LLMClient preserves public API
4. System works without API keys (stub mode)
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

from app.llm_providers import DualLLMRouter, GPT5Client, GeminiClient, create_default_llm_router
from app.ai_global_worker.llm_client import LLMClient
from app.ai_global_worker.schemas import (
    SystemSnapshot,
    AISummary,
    AIRecommendation,
    AIActionPlan,
)


# ==================== FAKE CLIENTS FOR TESTING ====================

class FakeGPT5Client:
    """Fake GPT-5 client for testing router logic."""
    
    def __init__(self, api_key=None, model="gpt-5.1"):
        self.api_key = api_key
        self.model = model
        self.name = "GPT5"
        self.calls = []
    
    async def generate_summary(self, snapshot):
        self.calls.append("generate_summary")
        return AISummary(
            overall_health="good",
            health_score=85.0,
            key_insights=["GPT-5 summary"],
            concerns=[],
            positives=[],
            generated_at=datetime.utcnow(),
        )
    
    async def generate_recommendations(self, snapshot):
        self.calls.append("generate_recommendations")
        return []
    
    async def generate_action_plan(self, snapshot, recommendations):
        self.calls.append("generate_action_plan")
        return AIActionPlan(
            plan_id="fake-plan",
            title="GPT-5 Plan",
            objective="Test",
            steps=[],
            estimated_duration="10 min",
            risk_level="low",
            automated=False,
        )


class FakeGeminiClient:
    """Fake Gemini client for testing router logic."""
    
    def __init__(self, api_key=None, model="gemini-2.0-pro"):
        self.api_key = api_key
        self.model = model
        self.name = "Gemini"
        self.calls = []
    
    async def generate_summary(self, snapshot):
        self.calls.append("generate_summary")
        return AISummary(
            overall_health="excellent",
            health_score=95.0,
            key_insights=["Gemini summary"],
            concerns=[],
            positives=[],
            generated_at=datetime.utcnow(),
        )


# ==================== HELPER: CREATE MOCK SNAPSHOT ====================

def create_mock_snapshot() -> SystemSnapshot:
    """Create a mock system snapshot for testing."""
    return SystemSnapshot(
        timestamp=datetime.utcnow(),
        queue_pending=10,
        queue_processing=2,
        queue_failed=1,
        queue_success=50,
        scheduler_pending=5,
        scheduler_due_soon=2,
        orchestrator_running=True,
        orchestrator_last_run=datetime.utcnow(),
        orchestrator_actions_last_24h=45,
        publish_success_rate=94.2,
        publish_total_24h=45,
        publish_failed_24h=3,
        clips_ready=15,
        clips_pending_analysis=3,
        jobs_pending=2,
        jobs_failed=1,
        campaigns_active=3,
        campaigns_draft=1,
        alerts_critical=0,
        alerts_warning=2,
        platform_stats={},
        best_clips={},
        rule_weights={},
        recent_events=[],
        additional_metrics={},
    )


# ==================== TEST 1: Router Uses GPT-5 for Critical Short Tasks ====================

@pytest.mark.asyncio
async def test_router_uses_gpt5_for_critical_short_tasks():
    """
    Test 1: Router selects GPT-5 for critical short tasks.
    
    Verifies:
    - router.for_critical_short() returns GPT5 client
    - Recommendations use GPT-5
    - Action plans use GPT-5
    """
    # Create fake clients with tracking
    fake_gpt5 = FakeGPT5Client()
    fake_gemini = FakeGeminiClient()
    
    # Create router
    router = DualLLMRouter(
        gemini_client=fake_gemini,
        gpt5_client=fake_gpt5,
    )
    
    # Verify for_critical_short returns GPT-5
    client = router.for_critical_short()
    assert client is fake_gpt5
    assert client.name == "GPT5"
    
    # Test recommendations (critical short task)
    snapshot = create_mock_snapshot()
    recommendations = await client.generate_recommendations(snapshot)
    assert "generate_recommendations" in fake_gpt5.calls
    assert "generate_recommendations" not in fake_gemini.calls
    
    # Test action plan (critical short task)
    action_plan = await client.generate_action_plan(snapshot, recommendations)
    assert "generate_action_plan" in fake_gpt5.calls


# ==================== TEST 2: Router Uses Gemini for Long Context ====================

@pytest.mark.asyncio
async def test_router_uses_gemini_for_long_context():
    """
    Test 2: Router selects Gemini for long context tasks.
    
    Verifies:
    - router.for_long_context() returns Gemini client
    - Summary uses Gemini
    """
    # Create fake clients with tracking
    fake_gpt5 = FakeGPT5Client()
    fake_gemini = FakeGeminiClient()
    
    # Create router
    router = DualLLMRouter(
        gemini_client=fake_gemini,
        gpt5_client=fake_gpt5,
    )
    
    # Verify for_long_context returns Gemini
    client = router.for_long_context()
    assert client is fake_gemini
    assert client.name == "Gemini"
    
    # Test summary (long context task)
    snapshot = create_mock_snapshot()
    summary = await client.generate_summary(snapshot)
    assert "generate_summary" in fake_gemini.calls
    assert "generate_summary" not in fake_gpt5.calls
    
    # Verify summary content from Gemini
    assert summary.key_insights == ["Gemini summary"]


# ==================== TEST 3: LLMClient Preserves Public API ====================

@pytest.mark.asyncio
async def test_llm_client_preserves_public_api():
    """
    Test 3: LLMClient maintains backward-compatible public API.
    
    Verifies:
    - generate_summary() works and returns AISummary
    - generate_recommendations() works and returns List[AIRecommendation]
    - generate_action_plan() works and returns AIActionPlan
    - No exceptions thrown
    - Pydantic models validated correctly
    """
    # Create fake router
    fake_gpt5 = FakeGPT5Client()
    fake_gemini = FakeGeminiClient()
    router = DualLLMRouter(
        gemini_client=fake_gemini,
        gpt5_client=fake_gpt5,
    )
    
    # Create LLMClient with fake router
    client = LLMClient(router=router)
    
    # Test snapshot
    snapshot = create_mock_snapshot()
    
    # Test generate_summary
    summary = await client.generate_summary(snapshot)
    assert isinstance(summary, AISummary)
    assert summary.overall_health in ["excellent", "good", "warning", "critical"]
    assert 0.0 <= summary.health_score <= 100.0
    assert isinstance(summary.key_insights, list)
    
    # Test generate_recommendations
    recommendations = await client.generate_recommendations(snapshot)
    assert isinstance(recommendations, list)
    for rec in recommendations:
        assert isinstance(rec, AIRecommendation)
    
    # Test generate_action_plan
    action_plan = await client.generate_action_plan(snapshot)
    assert isinstance(action_plan, AIActionPlan)
    assert len(action_plan.title) > 0
    assert isinstance(action_plan.steps, list)
    assert action_plan.risk_level in ["low", "medium", "high"]
    
    # Verify routing: summary→Gemini, recommendations→GPT-5, action_plan→GPT-5
    assert "generate_summary" in fake_gemini.calls
    assert "generate_recommendations" in fake_gpt5.calls
    assert "generate_action_plan" in fake_gpt5.calls


# ==================== TEST 4: System Works Without API Keys ====================

@pytest.mark.asyncio
async def test_llm_client_works_without_api_keys():
    """
    Test 4: System operates in stub mode without API keys.
    
    Verifies:
    - LLMClient can be instantiated without API keys
    - All methods work in stub mode
    - No exceptions or errors
    - Returns valid data structures
    """
    # Create LLMClient without providing API keys (uses default router from settings)
    # Settings will have None for API keys, triggering stub mode
    client = LLMClient()
    
    # Create test snapshot
    snapshot = create_mock_snapshot()
    
    # Test all methods work without API keys
    try:
        summary = await client.generate_summary(snapshot)
        assert isinstance(summary, AISummary)
        assert summary.health_score >= 0.0
        
        recommendations = await client.generate_recommendations(snapshot)
        assert isinstance(recommendations, list)
        
        action_plan = await client.generate_action_plan(snapshot)
        assert isinstance(action_plan, AIActionPlan)
        
    except Exception as e:
        pytest.fail(f"LLMClient failed without API keys: {e}")


# ==================== TEST 5: Real Clients Use Correct Models ====================

def test_real_clients_use_correct_models():
    """
    Test 5: Real GPT5Client and GeminiClient use configured models.
    
    Verifies:
    - GPT5Client stores correct model name
    - GeminiClient stores correct model name
    - API keys are stored (even if None)
    - Mode parameter controls behavior
    """
    # Test GPT5Client in stub mode
    gpt5 = GPT5Client(api_key="test-key", model="gpt-4", mode="stub")
    assert gpt5.api_key == "test-key"
    assert gpt5.model == "gpt-4"
    assert gpt5.mode == "stub"
    assert gpt5.client is None  # Stub mode
    
    # Test GeminiClient in stub mode
    gemini = GeminiClient(api_key="test-key-2", model="gemini-2.0-pro", mode="stub")
    assert gemini.api_key == "test-key-2"
    assert gemini.model == "gemini-2.0-pro"
    assert gemini.mode == "stub"
    assert gemini.client is None  # Stub mode
    
    # Test without API keys
    gpt5_no_key = GPT5Client(api_key=None, model="gpt-4", mode="stub")
    assert gpt5_no_key.api_key is None
    assert gpt5_no_key.model == "gpt-4"
    
    gemini_no_key = GeminiClient(api_key=None, model="gemini-2.0-pro", mode="stub")
    assert gemini_no_key.api_key is None
    assert gemini_no_key.model == "gemini-2.0-pro"


# ==================== TEST 6: create_default_llm_router Function ====================

def test_create_default_llm_router():
    """
    Test 6: create_default_llm_router creates valid router from settings.
    
    Verifies:
    - Function returns DualLLMRouter instance
    - Router has gemini and gpt5 clients
    - Clients are correctly typed
    """
    from app.core.config import settings
    
    router = create_default_llm_router(settings)
    
    assert isinstance(router, DualLLMRouter)
    assert isinstance(router.gemini, GeminiClient)
    assert isinstance(router.gpt5, GPT5Client)
    
    # Verify clients have correct models from settings
    assert router.gpt5.model == settings.AI_OPENAI_MODEL_NAME
    assert router.gemini.model == settings.AI_GEMINI_MODEL_NAME


# ==================== TEST 7: Router Method Names Are Descriptive ====================

def test_router_method_names():
    """
    Test 7: Router provides descriptive method names.
    
    Verifies:
    - for_critical_short() method exists
    - for_long_context() method exists
    - Methods return correct client types
    """
    fake_gpt5 = FakeGPT5Client()
    fake_gemini = FakeGeminiClient()
    router = DualLLMRouter(gemini_client=fake_gemini, gpt5_client=fake_gpt5)
    
    # Check method existence
    assert hasattr(router, "for_critical_short")
    assert hasattr(router, "for_long_context")
    
    # Check they're callable
    assert callable(router.for_critical_short)
    assert callable(router.for_long_context)
    
    # Check return types
    assert router.for_critical_short() is fake_gpt5
    assert router.for_long_context() is fake_gemini
