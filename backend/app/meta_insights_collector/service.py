# backend/app/meta_insights_collector/service.py

"""
Service layer para sincronización de insights de Meta Ads.
Proporciona funciones de alto nivel con manejo de transacciones y rollback automático.
"""

from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.logging import get_logger
from app.models.database import (
    MetaCampaignModel,
    MetaAdsetModel,
    MetaAdModel
)
from .collector import MetaInsightsCollector

logger = get_logger("meta_insights_service")


async def run_full_sync(
    db: AsyncSession,
    days_back: int = 7,
    mode: str = "stub"
) -> Dict[str, Any]:
    """
    Ejecuta sincronización completa de todos los insights.
    
    Args:
        db: Sesión de base de datos
        days_back: Días hacia atrás para sincronizar
        mode: Modo de operación ("stub" o "live")
        
    Returns:
        Reporte de sincronización con estadísticas
    """
    try:
        collector = MetaInsightsCollector(mode=mode)
        
        date_end = datetime.now()
        date_start = date_end - timedelta(days=days_back)
        
        logger.info(f"Starting full sync: {date_start.date()} to {date_end.date()}")
        
        report = await collector.collect_all_insights(
            date_start=date_start,
            date_end=date_end,
            db=db
        )
        
        logger.info(f"Full sync completed: {report['total_insights']} insights collected")
        
        return report
        
    except Exception as e:
        logger.exception(f"Error in run_full_sync: {e}")
        await db.rollback()
        raise


async def sync_campaign(
    db: AsyncSession,
    campaign_id: str,
    days_back: int = 7,
    mode: str = "stub"
) -> Dict[str, Any]:
    """
    Sincroniza insights de una campaña específica.
    
    Args:
        db: Sesión de base de datos
        campaign_id: ID de la campaña (puede ser UUID o campaign_id de Meta)
        days_back: Días hacia atrás para sincronizar
        mode: Modo de operación ("stub" o "live")
        
    Returns:
        Reporte de sincronización
    """
    try:
        collector = MetaInsightsCollector(mode=mode)
        
        # Buscar campaña
        try:
            # Intentar como UUID primero
            campaign_uuid = UUID(campaign_id)
            query = select(MetaCampaignModel).where(MetaCampaignModel.id == campaign_uuid)
        except ValueError:
            # Si no es UUID, buscar por campaign_id de Meta
            query = select(MetaCampaignModel).where(MetaCampaignModel.campaign_id == campaign_id)
        
        result = await db.execute(query)
        campaign = result.scalar_one_or_none()
        
        if not campaign:
            raise ValueError(f"Campaign not found: {campaign_id}")
        
        date_end = datetime.now()
        date_start = date_end - timedelta(days=days_back)
        
        logger.info(f"Syncing campaign {campaign.campaign_name}: {date_start.date()} to {date_end.date()}")
        
        # Recolectar insights
        insights = await collector.collect_campaign_insights(
            campaign_id=campaign.campaign_id,
            date_start=date_start,
            date_end=date_end,
            db=db
        )
        
        # Guardar en DB
        saved_count = await collector.save_insights_to_db(
            insights=insights,
            entity_type="campaign",
            entity_id=campaign.campaign_id,
            db=db
        )
        
        report = {
            "campaign_id": str(campaign.id),
            "campaign_name": campaign.campaign_name,
            "insights_collected": len(insights),
            "insights_saved": saved_count,
            "date_range": {
                "start": date_start.date().isoformat(),
                "end": date_end.date().isoformat()
            }
        }
        
        logger.info(f"Campaign sync completed: {saved_count}/{len(insights)} insights saved")
        
        return report
        
    except Exception as e:
        logger.exception(f"Error in sync_campaign: {e}")
        await db.rollback()
        raise


async def sync_adset(
    db: AsyncSession,
    adset_id: str,
    days_back: int = 7,
    mode: str = "stub"
) -> Dict[str, Any]:
    """
    Sincroniza insights de un adset específico.
    
    Args:
        db: Sesión de base de datos
        adset_id: ID del adset (puede ser UUID o adset_id de Meta)
        days_back: Días hacia atrás para sincronizar
        mode: Modo de operación ("stub" o "live")
        
    Returns:
        Reporte de sincronización
    """
    try:
        collector = MetaInsightsCollector(mode=mode)
        
        # Buscar adset
        try:
            # Intentar como UUID primero
            adset_uuid = UUID(adset_id)
            query = select(MetaAdsetModel).where(MetaAdsetModel.id == adset_uuid)
        except ValueError:
            # Si no es UUID, buscar por adset_id de Meta
            query = select(MetaAdsetModel).where(MetaAdsetModel.adset_id == adset_id)
        
        result = await db.execute(query)
        adset = result.scalar_one_or_none()
        
        if not adset:
            raise ValueError(f"Adset not found: {adset_id}")
        
        date_end = datetime.now()
        date_start = date_end - timedelta(days=days_back)
        
        logger.info(f"Syncing adset {adset.adset_name}: {date_start.date()} to {date_end.date()}")
        
        # Recolectar insights
        insights = await collector.collect_adset_insights(
            adset_id=adset.adset_id,
            date_start=date_start,
            date_end=date_end,
            db=db
        )
        
        # Guardar en DB
        saved_count = await collector.save_insights_to_db(
            insights=insights,
            entity_type="adset",
            entity_id=adset.adset_id,
            db=db
        )
        
        report = {
            "adset_id": str(adset.id),
            "adset_name": adset.adset_name,
            "insights_collected": len(insights),
            "insights_saved": saved_count,
            "date_range": {
                "start": date_start.date().isoformat(),
                "end": date_end.date().isoformat()
            }
        }
        
        logger.info(f"Adset sync completed: {saved_count}/{len(insights)} insights saved")
        
        return report
        
    except Exception as e:
        logger.exception(f"Error in sync_adset: {e}")
        await db.rollback()
        raise


async def sync_ad(
    db: AsyncSession,
    ad_id: str,
    days_back: int = 7,
    mode: str = "stub"
) -> Dict[str, Any]:
    """
    Sincroniza insights de un ad específico.
    
    Args:
        db: Sesión de base de datos
        ad_id: ID del ad (puede ser UUID o ad_id de Meta)
        days_back: Días hacia atrás para sincronizar
        mode: Modo de operación ("stub" o "live")
        
    Returns:
        Reporte de sincronización
    """
    try:
        collector = MetaInsightsCollector(mode=mode)
        
        # Buscar ad
        try:
            # Intentar como UUID primero
            ad_uuid = UUID(ad_id)
            query = select(MetaAdModel).where(MetaAdModel.id == ad_uuid)
        except ValueError:
            # Si no es UUID, buscar por ad_id de Meta
            query = select(MetaAdModel).where(MetaAdModel.ad_id == ad_id)
        
        result = await db.execute(query)
        ad = result.scalar_one_or_none()
        
        if not ad:
            raise ValueError(f"Ad not found: {ad_id}")
        
        date_end = datetime.now()
        date_start = date_end - timedelta(days=days_back)
        
        logger.info(f"Syncing ad {ad.ad_name}: {date_start.date()} to {date_end.date()}")
        
        # Recolectar insights
        insights = await collector.collect_ad_insights(
            ad_id=ad.ad_id,
            date_start=date_start,
            date_end=date_end,
            db=db
        )
        
        # Guardar en DB
        saved_count = await collector.save_insights_to_db(
            insights=insights,
            entity_type="ad",
            entity_id=ad.ad_id,
            db=db
        )
        
        report = {
            "ad_id": str(ad.id),
            "ad_name": ad.ad_name,
            "insights_collected": len(insights),
            "insights_saved": saved_count,
            "date_range": {
                "start": date_start.date().isoformat(),
                "end": date_end.date().isoformat()
            }
        }
        
        logger.info(f"Ad sync completed: {saved_count}/{len(insights)} insights saved")
        
        return report
        
    except Exception as e:
        logger.exception(f"Error in sync_ad: {e}")
        await db.rollback()
        raise
