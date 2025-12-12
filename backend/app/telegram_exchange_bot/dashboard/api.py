"""
Dashboard API - Sprint 7C
Backend FastAPI para monitorización en tiempo real.

Endpoints:
- /exchange/dashboard/overview - Métricas generales
- /exchange/dashboard/groups - ROI por grupo
- /exchange/dashboard/users - ROI por usuario
- /exchange/dashboard/platforms - Breakdown por plataforma
- /exchange/dashboard/errors - Log de errores recientes
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
import io
import csv
import json

from app.telegram_exchange_bot.metrics import (
    MetricsCollector,
    MetricPeriod,
    PerformanceDashboard
)
from app.telegram_exchange_bot.models import Platform

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/exchange/dashboard", tags=["Exchange Dashboard"])


# Dependency para DB session (ajustar según tu setup)
def get_db():
    """Get database session."""
    # TODO: Implementar según tu configuración de DB
    pass


@router.get("/overview")
async def get_dashboard_overview(
    period: MetricPeriod = Query(MetricPeriod.DAILY, description="Período de agregación"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Obtiene overview general del dashboard.
    
    Returns:
        - Total executions
        - Success rate
        - Global ROI
        - Total cost
        - Platform breakdown
        - Top groups/users
        - Health status
    """
    try:
        metrics = MetricsCollector(db=db)
        dashboard = await metrics.generate_dashboard(period=period)
        
        return {
            "period": dashboard.period.value,
            "generated_at": dashboard.generated_at.isoformat(),
            "totals": {
                "total_executions": dashboard.total_executions,
                "successful_executions": dashboard.successful_executions,
                "failed_executions": dashboard.failed_executions,
                "success_rate": dashboard.success_rate
            },
            "roi": {
                "global_roi": dashboard.global_roi,
                "total_cost_eur": dashboard.total_cost_eur,
                "avg_cost_per_interaction": dashboard.avg_cost_per_interaction
            },
            "platforms": {
                "youtube": dashboard.youtube_executions,
                "instagram": dashboard.instagram_executions,
                "tiktok": dashboard.tiktok_executions
            },
            "top_performers": {
                "groups": dashboard.top_groups[:10],
                "users": dashboard.top_users[:10]
            },
            "health": {
                "status": dashboard.health_status,
                "recommendations": dashboard.recommendations
            }
        }
        
    except Exception as e:
        logger.error(f"Error generating dashboard overview: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/groups")
async def get_groups_metrics(
    period: MetricPeriod = Query(MetricPeriod.DAILY),
    limit: int = Query(50, ge=1, le=200),
    sort_by: str = Query("roi_ratio", regex="^(roi_ratio|total_interactions|efficiency)$"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Obtiene métricas por grupo de Telegram.
    
    Args:
        period: Período de agregación
        limit: Máximo número de grupos
        sort_by: Campo de ordenamiento
        
    Returns:
        Lista de grupos con métricas ROI
    """
    try:
        metrics = MetricsCollector(db=db)
        
        # TODO: Query real a exchange_metrics donde entity_type="group"
        # Por ahora, mock data
        groups_data = [
            {
                "group_id": f"group_{i:03d}",
                "group_name": f"Grupo Ejemplo {i}",
                "total_interactions": 45 - i,
                "support_given": 40 - i,
                "support_received": int((40 - i) * (1.2 - i * 0.05)),
                "roi_ratio": 1.2 - i * 0.05,
                "success_rate": 0.90 - i * 0.02,
                "efficiency": "high" if i < 10 else "medium"
            }
            for i in range(min(limit, 30))
        ]
        
        # Ordenar
        reverse = sort_by == "roi_ratio"
        groups_data.sort(
            key=lambda x: x.get(sort_by, 0),
            reverse=reverse
        )
        
        return {
            "period": period.value,
            "total_groups": len(groups_data),
            "groups": groups_data[:limit]
        }
        
    except Exception as e:
        logger.error(f"Error getting groups metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/users")
async def get_users_metrics(
    period: MetricPeriod = Query(MetricPeriod.DAILY),
    limit: int = Query(50, ge=1, le=200),
    min_interactions: int = Query(5, ge=1),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Obtiene métricas por usuario externo.
    
    Args:
        period: Período de agregación
        limit: Máximo número de usuarios
        min_interactions: Mínimo de interacciones para incluir
        
    Returns:
        Lista de usuarios con métricas ROI
    """
    try:
        # TODO: Query real a exchange_metrics donde entity_type="user"
        users_data = [
            {
                "user_id": f"user_{i:03d}",
                "username": f"@user_{i}",
                "total_interactions": 30 - i,
                "completed_exchanges": 25 - i,
                "failed_exchanges": 5,
                "reliability_score": 0.85 - i * 0.02,
                "roi_ratio": 1.15 - i * 0.04,
                "is_trusted": (30 - i) >= min_interactions and (0.85 - i * 0.02) >= 0.75
            }
            for i in range(min(limit, 25))
        ]
        
        # Filtrar por min_interactions
        users_data = [u for u in users_data if u["total_interactions"] >= min_interactions]
        
        return {
            "period": period.value,
            "total_users": len(users_data),
            "min_interactions_filter": min_interactions,
            "users": users_data[:limit]
        }
        
    except Exception as e:
        logger.error(f"Error getting users metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/platforms")
async def get_platforms_metrics(
    period: MetricPeriod = Query(MetricPeriod.DAILY),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Obtiene métricas por plataforma.
    
    Returns:
        Breakdown completo por YouTube/Instagram/TikTok
    """
    try:
        metrics = MetricsCollector(db=db)
        
        # TODO: Query real a exchange_metrics donde entity_type="platform"
        platforms_data = {
            "youtube": {
                "total_interactions": 150,
                "successful": 135,
                "failed": 15,
                "success_rate": 0.90,
                "avg_execution_time": 2.5,
                "breakdown": {
                    "likes": 80,
                    "comments": 45,
                    "subscribes": 25
                },
                "cost_eur": 4.50
            },
            "instagram": {
                "total_interactions": 120,
                "successful": 108,
                "failed": 12,
                "success_rate": 0.90,
                "avg_execution_time": 3.2,
                "breakdown": {
                    "likes": 70,
                    "saves": 25,
                    "comments": 20,
                    "follows": 5
                },
                "cost_eur": 3.80
            },
            "tiktok": {
                "total_interactions": 80,
                "successful": 68,
                "failed": 12,
                "success_rate": 0.85,
                "avg_execution_time": 4.1,
                "breakdown": {
                    "likes": 50,
                    "comments": 20,
                    "follows": 10
                },
                "cost_eur": 3.20
            }
        }
        
        return {
            "period": period.value,
            "platforms": platforms_data,
            "summary": {
                "total_cost_eur": sum(p["cost_eur"] for p in platforms_data.values()),
                "avg_success_rate": sum(p["success_rate"] for p in platforms_data.values()) / 3
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting platforms metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/errors")
async def get_recent_errors(
    hours: int = Query(24, ge=1, le=168, description="Últimas N horas"),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Obtiene log de errores recientes.
    
    Args:
        hours: Ventana de tiempo (default 24h)
        limit: Máximo número de errores
        
    Returns:
        Lista de errores con contexto completo
    """
    try:
        since = datetime.utcnow() - timedelta(hours=hours)
        
        # TODO: Query real a exchange_interactions_executed WHERE status="failed"
        errors_data = [
            {
                "error_id": f"err_{i:05d}",
                "timestamp": (datetime.utcnow() - timedelta(hours=i*0.5)).isoformat(),
                "interaction_type": ["youtube_like", "instagram_comment", "tiktok_follow"][i % 3],
                "platform": ["youtube", "instagram", "tiktok"][i % 3],
                "account_id": f"acc_{(i % 5) + 1:03d}",
                "target_url": f"https://example.com/content_{i}",
                "error": [
                    "Network timeout",
                    "Proxy connection failed",
                    "Shadowban detected",
                    "Rate limit exceeded",
                    "Invalid credentials"
                ][i % 5],
                "vpn_active": True,
                "proxy_used": f"http://proxy{i%3}.example:8080"
            }
            for i in range(min(limit, 50))
        ]
        
        return {
            "period_hours": hours,
            "total_errors": len(errors_data),
            "errors": errors_data[:limit],
            "error_breakdown": {
                "network_errors": 20,
                "authentication_errors": 10,
                "rate_limit_errors": 8,
                "shadowban_errors": 7,
                "other_errors": 5
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting recent errors: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/export/csv")
async def export_dashboard_csv(
    period: MetricPeriod = Query(MetricPeriod.DAILY),
    entity_type: str = Query("groups", regex="^(groups|users|platforms)$"),
    db: Session = Depends(get_db)
) -> StreamingResponse:
    """
    Exporta dashboard a CSV.
    
    Args:
        period: Período de datos
        entity_type: Tipo de entidad (groups/users/platforms)
        
    Returns:
        CSV file stream
    """
    try:
        # Generate CSV
        output = io.StringIO()
        
        if entity_type == "groups":
            response = await get_groups_metrics(period=period, limit=200, db=db)
            data = response["groups"]
            
            if data:
                writer = csv.DictWriter(output, fieldnames=data[0].keys())
                writer.writeheader()
                writer.writerows(data)
        
        elif entity_type == "users":
            response = await get_users_metrics(period=period, limit=200, db=db)
            data = response["users"]
            
            if data:
                writer = csv.DictWriter(output, fieldnames=data[0].keys())
                writer.writeheader()
                writer.writerows(data)
        
        else:  # platforms
            response = await get_platforms_metrics(period=period, db=db)
            # Flatten platforms data
            data = []
            for platform, metrics in response["platforms"].items():
                row = {"platform": platform, **metrics}
                data.append(row)
            
            if data:
                writer = csv.DictWriter(output, fieldnames=data[0].keys())
                writer.writeheader()
                writer.writerows(data)
        
        output.seek(0)
        
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=exchange_dashboard_{entity_type}_{period.value}.csv"
            }
        )
        
    except Exception as e:
        logger.error(f"Error exporting CSV: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/export/json")
async def export_dashboard_json(
    period: MetricPeriod = Query(MetricPeriod.DAILY),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Exporta dashboard completo a JSON.
    
    Returns:
        JSON completo con todas las métricas
    """
    try:
        overview = await get_dashboard_overview(period=period, db=db)
        groups = await get_groups_metrics(period=period, limit=100, db=db)
        users = await get_users_metrics(period=period, limit=100, db=db)
        platforms = await get_platforms_metrics(period=period, db=db)
        errors = await get_recent_errors(hours=24, limit=50, db=db)
        
        export_data = {
            "exported_at": datetime.utcnow().isoformat(),
            "period": period.value,
            "overview": overview,
            "groups": groups,
            "users": users,
            "platforms": platforms,
            "recent_errors": errors
        }
        
        return export_data
        
    except Exception as e:
        logger.error(f"Error exporting JSON: {e}")
        raise HTTPException(status_code=500, detail=str(e))
