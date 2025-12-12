# backend/app/meta_insights_collector/scheduler.py

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

from app.core.logging import get_logger
from app.core.database import async_sessionmaker
from .collector import MetaInsightsCollector

logger = get_logger("meta_insights_scheduler")


class InsightsScheduler:
    """
    Programador de sincronización automática de insights.
    
    Responsable de:
    - Ejecutar sincronización cada 30 minutos
    - Manejar tareas en background
    - Gestionar lifecycle del scheduler
    - Logging detallado de operaciones
    """
    
    def __init__(self, interval_minutes: int = 30, mode: str = "stub"):
        self.interval_minutes = interval_minutes
        self.mode = mode
        self.is_running = False
        self.task: Optional[asyncio.Task] = None
        self.collector = MetaInsightsCollector(mode=mode)
        self._stop_event = asyncio.Event()
        
    async def start(self) -> None:
        """Inicia el scheduler en background."""
        if self.is_running:
            logger.warning("Scheduler is already running")
            return
            
        self.is_running = True
        self._stop_event.clear()
        
        logger.info(f"Starting insights scheduler (interval: {self.interval_minutes}min, mode: {self.mode})")
        
        self.task = asyncio.create_task(self._run_loop())
        
    async def stop(self) -> None:
        """Detiene el scheduler gracefully."""
        if not self.is_running:
            logger.info("Scheduler is not running")
            return
            
        logger.info("Stopping insights scheduler...")
        
        self.is_running = False
        self._stop_event.set()
        
        if self.task and not self.task.done():
            try:
                await asyncio.wait_for(self.task, timeout=10.0)
            except asyncio.TimeoutError:
                logger.warning("Scheduler task did not stop gracefully, cancelling")
                self.task.cancel()
                try:
                    await self.task
                except asyncio.CancelledError:
                    pass
                    
        logger.info("Insights scheduler stopped")
        
    async def _run_loop(self) -> None:
        """Loop principal del scheduler."""
        try:
            while self.is_running and not self._stop_event.is_set():
                try:
                    # Ejecutar sincronización
                    await self._execute_sync()
                    
                    # Esperar intervalo o hasta que se solicite parar
                    interval_seconds = self.interval_minutes * 60
                    
                    try:
                        await asyncio.wait_for(
                            self._stop_event.wait(), 
                            timeout=interval_seconds
                        )
                        # Si llegamos aquí, se solicitó parar
                        break
                    except asyncio.TimeoutError:
                        # Timeout normal, continuar con próxima iteración
                        continue
                        
                except Exception as e:
                    logger.exception(f"Error in scheduler loop: {e}")
                    # En caso de error, esperar un poco antes de reintentar
                    try:
                        await asyncio.wait_for(
                            self._stop_event.wait(), 
                            timeout=300  # 5 minutos en caso de error
                        )
                        break
                    except asyncio.TimeoutError:
                        continue
                        
        except asyncio.CancelledError:
            logger.info("Scheduler loop cancelled")
            raise
        except Exception as e:
            logger.exception(f"Fatal error in scheduler loop: {e}")
            raise
        finally:
            self.is_running = False
            
    async def _execute_sync(self) -> Dict[str, Any]:
        """
        Ejecuta una sincronización completa.
        
        Returns:
            Dict con reporte de la sincronización
        """
        start_time = datetime.utcnow()
        
        logger.info("Starting scheduled insights sync")
        
        try:
            # Sincronizar insights de los últimos 7 días
            sync_report = await self.collector.sync_all_insights(days_back=7)
            
            # Log resumen
            campaigns = sync_report.get("campaigns", {})
            adsets = sync_report.get("adsets", {})
            ads = sync_report.get("ads", {})
            
            logger.info(
                f"Sync completed: "
                f"Campaigns {campaigns.get('success', 0)}/{campaigns.get('processed', 0)}, "
                f"Adsets {adsets.get('success', 0)}/{adsets.get('processed', 0)}, "
                f"Ads {ads.get('success', 0)}/{ads.get('processed', 0)} "
                f"({sync_report.get('total_duration_seconds', 0):.2f}s)"
            )
            
            # Log errores si hay
            errors = sync_report.get("errors", [])
            if errors:
                logger.warning(f"Sync completed with {len(errors)} errors")
                for error in errors[:5]:  # Solo log los primeros 5 errores
                    logger.warning(f"Sync error: {error}")
                if len(errors) > 5:
                    logger.warning(f"... and {len(errors) - 5} more errors")
                    
            return sync_report
            
        except Exception as e:
            duration = (datetime.utcnow() - start_time).total_seconds()
            logger.exception(f"Scheduled sync failed after {duration:.2f}s: {e}")
            
            return {
                "sync_timestamp": start_time.isoformat(),
                "success": False,
                "error": str(e),
                "duration_seconds": duration,
                "campaigns": {"processed": 0, "success": 0, "errors": 1},
                "adsets": {"processed": 0, "success": 0, "errors": 0},
                "ads": {"processed": 0, "success": 0, "errors": 0}
            }
            
    async def run_manual_sync(self, days_back: int = 7, db_session=None) -> Dict[str, Any]:
        """
        Ejecuta una sincronización manual inmediata.
        
        Args:
            days_back: Días hacia atrás para sincronizar
            
        Returns:
            Dict con reporte de la sincronización
        """
        logger.info(f"Starting manual insights sync (days_back: {days_back})")
        
        try:
            sync_report = await self.collector.sync_all_insights(days_back=days_back, db_session=db_session)
            
            logger.info(
                f"Manual sync completed: "
                f"{sync_report.get('total_duration_seconds', 0):.2f}s"
            )
            
            return sync_report
            
        except Exception as e:
            logger.exception(f"Manual sync failed: {e}")
            raise
            
    def is_scheduler_running(self) -> bool:
        """Retorna True si el scheduler está corriendo."""
        return self.is_running
        
    def get_scheduler_status(self) -> Dict[str, Any]:
        """
        Obtiene el estado actual del scheduler.
        
        Returns:
            Dict con información de estado
        """
        return {
            "is_running": self.is_running,
            "interval_minutes": self.interval_minutes,
            "mode": self.mode,
            "task_done": self.task.done() if self.task else None,
            "next_run_in_seconds": None,  # TODO: Calcular tiempo hasta próxima ejecución
            "last_run": None  # TODO: Implementar tracking de última ejecución
        }

    async def force_sync_now(self) -> Dict[str, Any]:
        """
        Fuerza una sincronización inmediata sin interrumpir el scheduler.
        
        Returns:
            Dict con reporte de la sincronización
        """
        logger.info("Forcing immediate sync")
        
        try:
            # Crear nueva instancia del collector para evitar conflictos
            temp_collector = MetaInsightsCollector(mode=self.mode)
            sync_report = await temp_collector.sync_all_insights(days_back=3)
            
            logger.info("Forced sync completed successfully")
            return sync_report
            
        except Exception as e:
            logger.exception(f"Forced sync failed: {e}")
            raise


# Instancia global del scheduler (singleton pattern)
_scheduler_instance: Optional[InsightsScheduler] = None


def get_scheduler(mode: str = "stub") -> InsightsScheduler:
    """
    Obtiene la instancia global del scheduler.
    
    Args:
        mode: Modo de operación ("stub" o "live")
        
    Returns:
        Instancia del scheduler
    """
    global _scheduler_instance
    
    if _scheduler_instance is None:
        _scheduler_instance = InsightsScheduler(mode=mode)
        
    return _scheduler_instance


async def start_insights_scheduler(mode: str = "stub") -> None:
    """
    Función de conveniencia para iniciar el scheduler.
    
    Args:
        mode: Modo de operación ("stub" o "live")
    """
    scheduler = get_scheduler(mode=mode)
    await scheduler.start()
    

async def stop_insights_scheduler() -> None:
    """
    Función de conveniencia para detener el scheduler.
    """
    global _scheduler_instance
    
    if _scheduler_instance:
        await _scheduler_instance.stop()
        

def is_insights_scheduler_running() -> bool:
    """
    Función de conveniencia para verificar si el scheduler está corriendo.
    
    Returns:
        True si el scheduler está corriendo
    """
    global _scheduler_instance
    
    return _scheduler_instance is not None and _scheduler_instance.is_scheduler_running()