"""
Router para Meta Full Autonomous Cycle (PASO 10.11)
"""
import logging
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.auth.permissions import require_role
from app.meta_full_cycle.cycle import MetaFullCycleManager
from app.meta_full_cycle.models import MetaCycleRunModel, MetaCycleActionLogModel
from app.core.config import settings


logger = logging.getLogger(__name__)
router = APIRouter()


# ==================== Schemas ====================


class CycleRunResponse(BaseModel):
    """Response para un cycle run"""
    id: str
    started_at: str
    finished_at: Optional[str]
    duration_ms: Optional[int]
    status: str
    steps_executed: List[str]
    errors: List[dict]
    stats_snapshot: dict
    triggered_by: Optional[str]
    mode: str
    
    class Config:
        from_attributes = True


class CycleActionLogResponse(BaseModel):
    """Response para un action log"""
    id: int
    cycle_run_id: str
    step: str
    action: str
    input_snapshot: Optional[dict]
    output_snapshot: Optional[dict]
    success: bool
    error_message: Optional[str]
    entity_type: Optional[str]
    entity_id: Optional[str]
    created_at: str
    
    class Config:
        from_attributes = True


class RunCycleRequest(BaseModel):
    """Request para ejecutar ciclo manual"""
    mode: Optional[str] = Field(None, description="Modo: 'stub' o 'live'. Default: settings.META_API_MODE")


class RunCycleResponse(BaseModel):
    """Response de ejecución de ciclo"""
    cycle_run_id: str
    status: str
    duration_ms: Optional[int]
    stats_snapshot: dict
    message: str


class DebugStepRequest(BaseModel):
    """Request para ejecutar un step individual (debug)"""
    step: str = Field(..., description="Step a ejecutar: 'collection', 'decisions', 'api_actions', 'finalize'")
    mode: Optional[str] = Field(None, description="Modo: 'stub' o 'live'")


# ==================== Endpoints ====================


@router.post("/run", response_model=RunCycleResponse)
async def run_cycle_manual(
    request: RunCycleRequest = RunCycleRequest(),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role(["admin", "manager"]))
):
    """
    Ejecuta el ciclo autónomo completo manualmente.
    
    **RBAC:** admin, manager
    
    **Flujo:**
    1. Recolección de datos
    2. Decisiones automáticas
    3. Acciones en Meta API
    4. Logging
    
    **Mode:**
    - `stub`: Simulado (no hace llamadas reales a Meta)
    - `live`: Real (requiere credenciales Meta válidas)
    """
    try:
        logger.info(f"🔄 Manual cycle triggered by user {current_user.get('username')}")
        
        mode = request.mode or settings.META_API_MODE
        
        cycle_manager = MetaFullCycleManager()
        cycle_run = await cycle_manager.run_cycle(
            db=db,
            triggered_by=f"manual:{current_user.get('username')}",
            mode=mode,
        )
        
        return RunCycleResponse(
            cycle_run_id=str(cycle_run.id),
            status=cycle_run.status,
            duration_ms=cycle_run.duration_ms,
            stats_snapshot=cycle_run.stats_snapshot,
            message=f"Cycle executed successfully in {cycle_run.duration_ms}ms" if cycle_run.status == "success" else "Cycle failed",
        )
        
    except Exception as e:
        logger.error(f"Error running manual cycle: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/last", response_model=CycleRunResponse)
async def get_last_cycle(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role(["admin", "manager"]))
):
    """
    Obtiene el último ciclo ejecutado con su snapshot completo.
    
    **RBAC:** admin, manager
    
    **Returns:**
    - Cycle run completo con stats, steps, errors
    """
    try:
        result = await db.execute(
            select(MetaCycleRunModel)
            .order_by(desc(MetaCycleRunModel.started_at))
            .limit(1)
        )
        cycle_run = result.scalar_one_or_none()
        
        if not cycle_run:
            raise HTTPException(status_code=404, detail="No cycle runs found")
        
        return CycleRunResponse(
            id=str(cycle_run.id),
            started_at=cycle_run.started_at.isoformat(),
            finished_at=cycle_run.finished_at.isoformat() if cycle_run.finished_at else None,
            duration_ms=cycle_run.duration_ms,
            status=cycle_run.status,
            steps_executed=cycle_run.steps_executed or [],
            errors=cycle_run.errors or [],
            stats_snapshot=cycle_run.stats_snapshot or {},
            triggered_by=cycle_run.triggered_by,
            mode=cycle_run.mode,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting last cycle: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/log/{cycle_run_id}", response_model=List[CycleActionLogResponse])
async def get_cycle_logs(
    cycle_run_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role(["admin", "manager"]))
):
    """
    Devuelve todos los logs de acciones de un ciclo específico.
    
    **RBAC:** admin, manager
    
    **Args:**
    - cycle_run_id: UUID del cycle run
    
    **Returns:**
    - Lista de action logs con detalles de cada acción/decisión
    """
    try:
        result = await db.execute(
            select(MetaCycleActionLogModel)
            .where(MetaCycleActionLogModel.cycle_run_id == cycle_run_id)
            .order_by(MetaCycleActionLogModel.created_at)
        )
        logs = result.scalars().all()
        
        if not logs:
            raise HTTPException(status_code=404, detail=f"No logs found for cycle {cycle_run_id}")
        
        return [
            CycleActionLogResponse(
                id=log.id,
                cycle_run_id=str(log.cycle_run_id),
                step=log.step,
                action=log.action,
                input_snapshot=log.input_snapshot,
                output_snapshot=log.output_snapshot,
                success=log.success,
                error_message=log.error_message,
                entity_type=log.entity_type,
                entity_id=log.entity_id,
                created_at=log.created_at.isoformat(),
            )
            for log in logs
        ]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting cycle logs: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history", response_model=List[CycleRunResponse])
async def get_cycle_history(
    limit: int = Query(50, ge=1, le=500, description="Número de ciclos a retornar"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role(["admin", "manager"]))
):
    """
    Lista los últimos N ciclos ejecutados.
    
    **RBAC:** admin, manager
    
    **Args:**
    - limit: Número de ciclos (default: 50, max: 500)
    
    **Returns:**
    - Lista de cycle runs ordenados por fecha (más reciente primero)
    """
    try:
        result = await db.execute(
            select(MetaCycleRunModel)
            .order_by(desc(MetaCycleRunModel.started_at))
            .limit(limit)
        )
        cycles = result.scalars().all()
        
        return [
            CycleRunResponse(
                id=str(cycle.id),
                started_at=cycle.started_at.isoformat(),
                finished_at=cycle.finished_at.isoformat() if cycle.finished_at else None,
                duration_ms=cycle.duration_ms,
                status=cycle.status,
                steps_executed=cycle.steps_executed or [],
                errors=cycle.errors or [],
                stats_snapshot=cycle.stats_snapshot or {},
                triggered_by=cycle.triggered_by,
                mode=cycle.mode,
            )
            for cycle in cycles
        ]
        
    except Exception as e:
        logger.error(f"Error getting cycle history: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/debug/step")
async def debug_execute_step(
    request: DebugStepRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role(["admin"]))
):
    """
    Ejecuta un step individual del ciclo (solo para debugging).
    
    **RBAC:** admin only
    
    **Steps disponibles:**
    - `collection`: Solo recolección de datos
    - `decisions`: Solo decisiones automáticas
    - `api_actions`: Solo acciones API
    - `finalize`: Solo finalización
    
    ⚠️ **Warning:** Este endpoint es solo para testing/debugging.
    No ejecuta el ciclo completo.
    """
    try:
        logger.info(f"🐛 Debug step '{request.step}' triggered by {current_user.get('username')}")
        
        # TODO: Implement individual step execution
        # For now, return stub response
        
        return {
            "success": True,
            "step": request.step,
            "mode": request.mode or "stub",
            "message": f"Debug step '{request.step}' executed (TODO: implement individual step execution)",
        }
        
    except Exception as e:
        logger.error(f"Error in debug step: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """
    Health check del módulo Meta Full Cycle.
    
    **Public endpoint** (no requiere auth)
    """
    return {
        "status": "healthy",
        "module": "meta_full_cycle",
        "mode": settings.META_API_MODE or "stub",
        "scheduler_interval_minutes": 30,
    }
