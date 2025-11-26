# backend/app/meta_insights_collector/router.py

from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy import select, and_, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.permissions import require_role
from app.core.database import get_db
from app.core.logging import get_logger
from app.models.database import (
    MetaCampaignModel, 
    MetaAdsetModel, 
    MetaAdModel,
    MetaAdInsightsModel
)

from .models import (
    InsightsOverviewResponse,
    CampaignInsightsOverview,
    AdsetInsightsOverview,
    AdInsightsOverview,
    InsightTimeline,
    InsightResponse,
    InsightMetrics,
    SyncReport,
    ManualSyncRequest,
    InsightsQueryParams,
    ErrorResponse
)
from .collector import MetaInsightsCollector
from .scheduler import get_scheduler

logger = get_logger("meta_insights_router")

router = APIRouter(
    prefix="/meta/insights", 
    tags=["meta-insights"],
    responses={
        401: {"description": "No autorizado"},
        403: {"description": "Permisos insuficientes"},
        404: {"description": "Recurso no encontrado"},
        500: {"description": "Error interno del servidor"}
    }
)


@router.post("/sync-now", response_model=SyncReport)
async def sync_insights_now(
    request: ManualSyncRequest = ManualSyncRequest(),
    db: AsyncSession = Depends(get_db),
    _: Dict = Depends(require_role(["admin", "manager"]))
) -> SyncReport:
    """
    Ejecuta una sincronización manual inmediata de insights.
    
    - **Requiere permisos:** admin o manager
    - **Operación:** Sincroniza insights de Meta Ads
    - **Duración:** Puede tomar varios minutos dependiendo del volumen
    """
    try:
        logger.info(f"Manual sync requested: {request.days_back} days back")
        
        # Obtener scheduler y ejecutar sincronización
        scheduler = get_scheduler(mode="stub")  # TODO: Configurar mode desde settings
        sync_result = await scheduler.run_manual_sync(days_back=request.days_back)
        
        # Convertir resultado a modelo Pydantic
        sync_report = SyncReport(
            sync_id=str(uuid4()),
            sync_timestamp=datetime.fromisoformat(sync_result["sync_timestamp"]),
            sync_type="manual",
            mode="stub",  # TODO: Obtener desde configuración
            date_range=sync_result.get("date_range", {}),
            days_back=request.days_back,
            campaigns=sync_result.get("campaigns", {}),
            adsets=sync_result.get("adsets", {}),
            ads=sync_result.get("ads", {}),
            total_duration_seconds=sync_result.get("total_duration_seconds", 0),
            errors=sync_result.get("errors", []),
            success=len(sync_result.get("errors", [])) == 0,
            completion_percentage=100.0 if len(sync_result.get("errors", [])) == 0 else 85.0
        )
        
        logger.info(f"Manual sync completed in {sync_report.total_duration_seconds:.2f}s")
        return sync_report
        
    except Exception as e:
        logger.exception(f"Manual sync failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Sync failed: {str(e)}"
        )


@router.get("/recent-insights/{entity_id}", response_model=InsightTimeline)
async def get_recent_insights(
    entity_id: str = Path(..., description="ID de la entidad"),
    entity_type: str = Query(..., description="Tipo de entidad (campaign/adset/ad)"),
    days: int = Query(30, ge=1, le=365, description="Días hacia atrás"),
    db: AsyncSession = Depends(get_db),
    _: Dict = Depends(require_role(["analytics:read", "manager", "admin"]))
) -> InsightTimeline:
    """
    Obtiene insights recientes de una entidad específica.
    
    - **Requiere permisos:** analytics:read, manager o admin
    - **Parámetros:** entity_id, entity_type, días
    - **Retorna:** Timeline con insights y métricas agregadas
    """
    try:
        if entity_type not in ["campaign", "adset", "ad"]:
            raise HTTPException(
                status_code=400,
                detail="entity_type debe ser 'campaign', 'adset' o 'ad'"
            )
        
        # Usar collector para obtener insights
        collector = MetaInsightsCollector(db_session=db, mode="stub")
        insights_data = await collector.get_recent_insights(
            entity_id=entity_id,
            entity_type=entity_type,
            days=days
        )
        
        # Obtener nombre de la entidad
        entity_name = await _get_entity_name(db, entity_id, entity_type)
        
        # Convertir a modelos Pydantic
        insights = [
            InsightResponse(
                id=insight["id"],
                entity_id=entity_id,
                entity_type=entity_type,
                date_start=datetime.fromisoformat(insight["date_start"]),
                date_end=datetime.fromisoformat(insight["date_end"]),
                metrics=InsightMetrics(
                    spend=insight["spend"],
                    impressions=insight["impressions"],
                    clicks=insight["clicks"],
                    conversions=insight["conversions"],
                    revenue=insight["revenue"],
                    ctr=insight["ctr"],
                    cpc=insight["cpc"],
                    roas=insight["roas"],
                    frequency=insight["frequency"],
                    reach=insight.get("reach"),
                    unique_clicks=insight.get("unique_clicks"),
                    cost_per_conversion=insight.get("cost_per_conversion")
                ),
                created_at=datetime.utcnow(),  # TODO: Usar created_at real
                updated_at=datetime.utcnow()   # TODO: Usar updated_at real
            )
            for insight in insights_data
        ]
        
        # Calcular métricas agregadas
        total_spend = sum(i.metrics.spend for i in insights)
        total_impressions = sum(i.metrics.impressions for i in insights)
        total_clicks = sum(i.metrics.clicks for i in insights)
        total_conversions = sum(i.metrics.conversions for i in insights)
        total_revenue = sum(i.metrics.revenue for i in insights)
        
        avg_ctr = (total_clicks / total_impressions * 100) if total_impressions > 0 else 0
        avg_cpc = (total_spend / total_clicks) if total_clicks > 0 else 0
        avg_roas = (total_revenue / total_spend) if total_spend > 0 else 0
        
        timeline = InsightTimeline(
            entity_id=entity_id,
            entity_type=entity_type,
            entity_name=entity_name,
            date_range={
                "start": (datetime.utcnow() - timedelta(days=days)).isoformat(),
                "end": datetime.utcnow().isoformat()
            },
            insights=insights,
            total_insights=len(insights),
            total_spend=total_spend,
            total_impressions=total_impressions,
            total_clicks=total_clicks,
            total_conversions=total_conversions,
            total_revenue=total_revenue,
            avg_ctr=avg_ctr,
            avg_cpc=avg_cpc,
            avg_roas=avg_roas
        )
        
        return timeline
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error getting recent insights: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving insights: {str(e)}"
        )


@router.get("/overview", response_model=InsightsOverviewResponse)
async def get_insights_overview(
    days: int = Query(7, ge=1, le=90, description="Días hacia atrás para el overview"),
    db: AsyncSession = Depends(get_db),
    _: Dict = Depends(require_role(["analytics:read", "manager", "admin"]))
) -> InsightsOverviewResponse:
    """
    Obtiene una vista general de todos los insights.
    
    - **Requiere permisos:** analytics:read, manager o admin  
    - **Parámetros:** días hacia atrás
    - **Retorna:** Overview completo con métricas agregadas y top performers
    """
    try:
        date_limit = datetime.utcnow() - timedelta(days=days)
        
        # Contar entidades
        campaigns_query = select(func.count(MetaCampaignModel.id)).where(MetaCampaignModel.is_active == 1)
        campaigns_result = await db.execute(campaigns_query)
        total_campaigns = campaigns_result.scalar() or 0
        
        active_campaigns_query = select(func.count(MetaCampaignModel.id)).where(
            and_(MetaCampaignModel.is_active == 1, MetaCampaignModel.status == "ACTIVE")
        )
        active_campaigns_result = await db.execute(active_campaigns_query)
        active_campaigns = active_campaigns_result.scalar() or 0
        
        # Obtener métricas agregadas de insights recientes
        insights_query = select(
            func.sum(MetaAdInsightsModel.spend).label("total_spend"),
            func.sum(MetaAdInsightsModel.impressions).label("total_impressions"),
            func.sum(MetaAdInsightsModel.clicks).label("total_clicks"),
            func.sum(MetaAdInsightsModel.conversions).label("total_conversions"),
            func.sum(MetaAdInsightsModel.revenue).label("total_revenue"),
            func.avg(MetaAdInsightsModel.ctr).label("avg_ctr"),
            func.avg(MetaAdInsightsModel.cpc).label("avg_cpc"),
            func.avg(MetaAdInsightsModel.roas).label("avg_roas")
        ).where(MetaAdInsightsModel.date_start >= date_limit)
        
        insights_result = await db.execute(insights_query)
        metrics_row = insights_result.first()
        
        global_metrics = InsightMetrics(
            spend=float(metrics_row.total_spend or 0),
            impressions=int(metrics_row.total_impressions or 0),
            clicks=int(metrics_row.total_clicks or 0),
            conversions=int(metrics_row.total_conversions or 0),
            revenue=float(metrics_row.total_revenue or 0),
            ctr=float(metrics_row.avg_ctr or 0),
            cpc=float(metrics_row.avg_cpc or 0),
            roas=float(metrics_row.avg_roas or 0)
        )
        
        # Top campaigns por ROAS
        top_campaigns_query = select(
            MetaCampaignModel.id,
            MetaCampaignModel.name,
            func.avg(MetaAdInsightsModel.roas).label("avg_roas"),
            func.sum(MetaAdInsightsModel.spend).label("total_spend")
        ).select_from(
            MetaCampaignModel.__table__.join(
                MetaAdInsightsModel.__table__,
                MetaCampaignModel.id == MetaAdInsightsModel.campaign_id
            )
        ).where(
            and_(
                MetaAdInsightsModel.date_start >= date_limit,
                MetaAdInsightsModel.entity_type == "campaign"
            )
        ).group_by(
            MetaCampaignModel.id, MetaCampaignModel.name
        ).order_by(
            desc("avg_roas")
        ).limit(5)
        
        top_campaigns_result = await db.execute(top_campaigns_query)
        top_campaigns = [
            {
                "id": str(row.id),
                "name": row.name,
                "avg_roas": float(row.avg_roas or 0),
                "total_spend": float(row.total_spend or 0)
            }
            for row in top_campaigns_result
        ]
        
        overview = InsightsOverviewResponse(
            timestamp=datetime.utcnow(),
            date_range={
                "start": date_limit.isoformat(),
                "end": datetime.utcnow().isoformat()
            },
            total_campaigns=total_campaigns,
            active_campaigns=active_campaigns,
            total_adsets=0,  # TODO: Implementar conteo de adsets
            active_adsets=0,
            total_ads=0,     # TODO: Implementar conteo de ads  
            active_ads=0,
            global_metrics=global_metrics,
            top_campaigns=top_campaigns,
            top_adsets=[],   # TODO: Implementar top adsets
            top_ads=[],      # TODO: Implementar top ads
            last_sync={      # TODO: Obtener info de última sincronización
                "timestamp": datetime.utcnow().isoformat(),
                "success": True,
                "duration_seconds": 45.2
            },
            alerts=[]        # TODO: Implementar sistema de alertas
        )
        
        return overview
        
    except Exception as e:
        logger.exception(f"Error getting overview: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving overview: {str(e)}"
        )


@router.get("/campaign/{campaign_id}", response_model=CampaignInsightsOverview)
async def get_campaign_insights(
    campaign_id: str = Path(..., description="ID de la campaña"),
    days: int = Query(30, ge=1, le=365, description="Días hacia atrás"),
    db: AsyncSession = Depends(get_db),
    _: Dict = Depends(require_role(["analytics:read", "manager", "admin"]))
) -> CampaignInsightsOverview:
    """
    Obtiene insights detallados de una campaña específica.
    
    - **Requiere permisos:** analytics:read, manager o admin
    - **Parámetros:** campaign_id, días
    - **Retorna:** Overview completo de la campaña con adsets y ads
    """
    try:
        # Obtener información de la campaña
        campaign_query = select(MetaCampaignModel).where(MetaCampaignModel.id == campaign_id)
        campaign_result = await db.execute(campaign_query)
        campaign = campaign_result.scalars().first()
        
        if not campaign:
            raise HTTPException(
                status_code=404,
                detail=f"Campaign {campaign_id} not found"
            )
        
        # Obtener insights de la campaña usando el endpoint existente
        campaign_timeline = await get_recent_insights(
            entity_id=campaign_id,
            entity_type="campaign",
            days=days,
            db=db,
            _={}  # Ya validamos permisos arriba
        )
        
        # Contar adsets y ads
        adsets_query = select(func.count(MetaAdsetModel.id)).where(
            MetaAdsetModel.campaign_id == campaign_id
        )
        adsets_result = await db.execute(adsets_query)
        adsets_count = adsets_result.scalar() or 0
        
        ads_query = select(func.count(MetaAdModel.id)).select_from(
            MetaAdModel.__table__.join(
                MetaAdsetModel.__table__,
                MetaAdModel.adset_id == MetaAdsetModel.id
            )
        ).where(MetaAdsetModel.campaign_id == campaign_id)
        ads_result = await db.execute(ads_query)
        ads_count = ads_result.scalar() or 0
        
        overview = CampaignInsightsOverview(
            campaign_id=campaign_id,
            campaign_name=campaign.name,
            status=campaign.status,
            campaign_insights=campaign_timeline,
            adsets_count=adsets_count,
            adsets_active=0,  # TODO: Implementar conteo por estado
            adsets_paused=0,
            ads_count=ads_count,
            ads_active=0,     # TODO: Implementar conteo por estado
            ads_paused=0,
            performance_summary={
                "roas": campaign_timeline.avg_roas,
                "spend": campaign_timeline.total_spend,
                "revenue": campaign_timeline.total_revenue,
                "efficiency_score": min(100, campaign_timeline.avg_roas * 50) if campaign_timeline.avg_roas > 0 else 0
            }
        )
        
        return overview
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error getting campaign insights: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving campaign insights: {str(e)}"
        )


@router.get("/adset/{adset_id}", response_model=AdsetInsightsOverview)
async def get_adset_insights(
    adset_id: str = Path(..., description="ID del adset"),
    days: int = Query(30, ge=1, le=365, description="Días hacia atrás"),
    db: AsyncSession = Depends(get_db),
    _: Dict = Depends(require_role(["analytics:read", "manager", "admin"]))
) -> AdsetInsightsOverview:
    """
    Obtiene insights detallados de un adset específico.
    
    - **Requiere permisos:** analytics:read, manager o admin
    - **Parámetros:** adset_id, días
    - **Retorna:** Overview completo del adset
    """
    try:
        # Obtener información del adset y campaña
        adset_query = select(MetaAdsetModel, MetaCampaignModel).select_from(
            MetaAdsetModel.__table__.join(
                MetaCampaignModel.__table__,
                MetaAdsetModel.campaign_id == MetaCampaignModel.id
            )
        ).where(MetaAdsetModel.id == adset_id)
        
        adset_result = await db.execute(adset_query)
        row = adset_result.first()
        
        if not row:
            raise HTTPException(
                status_code=404,
                detail=f"Adset {adset_id} not found"
            )
        
        adset, campaign = row
        
        # Obtener insights del adset
        adset_timeline = await get_recent_insights(
            entity_id=adset_id,
            entity_type="adset", 
            days=days,
            db=db,
            _={}
        )
        
        # Contar ads del adset
        ads_query = select(func.count(MetaAdModel.id)).where(MetaAdModel.adset_id == adset_id)
        ads_result = await db.execute(ads_query)
        ads_count = ads_result.scalar() or 0
        
        overview = AdsetInsightsOverview(
            adset_id=adset_id,
            adset_name=adset.name,
            campaign_id=str(campaign.id),
            campaign_name=campaign.name,
            status=adset.status,
            adset_insights=adset_timeline,
            ads_count=ads_count,
            ads_active=0,  # TODO: Implementar conteo por estado
            ads_paused=0,
            targeting_summary={  # TODO: Implementar desde adset.targeting_config
                "age_range": "25-65",
                "locations": ["US", "CA"],
                "interests": ["Digital Marketing", "E-commerce"]
            },
            budget_info={  # TODO: Implementar desde adset config
                "daily_budget": 100.0,
                "lifetime_budget": None,
                "bid_strategy": "LOWEST_COST_WITHOUT_CAP"
            }
        )
        
        return overview
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error getting adset insights: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving adset insights: {str(e)}"
        )


@router.get("/ad/{ad_id}", response_model=AdInsightsOverview)
async def get_ad_insights(
    ad_id: str = Path(..., description="ID del ad"),
    days: int = Query(30, ge=1, le=365, description="Días hacia atrás"),
    db: AsyncSession = Depends(get_db),
    _: Dict = Depends(require_role(["analytics:read", "manager", "admin"]))
) -> AdInsightsOverview:
    """
    Obtiene insights detallados de un ad específico.
    
    - **Requiere permisos:** analytics:read, manager o admin
    - **Parámetros:** ad_id, días
    - **Retorna:** Overview completo del ad con comparación de peers
    """
    try:
        # Obtener información completa del ad, adset y campaña
        ad_query = select(MetaAdModel, MetaAdsetModel, MetaCampaignModel).select_from(
            MetaAdModel.__table__.join(
                MetaAdsetModel.__table__,
                MetaAdModel.adset_id == MetaAdsetModel.id
            ).join(
                MetaCampaignModel.__table__,
                MetaAdsetModel.campaign_id == MetaCampaignModel.id
            )
        ).where(MetaAdModel.id == ad_id)
        
        ad_result = await db.execute(ad_query)
        row = ad_result.first()
        
        if not row:
            raise HTTPException(
                status_code=404,
                detail=f"Ad {ad_id} not found"
            )
        
        ad, adset, campaign = row
        
        # Obtener insights del ad
        ad_timeline = await get_recent_insights(
            entity_id=ad_id,
            entity_type="ad",
            days=days,
            db=db,
            _={}
        )
        
        overview = AdInsightsOverview(
            ad_id=ad_id,
            ad_name=ad.name,
            adset_id=str(adset.id),
            adset_name=adset.name,
            campaign_id=str(campaign.id),
            campaign_name=campaign.name,
            status=ad.status,
            ad_insights=ad_timeline,
            creative_info={  # TODO: Implementar desde ad.creative_config
                "format": "SINGLE_IMAGE",
                "headline": "Sample Headline",
                "description": "Sample Description",
                "call_to_action": "LEARN_MORE"
            },
            peer_comparison={  # TODO: Implementar comparación real
                "adset_avg_roas": 1.85,
                "rank_in_adset": 2,
                "total_ads_in_adset": 5,
                "performance_percentile": 75
            }
        )
        
        return overview
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error getting ad insights: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving ad insights: {str(e)}"
        )


# Funciones auxiliares

async def _get_entity_name(db: AsyncSession, entity_id: str, entity_type: str) -> Optional[str]:
    """Obtiene el nombre de una entidad por su ID y tipo."""
    try:
        if entity_type == "campaign":
            query = select(MetaCampaignModel.name).where(MetaCampaignModel.id == entity_id)
        elif entity_type == "adset":
            query = select(MetaAdsetModel.name).where(MetaAdsetModel.id == entity_id)
        elif entity_type == "ad":
            query = select(MetaAdModel.name).where(MetaAdModel.id == entity_id)
        else:
            return None
            
        result = await db.execute(query)
        name = result.scalar()
        return name
        
    except Exception:
        return f"{entity_type}_{entity_id[:8]}"


# ============================================================================
# ENDPOINTS ADICIONALES ESPECIFICADOS EN PASO 10.7
# ============================================================================

@router.get("/summary")
async def get_insights_summary(
    db: AsyncSession = Depends(get_db),
    _: Dict = Depends(require_role(["admin", "manager", "operator", "viewer"]))
) -> Dict[str, Any]:
    """
    Obtiene un resumen de insights.
    
    - **Requiere permisos:** admin, manager, operator o viewer
    - **Retorna:** Resumen con métricas agregadas
    """
    try:
        # Obtener estadísticas generales
        total_insights_query = select(func.count(MetaAdInsightsModel.id))
        total_result = await db.execute(total_insights_query)
        total_insights = total_result.scalar() or 0
        
        # Obtener fecha más reciente
        latest_date_query = select(func.max(MetaAdInsightsModel.date_start))
        latest_result = await db.execute(latest_date_query)
        latest_date = latest_result.scalar()
        
        # Métricas agregadas de los últimos 30 días
        thirty_days_ago = datetime.now() - timedelta(days=30)
        metrics_query = select(
            func.sum(MetaAdInsightsModel.spend),
            func.sum(MetaAdInsightsModel.impressions),
            func.sum(MetaAdInsightsModel.clicks),
            func.sum(MetaAdInsightsModel.conversions),
            func.sum(MetaAdInsightsModel.revenue)
        ).where(MetaAdInsightsModel.date_start >= thirty_days_ago.date())
        
        metrics_result = await db.execute(metrics_query)
        spend, impressions, clicks, conversions, revenue = metrics_result.one()
        
        summary = {
            "total_insights": total_insights,
            "latest_date": latest_date.isoformat() if latest_date else None,
            "last_30_days": {
                "spend": float(spend or 0),
                "impressions": int(impressions or 0),
                "clicks": int(clicks or 0),
                "conversions": int(conversions or 0),
                "revenue": float(revenue or 0),
                "roas": round(float(revenue or 0) / float(spend or 1), 2)
            }
        }
        
        return summary
        
    except Exception as e:
        logger.exception(f"Error getting insights summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/run")
async def run_insights_sync(
    days_back: int = Query(7, ge=1, le=90),
    db: AsyncSession = Depends(get_db),
    _: Dict = Depends(require_role(["admin", "manager"]))
) -> Dict[str, Any]:
    """
    Ejecuta sincronización completa de insights.
    
    - **Requiere permisos:** admin o manager
    - **Parámetros:** days_back - días hacia atrás para sincronizar
    """
    try:
        from .service import run_full_sync
        
        logger.info(f"Starting full sync via /run endpoint: {days_back} days")
        report = await run_full_sync(db, days_back=days_back, mode="stub")
        
        return {
            "status": "completed",
            "report": report
        }
        
    except Exception as e:
        logger.exception(f"Error in run endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sync/campaign/{campaign_id}")
async def sync_campaign_insights(
    campaign_id: str = Path(..., description="ID de la campaña"),
    days_back: int = Query(7, ge=1, le=90),
    db: AsyncSession = Depends(get_db),
    _: Dict = Depends(require_role(["admin", "manager"]))
) -> Dict[str, Any]:
    """
    Sincroniza insights de una campaña específica.
    
    - **Requiere permisos:** admin o manager
    - **Parámetros:** campaign_id, days_back
    """
    try:
        from .service import sync_campaign
        
        logger.info(f"Syncing campaign {campaign_id}: {days_back} days")
        report = await sync_campaign(db, campaign_id, days_back=days_back, mode="stub")
        
        return {
            "status": "completed",
            "report": report
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception(f"Error syncing campaign: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sync/adset/{adset_id}")
async def sync_adset_insights(
    adset_id: str = Path(..., description="ID del adset"),
    days_back: int = Query(7, ge=1, le=90),
    db: AsyncSession = Depends(get_db),
    _: Dict = Depends(require_role(["admin", "manager"]))
) -> Dict[str, Any]:
    """
    Sincroniza insights de un adset específico.
    
    - **Requiere permisos:** admin o manager
    - **Parámetros:** adset_id, days_back
    """
    try:
        from .service import sync_adset
        
        logger.info(f"Syncing adset {adset_id}: {days_back} days")
        report = await sync_adset(db, adset_id, days_back=days_back, mode="stub")
        
        return {
            "status": "completed",
            "report": report
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception(f"Error syncing adset: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sync/ad/{ad_id}")
async def sync_ad_insights(
    ad_id: str = Path(..., description="ID del ad"),
    days_back: int = Query(7, ge=1, le=90),
    db: AsyncSession = Depends(get_db),
    _: Dict = Depends(require_role(["admin", "manager"]))
) -> Dict[str, Any]:
    """
    Sincroniza insights de un ad específico.
    
    - **Requiere permisos:** admin o manager
    - **Parámetros:** ad_id, days_back
    """
    try:
        from .service import sync_ad
        
        logger.info(f"Syncing ad {ad_id}: {days_back} days")
        report = await sync_ad(db, ad_id, days_back=days_back, mode="stub")
        
        return {
            "status": "completed",
            "report": report
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception(f"Error syncing ad: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/last")
async def get_last_sync_info(
    db: AsyncSession = Depends(get_db),
    _: Dict = Depends(require_role(["admin", "manager", "operator"]))
) -> Dict[str, Any]:
    """
    Obtiene información de la última sincronización.
    
    - **Requiere permisos:** admin, manager u operator
    - **Retorna:** Info de la última sync ejecutada
    """
    try:
        # Obtener la última fecha de insights
        latest_query = select(
            func.max(MetaAdInsightsModel.date_start),
            func.count(MetaAdInsightsModel.id)
        )
        result = await db.execute(latest_query)
        latest_date, count = result.one()
        
        # Obtener scheduler para info de última sync
        scheduler = get_scheduler(mode="stub")
        last_run = scheduler.last_sync_time
        
        return {
            "last_sync_time": last_run.isoformat() if last_run else None,
            "latest_insight_date": latest_date.isoformat() if latest_date else None,
            "total_insights": count or 0,
            "scheduler_status": "running" if scheduler.is_running else "stopped"
        }
        
    except Exception as e:
        logger.exception(f"Error getting last sync info: {e}")
        raise HTTPException(status_code=500, detail=str(e))
