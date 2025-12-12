"""
SPRINT 13 - Human Observability & Cognitive Dashboard
Module: Observability API

FastAPI router que expone el sistema completo de BirthFlow, warmup, riesgo y estado.

REGLAS:
- NO ejecuta acciones (solo lectura)
- Real-time o near real-time (< 3s)
- Toda acción humana auditada
- Integración con Sprint 12/12.1
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, Field

from app.account_birthflow import (
    AccountBirthFlowStateMachine,
    AccountState,
    AccountWarmupMetrics,
    AccountRiskProfile,
    HumanWarmupScheduler,
    HumanActionVerifier,
    WarmupToAutonomyBridge,
    get_audit_logger,
    OrchestratorBirthFlowBridge,
)

logger = logging.getLogger(__name__)

# ============================================================================
# ROUTER SETUP
# ============================================================================

router = APIRouter(
    prefix="/observability",
    tags=["observability"],
    responses={404: {"description": "Not found"}},
)


# ============================================================================
# RESPONSE MODELS
# ============================================================================

class AccountStateResponse(BaseModel):
    """Account state snapshot"""
    account_id: str
    current_state: str
    created_at: str
    state_duration_days: int
    next_state: Optional[str] = None
    can_advance: bool
    blockers: List[str] = Field(default_factory=list)
    metadata: Dict = Field(default_factory=dict)


class AccountMetricsResponse(BaseModel):
    """Account metrics snapshot"""
    account_id: str
    maturity_score: float
    risk_score: float
    readiness_level: float
    total_actions: int
    action_diversity: float
    impressions: int = 0
    blocks: int = 0
    comments: int = 0
    timestamp: str


class AccountRiskResponse(BaseModel):
    """Account risk snapshot"""
    account_id: str
    total_risk_score: float
    shadowban_risk: float
    correlation_risk: float
    behavioral_risk: float
    risk_level: str
    signals: List[str] = Field(default_factory=list)
    last_check: str


class AccountReadinessResponse(BaseModel):
    """Account autonomy readiness"""
    account_id: str
    readiness_score: float  # 0-1
    can_transition_to_secured: bool
    requirements_met: Dict[str, bool]
    blockers: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    estimated_days_remaining: int


class HumanWarmupTaskResponse(BaseModel):
    """Human warmup task"""
    task_id: str
    account_id: str
    warmup_day: int
    warmup_phase: str
    status: str
    required_actions: List[Dict]
    deadline: Optional[str] = None
    created_at: str
    completed_at: Optional[str] = None


class LifecycleEventResponse(BaseModel):
    """Lifecycle event"""
    event_id: str
    account_id: str
    event_type: str
    previous_state: Optional[str] = None
    new_state: Optional[str] = None
    reason: str
    risk_snapshot: Dict = Field(default_factory=dict)
    timestamp: str


class OrchestratorPermissionsResponse(BaseModel):
    """Orchestrator permissions for account"""
    account_id: str
    state: str
    allowed_actions: List[str]
    daily_limits: Dict[str, int]
    cooldowns: Dict[str, int]
    flags: Dict[str, bool]
    risk_level: str
    can_automate: bool


class GlobalRiskResponse(BaseModel):
    """Global system risk"""
    total_accounts: int
    accounts_at_risk: int
    avg_risk_score: float
    shadowban_signals: int
    recent_rollbacks: int
    high_risk_accounts: List[str]
    timestamp: str


class SystemHealthResponse(BaseModel):
    """System health metrics"""
    total_accounts: int
    accounts_by_state: Dict[str, int]
    accounts_secured: int
    accounts_active: int
    accounts_blocked: int
    pending_human_tasks: int
    verification_pass_rate: float
    avg_maturity_score: float
    timestamp: str


# ============================================================================
# DEPENDENCIES
# ============================================================================

def get_birthflow_machine() -> AccountBirthFlowStateMachine:
    """Get BirthFlow state machine instance"""
    return AccountBirthFlowStateMachine()


def get_warmup_scheduler() -> HumanWarmupScheduler:
    """Get warmup scheduler instance"""
    return HumanWarmupScheduler()


def get_action_verifier() -> HumanActionVerifier:
    """Get action verifier instance"""
    return HumanActionVerifier()


def get_autonomy_bridge() -> WarmupToAutonomyBridge:
    """Get autonomy bridge instance"""
    return WarmupToAutonomyBridge()


def get_orchestrator_bridge() -> OrchestratorBirthFlowBridge:
    """Get orchestrator bridge instance"""
    from app.account_birthflow import create_orchestrator_bridge
    return create_orchestrator_bridge()


# ============================================================================
# ENDPOINTS - ACCOUNT STATE & METRICS
# ============================================================================

@router.get("/accounts/{account_id}/state", response_model=AccountStateResponse)
async def get_account_state(
    account_id: str,
    machine: AccountBirthFlowStateMachine = Depends(get_birthflow_machine)
):
    """
    Get current account state.
    
    Returns:
    - Current state
    - Time in state
    - Next possible state
    - Blockers preventing advancement
    """
    try:
        account = machine.get_account(account_id)
        if not account:
            raise HTTPException(status_code=404, detail="Account not found")
        
        # Calculate state duration
        duration = (datetime.now() - account.created_at).days
        
        # Determine next state
        next_state = None
        can_advance = False
        blockers = []
        
        current_state = account.current_state
        
        if current_state == AccountState.CREATED:
            next_state = "W1_3"
            can_advance = True
        elif current_state == AccountState.W1_3:
            next_state = "W4_7"
            # Check if ready to advance
            if duration >= 3:
                can_advance = True
            else:
                blockers.append(f"Need {3 - duration} more days")
        elif current_state == AccountState.W4_7:
            next_state = "W8_14"
            if duration >= 7:
                can_advance = True
            else:
                blockers.append(f"Need {7 - duration} more days")
        elif current_state == AccountState.W8_14:
            next_state = "SECURED"
            # Check autonomy readiness (complex)
            blockers.append("Check /readiness for full validation")
        elif current_state == AccountState.SECURED:
            next_state = "ACTIVE"
            can_advance = True
        
        return AccountStateResponse(
            account_id=account_id,
            current_state=current_state.value,
            created_at=account.created_at.isoformat(),
            state_duration_days=duration,
            next_state=next_state,
            can_advance=can_advance,
            blockers=blockers,
            metadata={
                "platform": account.platform.value if account.platform else None,
                "proxy_ip": account.proxy_ip,
                "last_action_at": account.last_action_at.isoformat() if account.last_action_at else None,
            }
        )
    
    except Exception as e:
        logger.error(f"Error getting state for {account_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/accounts/{account_id}/metrics", response_model=AccountMetricsResponse)
async def get_account_metrics(
    account_id: str,
    machine: AccountBirthFlowStateMachine = Depends(get_birthflow_machine)
):
    """
    Get account metrics (maturity, risk, readiness).
    """
    try:
        metrics = machine.get_metrics(account_id)
        if not metrics:
            raise HTTPException(status_code=404, detail="Metrics not found")
        
        return AccountMetricsResponse(
            account_id=account_id,
            maturity_score=metrics.maturity_score,
            risk_score=metrics.risk_score,
            readiness_level=metrics.readiness_level,
            total_actions=metrics.total_actions,
            action_diversity=metrics.action_diversity,
            impressions=0,  # TODO: integrate with real metrics
            blocks=0,
            comments=0,
            timestamp=datetime.now().isoformat()
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting metrics for {account_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/accounts/{account_id}/risk", response_model=AccountRiskResponse)
async def get_account_risk(
    account_id: str,
    machine: AccountBirthFlowStateMachine = Depends(get_birthflow_machine)
):
    """
    Get account risk profile.
    """
    try:
        risk_profile = machine.get_risk_profile(account_id)
        if not risk_profile:
            raise HTTPException(status_code=404, detail="Risk profile not found")
        
        # Collect risk signals
        signals = []
        if risk_profile.shadowban_risk > 0.30:
            signals.append("High shadowban risk")
        if risk_profile.correlation_risk > 0.35:
            signals.append("Correlation detected")
        if risk_profile.behavioral_risk > 0.40:
            signals.append("Behavioral anomalies")
        if risk_profile.total_risk_score > 0.50:
            signals.append("CRITICAL: Total risk high")
        
        return AccountRiskResponse(
            account_id=account_id,
            total_risk_score=risk_profile.total_risk_score,
            shadowban_risk=risk_profile.shadowban_risk,
            correlation_risk=risk_profile.correlation_risk,
            behavioral_risk=risk_profile.behavioral_risk,
            risk_level=risk_profile.risk_level.value,
            signals=signals,
            last_check=datetime.now().isoformat()
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting risk for {account_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/accounts/{account_id}/readiness", response_model=AccountReadinessResponse)
async def get_account_readiness(
    account_id: str,
    machine: AccountBirthFlowStateMachine = Depends(get_birthflow_machine),
    bridge: WarmupToAutonomyBridge = Depends(get_autonomy_bridge),
    verifier: HumanActionVerifier = Depends(get_action_verifier)
):
    """
    Get account autonomy readiness (can transition to SECURED).
    """
    try:
        account = machine.get_account(account_id)
        if not account:
            raise HTTPException(status_code=404, detail="Account not found")
        
        metrics = machine.get_metrics(account_id)
        risk_profile = machine.get_risk_profile(account_id)
        
        # Get verification history
        verification_history = verifier.get_verification_history(account_id)
        
        # Calculate task completion rate
        passed = len([v for v in verification_history if v.verification_passed])
        total = len(verification_history)
        task_completion_rate = passed / total if total > 0 else 0.0
        
        # Evaluate readiness
        decision = bridge.evaluate_transition_readiness(
            account=account,
            metrics=metrics,
            risk_profile=risk_profile,
            verification_history=verification_history,
            task_completion_rate=task_completion_rate
        )
        
        # Calculate readiness score
        readiness_score = sum(decision.requirements_met.values()) / len(decision.requirements_met)
        
        return AccountReadinessResponse(
            account_id=account_id,
            readiness_score=readiness_score,
            can_transition_to_secured=decision.can_transition,
            requirements_met=decision.requirements_met,
            blockers=decision.blockers,
            recommendations=decision.recommendations,
            estimated_days_remaining=decision.estimated_days_remaining
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting readiness for {account_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# ENDPOINTS - WARMUP HUMAN TASKS
# ============================================================================

@router.get("/warmup/human/tasks/today", response_model=List[HumanWarmupTaskResponse])
async def get_today_human_tasks(
    scheduler: HumanWarmupScheduler = Depends(get_warmup_scheduler)
):
    """
    Get all human warmup tasks for today (all accounts).
    """
    try:
        # Get all pending tasks
        all_tasks = []
        
        # TODO: Should iterate over all accounts in warmup
        # For now, return pending tasks from scheduler
        for account_id, tasks in scheduler._tasks.items():
            for task in tasks:
                if task.status == "pending":
                    all_tasks.append(HumanWarmupTaskResponse(
                        task_id=task.task_id,
                        account_id=task.account_id,
                        warmup_day=task.warmup_day,
                        warmup_phase=task.warmup_phase.value,
                        status=task.status,
                        required_actions=[action.to_dict() for action in task.required_actions],
                        deadline=task.verification_deadline.isoformat() if task.verification_deadline else None,
                        created_at=task.created_at.isoformat(),
                        completed_at=task.completed_at.isoformat() if task.completed_at else None
                    ))
        
        return all_tasks
    
    except Exception as e:
        logger.error(f"Error getting today tasks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/warmup/human/submit/{task_id}")
async def submit_human_task(
    task_id: str,
    session_data: Dict,
    scheduler: HumanWarmupScheduler = Depends(get_warmup_scheduler),
    verifier: HumanActionVerifier = Depends(get_action_verifier)
):
    """
    Submit completed human warmup task.
    
    Body:
    {
        "session_start": "2025-12-12T10:00:00Z",
        "session_end": "2025-12-12T10:05:30Z",
        "actions": [
            {"type": "scroll", "timestamp": "...", "duration_seconds": 180},
            {"type": "like", "timestamp": "..."}
        ]
    }
    """
    try:
        # Get task
        task = scheduler.get_task(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        if task.status != "pending":
            raise HTTPException(status_code=400, detail=f"Task already {task.status}")
        
        # Parse session data
        session_start = datetime.fromisoformat(session_data["session_start"].replace("Z", "+00:00"))
        session_end = datetime.fromisoformat(session_data["session_end"].replace("Z", "+00:00"))
        actions = session_data["actions"]
        
        # Verify completion
        result = verifier.verify_task_completion(
            account_id=task.account_id,
            task_id=task_id,
            session_start=session_start,
            session_end=session_end,
            actions=actions
        )
        
        # Mark task completed/failed
        if result.verification_passed:
            scheduler.mark_task_completed(task_id, result.to_dict())
            
            # Log to audit
            audit_logger = get_audit_logger()
            audit_logger.log_event(
                account_id=task.account_id,
                event_type="human_warmup_task_completed",
                state=task.warmup_phase,
                action_details={
                    "task_id": task_id,
                    "warmup_day": task.warmup_day,
                    "time_spent": result.time_spent_seconds,
                    "actions": result.detected_actions,
                    "risk_adjustment": result.risk_adjustment
                },
                risk_updates={"behavioral_risk": result.risk_adjustment},
                metadata={"verification_result": "passed"}
            )
            
            return {
                "success": True,
                "message": "Task completed successfully",
                "verification_result": result.to_dict()
            }
        else:
            scheduler.mark_task_failed(task_id, result.issues)
            
            # Log failure
            audit_logger = get_audit_logger()
            audit_logger.log_event(
                account_id=task.account_id,
                event_type="human_warmup_task_failed",
                state=task.warmup_phase,
                action_details={
                    "task_id": task_id,
                    "warmup_day": task.warmup_day,
                    "issues": result.issues,
                    "risk_adjustment": result.risk_adjustment
                },
                risk_updates={"behavioral_risk": result.risk_adjustment},
                metadata={"verification_result": "failed"}
            )
            
            return {
                "success": False,
                "message": "Task verification failed",
                "verification_result": result.to_dict()
            }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting task {task_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/warmup/human/history/{account_id}", response_model=List[Dict])
async def get_warmup_history(
    account_id: str,
    limit: int = Query(30, ge=1, le=100),
    verifier: HumanActionVerifier = Depends(get_action_verifier)
):
    """
    Get warmup verification history for account.
    """
    try:
        history = verifier.get_verification_history(account_id, limit=limit)
        
        return [result.to_dict() for result in history]
    
    except Exception as e:
        logger.error(f"Error getting warmup history for {account_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# ENDPOINTS - LIFECYCLE & AUDIT
# ============================================================================

@router.get("/accounts/{account_id}/lifecycle_log", response_model=List[LifecycleEventResponse])
async def get_lifecycle_log(
    account_id: str,
    limit: int = Query(50, ge=1, le=200)
):
    """
    Get complete lifecycle log for account.
    """
    try:
        audit_logger = get_audit_logger()
        
        # Read audit log
        events = audit_logger.read_logs(account_id=account_id, limit=limit)
        
        # Convert to response format
        lifecycle_events = []
        for event in events:
            lifecycle_events.append(LifecycleEventResponse(
                event_id=event.event_id,
                account_id=event.account_id,
                event_type=event.event_type,
                previous_state=event.previous_state.value if event.previous_state else None,
                new_state=event.new_state.value if event.new_state else None,
                reason=event.reason or "",
                risk_snapshot=event.risk_updates or {},
                timestamp=event.timestamp.isoformat()
            ))
        
        return lifecycle_events
    
    except Exception as e:
        logger.error(f"Error getting lifecycle log for {account_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/audit/events")
async def get_audit_events(
    limit: int = Query(100, ge=1, le=500),
    event_type: Optional[str] = None,
    account_id: Optional[str] = None
):
    """
    Get recent audit events (all accounts).
    """
    try:
        audit_logger = get_audit_logger()
        
        # Read audit log
        events = audit_logger.read_logs(
            account_id=account_id,
            event_type=event_type,
            limit=limit
        )
        
        # Convert to dict format
        return [
            {
                "event_id": event.event_id,
                "account_id": event.account_id,
                "event_type": event.event_type,
                "state": event.new_state.value if event.new_state else None,
                "reason": event.reason,
                "timestamp": event.timestamp.isoformat()
            }
            for event in events
        ]
    
    except Exception as e:
        logger.error(f"Error getting audit events: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# ENDPOINTS - ORCHESTRATOR INTEGRATION
# ============================================================================

@router.get("/orchestrator/permissions/{account_id}", response_model=OrchestratorPermissionsResponse)
async def get_orchestrator_permissions(
    account_id: str,
    machine: AccountBirthFlowStateMachine = Depends(get_birthflow_machine),
    bridge: OrchestratorBirthFlowBridge = Depends(get_orchestrator_bridge)
):
    """
    Get orchestrator permissions for account.
    
    Returns:
    - Allowed actions
    - Daily limits by action type
    - Cooldowns
    - Risk flags
    """
    try:
        account = machine.get_account(account_id)
        if not account:
            raise HTTPException(status_code=404, detail="Account not found")
        
        risk_profile = machine.get_risk_profile(account_id)
        
        # Get limits
        limits_response = bridge.get_action_limits(account_id)
        
        # Determine allowed actions
        from app.account_birthflow import ActionType, can_automate
        
        allowed_actions = []
        if can_automate(account.current_state):
            # Check each action type
            for action_type in ActionType:
                can_execute, reason = bridge.can_execute_action(account_id, action_type)
                if can_execute:
                    allowed_actions.append(action_type.value)
        
        # Build flags
        flags = {
            "can_automate": can_automate(account.current_state),
            "requires_human": not can_automate(account.current_state),
            "high_risk": risk_profile.total_risk_score > 0.50,
            "shadowban_detected": risk_profile.shadowban_risk > 0.40,
            "correlation_detected": risk_profile.correlation_risk > 0.40,
            "fingerprint_stable": True,  # TODO: implement
            "proxy_healthy": True,  # TODO: implement
        }
        
        return OrchestratorPermissionsResponse(
            account_id=account_id,
            state=account.current_state.value,
            allowed_actions=allowed_actions,
            daily_limits=limits_response.limits,
            cooldowns={},  # TODO: implement cooldown tracking
            flags=flags,
            risk_level=risk_profile.risk_level.value,
            can_automate=flags["can_automate"]
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting orchestrator permissions for {account_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# ENDPOINTS - GLOBAL OBSERVABILITY
# ============================================================================

@router.get("/global_risk", response_model=GlobalRiskResponse)
async def get_global_risk(
    machine: AccountBirthFlowStateMachine = Depends(get_birthflow_machine)
):
    """
    Get global system risk metrics.
    """
    try:
        # Get all accounts
        all_accounts = list(machine._accounts.values())
        
        if not all_accounts:
            return GlobalRiskResponse(
                total_accounts=0,
                accounts_at_risk=0,
                avg_risk_score=0.0,
                shadowban_signals=0,
                recent_rollbacks=0,
                high_risk_accounts=[],
                timestamp=datetime.now().isoformat()
            )
        
        # Calculate metrics
        total_risk = 0.0
        accounts_at_risk = 0
        shadowban_signals = 0
        high_risk_accounts = []
        
        for account in all_accounts:
            risk_profile = machine.get_risk_profile(account.account_id)
            if risk_profile:
                total_risk += risk_profile.total_risk_score
                
                if risk_profile.total_risk_score > 0.50:
                    accounts_at_risk += 1
                    high_risk_accounts.append(account.account_id)
                
                if risk_profile.shadowban_risk > 0.40:
                    shadowban_signals += 1
        
        avg_risk = total_risk / len(all_accounts)
        
        # Count recent rollbacks (from audit log)
        audit_logger = get_audit_logger()
        recent_events = audit_logger.read_logs(limit=100)
        recent_rollbacks = len([
            e for e in recent_events 
            if e.event_type == "state_rollback" 
            and (datetime.now() - e.timestamp).days <= 7
        ])
        
        return GlobalRiskResponse(
            total_accounts=len(all_accounts),
            accounts_at_risk=accounts_at_risk,
            avg_risk_score=avg_risk,
            shadowban_signals=shadowban_signals,
            recent_rollbacks=recent_rollbacks,
            high_risk_accounts=high_risk_accounts[:10],  # Top 10
            timestamp=datetime.now().isoformat()
        )
    
    except Exception as e:
        logger.error(f"Error getting global risk: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/system_health", response_model=SystemHealthResponse)
async def get_system_health(
    machine: AccountBirthFlowStateMachine = Depends(get_birthflow_machine),
    scheduler: HumanWarmupScheduler = Depends(get_warmup_scheduler),
    verifier: HumanActionVerifier = Depends(get_action_verifier)
):
    """
    Get system health metrics.
    """
    try:
        all_accounts = list(machine._accounts.values())
        
        if not all_accounts:
            return SystemHealthResponse(
                total_accounts=0,
                accounts_by_state={},
                accounts_secured=0,
                accounts_active=0,
                accounts_blocked=0,
                pending_human_tasks=0,
                verification_pass_rate=0.0,
                avg_maturity_score=0.0,
                timestamp=datetime.now().isoformat()
            )
        
        # Count by state
        accounts_by_state = {}
        accounts_secured = 0
        accounts_active = 0
        accounts_blocked = 0
        total_maturity = 0.0
        
        for account in all_accounts:
            state_name = account.current_state.value
            accounts_by_state[state_name] = accounts_by_state.get(state_name, 0) + 1
            
            if account.current_state == AccountState.SECURED:
                accounts_secured += 1
            elif account.current_state == AccountState.ACTIVE:
                accounts_active += 1
            elif account.current_state == AccountState.BLOCKED:
                accounts_blocked += 1
            
            metrics = machine.get_metrics(account.account_id)
            if metrics:
                total_maturity += metrics.maturity_score
        
        # Count pending human tasks
        pending_human_tasks = 0
        for tasks in scheduler._tasks.values():
            pending_human_tasks += len([t for t in tasks if t.status == "pending"])
        
        # Calculate verification pass rate
        all_verifications = []
        for history in verifier.verification_history.values():
            all_verifications.extend(history)
        
        if all_verifications:
            passed = len([v for v in all_verifications if v.verification_passed])
            verification_pass_rate = passed / len(all_verifications)
        else:
            verification_pass_rate = 0.0
        
        avg_maturity = total_maturity / len(all_accounts) if all_accounts else 0.0
        
        return SystemHealthResponse(
            total_accounts=len(all_accounts),
            accounts_by_state=accounts_by_state,
            accounts_secured=accounts_secured,
            accounts_active=accounts_active,
            accounts_blocked=accounts_blocked,
            pending_human_tasks=pending_human_tasks,
            verification_pass_rate=verification_pass_rate,
            avg_maturity_score=avg_maturity,
            timestamp=datetime.now().isoformat()
        )
    
    except Exception as e:
        logger.error(f"Error getting system health: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/shadowban_signals")
async def get_shadowban_signals(
    machine: AccountBirthFlowStateMachine = Depends(get_birthflow_machine)
):
    """
    Get shadowban detection signals across all accounts.
    """
    try:
        all_accounts = list(machine._accounts.values())
        
        signals = []
        
        for account in all_accounts:
            risk_profile = machine.get_risk_profile(account.account_id)
            if risk_profile and risk_profile.shadowban_risk > 0.30:
                signals.append({
                    "account_id": account.account_id,
                    "shadowban_risk": risk_profile.shadowban_risk,
                    "state": account.current_state.value,
                    "detected_at": datetime.now().isoformat(),
                    "severity": "critical" if risk_profile.shadowban_risk > 0.60 else "high" if risk_profile.shadowban_risk > 0.40 else "medium"
                })
        
        return {
            "total_signals": len(signals),
            "signals": sorted(signals, key=lambda x: x["shadowban_risk"], reverse=True),
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error getting shadowban signals: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# HEALTH CHECK
# ============================================================================

@router.get("/health")
async def health_check():
    """
    API health check.
    """
    return {
        "status": "healthy",
        "service": "observability_api",
        "timestamp": datetime.now().isoformat()
    }


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    "router",
    "AccountStateResponse",
    "AccountMetricsResponse",
    "AccountRiskResponse",
    "AccountReadinessResponse",
    "HumanWarmupTaskResponse",
    "LifecycleEventResponse",
    "OrchestratorPermissionsResponse",
    "GlobalRiskResponse",
    "SystemHealthResponse",
]
