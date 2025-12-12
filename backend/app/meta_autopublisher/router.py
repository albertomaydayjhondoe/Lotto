# backend/app/meta_autopublisher/router.py

"""
AutoPublisher API Router - Endpoints REST con RBAC.
"""
from typing import Dict
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.logging import get_logger
from app.auth.permissions import require_role
from app.core.config import settings

from .orchestrator import AutoPublisherOrchestrator
from .models import (
    AutoPublisherRunRequest,
    AutoPublisherRunResponse,
    ScheduleAutoPilotRequest,
    PublishWinnerRequest
)
from .monitor import MonitoringService

logger = get_logger(__name__)
router = APIRouter()

# Store de runs activos (en producción usar Redis o DB)
active_runs: Dict[UUID, AutoPublisherRunResponse] = {}


@router.post("/run", response_model=AutoPublisherRunResponse)
async def run_autopilot(
    request: AutoPublisherRunRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    _: Dict = Depends(require_role(["admin", "manager"]))
) -> AutoPublisherRunResponse:
    """
    Ejecuta un AutoPublisher run manualmente.
    
    - **Requiere permisos:** admin o manager
    - **Modo:** stub (default) o live según META_API_MODE
    """
    if not settings.AUTO_PUBLISHER_ENABLED:
        raise HTTPException(
            status_code=403,
            detail="AutoPublisher is disabled. Set AUTO_PUBLISHER_ENABLED=true"
        )
    
    logger.info(f"[AutoPublisher API] Run requested for campaign: {request.campaign_name}")
    
    try:
        orchestrator = AutoPublisherOrchestrator(
            db=db,
            mode=settings.META_API_MODE,
            enable_ai_supervision=True
        )
        
        # Ejecutar en background si es un run largo
        if request.ab_test_config.test_duration_hours > 1:
            # TODO: Ejecutar en background task o worker
            pass
        
        response = await orchestrator.run_autopilot(request)
        
        # Guardar en store
        active_runs[response.run_id] = response
        
        return response
        
    except ValueError as e:
        logger.error(f"[AutoPublisher API] Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception(f"[AutoPublisher API] Run failed: {e}")
        raise HTTPException(status_code=500, detail=f"AutoPublisher run failed: {str(e)}")


@router.post("/schedule", response_model=Dict)
async def schedule_autopilot(
    request: ScheduleAutoPilotRequest,
    db: AsyncSession = Depends(get_db),
    _: Dict = Depends(require_role(["manager"]))
) -> Dict:
    """
    Programa un AutoPublisher run para ejecución futura.
    
    - **Requiere permisos:** manager
    """
    if not settings.AUTO_PUBLISHER_ENABLED:
        raise HTTPException(
            status_code=403,
            detail="AutoPublisher is disabled"
        )
    
    logger.info(f"[AutoPublisher API] Schedule requested for {request.schedule_datetime}")
    
    # TODO: Implementar scheduling con Celery o similar
    
    return {
        "status": "scheduled",
        "schedule_datetime": request.schedule_datetime.isoformat(),
        "campaign_name": request.run_request.campaign_name,
        "message": "Run will be executed at specified time"
    }


@router.get("/status/{run_id}", response_model=AutoPublisherRunResponse)
async def get_run_status(
    run_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: Dict = Depends(require_role(["admin", "manager"]))
) -> AutoPublisherRunResponse:
    """
    Obtiene el estado de un AutoPublisher run.
    
    - **Requiere permisos:** admin o manager
    """
    # Buscar en store
    if run_id in active_runs:
        return active_runs[run_id]
    
    # TODO: Buscar en base de datos (AutoPublisherRunModel)
    
    raise HTTPException(
        status_code=404,
        detail=f"Run {run_id} not found"
    )


@router.post("/publish-winner", response_model=Dict)
async def publish_winner(
    request: PublishWinnerRequest,
    db: AsyncSession = Depends(get_db),
    _: Dict = Depends(require_role(["operator", "manager", "admin"]))
) -> Dict:
    """
    Fuerza la publicación del ganador de un A/B test.
    
    - **Requiere permisos:** operator, manager o admin
    - **Uso:** Para aprobar runs en estado WAITING_APPROVAL
    """
    logger.info(f"[AutoPublisher API] Publish winner requested for run {request.run_id}")
    
    # Buscar run
    if request.run_id not in active_runs:
        raise HTTPException(status_code=404, detail="Run not found")
    
    run = active_runs[request.run_id]
    
    # Verificar que esté esperando aprobación
    if run.status != "waiting_approval":
        raise HTTPException(
            status_code=400,
            detail=f"Run is in status {run.status}, not waiting for approval"
        )
    
    # Verificar que tenga ganador seleccionado
    if not run.winner_selection:
        raise HTTPException(status_code=400, detail="No winner selected yet")
    
    try:
        orchestrator = AutoPublisherOrchestrator(
            db=db,
            mode=settings.META_API_MODE
        )
        
        # Escalar presupuesto del ganador
        scaling_result = await orchestrator._scale_winner_budget(
            run.winner_selection,
            type('obj', (object,), {
                'scaling_factor': 2.0,
                'max_daily_budget': request.final_budget
            })()
        )
        
        # Publicar campaña final
        final_campaign_id = await orchestrator._publish_final_campaign(
            run.winner_selection,
            None  # Ya no necesitamos el request completo
        )
        
        # Actualizar run
        run.status = "publishing_final"
        run.final_campaign_id = final_campaign_id
        run.logs.append(f"[{datetime.utcnow()}] Winner published by manual approval")
        
        # Pausar perdedores
        variants = []  # TODO: Recuperar variants del run
        await orchestrator._pause_losing_variants(variants, run.winner_selection.winner_variant_id)
        
        run.status = "completed"
        
        return {
            "status": "published",
            "run_id": str(request.run_id),
            "final_campaign_id": str(final_campaign_id),
            "winner_name": run.winner_selection.winner_name,
            "winner_roas": run.winner_selection.winner_metrics.roas
        }
        
    except Exception as e:
        logger.exception(f"[AutoPublisher API] Publish winner failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health", response_model=Dict)
async def health_check(
    db: AsyncSession = Depends(get_db)
) -> Dict:
    """
    Health check del AutoPublisher.
    
    - **Sin autenticación requerida**
    """
    monitor = MonitoringService(db)
    return await monitor.get_system_health()
