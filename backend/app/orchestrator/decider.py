"""
Orchestrator Decider - Decision Making Engine
Analyzes system snapshot and decides actions to take
"""
from typing import Dict, Any, List
from datetime import datetime


class OrchestratorAction:
    """Represents an action to be executed"""
    
    def __init__(self, action_type: str, params: Dict[str, Any], priority: int = 5, reason: str = ""):
        self.action_type = action_type
        self.params = params
        self.priority = priority  # 1-10, higher = more urgent
        self.reason = reason
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "action_type": self.action_type,
            "params": self.params,
            "priority": self.priority,
            "reason": self.reason
        }


def decide_actions(snapshot: Dict[str, Any]) -> List[OrchestratorAction]:
    """
    Analyze system snapshot and decide what actions to take
    
    Action types:
    - schedule_clip: Schedule a high-score clip
    - retry_failed_log: Retry a failed publication
    - trigger_reconciliation: Run reconciliation process
    - promote_high_score_clip: Promote clip with high visual score
    - downgrade_low_score_clip: Deprioritize low-score clip
    - force_publish: Force immediate publication
    - rebalance_queue: Rebalance job queue
    
    Heuristics based on:
    - Last activity time
    - Average clip scores
    - Queue saturation
    - Active campaigns
    - Publishing windows
    - Recent errors in ledger
    """
    
    actions = []
    
    # 1. Handle failed publications
    actions.extend(_handle_failed_publications(snapshot))
    
    # 2. Handle high-score clips
    actions.extend(_handle_high_score_clips(snapshot))
    
    # 3. Handle queue saturation
    actions.extend(_handle_queue_saturation(snapshot))
    
    # 4. Handle publishing windows
    actions.extend(_handle_publishing_windows(snapshot))
    
    # 5. Handle campaigns
    actions.extend(_handle_campaigns(snapshot))
    
    # 6. Handle reconciliation
    actions.extend(_handle_reconciliation(snapshot))
    
    # 7. Handle system health
    actions.extend(_handle_system_health(snapshot))
    
    # Sort by priority (highest first)
    actions.sort(key=lambda a: a.priority, reverse=True)
    
    return actions


def _handle_failed_publications(snapshot: Dict[str, Any]) -> List[OrchestratorAction]:
    """Handle failed publication logs"""
    actions = []
    
    publish_logs = snapshot.get("publish_logs", {})
    
    # If we have failures, trigger retry
    if publish_logs.get("has_failures", False):
        failed_count = publish_logs.get("failed", 0)
        recent_failures = publish_logs.get("recent_failures_1h", 0)
        
        if recent_failures > 0:
            # Recent failures need immediate attention
            actions.append(OrchestratorAction(
                action_type="retry_failed_log",
                params={"max_retries": 3},
                priority=8,
                reason=f"Detected {recent_failures} recent failures in last hour"
            ))
        elif failed_count > 5:
            # Too many old failures, trigger reconciliation
            actions.append(OrchestratorAction(
                action_type="trigger_reconciliation",
                params={"reason": "too_many_failures"},
                priority=6,
                reason=f"High failure count: {failed_count}"
            ))
    
    return actions


def _handle_high_score_clips(snapshot: Dict[str, Any]) -> List[OrchestratorAction]:
    """Handle high-performing clips"""
    actions = []
    
    clips = snapshot.get("clips", {})
    scheduler = snapshot.get("scheduler", {})
    
    # If we have high-score clips and we're in a publishing window
    if clips.get("has_high_score_clips", False):
        high_score_count = clips.get("high_score_count_24h", 0)
        any_window_active = scheduler.get("any_window_active", False)
        
        if any_window_active and high_score_count > 0:
            # Promote high-score clips during active windows
            actions.append(OrchestratorAction(
                action_type="promote_high_score_clip",
                params={
                    "min_visual_score": 80,
                    "platform": "auto"  # Let APIL decide
                },
                priority=7,
                reason=f"Found {high_score_count} high-score clips and window is active"
            ))
        elif high_score_count > 3:
            # Many high-score clips waiting, schedule even outside window
            actions.append(OrchestratorAction(
                action_type="schedule_clip",
                params={
                    "min_visual_score": 85,
                    "use_intelligence": True
                },
                priority=6,
                reason=f"Accumulation of {high_score_count} high-score clips"
            ))
    
    # Check average score
    avg_score = clips.get("avg_visual_score", 0)
    if avg_score < 40:
        # Low average quality, downgrade low performers
        actions.append(OrchestratorAction(
            action_type="downgrade_low_score_clip",
            params={"max_visual_score": 30},
            priority=3,
            reason=f"Low average visual score: {avg_score:.1f}"
        ))
    
    return actions


def _handle_queue_saturation(snapshot: Dict[str, Any]) -> List[OrchestratorAction]:
    """Handle job queue saturation"""
    actions = []
    
    jobs = snapshot.get("jobs", {})
    
    if jobs.get("queue_saturated", False):
        pending_count = jobs.get("pending", 0)
        
        # Queue is saturated, rebalance
        actions.append(OrchestratorAction(
            action_type="rebalance_queue",
            params={
                "pending_count": pending_count,
                "strategy": "priority"
            },
            priority=9,
            reason=f"Queue saturated with {pending_count} pending jobs"
        ))
    
    # Check for old pending jobs
    oldest_age = jobs.get("oldest_pending_age_minutes")
    if oldest_age and oldest_age > 60:
        # Jobs stuck for over 1 hour
        actions.append(OrchestratorAction(
            action_type="force_publish",
            params={"age_threshold_minutes": 60},
            priority=8,
            reason=f"Jobs stuck for {oldest_age:.0f} minutes"
        ))
    
    return actions


def _handle_publishing_windows(snapshot: Dict[str, Any]) -> List[OrchestratorAction]:
    """Handle publishing windows optimization"""
    actions = []
    
    scheduler = snapshot.get("scheduler", {})
    publish_logs = snapshot.get("publish_logs", {})
    
    any_window_active = scheduler.get("any_window_active", False)
    scheduled_due_soon = scheduler.get("scheduled_due_soon_1h", 0)
    pending_count = publish_logs.get("pending", 0)
    
    # If window is active and we have pending logs, accelerate
    if any_window_active and pending_count > 0:
        actions.append(OrchestratorAction(
            action_type="force_publish",
            params={
                "reason": "active_window",
                "limit": min(pending_count, 5)
            },
            priority=7,
            reason=f"Window active, {pending_count} pending publications"
        ))
    
    # If window is closing soon and scheduled posts are waiting
    current_hour = scheduler.get("current_hour", 0)
    windows = scheduler.get("windows", {})
    
    for platform, window_info in windows.items():
        if window_info.get("active") and window_info.get("end") - current_hour <= 1:
            # Window closing in 1 hour
            if scheduled_due_soon > 0:
                actions.append(OrchestratorAction(
                    action_type="schedule_clip",
                    params={
                        "platform": platform,
                        "urgency": "high"
                    },
                    priority=8,
                    reason=f"{platform} window closing soon, {scheduled_due_soon} posts due"
                ))
    
    return actions


def _handle_campaigns(snapshot: Dict[str, Any]) -> List[OrchestratorAction]:
    """Handle active campaigns"""
    actions = []
    
    campaigns = snapshot.get("campaigns", {})
    
    if campaigns.get("has_active_campaigns", False):
        active_count = campaigns.get("active_count", 0)
        campaigns_list = campaigns.get("campaigns", [])
        
        # For each active campaign, check if clip needs scheduling
        for campaign in campaigns_list:
            clip_id = campaign.get("clip_id")
            budget = campaign.get("budget_cents", 0)
            
            if clip_id and budget > 10000:  # Budget > $100
                # High-budget campaign, prioritize
                actions.append(OrchestratorAction(
                    action_type="schedule_clip",
                    params={
                        "clip_id": clip_id,
                        "campaign_id": campaign.get("id"),
                        "use_intelligence": True
                    },
                    priority=9,
                    reason=f"High-budget campaign: ${budget/100:.0f}"
                ))
    
    return actions


def _handle_reconciliation(snapshot: Dict[str, Any]) -> List[OrchestratorAction]:
    """Handle reconciliation needs"""
    actions = []
    
    publish_logs = snapshot.get("publish_logs", {})
    ledger = snapshot.get("ledger", {})
    
    # Trigger reconciliation if we have errors or mismatches
    if ledger.get("has_errors", False):
        error_count = ledger.get("errors_1h", 0)
        
        if error_count > 5:
            actions.append(OrchestratorAction(
                action_type="trigger_reconciliation",
                params={"reason": "high_error_count"},
                priority=7,
                reason=f"{error_count} errors in last hour"
            ))
    
    # Periodic reconciliation for published logs
    published_count = publish_logs.get("published", 0)
    if published_count > 10:
        # Run reconciliation every N published items
        actions.append(OrchestratorAction(
            action_type="trigger_reconciliation",
            params={"reason": "periodic_check"},
            priority=3,
            reason="Periodic reconciliation check"
        ))
    
    return actions


def _handle_system_health(snapshot: Dict[str, Any]) -> List[OrchestratorAction]:
    """Handle overall system health"""
    actions = []
    
    system = snapshot.get("system", {})
    
    if system.get("requires_attention", False):
        health_score = system.get("health_score", 100)
        health_status = system.get("health_status", "healthy")
        recommendations = system.get("recommendations", [])
        
        if health_status == "critical":
            # Critical health, trigger emergency actions
            actions.append(OrchestratorAction(
                action_type="rebalance_queue",
                params={"emergency": True},
                priority=10,
                reason=f"Critical system health: {health_score}"
            ))
        
        # Add actions based on recommendations
        for recommendation in recommendations:
            if "publishing failures" in recommendation.lower():
                actions.append(OrchestratorAction(
                    action_type="retry_failed_log",
                    params={"force": True},
                    priority=8,
                    reason=recommendation
                ))
            elif "error logs" in recommendation.lower():
                actions.append(OrchestratorAction(
                    action_type="trigger_reconciliation",
                    params={"reason": "error_investigation"},
                    priority=7,
                    reason=recommendation
                ))
    
    return actions


def summarize_decisions(actions: List[OrchestratorAction]) -> Dict[str, Any]:
    """Summarize decisions for logging"""
    
    if not actions:
        return {
            "total_actions": 0,
            "decision": "no_action_needed",
            "summary": "System is healthy, no actions required"
        }
    
    # Count by action type
    action_counts = {}
    for action in actions:
        action_type = action.action_type
        action_counts[action_type] = action_counts.get(action_type, 0) + 1
    
    # Get highest priority action
    top_action = actions[0] if actions else None
    
    return {
        "total_actions": len(actions),
        "decision": "execute_actions",
        "action_counts": action_counts,
        "top_priority": {
            "action_type": top_action.action_type,
            "priority": top_action.priority,
            "reason": top_action.reason
        } if top_action else None,
        "summary": f"{len(actions)} actions decided, top priority: {top_action.action_type if top_action else 'none'}"
    }
