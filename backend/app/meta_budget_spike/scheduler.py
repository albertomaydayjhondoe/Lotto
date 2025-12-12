"""
Scheduler para Meta Budget SPIKE Manager.
Ejecuta detección y escalado automático cada 30 minutos.
"""

import asyncio
import logging
from datetime import datetime

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.ledger import log_job_event
from app.meta_budget_spike.models import AutoRunRequest, AutoRunResponse
from app.meta_budget_spike.scaler import BudgetScaler
from app.meta_budget_spike.spike_detector import SpikeDetector

logger = logging.getLogger(__name__)


async def spike_scheduler_task():
    """
    Background task que ejecuta cada 30 minutos:
    1. Detectar spikes en todos los adsets activos
    2. Aplicar escalado automático según recomendaciones
    3. Guardar resultados en DB
    4. Log de actividad
    """
    
    if not settings.AUTO_PUBLISHER_ENABLED:
        logger.warning("SPIKE Scheduler deshabilitado (AUTO_PUBLISHER_ENABLED=False)")
        return
    
    logger.info("Iniciando SPIKE Scheduler...")
    
    while True:
        try:
            # Obtener session de DB
            db = next(get_db())
            
            # Ejecutar auto-run
            result = await run_auto_spike_detection(
                db=db,
                request=AutoRunRequest(
                    campaign_ids=None,  # Analizar todas
                    dry_run=False,
                    min_spend_threshold=50.0,
                ),
            )
            
            # Log del resultado
            log_job_event(
                job_id=None,
                event_type="spike_scheduler_run",
                message=f"SPIKE Scheduler ejecutado: {result.spikes_detected} spikes, {result.scales_applied} escalados",
                metadata={
                    "total_adsets_analyzed": result.total_adsets_analyzed,
                    "spikes_detected": result.spikes_detected,
                    "scales_applied": result.scales_applied,
                    "scales_failed": result.scales_failed,
                    "execution_time": result.execution_time_seconds,
                },
            )
            
            logger.info(
                f"SPIKE Scheduler completado: "
                f"{result.spikes_detected} spikes, "
                f"{result.scales_applied} escalados en "
                f"{result.execution_time_seconds:.2f}s"
            )
        
        except Exception as e:
            logger.error(f"Error en SPIKE Scheduler: {e}")
            log_job_event(
                job_id=None,
                event_type="spike_scheduler_error",
                message=f"Error en SPIKE Scheduler: {str(e)}",
                metadata={"error": str(e)},
            )
        
        finally:
            # Cerrar session
            db.close()
        
        # Esperar 30 minutos
        await asyncio.sleep(30 * 60)


async def run_auto_spike_detection(
    db: Session,
    request: AutoRunRequest,
) -> AutoRunResponse:
    """
    Ejecuta detección automática de spikes y escalado.
    
    Args:
        db: Session de base de datos
        request: Configuración de la ejecución
    
    Returns:
        Resultado de la ejecución
    """
    
    start_time = datetime.utcnow()
    
    detector = SpikeDetector(db)
    scaler = BudgetScaler(db)
    
    # 1. Obtener lista de adsets a analizar
    adsets = await _get_active_adsets(
        db=db,
        campaign_ids=request.campaign_ids,
        min_spend_threshold=request.min_spend_threshold,
    )
    
    logger.info(f"Analizando {len(adsets)} adsets activos...")
    
    # 2. Detectar spikes en cada adset
    spike_results = []
    for adset in adsets:
        try:
            spike_result = await detector.detect_spike(
                adset_id=adset["id"],
                campaign_id=adset.get("campaign_id"),
            )
            spike_results.append(spike_result)
        except Exception as e:
            logger.warning(f"Error detectando spike en adset {adset['id']}: {e}")
    
    # Contar spikes detectados
    spikes_detected = sum(1 for r in spike_results if r.spike_detected)
    
    logger.info(f"{spikes_detected} spikes detectados de {len(spike_results)} adsets")
    
    # 3. Aplicar escalado (si no es dry_run)
    scale_results = []
    if not request.dry_run:
        scale_results = await scaler.scale_multiple(
            spike_results=spike_results,
            dry_run=False,
        )
    else:
        logger.info("DRY RUN: No se aplicarán cambios")
    
    # Contar escalados exitosos
    scales_applied = sum(1 for r in scale_results if r.success)
    scales_failed = sum(1 for r in scale_results if not r.success)
    
    # 4. Calcular tiempo de ejecución
    end_time = datetime.utcnow()
    execution_time = (end_time - start_time).total_seconds()
    
    return AutoRunResponse(
        total_adsets_analyzed=len(adsets),
        spikes_detected=spikes_detected,
        scales_applied=scales_applied,
        scales_failed=scales_failed,
        dry_run=request.dry_run,
        spike_results=spike_results,
        scale_results=scale_results,
        execution_time_seconds=execution_time,
        timestamp=end_time,
    )


async def _get_active_adsets(
    db: Session,
    campaign_ids: list[str] | None,
    min_spend_threshold: float,
) -> list[dict]:
    """
    Obtiene lista de adsets activos a analizar.
    
    Args:
        db: Session de base de datos
        campaign_ids: IDs de campañas a filtrar (None = todas)
        min_spend_threshold: Mínimo gasto diario para incluir
    
    Returns:
        Lista de dicts con adset info
    """
    
    if settings.META_API_MODE == "stub":
        # STUB: Generar adsets sintéticos
        import random
        
        num_adsets = random.randint(5, 20)
        adsets = []
        
        for i in range(num_adsets):
            adsets.append({
                "id": f"adset_{i + 1}",
                "name": f"Test Adset {i + 1}",
                "campaign_id": f"campaign_{random.randint(1, 5)}",
                "daily_budget": random.uniform(50, 500),
                "status": "ACTIVE",
            })
        
        # Filtrar por campaign_ids si se especificó
        if campaign_ids:
            adsets = [a for a in adsets if a["campaign_id"] in campaign_ids]
        
        # Filtrar por min_spend_threshold
        adsets = [a for a in adsets if a["daily_budget"] >= min_spend_threshold]
        
        return adsets
    
    # LIVE: Consultar DB o Meta API
    # TODO: Implementar consulta real
    return []


def start_scheduler_background():
    """
    Inicia el scheduler en background (usar en main.py startup event).
    """
    
    if not settings.AUTO_PUBLISHER_ENABLED:
        logger.warning("SPIKE Scheduler deshabilitado")
        return
    
    logger.info("Iniciando SPIKE Scheduler en background...")
    
    # Crear tarea en background
    asyncio.create_task(spike_scheduler_task())
