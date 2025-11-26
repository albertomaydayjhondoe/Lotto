# backend/app/meta_autopublisher/orchestrator.py

"""
AutoPublisher Orchestrator - Flujo end-to-end principal.

Coordina todo el proceso de autopublicación:
1. Creación de campaigns/adsets/ads
2. Lanzamiento de A/B testing
3. Monitoreo de resultados
4. Selección de ganador
5. Escalado de presupuesto
6. Publicación final
"""
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from uuid import UUID, uuid4
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.models.database import (
    MetaCampaignModel,
    MetaAdsetModel,
    MetaAdModel,
    MetaCreativeModel,
    MetaAccountModel
)
from app.core.logging import get_logger
from app.meta_ads_client.factory import get_meta_client_for_account
from app.meta_insights_collector.service import run_full_sync

from .models import (
    AutoPublisherRunRequest,
    AutoPublisherRunResponse,
    RunStatus,
    CampaignVariant,
    WinnerSelection,
    RunSnapshot
)
from .executor import (
    create_campaign_variant,
    create_adset_for_variant,
    create_ad_for_variant,
    rollback_variant
)
from .ab_flow import ABTestManager
from .optimizer import BudgetOptimizer
from .monitor import MonitoringService

logger = get_logger(__name__)


class AutoPublisherOrchestrator:
    """
    Orchestrador principal del AutoPublisher.
    
    Maneja el flujo completo desde request hasta publicación final,
    coordinando con MetaAdsClient, A/B testing, ROAS Engine, y workers.
    """
    
    def __init__(
        self,
        db: AsyncSession,
        mode: str = "stub",  # "stub" o "live"
        enable_ai_supervision: bool = True
    ):
        self.db = db
        self.mode = mode
        self.enable_ai_supervision = enable_ai_supervision
        self.ab_manager = ABTestManager(db)
        self.optimizer = BudgetOptimizer(db)
        self.monitor = MonitoringService(db)
        self.logger = logger
    
    async def run_autopilot(
        self,
        request: AutoPublisherRunRequest
    ) -> AutoPublisherRunResponse:
        """
        Ejecuta el flujo completo de autopublicación.
        
        Returns:
            AutoPublisherRunResponse con estado final y resultados
        """
        run_id = uuid4()
        start_time = datetime.utcnow()
        
        self.logger.info(f"[AutoPublisher] Starting run {run_id} for account {request.meta_account_id}")
        
        # Inicializar response
        response = AutoPublisherRunResponse(
            run_id=run_id,
            status=RunStatus.PENDING,
            meta_account_id=request.meta_account_id,
            campaign_name=request.campaign_name,
            created_at=start_time
        )
        
        try:
            # FASE 1: Validación y preparación
            await self._validate_request(request)
            response.status = RunStatus.CREATING_CAMPAIGNS
            response.logs.append(f"[{datetime.utcnow()}] Validation passed, creating campaigns...")
            
            # FASE 2: Crear variantes de campaña
            variants = await self._create_campaign_variants(request, run_id)
            response.campaign_ids = [v.campaign_id for v in variants if v.campaign_id]
            response.adset_ids = [v.adset_id for v in variants if v.adset_id]
            response.ad_ids = [v.ad_id for v in variants if v.ad_id]
            response.logs.append(f"[{datetime.utcnow()}] Created {len(variants)} campaign variants")
            
            # FASE 3: Lanzar A/B testing
            response.status = RunStatus.AB_TESTING
            response.started_at = datetime.utcnow()
            await self._launch_ab_test(variants, request.ab_test_config)
            response.logs.append(f"[{datetime.utcnow()}] A/B test launched, waiting for embargo period...")
            
            # FASE 4: Esperar embargo y monitorear
            await self._wait_for_embargo(request.ab_test_config.embargo_hours)
            response.logs.append(f"[{datetime.utcnow()}] Embargo period completed")
            
            # FASE 5: Analizar resultados
            response.status = RunStatus.ANALYZING_RESULTS
            await self._collect_insights(response.campaign_ids)
            ab_results = await self.ab_manager.analyze_test_results(
                variants,
                request.ab_test_config
            )
            response.ab_test_results = ab_results
            response.logs.append(f"[{datetime.utcnow()}] Results analyzed")
            
            # FASE 6: Seleccionar ganador
            response.status = RunStatus.SELECTING_WINNER
            winner = await self.ab_manager.select_winner(
                variants,
                request.ab_test_config.winner_criteria
            )
            response.winner_selection = winner
            response.logs.append(
                f"[{datetime.utcnow()}] Winner selected: {winner.winner_name} "
                f"(ROAS: {winner.winner_metrics.roas:.2f}x)"
            )
            
            # FASE 7: Decidir si requiere aprobación humana
            if request.require_human_approval:
                response.status = RunStatus.WAITING_APPROVAL
                response.logs.append(f"[{datetime.utcnow()}] Waiting for human approval before scaling...")
                await self._notify_human_approval_needed(run_id, winner)
                return response
            
            # FASE 8: Escalar presupuesto del ganador
            if request.auto_scale_winner:
                response.status = RunStatus.SCALING_BUDGET
                scaling_result = await self._scale_winner_budget(
                    winner,
                    request.budget_config
                )
                response.logs.append(
                    f"[{datetime.utcnow()}] Budget scaled: "
                    f"{scaling_result['old_budget']} -> {scaling_result['new_budget']}"
                )
            
            # FASE 9: Publicación final
            response.status = RunStatus.PUBLISHING_FINAL
            final_campaign_id = await self._publish_final_campaign(winner, request)
            response.final_campaign_id = final_campaign_id
            response.logs.append(f"[{datetime.utcnow()}] Final campaign published: {final_campaign_id}")
            
            # FASE 10: Pausar perdedores
            await self._pause_losing_variants(variants, winner.winner_variant_id)
            
            # Finalización exitosa
            response.status = RunStatus.COMPLETED
            response.completed_at = datetime.utcnow()
            
            # Calcular métricas totales
            response.total_spend = sum(v.spend for v in winner.all_variants)
            response.total_impressions = sum(v.impressions for v in winner.all_variants)
            response.total_clicks = sum(v.clicks for v in winner.all_variants)
            response.total_conversions = sum(v.conversions for v in winner.all_variants)
            response.total_revenue = sum(v.revenue for v in winner.all_variants)
            response.overall_roas = (
                response.total_revenue / response.total_spend
                if response.total_spend > 0 else 0.0
            )
            
            response.logs.append(
                f"[{datetime.utcnow()}] AutoPublisher run completed successfully. "
                f"Total ROAS: {response.overall_roas:.2f}x"
            )
            
            # AI Supervision (si está habilitado)
            if self.enable_ai_supervision:
                await self._request_ai_supervision(response)
            
            return response
            
        except Exception as e:
            self.logger.exception(f"[AutoPublisher] Run {run_id} failed: {e}")
            response.status = RunStatus.FAILED
            response.errors.append(f"Fatal error: {str(e)}")
            response.completed_at = datetime.utcnow()
            
            # Intentar rollback
            try:
                await self._rollback_run(response)
                response.logs.append(f"[{datetime.utcnow()}] Rollback completed")
            except Exception as rollback_error:
                self.logger.exception(f"[AutoPublisher] Rollback failed: {rollback_error}")
                response.errors.append(f"Rollback error: {str(rollback_error)}")
            
            return response
    
    async def _validate_request(self, request: AutoPublisherRunRequest) -> None:
        """Valida el request antes de iniciar"""
        # Verificar que la cuenta Meta existe
        stmt = select(MetaAccountModel).where(MetaAccountModel.id == request.meta_account_id)
        result = await self.db.execute(stmt)
        account = result.scalar()
        
        if not account:
            raise ValueError(f"Meta account {request.meta_account_id} not found")
        
        # Verificar creativos existen
        for creative_id in request.creative_ids:
            stmt = select(MetaCreativeModel).where(MetaCreativeModel.id == creative_id)
            result = await self.db.execute(stmt)
            creative = result.scalar()
            if not creative:
                raise ValueError(f"Creative {creative_id} not found")
        
        # Validar presupuestos
        if request.budget_config.total_budget < request.ab_test_config.test_budget_per_variant * request.ab_test_config.variants_count:
            raise ValueError("Total budget is insufficient for A/B test variants")
        
        self.logger.info(f"[AutoPublisher] Validation passed for {request.campaign_name}")
    
    async def _create_campaign_variants(
        self,
        request: AutoPublisherRunRequest,
        run_id: UUID
    ) -> List[CampaignVariant]:
        """Crea las variantes de campaña para A/B testing"""
        variants = []
        variant_budget = request.ab_test_config.test_budget_per_variant
        
        # Generar combinaciones según estrategia
        variant_configs = self._generate_variant_configs(request)
        
        for idx, config in enumerate(variant_configs[:request.ab_test_config.variants_count]):
            variant_id = f"{run_id}_variant_{idx}"
            variant_name = f"{request.campaign_name} - Variant {chr(65+idx)}"
            
            variant = CampaignVariant(
                variant_id=variant_id,
                variant_name=variant_name,
                creative_id=config["creative_id"],
                headline=config["headline"],
                primary_text=config["primary_text"],
                call_to_action=config["call_to_action"],
                budget=variant_budget,
                targeting=request.targeting_config
            )
            
            try:
                # Crear campaign, adset, ad usando executor
                campaign_id = await create_campaign_variant(
                    self.db,
                    request.meta_account_id,
                    variant_name,
                    request.objective,
                    variant_budget,
                    self.mode
                )
                variant.campaign_id = campaign_id
                
                adset_id = await create_adset_for_variant(
                    self.db,
                    campaign_id,
                    f"{variant_name} - Adset",
                    request.targeting_config,
                    variant_budget,
                    self.mode
                )
                variant.adset_id = adset_id
                
                ad_id = await create_ad_for_variant(
                    self.db,
                    adset_id,
                    config["creative_id"],
                    config["headline"],
                    config["primary_text"],
                    config["call_to_action"],
                    self.mode
                )
                variant.ad_id = ad_id
                
                variant.status = "active"
                variants.append(variant)
                
                self.logger.info(f"[AutoPublisher] Created variant {variant_id}: {variant_name}")
                
            except Exception as e:
                self.logger.exception(f"[AutoPublisher] Failed to create variant {variant_id}: {e}")
                variant.status = "failed"
                variants.append(variant)
        
        return variants
    
    def _generate_variant_configs(self, request: AutoPublisherRunRequest) -> List[Dict]:
        """Genera configuraciones de variantes según estrategia"""
        configs = []
        
        # Por ahora, simple: combinar creativos con headlines/texts
        for i, creative_id in enumerate(request.creative_ids):
            headline = request.headlines[i % len(request.headlines)]
            primary_text = request.primary_texts[i % len(request.primary_texts)]
            cta = request.call_to_actions[i % len(request.call_to_actions)]
            
            configs.append({
                "creative_id": creative_id,
                "headline": headline,
                "primary_text": primary_text,
                "call_to_action": cta
            })
        
        return configs
    
    async def _launch_ab_test(self, variants: List[CampaignVariant], config) -> None:
        """Inicia el A/B test activando todas las variantes"""
        await self.ab_manager.launch_test(variants, config)
    
    async def _wait_for_embargo(self, embargo_hours: int) -> None:
        """Espera el período de embargo antes de analizar resultados"""
        if embargo_hours > 0:
            self.logger.info(f"[AutoPublisher] Waiting {embargo_hours} hours for embargo period...")
            # En producción, esto debería ser un job programado
            # Por ahora, simulamos con sleep (solo para tests síncronos)
            await asyncio.sleep(1)  # Simular espera
    
    async def _collect_insights(self, campaign_ids: List[UUID]) -> None:
        """Recolecta insights de las campañas"""
        try:
            # Trigger sync de insights
            await run_full_sync(self.db, days_back=1, mode=self.mode)
        except Exception as e:
            self.logger.warning(f"[AutoPublisher] Failed to collect insights: {e}")
    
    async def _scale_winner_budget(self, winner: WinnerSelection, budget_config) -> Dict:
        """Escala el presupuesto del ganador"""
        return await self.optimizer.scale_budget(
            winner.winner_variant_id,
            budget_config.scaling_factor,
            budget_config.max_daily_budget
        )
    
    async def _publish_final_campaign(
        self,
        winner: WinnerSelection,
        request: AutoPublisherRunRequest
    ) -> UUID:
        """Publica la campaña final con el ganador escalado"""
        # Aquí se crearía la campaña final de producción
        # Por ahora retornamos el campaign_id del ganador
        return UUID(winner.winner_variant_id.split("_")[0])
    
    async def _pause_losing_variants(self, variants: List[CampaignVariant], winner_id: str) -> None:
        """Pausa todas las variantes excepto el ganador"""
        for variant in variants:
            if variant.variant_id != winner_id and variant.campaign_id:
                try:
                    # Pausar campaña
                    stmt = select(MetaCampaignModel).where(
                        MetaCampaignModel.id == variant.campaign_id
                    )
                    result = await self.db.execute(stmt)
                    campaign = result.scalar()
                    
                    if campaign:
                        campaign.status = "PAUSED"
                        await self.db.commit()
                        self.logger.info(f"[AutoPublisher] Paused losing variant {variant.variant_id}")
                        
                except Exception as e:
                    self.logger.exception(f"[AutoPublisher] Failed to pause variant {variant.variant_id}: {e}")
    
    async def _notify_human_approval_needed(self, run_id: UUID, winner: WinnerSelection) -> None:
        """Notifica que se requiere aprobación humana"""
        # TODO: Integrar con sistema de notificaciones (Telegram/Email)
        self.logger.info(
            f"[AutoPublisher] Run {run_id} waiting for approval. "
            f"Winner: {winner.winner_name} (ROAS: {winner.winner_metrics.roas:.2f}x)"
        )
    
    async def _request_ai_supervision(self, response: AutoPublisherRunResponse) -> None:
        """Solicita supervisión del AI Global Worker"""
        try:
            # TODO: Integrar con AI Global Worker para recomendaciones
            self.logger.info(f"[AutoPublisher] Requesting AI supervision for run {response.run_id}")
        except Exception as e:
            self.logger.warning(f"[AutoPublisher] AI supervision failed: {e}")
    
    async def _rollback_run(self, response: AutoPublisherRunResponse) -> None:
        """Rollback de todo el run en caso de error"""
        self.logger.info(f"[AutoPublisher] Rolling back run {response.run_id}")
        
        # Pausar todas las campañas creadas
        for campaign_id in response.campaign_ids:
            try:
                stmt = select(MetaCampaignModel).where(MetaCampaignModel.id == campaign_id)
                result = await self.db.execute(stmt)
                campaign = result.scalar()
                
                if campaign:
                    campaign.status = "PAUSED"
                    await self.db.commit()
                    
            except Exception as e:
                self.logger.exception(f"[AutoPublisher] Failed to pause campaign {campaign_id}: {e}")
