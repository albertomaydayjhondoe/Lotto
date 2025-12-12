# backend/app/meta_autopublisher/executor.py

"""
Executor - Tareas idempotentes para crear entidades en Meta.

Funciones atómicas que crean campaign/adset/ad/creative con:
- Idempotencia (deduplicación)
- Rollback automático
- Integración con MetaAdsClient
- Logging en PublishLog
"""
from datetime import datetime
from typing import Dict, Optional, Any
from uuid import UUID, uuid4
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.database import (
    MetaCampaignModel,
    MetaAdsetModel,
    MetaAdModel,
    MetaCreativeModel,
    PublishLogModel
)
from app.core.logging import get_logger
from app.meta_ads_client.factory import get_meta_client_for_account

from .models import TargetingConfig

logger = get_logger(__name__)


async def create_campaign_variant(
    db: AsyncSession,
    meta_account_id: UUID,
    campaign_name: str,
    objective: str,
    budget: float,
    mode: str = "stub"
) -> UUID:
    """
    Crea una campaña Meta de forma idempotente.
    
    Returns:
        UUID de la campaña creada
    """
    # Verificar si ya existe (deduplicación)
    stmt = select(MetaCampaignModel).where(
        MetaCampaignModel.meta_account_id == meta_account_id,
        MetaCampaignModel.campaign_name == campaign_name
    )
    result = await db.execute(stmt)
    existing = result.scalar()
    
    if existing:
        logger.info(f"[Executor] Campaign '{campaign_name}' already exists: {existing.id}")
        return existing.id
    
    # Crear campaña
    campaign_id = uuid4()
    
    try:
        # Obtener cliente Meta
        client = await get_meta_client_for_account(db, meta_account_id, mode=mode)
        
        # Crear en Meta API
        meta_campaign_id = await client.create_campaign(
            name=campaign_name,
            objective=objective,
            status="PAUSED"  # Empezar pausado
        )
        
        # Crear en base de datos
        campaign = MetaCampaignModel(
            id=campaign_id,
            meta_account_id=meta_account_id,
            campaign_id=meta_campaign_id,
            campaign_name=campaign_name,
            objective=objective,
            status="PAUSED",
            daily_budget=budget
        )
        
        db.add(campaign)
        await db.commit()
        
        logger.info(f"[Executor] Created campaign '{campaign_name}': {campaign_id}")
        return campaign_id
        
    except Exception as e:
        await db.rollback()
        logger.exception(f"[Executor] Failed to create campaign '{campaign_name}': {e}")
        raise


async def create_adset_for_variant(
    db: AsyncSession,
    campaign_id: UUID,
    adset_name: str,
    targeting: TargetingConfig,
    budget: float,
    mode: str = "stub"
) -> UUID:
    """
    Crea un adset Meta de forma idempotente.
    
    Returns:
        UUID del adset creado
    """
    # Verificar si ya existe
    stmt = select(MetaAdsetModel).where(
        MetaAdsetModel.campaign_id == campaign_id,
        MetaAdsetModel.adset_name == adset_name
    )
    result = await db.execute(stmt)
    existing = result.scalar()
    
    if existing:
        logger.info(f"[Executor] Adset '{adset_name}' already exists: {existing.id}")
        return existing.id
    
    # Obtener campaña
    stmt = select(MetaCampaignModel).where(MetaCampaignModel.id == campaign_id)
    result = await db.execute(stmt)
    campaign = result.scalar()
    
    if not campaign:
        raise ValueError(f"Campaign {campaign_id} not found")
    
    adset_id = uuid4()
    
    try:
        # Obtener cliente Meta
        client = await get_meta_client_for_account(
            db,
            campaign.meta_account_id,
            mode=mode
        )
        
        # Convertir targeting a formato Meta
        targeting_spec = {
            "geo_locations": {"countries": targeting.countries},
            "age_min": targeting.age_min,
            "age_max": targeting.age_max,
            "genders": [1] if targeting.gender == "male" else [2] if targeting.gender == "female" else [0],
            "publisher_platforms": ["instagram"] if "instagram" in targeting.placements else ["facebook"]
        }
        
        # Crear en Meta API
        meta_adset_id = await client.create_adset(
            campaign_id=campaign.campaign_id,
            name=adset_name,
            targeting=targeting_spec,
            daily_budget=budget,
            billing_event="IMPRESSIONS",
            optimization_goal="REACH"
        )
        
        # Crear en base de datos
        adset = MetaAdsetModel(
            id=adset_id,
            campaign_id=campaign_id,
            adset_id=meta_adset_id,
            adset_name=adset_name,
            status="PAUSED",
            daily_budget=budget,
            targeting=targeting.dict(),
            age_min=targeting.age_min,
            age_max=targeting.age_max,
            gender=targeting.gender,
            locations={"countries": targeting.countries},
            placements=targeting.placements
        )
        
        db.add(adset)
        await db.commit()
        
        logger.info(f"[Executor] Created adset '{adset_name}': {adset_id}")
        return adset_id
        
    except Exception as e:
        await db.rollback()
        logger.exception(f"[Executor] Failed to create adset '{adset_name}': {e}")
        raise


async def create_ad_for_variant(
    db: AsyncSession,
    adset_id: UUID,
    creative_id: UUID,
    headline: str,
    primary_text: str,
    call_to_action: str,
    mode: str = "stub"
) -> UUID:
    """
    Crea un ad Meta de forma idempotente.
    
    Returns:
        UUID del ad creado
    """
    # Verificar si ya existe
    stmt = select(MetaAdModel).where(
        MetaAdModel.adset_id == adset_id,
        MetaAdModel.headline == headline,
        MetaAdModel.primary_text == primary_text
    )
    result = await db.execute(stmt)
    existing = result.scalar()
    
    if existing:
        logger.info(f"[Executor] Ad with headline '{headline}' already exists: {existing.id}")
        return existing.id
    
    # Obtener adset y campaign
    stmt = select(MetaAdsetModel).where(MetaAdsetModel.id == adset_id)
    result = await db.execute(stmt)
    adset = result.scalar()
    
    if not adset:
        raise ValueError(f"Adset {adset_id} not found")
    
    stmt = select(MetaCampaignModel).where(MetaCampaignModel.id == adset.campaign_id)
    result = await db.execute(stmt)
    campaign = result.scalar()
    
    if not campaign:
        raise ValueError(f"Campaign {adset.campaign_id} not found")
    
    # Obtener creative
    stmt = select(MetaCreativeModel).where(MetaCreativeModel.id == creative_id)
    result = await db.execute(stmt)
    creative = result.scalar()
    
    if not creative:
        raise ValueError(f"Creative {creative_id} not found")
    
    ad_id = uuid4()
    ad_name = f"{adset.adset_name} - Ad"
    
    try:
        # Obtener cliente Meta
        client = await get_meta_client_for_account(
            db,
            campaign.meta_account_id,
            mode=mode
        )
        
        # Crear creative en Meta primero (si no existe)
        meta_creative_id = creative.creative_id
        if not meta_creative_id:
            meta_creative_id = await client.create_creative(
                name=f"Creative {creative_id}",
                object_story_spec={
                    "page_id": "123456789",  # TODO: Get from account
                    "instagram_actor_id": "123456789",
                    "link_data": {
                        "message": primary_text,
                        "link": "https://example.com",  # TODO: Get from creative
                        "name": headline,
                        "call_to_action": {
                            "type": call_to_action
                        }
                    }
                }
            )
            
            # Actualizar creative en DB
            creative.creative_id = meta_creative_id
            await db.commit()
        
        # Crear ad en Meta API
        meta_ad_id = await client.create_ad(
            adset_id=adset.adset_id,
            name=ad_name,
            creative_id=meta_creative_id,
            status="PAUSED"
        )
        
        # Crear en base de datos
        ad = MetaAdModel(
            id=ad_id,
            adset_id=adset_id,
            creative_id=creative_id,
            ad_id=meta_ad_id,
            ad_name=ad_name,
            status="PAUSED",
            headline=headline,
            primary_text=primary_text,
            call_to_action=call_to_action
        )
        
        db.add(ad)
        await db.commit()
        
        logger.info(f"[Executor] Created ad '{ad_name}': {ad_id}")
        return ad_id
        
    except Exception as e:
        await db.rollback()
        logger.exception(f"[Executor] Failed to create ad '{ad_name}': {e}")
        raise


async def rollback_variant(
    db: AsyncSession,
    campaign_id: Optional[UUID] = None,
    adset_id: Optional[UUID] = None,
    ad_id: Optional[UUID] = None,
    mode: str = "stub"
) -> None:
    """
    Rollback de una variante (pausa y marca para eliminación).
    """
    try:
        if ad_id:
            stmt = select(MetaAdModel).where(MetaAdModel.id == ad_id)
            result = await db.execute(stmt)
            ad = result.scalar()
            if ad:
                ad.status = "DELETED"
                logger.info(f"[Executor] Rolled back ad {ad_id}")
        
        if adset_id:
            stmt = select(MetaAdsetModel).where(MetaAdsetModel.id == adset_id)
            result = await db.execute(stmt)
            adset = result.scalar()
            if adset:
                adset.status = "DELETED"
                logger.info(f"[Executor] Rolled back adset {adset_id}")
        
        if campaign_id:
            stmt = select(MetaCampaignModel).where(MetaCampaignModel.id == campaign_id)
            result = await db.execute(stmt)
            campaign = result.scalar()
            if campaign:
                campaign.status = "DELETED"
                logger.info(f"[Executor] Rolled back campaign {campaign_id}")
        
        await db.commit()
        
    except Exception as e:
        await db.rollback()
        logger.exception(f"[Executor] Rollback failed: {e}")
        raise


async def activate_campaign(
    db: AsyncSession,
    campaign_id: UUID,
    mode: str = "stub"
) -> None:
    """Activa una campaña (y sus adsets/ads)."""
    stmt = select(MetaCampaignModel).where(MetaCampaignModel.id == campaign_id)
    result = await db.execute(stmt)
    campaign = result.scalar()
    
    if not campaign:
        raise ValueError(f"Campaign {campaign_id} not found")
    
    try:
        # Activar en Meta API
        client = await get_meta_client_for_account(
            db,
            campaign.meta_account_id,
            mode=mode
        )
        
        await client.update_campaign_status(campaign.campaign_id, "ACTIVE")
        
        # Actualizar en DB
        campaign.status = "ACTIVE"
        await db.commit()
        
        logger.info(f"[Executor] Activated campaign {campaign_id}")
        
    except Exception as e:
        await db.rollback()
        logger.exception(f"[Executor] Failed to activate campaign {campaign_id}: {e}")
        raise
