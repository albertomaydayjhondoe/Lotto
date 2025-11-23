"""
Serializers for Dashboard AI Integration.

Converts AIReasoningOutput to compact formats optimized for frontend consumption.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime

from app.ai_global_worker.schemas import (
    AIReasoningOutput,
    AISummary,
    AIRecommendation,
    AIActionPlan
)


def serialize_ai_reasoning_compact(reasoning: AIReasoningOutput) -> Dict[str, Any]:
    """
    Serialize AIReasoningOutput to compact format for frontend.
    
    Returns a lightweight version with all essential data but optimized
    for network transfer and frontend rendering.
    """
    return {
        "reasoning_id": reasoning.reasoning_id,
        "timestamp": reasoning.timestamp.isoformat(),
        "execution_time_ms": reasoning.execution_time_ms,
        "summary": serialize_summary(reasoning.summary),
        "recommendations": [serialize_recommendation(r) for r in reasoning.recommendations],
        "action_plan": serialize_action_plan(reasoning.action_plan),
        "snapshot": serialize_snapshot_minimal(reasoning.snapshot)
    }


def serialize_summary(summary: AISummary) -> Dict[str, Any]:
    """Serialize AISummary to frontend format."""
    return {
        "overall_health": summary.overall_health,
        "health_score": summary.health_score,
        "content_health": summary.content_health,
        "publishing_health": summary.publishing_health,
        "opportunities": summary.opportunities,
        "risks": summary.risks,
        "top_priority": summary.top_priority
    }


def serialize_recommendation(rec: AIRecommendation) -> Dict[str, Any]:
    """Serialize AIRecommendation to frontend format."""
    return {
        "category": rec.category,
        "priority": rec.priority,
        "title": rec.title,
        "description": rec.description,
        "impact": rec.impact,
        "effort": rec.effort,
        "reasoning": rec.reasoning
    }


def serialize_action_plan(plan: AIActionPlan) -> Dict[str, Any]:
    """Serialize AIActionPlan to frontend format."""
    return {
        "objective": plan.objective,
        "steps": plan.steps,
        "estimated_duration": plan.estimated_duration,
        "risk_level": plan.risk_level,
        "automated": plan.automated
    }


def serialize_snapshot_minimal(snapshot: Any) -> Dict[str, Any]:
    """
    Serialize SystemSnapshot to minimal format.
    
    Only includes key metrics needed for dashboard context.
    """
    return {
        "timestamp": snapshot.timestamp.isoformat() if hasattr(snapshot, 'timestamp') else None,
        "clips_ready": snapshot.clips_ready if hasattr(snapshot, 'clips_ready') else 0,
        "clips_pending_analysis": snapshot.clips_pending_analysis if hasattr(snapshot, 'clips_pending_analysis') else 0,
        "jobs_pending": snapshot.jobs_pending if hasattr(snapshot, 'jobs_pending') else 0,
        "jobs_failed": snapshot.jobs_failed if hasattr(snapshot, 'jobs_failed') else 0,
        "campaigns_active": snapshot.campaigns_active if hasattr(snapshot, 'campaigns_active') else 0,
        "campaigns_draft": snapshot.campaigns_draft if hasattr(snapshot, 'campaigns_draft') else 0
    }
