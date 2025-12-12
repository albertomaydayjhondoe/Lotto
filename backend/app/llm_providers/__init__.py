"""
LLM Providers Module - Dual Router Architecture (PASO 7.3)

This module provides a dual LLM routing system that intelligently
selects between GPT (OpenAI) and Gemini 2.0 (Google) based on
task characteristics:

- GPT: Short, critical tasks (recommendations, action plans)
- Gemini 2.0: Long context, less critical tasks (summaries)

Implementation: Supports both LIVE and STUB modes
- LIVE mode: Real API calls with fallback to stub on errors
- STUB mode: Deterministic heuristics-based responses
"""

from app.llm_providers.router import DualLLMRouter
from app.llm_providers.gpt5_client import GPT5Client
from app.llm_providers.gemini_client import GeminiClient

__all__ = [
    "DualLLMRouter",
    "GPT5Client",
    "GeminiClient",
    "create_default_llm_router",
]


def create_default_llm_router(settings) -> DualLLMRouter:
    """
    Create a DualLLMRouter instance with default configuration.
    
    Reads API keys, model names, and operation mode from settings.
    
    Args:
        settings: Application settings instance with LLM configuration
        
    Returns:
        DualLLMRouter instance configured with GPT and Gemini clients
        
    Configuration (from settings):
        - AI_LLM_MODE: "live" or "stub" (default: "stub")
        - OPENAI_API_KEY: OpenAI API key (optional)
        - AI_OPENAI_MODEL_NAME: Model identifier (default: "gpt-4")
        - GEMINI_API_KEY: Google Gemini API key (optional)
        - AI_GEMINI_MODEL_NAME: Model identifier (default: "gemini-2.0-flash-exp")
    
    Behavior:
        - If AI_LLM_MODE="live" and API keys present → real API calls
        - If AI_LLM_MODE="stub" or missing keys → stub mode
        - Automatic fallback to stub on API errors
    """
    # Create GPT client
    gpt5_client = GPT5Client(
        api_key=settings.OPENAI_API_KEY,
        model=settings.AI_OPENAI_MODEL_NAME,
        mode=settings.AI_LLM_MODE,
    )
    
    # Create Gemini client
    gemini_client = GeminiClient(
        api_key=settings.GEMINI_API_KEY,
        model=settings.AI_GEMINI_MODEL_NAME,
        mode=settings.AI_LLM_MODE,
    )
    
    # Create and return router
    return DualLLMRouter(
        gemini_client=gemini_client,
        gpt5_client=gpt5_client,
    )
