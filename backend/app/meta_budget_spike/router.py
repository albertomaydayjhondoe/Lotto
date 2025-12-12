"""
Router FastAPI para Meta Budget SPIKE Manager.
Endpoints REST con RBAC.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.auth.permissions import require_role
from app.core.database import get_db
from app.meta_budget_spike.models import (
    AutoRunRequest,
    AutoRunResponse,
    BudgetScaleRequest,
    BudgetScaleResponse,
    MetaBudgetSpikeLogModel,
    SpikeDetectionResult,
    SpikeLogResponse,
)
from app.meta_budget_spike.scaler import BudgetScaler
from app.meta_budget_spike.scheduler import run_auto_spike_detection
from app.meta_budget_spike.spike_detector import SpikeDetector

router = APIRouter()


@router.post(
    "/detect",
    response_model=SpikeDetectionResult,
    summary="Detectar spike en un adset",
    dependencies=[Depends(require_role(["admin", "manager"]))],
)
async def detect_spike(
    adset_id: str = Query(..., description="ID del adset a analizar"),
    campaign_id: str | None = Query(None, description="ID de la campaña (opcional)"),
    db: Session = Depends(get_db),
):
    """
    Fuerza una detección manual de spike en un adset específico.
    
    **Requiere rol:** admin o manager
    
    **Proceso:**
    1. Obtiene métricas actuales e históricas
    2. Calcula Z-Scores y percentiles
    3. Clasifica spike (positive/negative/risk)
    4. Recomienda acción de escalado
    
    **Returns:**
    - Resultado completo de detección con métricas, scores y recomendación
    """
    
    detector = SpikeDetector(db)
    
    try:
        result = await detector.detect_spike(
            adset_id=adset_id,
            campaign_id=campaign_id,
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error detectando spike: {str(e)}",
        )


@router.post(
    "/scale/{adset_id}",
    response_model=BudgetScaleResponse,
    summary="Escalar presupuesto de un adset",
    dependencies=[Depends(require_role(["admin"]))],
)
async def scale_budget(
    adset_id: str,
    request: BudgetScaleRequest,
    db: Session = Depends(get_db),
):
    """
    Aplica escalado de presupuesto en un adset.
    
    **Requiere rol:** admin
    
    **Proceso:**
    1. Obtiene presupuesto actual
    2. Calcula nuevo presupuesto según acción
    3. Aplica límites de seguridad
    4. Actualiza en Meta API
    5. Persiste en DB
    
    **Acciones disponibles:**
    - `scale_up_10`, `scale_up_20`, `scale_up_30`, `scale_up_50`
    - `maintain`
    - `scale_down_10`, `scale_down_20`, `scale_down_40`
    - `pause`
    
    **Returns:**
    - Resultado del escalado con presupuestos old/new
    """
    
    if request.adset_id != adset_id:
        raise HTTPException(
            status_code=400,
            detail="adset_id en path y body no coinciden",
        )
    
    scaler = BudgetScaler(db)
    
    try:
        result = await scaler.scale_budget(request=request)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error escalando presupuesto: {str(e)}",
        )


@router.get(
    "/log",
    response_model=list[SpikeLogResponse],
    summary="Listar logs de spikes",
    dependencies=[Depends(require_role(["admin", "manager"]))],
)
async def get_spike_logs(
    adset_id: str | None = Query(None, description="Filtrar por adset_id"),
    campaign_id: str | None = Query(None, description="Filtrar por campaign_id"),
    spike_type: str | None = Query(None, description="Filtrar por tipo (positive/negative/risk)"),
    limit: int = Query(50, ge=1, le=500, description="Límite de resultados"),
    offset: int = Query(0, ge=0, description="Offset para paginación"),
    db: Session = Depends(get_db),
):
    """
    Lista logs históricos de spikes detectados y escalados.
    
    **Requiere rol:** admin o manager
    
    **Filtros disponibles:**
    - `adset_id`: Filtrar por adset específico
    - `campaign_id`: Filtrar por campaña específica
    - `spike_type`: Filtrar por tipo (positive, negative, risk)
    - `limit`: Número máximo de resultados (default: 50)
    - `offset`: Offset para paginación (default: 0)
    
    **Returns:**
    - Lista de logs con métricas, scores y estado de aplicación
    """
    
    query = db.query(MetaBudgetSpikeLogModel)
    
    # Aplicar filtros
    if adset_id:
        query = query.filter(MetaBudgetSpikeLogModel.adset_id == adset_id)
    if campaign_id:
        query = query.filter(MetaBudgetSpikeLogModel.campaign_id == campaign_id)
    if spike_type:
        query = query.filter(MetaBudgetSpikeLogModel.spike_type == spike_type)
    
    # Ordenar por más reciente
    query = query.order_by(MetaBudgetSpikeLogModel.created_at.desc())
    
    # Paginación
    query = query.offset(offset).limit(limit)
    
    logs = query.all()
    
    return [SpikeLogResponse.from_orm(log) for log in logs]


@router.get(
    "/log/{log_id}",
    response_model=SpikeLogResponse,
    summary="Obtener detalle de un log",
    dependencies=[Depends(require_role(["admin", "manager"]))],
)
async def get_spike_log_detail(
    log_id: int,
    db: Session = Depends(get_db),
):
    """
    Obtiene detalle completo de un log de spike específico.
    
    **Requiere rol:** admin o manager
    
    **Returns:**
    - Log completo con métricas snapshot, scores y resultado
    """
    
    log = db.query(MetaBudgetSpikeLogModel).filter(
        MetaBudgetSpikeLogModel.id == log_id
    ).first()
    
    if not log:
        raise HTTPException(
            status_code=404,
            detail=f"Log {log_id} no encontrado",
        )
    
    return SpikeLogResponse.from_orm(log)


@router.post(
    "/auto-run",
    response_model=AutoRunResponse,
    summary="Ejecución automática completa",
    dependencies=[Depends(require_role(["admin", "manager"]))],
)
async def auto_run(
    request: AutoRunRequest,
    db: Session = Depends(get_db),
):
    """
    Ejecuta detección y escalado automático completo.
    
    **Requiere rol:** admin o manager
    
    **Proceso:**
    1. Obtiene lista de adsets activos (filtrados por campaign_ids si se especifica)
    2. Detecta spikes en cada adset
    3. Aplica escalado según recomendaciones (si dry_run=False)
    4. Persiste resultados en DB
    
    **Parámetros:**
    - `campaign_ids`: Lista de IDs de campañas a analizar (None = todas)
    - `dry_run`: Si True, solo detecta pero no aplica cambios (default: False)
    - `min_spend_threshold`: Mínimo gasto diario para incluir adset (default: 50.0)
    
    **Returns:**
    - Resumen completo con estadísticas y resultados detallados
    """
    
    try:
        result = await run_auto_spike_detection(db=db, request=request)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error en auto-run: {str(e)}",
        )


@router.get(
    "/health",
    summary="Health check del módulo SPIKE",
)
async def health_check():
    """
    Health check del módulo SPIKE Manager.
    
    **Public endpoint** (sin autenticación requerida)
    
    **Returns:**
    - Estado del servicio
    """
    
    return {
        "status": "healthy",
        "service": "meta_budget_spike_manager",
        "version": "1.0.0",
    }
