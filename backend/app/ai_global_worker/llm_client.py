"""
LLM Client for AI Global Worker - PASO 7.2 with Dual Router Architecture.

This module now uses a dual-router approach:
- GPT-5 (OpenAI) for critical, short tasks
- Gemini 2.0 (Google) for long context, less critical tasks

The public API remains unchanged to maintain backward compatibility.
Internal implementation delegates to appropriate LLM based on task type.

Routing Policy:
---------------
- generate_summary() → Gemini 2.0 (long context, comprehensive analysis)
- generate_recommendations() → GPT-5 (critical, prioritized decisions)
- generate_action_plan() → GPT-5 (critical execution planning)
"""

from typing import List, TYPE_CHECKING

from app.ai_global_worker.schemas import (
    SystemSnapshot,
    AISummary,
    AIRecommendation,
    AIActionPlan
)

# Avoid circular import by using TYPE_CHECKING
if TYPE_CHECKING:
    from app.llm_providers import DualLLMRouter


class LLMClient:
    """
    LLM client for generating AI insights using dual-router architecture.
    
    Architecture (PASO 7.2):
    ------------------------
    Internally uses DualLLMRouter to distribute work between:
    - GPT-5: Critical short tasks (recommendations, action plans)
    - Gemini 2.0: Long context tasks (summaries)
    
    Public API (Preserved for Backward Compatibility):
    --------------------------------------------------
    - generate_summary(snapshot) → AISummary
    - generate_recommendations(snapshot) → List[AIRecommendation]
    - generate_action_plan(snapshot) → AIActionPlan
    
    Current Status:
    ---------------
    - PASO 7.2: Dual router architecture in STUB mode
    - All clients operate without real API calls
    - Future PASO 7.3: Activate real OpenAI + Gemini APIs
    
    Usage:
    ------
    client = LLMClient()
    summary = await client.generate_summary(snapshot)  # Uses Gemini
    recs = await client.generate_recommendations(snapshot)  # Uses GPT-5
    plan = await client.generate_action_plan(snapshot)  # Uses GPT-5
    """
    
    def __init__(self, router: "DualLLMRouter" = None):
        """
        Initialize LLM client with dual router.
        
        Args:
            router: Optional DualLLMRouter instance. If None, creates default
                    router from settings (recommended for production use).
        
        Note:
            Custom router parameter allows dependency injection for testing.
        """
        if router is None:
            # Lazy import to avoid circular dependency
            from app.llm_providers import create_default_llm_router
            from app.core.config import settings
            
            # Create default router from settings
            self.router = create_default_llm_router(settings)
        else:
            # Use provided router (useful for testing)
            self.router = router
    
    async def generate_summary(self, snapshot: SystemSnapshot) -> AISummary:
        """
        Generate comprehensive system health summary.
        
        Routing: Uses Gemini 2.0 (long context, less critical)
        
        Gemini 2.0 is optimal for:
        - Comprehensive health assessments
        - Long-form narrative analysis
        - Broad context understanding
        - Cost-effective for detailed summaries
        
        Args:
            snapshot: Complete system state snapshot
            
        Returns:
            AISummary: Comprehensive health assessment with detailed insights
        
        Implementation:
        ---------------
        Delegates to router.for_long_context() which returns GeminiClient.
        GeminiClient.generate_summary() currently operates in stub mode.
        Real API integration will be activated in PASO 7.3.
        """
        # Route to Gemini 2.0 for long context task
        gemini_client = self.router.for_long_context()
        return await gemini_client.generate_summary(snapshot)
    
    async def generate_recommendations(self, snapshot: SystemSnapshot) -> List[AIRecommendation]:
        """
        Generate prioritized, actionable recommendations.
        
        Routing: Uses GPT-5 (critical, short)
        
        GPT-5 is optimal for:
        - Critical decision-making
        - High-impact prioritization
        - Precise, actionable recommendations
        - Short, focused outputs
        
        Args:
            snapshot: Complete system state snapshot
            
        Returns:
            List[AIRecommendation]: Prioritized recommendations (1-5 items)
        
        Implementation:
        ---------------
        Delegates to router.for_critical_short() which returns GPT5Client.
        GPT5Client.generate_recommendations() currently operates in stub mode.
        Real API integration will be activated in PASO 7.3.
        """
        # Route to GPT-5 for critical short task
        gpt5_client = self.router.for_critical_short()
        return await gpt5_client.generate_recommendations(snapshot)
    
    async def generate_action_plan(self, snapshot: SystemSnapshot) -> AIActionPlan:
        """
        Generate executable action plan with ordered steps.
        
        Routing: Uses GPT-5 (critical, short)
        
        GPT-5 is optimal for:
        - Critical execution planning
        - Risk assessment
        - Precise step ordering
        - Automation capability analysis
        
        Args:
            snapshot: Complete system state snapshot
            
        Returns:
            AIActionPlan: Ordered steps with risk assessment and automation info
        
        Implementation:
        ---------------
        Delegates to router.for_critical_short() which returns GPT5Client.
        GPT5Client.generate_action_plan() currently operates in stub mode.
        
        Note:
        -----
        Action plan generation may use previously generated recommendations
        as context. In future PASO 7.3, we can pass recommendations to
        generate_action_plan() for better coherence.
        """
        # Route to GPT-5 for critical short task
        gpt5_client = self.router.for_critical_short()
        
        # First get recommendations for context
        recommendations = await self.generate_recommendations(snapshot)
        
        # Generate action plan based on snapshot and recommendations
        return await gpt5_client.generate_action_plan(snapshot, recommendations)
