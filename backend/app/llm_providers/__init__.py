"""
LLM Providers Module - Dual Router Architecture (PASO 7.2)

This module provides a dual LLM routing system that intelligently
selects between GPT-5 (OpenAI) and Gemini 2.0 (Google) based on
task characteristics:

- GPT-5: Short, critical tasks (recommendations, action plans)
- Gemini 2.0: Long context, less critical tasks (summaries)

Current implementation: STUB mode (no real API calls)
Future: PASO 7.3 will activate real API integrations
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
    
    Reads API keys and model names from settings (environment variables).
    
    Args:
        settings: Application settings instance with LLM configuration
        
    Returns:
        DualLLMRouter instance configured with GPT-5 and Gemini clients
        
    Configuration (from settings):
        - OPENAI_API_KEY: OpenAI API key (optional, None = stub mode)
        - OPENAI_GPT5_MODEL: Model identifier (default: "gpt-5.1")
        - GEMINI_API_KEY: Google Gemini API key (optional, None = stub mode)
        - GEMINI_MODEL: Model identifier (default: "gemini-2.0-pro")
    
    Note:
        Current implementation works in STUB mode even with API keys.
        Real API calls will be activated in PASO 7.3.
    """
    # Create GPT-5 client
    gpt5_client = GPT5Client(
        api_key=settings.OPENAI_API_KEY,
        model=settings.OPENAI_GPT5_MODEL,
    )
    
    # Create Gemini client
    gemini_client = GeminiClient(
        api_key=settings.GEMINI_API_KEY,
        model=settings.GEMINI_MODEL,
    )
    
    # Create and return router
    return DualLLMRouter(
        gemini_client=gemini_client,
        gpt5_client=gpt5_client,
    )
