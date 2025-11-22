"""
AI Reasoning Engine.

Orchestrates LLM client to generate complete AI reasoning output.
"""

import time
import uuid
from datetime import datetime

from app.ai_global_worker.schemas import (
    SystemSnapshot,
    AIReasoningOutput
)
from app.ai_global_worker.llm_client import LLMClient


# Global LLM client instance
_llm_client = LLMClient()


async def run_full_reasoning(snapshot: SystemSnapshot) -> AIReasoningOutput:
    """
    Run complete AI reasoning cycle.
    
    Generates:
    1. System summary with health assessment
    2. Prioritized recommendations
    3. Executable action plan
    
    Args:
        snapshot: System snapshot to analyze
        
    Returns:
        Complete AIReasoningOutput
    """
    start_time = time.time()
    
    # Generate all AI outputs
    summary = await _llm_client.generate_summary(snapshot)
    recommendations = await _llm_client.generate_recommendations(snapshot)
    action_plan = await _llm_client.generate_action_plan(snapshot)
    
    # Calculate execution time
    execution_time_ms = int((time.time() - start_time) * 1000)
    
    # Build complete output
    return AIReasoningOutput(
        reasoning_id=str(uuid.uuid4()),
        timestamp=datetime.utcnow(),
        snapshot=snapshot,
        summary=summary,
        recommendations=recommendations,
        action_plan=action_plan,
        execution_time_ms=execution_time_ms
    )
