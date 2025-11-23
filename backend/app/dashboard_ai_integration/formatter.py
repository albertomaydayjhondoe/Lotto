"""
Formatters for Dashboard AI Integration.

Generates derived data formats for frontend consumption:
- ai_health_card: Health score card summary
- ai_recommendations_cards: Summarized recommendation list
- ai_actions_summary: Action plan overview
"""

from typing import Dict, Any, List
from app.ai_global_worker.schemas import AIReasoningOutput, AISummary, AIRecommendation, AIActionPlan


def generate_health_card(reasoning: AIReasoningOutput) -> Dict[str, Any]:
    """
    Generate health card summary.
    
    Returns:
        {
            "score": 0-100,
            "status": "critical" | "warning" | "healthy",
            "status_label": "Critical" | "Warning" | "Healthy",
            "top_issue": str,
            "color": "red" | "yellow" | "green"
        }
    """
    summary = reasoning.summary
    score = summary.health_score
    
    # Determine status
    if score < 40:
        status = "critical"
        status_label = "Critical"
        color = "red"
    elif score < 70:
        status = "warning"
        status_label = "Warning"
        color = "yellow"
    else:
        status = "healthy"
        status_label = "Healthy"
        color = "green"
    
    # Get top issue from concerns
    top_issue = summary.concerns[0] if summary.concerns else "No issues detected"
    
    return {
        "score": score,
        "status": status,
        "status_label": status_label,
        "top_issue": top_issue,
        "color": color,
        "overall_health": summary.overall_health
    }


def generate_recommendations_cards(reasoning: AIReasoningOutput) -> List[Dict[str, Any]]:
    """
    Generate summarized recommendations list.
    
    Returns list of recommendations with:
        - category
        - priority
        - title
        - description (truncated)
        - impact
        - effort
        - badge_color (based on priority)
    """
    cards = []
    
    for rec in reasoning.recommendations:
        # Determine badge color based on priority
        if rec.priority == "critical":
            badge_color = "red"
        elif rec.priority == "high":
            badge_color = "orange"
        elif rec.priority == "medium":
            badge_color = "yellow"
        else:
            badge_color = "blue"
        
        # Truncate description for card view
        description = rec.description
        if len(description) > 150:
            description = description[:147] + "..."
        
        cards.append({
            "category": rec.category,
            "priority": rec.priority,
            "title": rec.title,
            "description": description,
            "full_description": rec.description,
            "impact": rec.impact,
            "effort": rec.effort,
            "badge_color": badge_color
        })
    
    return cards


def generate_actions_summary(reasoning: AIReasoningOutput) -> Dict[str, Any]:
    """
    Generate action plan summary overview.
    
    Returns:
        {
            "total_steps": int,
            "estimated_duration": str,
            "risk_level": str,
            "automated": bool,
            "objective": str,
            "risk_badge_color": str
        }
    """
    plan = reasoning.action_plan
    
    # Determine risk badge color
    if plan.risk_level == "high":
        risk_badge_color = "red"
    elif plan.risk_level == "medium":
        risk_badge_color = "yellow"
    else:
        risk_badge_color = "green"
    
    return {
        "total_steps": len(plan.steps),
        "estimated_duration": plan.estimated_duration,
        "risk_level": plan.risk_level,
        "automated": plan.automated,
        "objective": plan.objective,
        "risk_badge_color": risk_badge_color,
        "steps": plan.steps
    }


def generate_full_dashboard_response(reasoning: AIReasoningOutput) -> Dict[str, Any]:
    """
    Generate complete dashboard response with all formatted sections.
    
    This is the primary function used by the /dashboard/ai/last endpoint.
    """
    return {
        "reasoning_id": reasoning.reasoning_id,
        "timestamp": reasoning.timestamp.isoformat(),
        "execution_time_ms": reasoning.execution_time_ms,
        "health_card": generate_health_card(reasoning),
        "recommendations_cards": generate_recommendations_cards(reasoning),
        "actions_summary": generate_actions_summary(reasoning),
        "raw": {
            "summary": {
                "overall_health": reasoning.summary.overall_health,
                "health_score": reasoning.summary.health_score,
                "key_insights": reasoning.summary.key_insights,
                "concerns": reasoning.summary.concerns,
                "positives": reasoning.summary.positives
            },
            "snapshot": {
                "clips_ready": reasoning.snapshot.clips_ready,
                "clips_pending_analysis": reasoning.snapshot.clips_pending_analysis,
                "jobs_pending": reasoning.snapshot.jobs_pending,
                "jobs_failed": reasoning.snapshot.jobs_failed,
                "campaigns_active": reasoning.snapshot.campaigns_active,
                "campaigns_draft": reasoning.snapshot.campaigns_draft
            }
        }
    }
