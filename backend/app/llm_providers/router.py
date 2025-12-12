"""
Dual LLM Router (PASO 7.2)

Routes LLM requests to the appropriate model based on task characteristics:
- GPT-5: Short, critical tasks
- Gemini 2.0: Long context, less critical tasks

This router does NOT make HTTP calls directly - it delegates to client classes.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.llm_providers.gpt5_client import GPT5Client
    from app.llm_providers.gemini_client import GeminiClient


class DualLLMRouter:
    """
    Routes LLM requests between GPT-5 and Gemini 2.0 based on task type.
    
    Routing Policy:
    ---------------
    GPT-5 (OpenAI) → SHORT + CRITICAL:
        - Important system decisions
        - High-impact recommendations
        - Action plans
        - Critical orchestrator diagnostics
    
    Gemini 2.0 (Google) → LONG + LESS CRITICAL:
        - Long summaries
        - Extended reports
        - Long explanations / general narrative
        - Broad context analysis
    
    Usage:
    ------
    router = DualLLMRouter(gemini_client, gpt5_client)
    
    # For critical short tasks (recommendations, action plan)
    gpt5 = router.for_critical_short()
    recommendations = await gpt5.generate_recommendations(snapshot)
    
    # For long context tasks (summary)
    gemini = router.for_long_context()
    summary = await gemini.generate_summary(snapshot)
    """
    
    def __init__(
        self,
        gemini_client: "GeminiClient",
        gpt5_client: "GPT5Client",
    ):
        """
        Initialize router with both LLM clients.
        
        Args:
            gemini_client: Gemini 2.0 client instance
            gpt5_client: GPT-5 client instance
        """
        self.gemini = gemini_client
        self.gpt5 = gpt5_client
    
    def for_critical_short(self) -> "GPT5Client":
        """
        Get LLM client for critical, short tasks.
        
        Use cases:
        - generate_recommendations() → High-impact, prioritized actions
        - generate_action_plan() → Critical execution steps
        - Quick diagnostic decisions
        
        Returns:
            GPT5Client: Client optimized for critical short tasks
        """
        return self.gpt5
    
    def for_long_context(self) -> "GeminiClient":
        """
        Get LLM client for long context, less critical tasks.
        
        Use cases:
        - generate_summary() → Comprehensive system health overview
        - Long-form reports
        - Extended narrative explanations
        - Broad context analysis
        
        Returns:
            GeminiClient: Client optimized for long context tasks
        """
        return self.gemini
