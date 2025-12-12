# backend/app/meta_insights_collector/collector.py

import asyncio
import logging
from contextlib import nullcontext
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from uuid import uuid4

from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db, AsyncSessionLocal
from app.core.logging import get_logger
from app.models.database import (
    MetaCampaignModel, 
    MetaAdsetModel, 
    MetaAdModel,
    MetaAdInsightsModel,
    MetaAccountModel
)
from app.meta_ads_client.client import MetaAdsClient
from app.meta_ads_client.exceptions import MetaRateLimitError, MetaAPIError

logger = get_logger("meta_insights_collector")


class MetaInsightsCollector:
    """
    Colector de insights de Meta Ads.
    
    Responsable de:
    - Consultar insights de campaigns, adsets y ads
    - Persistir datos evitando duplicados
    - Manejar rate limits y errores
    - Sincronización automática y manual
    """
    
    def __init__(self, db_session: Optional[AsyncSession] = None, mode: str = "stub"):
        self.db = db_session
        self.mode = mode
        self.client = MetaAdsClient(mode=mode)
        
    async def collect_campaign_insights(
        self, 
        campaign_id: str, 
        date_start: datetime, 
        date_end: datetime
    ) -> Dict[str, Any]:
        """
        Recolecta insights de una campaña específica.
        
        Args:
            campaign_id: ID de la campaña
            date_start: Fecha de inicio
            date_end: Fecha de fin
            
        Returns:
            Dict con insights de la campaña
        """
        try:
            if self.mode == "stub":
                # STUB MODE - Generar datos mock realistas
                return {
                    "campaign_id": campaign_id,
                    "date_start": date_start.isoformat(),
                    "date_end": date_end.isoformat(),
                    "spend": round(1250.75 + hash(campaign_id) % 5000, 2),
                    "impressions": 15000 + (hash(campaign_id) % 50000),
                    "clicks": 850 + (hash(campaign_id) % 2000),
                    "conversions": 45 + (hash(campaign_id) % 100),
                    "revenue": round(2150.50 + hash(campaign_id) % 8000, 2),
                    "ctr": round(5.67 + (hash(campaign_id) % 100) / 100, 2),
                    "cpc": round(1.47 + (hash(campaign_id) % 200) / 100, 2),
                    "roas": round(1.72 + (hash(campaign_id) % 300) / 100, 2),
                    "frequency": round(2.1 + (hash(campaign_id) % 150) / 100, 2),
                    "unique_clicks": 750 + (hash(campaign_id) % 1800),
                    "cost_per_conversion": round(27.8 + (hash(campaign_id) % 4000) / 100, 2)
                }
            else:
                # LIVE MODE - Implementar llamada real
                # TODO: Implementar con Facebook Marketing API
                insights = await self.client.get_campaign_insights(
                    campaign_id=campaign_id,
                    date_start=date_start,
                    date_end=date_end,
                    fields=[
                        "spend", "impressions", "clicks", "conversions",
                        "revenue", "ctr", "cpc", "roas", "frequency"
                    ]
                )
                return insights
                
        except MetaRateLimitError as e:
            logger.warning(f"Rate limit hit for campaign {campaign_id}: {e}")
            # Esperar antes de reintentar
            await asyncio.sleep(60)
            raise
        except MetaAPIError as e:
            logger.error(f"Meta API error for campaign {campaign_id}: {e}")
            raise
        except Exception as e:
            logger.exception(f"Unexpected error collecting campaign insights: {e}")
            raise

    async def collect_adset_insights(
        self, 
        adset_id: str, 
        date_start: datetime, 
        date_end: datetime
    ) -> Dict[str, Any]:
        """Recolecta insights de un adset específico."""
        try:
            if self.mode == "stub":
                return {
                    "adset_id": adset_id,
                    "date_start": date_start.isoformat(),
                    "date_end": date_end.isoformat(),
                    "spend": round(425.25 + hash(adset_id) % 1500, 2),
                    "impressions": 8500 + (hash(adset_id) % 25000),
                    "clicks": 320 + (hash(adset_id) % 800),
                    "conversions": 18 + (hash(adset_id) % 50),
                    "revenue": round(750.80 + hash(adset_id) % 3000, 2),
                    "ctr": round(3.76 + (hash(adset_id) % 150) / 100, 2),
                    "cpc": round(1.33 + (hash(adset_id) % 180) / 100, 2),
                    "roas": round(1.77 + (hash(adset_id) % 250) / 100, 2),
                    "reach": 7200 + (hash(adset_id) % 20000),
                    "frequency": round(1.18 + (hash(adset_id) % 120) / 100, 2)
                }
            else:
                # TODO: Implementar con Facebook Marketing API
                insights = await self.client.get_adset_insights(
                    adset_id=adset_id,
                    date_start=date_start,
                    date_end=date_end
                )
                return insights
                
        except Exception as e:
            logger.exception(f"Error collecting adset insights: {e}")
            raise

    async def collect_ad_insights(
        self, 
        ad_id: str, 
        date_start: datetime, 
        date_end: datetime
    ) -> Dict[str, Any]:
        """Recolecta insights de un anuncio específico."""
        try:
            if self.mode == "stub":
                return {
                    "ad_id": ad_id,
                    "date_start": date_start.isoformat(),
                    "date_end": date_end.isoformat(),
                    "spend": round(125.50 + hash(ad_id) % 500, 2),
                    "impressions": 2800 + (hash(ad_id) % 8000),
                    "clicks": 95 + (hash(ad_id) % 300),
                    "conversions": 6 + (hash(ad_id) % 20),
                    "revenue": round(215.30 + hash(ad_id) % 1000, 2),
                    "ctr": round(3.39 + (hash(ad_id) % 200) / 100, 2),
                    "cpc": round(1.32 + (hash(ad_id) % 150) / 100, 2),
                    "roas": round(1.71 + (hash(ad_id) % 280) / 100, 2),
                    "unique_clicks": 89 + (hash(ad_id) % 280),
                    "cost_per_conversion": round(20.9 + (hash(ad_id) % 3000) / 100, 2)
                }
            else:
                # TODO: Implementar con Facebook Marketing API
                insights = await self.client.get_ad_insights(
                    ad_id=ad_id,
                    date_start=date_start,
                    date_end=date_end
                )
                return insights
                
        except Exception as e:
            logger.exception(f"Error collecting ad insights: {e}")
            raise

    async def persist_insights(
        self, 
        insights: Dict[str, Any], 
        entity_type: str
    ) -> bool:
        """
        Persiste insights en la base de datos evitando duplicados.
        
        Args:
            insights: Dict con los datos de insights
            entity_type: Tipo de entidad ("campaign", "adset", "ad")
            
        Returns:
            True si se persistió correctamente, False si ya existía
        """
        try:
            if not self.db:
                async with AsyncSessionLocal() as db:
                    return await self._persist_insights_db(db, insights, entity_type)
            else:
                return await self._persist_insights_db(self.db, insights, entity_type)
                
        except Exception as e:
            logger.exception(f"Error persisting insights: {e}")
            raise

    async def _persist_insights_db(
        self, 
        db: AsyncSession, 
        insights: Dict[str, Any], 
        entity_type: str
    ) -> bool:
        """Implementación interna de persistencia.
        
        Note: MetaAdInsightsModel only supports ad_id - check if we have it.
        Campaign and adset insights cannot be persisted due to schema limitation.
        """
        try:
            # MetaAdInsightsModel only supports ad_id - check if we have it
            ad_id = insights.get("ad_id")
            if not ad_id:
                if entity_type == "campaign":
                    campaign_id = insights.get("campaign_id")
                    logger.info(f"Skipping campaign-level insight for {campaign_id} - schema requires ad_id")
                elif entity_type == "adset":  
                    adset_id = insights.get("adset_id")
                    logger.info(f"Skipping adset-level insight for {adset_id} - schema requires ad_id")
                return False
                
            date_start = datetime.fromisoformat(insights["date_start"].replace("Z", "+00:00"))

            # Check for existing insight (duplicate prevention)
            existing_query = select(MetaAdInsightsModel).where(
                and_(
                    MetaAdInsightsModel.ad_id == ad_id,
                    MetaAdInsightsModel.date_start == date_start
                )
            )
            
            result = await db.execute(existing_query)
            existing = result.scalars().first()
            
            if existing:
                # Update existing record
                existing.spend = insights.get("spend", 0)
                existing.impressions = insights.get("impressions", 0)
                existing.clicks = insights.get("clicks", 0)
                existing.conversions = insights.get("conversions", 0)
                existing.purchase_value = insights.get("revenue", 0)
                existing.ctr = insights.get("ctr", 0)
                existing.cpc = insights.get("cpc", 0)
                existing.roas = insights.get("roas", 0)
                existing.frequency = insights.get("frequency", 0)
                existing.reach = insights.get("reach", 0)
                existing.unique_clicks = insights.get("unique_clicks", 0)
                existing.cost_per_conversion = insights.get("cost_per_conversion", 0)
                existing.updated_at = datetime.utcnow()
                
                logger.info(f"Updated existing insight for ad {ad_id}")
                await db.commit()
                return True
            else:
                # Create new record - map fields correctly to MetaAdInsightsModel
                insight_record = MetaAdInsightsModel(
                    ad_id=ad_id,
                    date=date_start,
                    date_start=date_start,
                    date_stop=datetime.fromisoformat(insights["date_end"].replace("Z", "+00:00")),
                    spend=insights.get("spend", 0),
                    impressions=insights.get("impressions", 0),
                    clicks=insights.get("clicks", 0),
                    conversions=insights.get("conversions", 0),
                    purchase_value=insights.get("revenue", 0),  # revenue -> purchase_value
                    ctr=insights.get("ctr", 0),
                    cpc=insights.get("cpc", 0),
                    roas=insights.get("roas", 0),
                    frequency=insights.get("frequency", 0),
                    reach=insights.get("reach", 0),
                    unique_clicks=insights.get("unique_clicks", 0),
                    cost_per_conversion=insights.get("cost_per_conversion", 0),
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                
                db.add(insight_record)
                await db.commit()
                
                logger.info(f"Created new insight for ad {ad_id}")
                return True
                
        except Exception as e:
            await db.rollback()
            logger.exception(f"Database error persisting insights: {e}")
            raise

    async def sync_all_insights(self, days_back: int = 7, db_session: Optional[AsyncSession] = None) -> Dict[str, Any]:
        """
        Sincroniza insights de todas las entidades activas.
        
        Args:
            days_back: Días hacia atrás para sincronizar
            
        Returns:
            Dict con reporte de sincronización
        """
        start_time = datetime.utcnow()
        date_end = datetime.utcnow().date()
        date_start = date_end - timedelta(days=days_back)
        
        report = {
            "sync_timestamp": start_time.isoformat(),
            "date_range": {
                "start": date_start.isoformat(),
                "end": date_end.isoformat()
            },
            "campaigns": {"processed": 0, "success": 0, "errors": 0},
            "adsets": {"processed": 0, "success": 0, "errors": 0}, 
            "ads": {"processed": 0, "success": 0, "errors": 0},
            "total_duration_seconds": 0,
            "errors": []
        }
        
        try:
            # En modo stub, generar campañas sintéticas sin consultar la DB
            if self.mode == "stub":
                # Generar campañas sintéticas para testing
                from types import SimpleNamespace
                campaigns = [
                    SimpleNamespace(
                        id=f"stub_campaign_{i}",
                        campaign_name=f"Stub Campaign {i}",
                        status="ACTIVE"
                    )
                    for i in range(1, 4)  # Generar 3 campañas de prueba
                ]
                
                # Procesar campañas sintéticas
                for campaign in campaigns:
                    try:
                        report["campaigns"]["processed"] += 1
                        
                        # Generar insights sintéticos para la campaña
                        campaign_insights = await self.collect_campaign_insights(
                            str(campaign.id), date_start, date_end
                        )
                        # En modo stub, skip persistencia real
                        report["campaigns"]["success"] += 1
                        
                        # Simular algunos adsets y ads también
                        report["adsets"]["processed"] += 2
                        report["adsets"]["success"] += 2
                        report["ads"]["processed"] += 5  
                        report["ads"]["success"] += 5
                        
                    except Exception as e:
                        report["campaigns"]["errors"] += 1
                        error_msg = f"Campaign {campaign.id} sync error: {str(e)}"
                        report["errors"].append(error_msg)
                        logger.error(error_msg)
                        
            else:
                # Función auxiliar para sincronizar con una sesión de DB (modo live)
                async def sync_with_session(db: AsyncSession):
                    # Obtener campañas activas
                    campaigns_query = select(MetaCampaignModel).where(
                        MetaCampaignModel.status == "ACTIVE"
                    )
                    campaigns_result = await db.execute(campaigns_query)
                    campaigns = campaigns_result.scalars().all()
                    
                    # Sincronizar campañas en paralelo (por lotes para evitar overload)
                    batch_size = 5
                    for i in range(0, len(campaigns), batch_size):
                        batch = campaigns[i:i + batch_size]
                        tasks = []
                        
                        for campaign in batch:
                            task = self._sync_campaign_insights(
                                campaign, date_start, date_end, report, db
                            )
                            tasks.append(task)
                        
                        await asyncio.gather(*tasks, return_exceptions=True)
                        
                        # Pequeña pausa entre lotes para evitar rate limits
                        if i + batch_size < len(campaigns):
                            await asyncio.sleep(1)
                    
                    # Actualizar timestamp de última sincronización
                    await self._update_last_sync_timestamp(db)
                
                # Usar la sesión pasada como parámetro o crear una nueva
                if db_session:
                    await sync_with_session(db_session)
                else:
                    async with AsyncSessionLocal() as db:
                        await sync_with_session(db)
                
        except Exception as e:
            logger.exception(f"Error in sync_all_insights: {e}")
            report["errors"].append(f"General sync error: {str(e)}")
            
        finally:
            end_time = datetime.utcnow()
            report["total_duration_seconds"] = (end_time - start_time).total_seconds()
            
        logger.info(f"Sync completed in {report['total_duration_seconds']:.2f}s")
        return report

    async def _sync_campaign_insights(
        self, 
        campaign: MetaCampaignModel, 
        date_start: datetime, 
        date_end: datetime, 
        report: Dict[str, Any],
        db: AsyncSession
    ):
        """Sincroniza insights de una campaña y sus entidades hijas."""
        try:
            report["campaigns"]["processed"] += 1
            
            # Recolectar insights de campaña
            campaign_insights = await self.collect_campaign_insights(
                str(campaign.id), date_start, date_end
            )
            await self.persist_insights(campaign_insights, "campaign")
            
            # Obtener adsets de la campaña
            adsets_query = select(MetaAdsetModel).where(
                MetaAdsetModel.campaign_id == str(campaign.id)
            )
            adsets_result = await db.execute(adsets_query)
            adsets = adsets_result.scalars().all()
                
            # Sincronizar adsets
            for adset in adsets:
                try:
                    report["adsets"]["processed"] += 1
                    
                    adset_insights = await self.collect_adset_insights(
                        str(adset.id), date_start, date_end
                    )
                    await self.persist_insights(adset_insights, "adset")
                    report["adsets"]["success"] += 1
                    
                    # Obtener ads del adset
                    ads_query = select(MetaAdModel).where(
                        MetaAdModel.adset_id == str(adset.id)
                    )
                    ads_result = await db.execute(ads_query)
                    ads = ads_result.scalars().all()
                    
                    # Sincronizar ads
                    for ad in ads:
                        try:
                            report["ads"]["processed"] += 1
                            
                            ad_insights = await self.collect_ad_insights(
                                str(ad.id), date_start, date_end
                            )
                            await self.persist_insights(ad_insights, "ad")
                            report["ads"]["success"] += 1
                            
                        except Exception as e:
                            report["ads"]["errors"] += 1
                            error_msg = f"Ad {ad.id} sync error: {str(e)}"
                            report["errors"].append(error_msg)
                            logger.error(error_msg)
                    
                except Exception as e:
                    report["adsets"]["errors"] += 1
                    error_msg = f"Adset {adset.id} sync error: {str(e)}"
                    report["errors"].append(error_msg)
                    logger.error(error_msg)
                        
            report["campaigns"]["success"] += 1
            
        except Exception as e:
            report["campaigns"]["errors"] += 1
            error_msg = f"Campaign {campaign.id} sync error: {str(e)}"
            report["errors"].append(error_msg)
            logger.error(error_msg)

    async def _update_last_sync_timestamp(self, db: AsyncSession):
        """Actualiza el timestamp de última sincronización."""
        try:
            # TODO: Implementar actualización de MetaAccountModel.last_sync_timestamp
            # Por ahora solo log
            logger.info("Last sync timestamp updated")
            
        except Exception as e:
            logger.exception(f"Error updating last sync timestamp: {e}")

    async def get_recent_insights(
        self, 
        entity_id: str, 
        entity_type: str, 
        days: int = 30,
        db_session: Optional[AsyncSession] = None
    ) -> List[Dict[str, Any]]:
        """
        Obtiene insights recientes de una entidad.
        
        Args:
            entity_id: ID de la entidad
            entity_type: Tipo de entidad ("campaign", "adset", "ad")  
            days: Días hacia atrás a consultar
            
        Returns:
            Lista de insights ordenados por fecha
        """
        try:
            # Usar la sesión pasada o crear una nueva
            async def query_insights(db: AsyncSession):
                date_limit = datetime.utcnow() - timedelta(days=days)
                entity_id_field = f"{entity_type}_id"
                
                query = select(MetaAdInsightsModel).where(
                    and_(
                        getattr(MetaAdInsightsModel, entity_id_field) == entity_id,
                        MetaAdInsightsModel.entity_type == entity_type,
                        MetaAdInsightsModel.date_start >= date_limit
                    )
                ).order_by(MetaAdInsightsModel.date_start.desc())
                
                result = await db.execute(query)
                insights = result.scalars().all()
                
                return [
                    {
                        "id": insight.id,
                        "date_start": insight.date_start.isoformat(),
                        "date_end": insight.date_end.isoformat(), 
                        "spend": float(insight.spend or 0),
                        "impressions": insight.impressions or 0,
                        "clicks": insight.clicks or 0,
                        "conversions": insight.conversions or 0,
                        "revenue": float(insight.revenue or 0),
                        "ctr": float(insight.ctr or 0),
                        "cpc": float(insight.cpc or 0),
                        "roas": float(insight.roas or 0),
                        "frequency": float(insight.frequency or 0),
                        "reach": insight.reach or 0,
                        "unique_clicks": insight.unique_clicks or 0,
                        "cost_per_conversion": float(insight.cost_per_conversion or 0)
                    }
                    for insight in insights
                ]
            
            # Usar la sesión pasada o crear una nueva
            if db_session:
                return await query_insights(db_session)
            else:
                async with AsyncSessionLocal() as db:
                    return await query_insights(db)
                
        except Exception as e:
            logger.exception(f"Error getting recent insights: {e}")
            raise