"""
Meta Full Autonomous Cycle Manager (PASO 10.11)

Ciclo autónomo end-to-end que integra todos los módulos Meta Ads.
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func

from app.meta_full_cycle.models import MetaCycleRunModel, MetaCycleActionLogModel
from app.models.database import (
    MetaCampaignModel,
    MetaAdsetModel,
    MetaAdModel,
    MetaAdInsightsModel,
)
from app.meta_ads_client.client import MetaAdsClient
from app.meta_insights_collector.collector import MetaInsightsCollector
from app.meta_ads_orchestrator.roas_engine import ROASEngine
from app.meta_budget_spike.spike_detector import SpikeDetector
from app.core.config import settings


logger = logging.getLogger(__name__)


class MetaFullCycleManager:
    """
    Gestor del ciclo autónomo completo de Meta Ads.
    
    Integra:
    - 10.1 Meta Models
    - 10.2 Meta Client
    - 10.3 Orchestrator
    - 10.4 A/B Testing
    - 10.5 ROAS Engine
    - 10.7 Insights Collector
    - 10.9 Spike Manager
    - 10.10 Creative Variants
    
    Flujo:
    1. STEP 1: Recolección (insights, campañas, ROAS, A/B, spikes)
    2. STEP 2: Decisiones automáticas (A/B winner, budget, spikes, fatigue)
    3. STEP 3: Acciones en Meta API
    4. STEP 4: Logging y persistencia
    """
    
    def __init__(self):
        self.meta_client = MetaAdsClient()
        self.current_run: Optional[MetaCycleRunModel] = None
        self.action_logs: List[MetaCycleActionLogModel] = []
        
    async def run_cycle(
        self,
        db: AsyncSession,
        triggered_by: str = "scheduler",
        mode: str = None,
    ) -> MetaCycleRunModel:
        """
        Ejecuta el ciclo completo autónomo.
        
        Args:
            db: Database session
            triggered_by: Origen de la ejecución ("scheduler", "manual", "api")
            mode: Modo de operación ("stub" o "live"). Default: settings.META_API_MODE
            
        Returns:
            MetaCycleRunModel con el resultado de la ejecución
        """
        mode = mode or settings.META_API_MODE
        start_time = datetime.utcnow()
        
        logger.info(f"🔄 Starting Meta Full Autonomous Cycle (mode={mode}, trigger={triggered_by})")
        
        # Create cycle run record
        self.current_run = MetaCycleRunModel(
            started_at=start_time,
            status="running",
            triggered_by=triggered_by,
            mode=mode,
            steps_executed=[],
            errors=[],
            stats_snapshot={},
        )
        db.add(self.current_run)
        await db.commit()
        await db.refresh(self.current_run)
        
        try:
            # STEP 1: Data Collection
            stats = await self._step_1_collection(db)
            self.current_run.stats_snapshot = stats
            self.current_run.steps_executed.append("step_1_collection")
            await db.commit()
            
            # STEP 2: Automated Decisions
            decisions = await self._step_2_decisions(db, stats)
            self.current_run.steps_executed.append("step_2_decisions")
            await db.commit()
            
            # STEP 3: Execute Actions via Meta API
            actions_results = await self._step_3_api_actions(db, decisions, mode)
            self.current_run.steps_executed.append("step_3_api_actions")
            await db.commit()
            
            # STEP 4: Finalize Logging
            await self._step_4_finalize(db, actions_results)
            self.current_run.steps_executed.append("step_4_finalize")
            
            # Mark as success
            self.current_run.status = "success"
            self.current_run.finished_at = datetime.utcnow()
            self.current_run.duration_ms = int(
                (self.current_run.finished_at - self.current_run.started_at).total_seconds() * 1000
            )
            
            await db.commit()
            await db.refresh(self.current_run)
            
            logger.info(
                f"✅ Cycle completed successfully in {self.current_run.duration_ms}ms. "
                f"Actions: {stats.get('actions_taken', 0)}"
            )
            
        except Exception as e:
            logger.error(f"❌ Cycle failed: {e}", exc_info=True)
            
            self.current_run.status = "failed"
            self.current_run.finished_at = datetime.utcnow()
            self.current_run.duration_ms = int(
                (self.current_run.finished_at - self.current_run.started_at).total_seconds() * 1000
            )
            self.current_run.errors.append({
                "step": "general",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            })
            
            await db.commit()
            await db.refresh(self.current_run)
            
        return self.current_run
    
    async def _step_1_collection(self, db: AsyncSession) -> Dict[str, Any]:
        """
        STEP 1: Recolección de datos.
        
        Carga:
        - Campañas activas
        - Insights recientes
        - Métricas ROAS
        - A/B tests activos
        - Spikes detectados
        """
        logger.info("📊 STEP 1: Data Collection")
        
        stats = {
            "campaigns_active": 0,
            "adsets_active": 0,
            "ads_active": 0,
            "total_spend_today": 0.0,
            "avg_roas": 0.0,
            "ab_tests_active": 0,
            "spikes_detected": 0,
            "variants_generated": 0,
            "actions_taken": 0,
        }
        
        try:
            # 1. Load active campaigns
            result = await db.execute(
                select(MetaCampaignModel).where(MetaCampaignModel.status == "ACTIVE")
            )
            campaigns = result.scalars().all()
            stats["campaigns_active"] = len(campaigns)
            
            # 2. Load active adsets
            result = await db.execute(
                select(MetaAdsetModel).where(MetaAdsetModel.status == "ACTIVE")
            )
            adsets = result.scalars().all()
            stats["adsets_active"] = len(adsets)
            
            # 3. Load active ads
            result = await db.execute(
                select(MetaAdModel).where(MetaAdModel.status == "ACTIVE")
            )
            ads = result.scalars().all()
            stats["ads_active"] = len(ads)
            
            # 4. Calculate total spend today
            today = datetime.utcnow().date()
            result = await db.execute(
                select(func.sum(MetaAdInsightsModel.spend))
                .where(
                    and_(
                        MetaAdInsightsModel.date_start >= today,
                        MetaAdInsightsModel.date_start < today + timedelta(days=1)
                    )
                )
            )
            total_spend = result.scalar()
            stats["total_spend_today"] = float(total_spend or 0.0)
            
            # 5. Calculate average ROAS (stub calculation)
            if stats["total_spend_today"] > 0:
                # In stub mode, use synthetic ROAS
                stats["avg_roas"] = 3.2  # Stub value
            
            # 6. Count A/B tests (stub)
            stats["ab_tests_active"] = 2  # Stub value
            
            # 7. Count spikes detected (stub)
            stats["spikes_detected"] = 1  # Stub value
            
            self._log_action(
                step="collection",
                action="load_data",
                input_snapshot={},
                output_snapshot=stats,
                success=True,
            )
            
            logger.info(f"📊 Collected: {stats['campaigns_active']} campaigns, {stats['adsets_active']} adsets")
            
        except Exception as e:
            logger.error(f"Error in collection step: {e}")
            self._log_action(
                step="collection",
                action="load_data",
                input_snapshot={},
                output_snapshot={},
                success=False,
                error_message=str(e),
            )
            raise
        
        return stats
    
    async def _step_2_decisions(
        self,
        db: AsyncSession,
        stats: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        STEP 2: Toma de decisiones automáticas.
        
        Decisiones:
        - A) A/B Test winner selection
        - B) Budget scaling basado en ROAS
        - C) Spike handling
        - D) Creative fatigue detection
        """
        logger.info("🧠 STEP 2: Automated Decisions")
        
        decisions = []
        
        try:
            # Decision A: A/B Test Winner Selection
            ab_decisions = await self._decision_a_ab_winner(db)
            decisions.extend(ab_decisions)
            
            # Decision B: ROAS-based Budget Scaling
            roas_decisions = await self._decision_b_roas_budget(db)
            decisions.extend(roas_decisions)
            
            # Decision C: Spike Handling
            spike_decisions = await self._decision_c_spike_handling(db)
            decisions.extend(spike_decisions)
            
            # Decision D: Creative Fatigue Detection
            fatigue_decisions = await self._decision_d_creative_fatigue(db)
            decisions.extend(fatigue_decisions)
            
            stats["actions_taken"] = len(decisions)
            
            logger.info(f"🧠 Made {len(decisions)} decisions")
            
        except Exception as e:
            logger.error(f"Error in decisions step: {e}")
            self._log_action(
                step="decisions",
                action="compute_decisions",
                input_snapshot=stats,
                output_snapshot={},
                success=False,
                error_message=str(e),
            )
            raise
        
        return decisions
    
    async def _decision_a_ab_winner(self, db: AsyncSession) -> List[Dict[str, Any]]:
        """
        Decision A: A/B Test winner selection.
        
        Lógica:
        - Si test > 48h y impresiones > 1000
        - Calcular ganador
        - Publicar ganador, desactivar perdedor
        """
        decisions = []
        
        # STUB: Simulamos que hay 1 test listo
        test_duration_hours = 72  # Stub
        impressions = 1500  # Stub
        
        if test_duration_hours >= 48 and impressions >= 1000:
            # Simular winner selection
            winner_ad_id = "23847656789012345"
            loser_ad_id = "23847656789012346"
            
            decisions.append({
                "type": "ab_winner",
                "action": "publish_winner",
                "entity_type": "ad",
                "entity_id": winner_ad_id,
                "metadata": {
                    "winner_ad_id": winner_ad_id,
                    "loser_ad_id": loser_ad_id,
                    "test_duration_hours": test_duration_hours,
                    "impressions": impressions,
                    "winner_ctr": 3.5,
                    "loser_ctr": 2.8,
                },
            })
            
            decisions.append({
                "type": "ab_winner",
                "action": "pause_loser",
                "entity_type": "ad",
                "entity_id": loser_ad_id,
                "metadata": {
                    "reason": "Lost A/B test",
                },
            })
            
            self._log_action(
                step="ab_decision",
                action="select_winner",
                input_snapshot={"test_duration_hours": test_duration_hours, "impressions": impressions},
                output_snapshot={"winner": winner_ad_id, "loser": loser_ad_id},
                success=True,
                entity_type="ad",
                entity_id=winner_ad_id,
            )
        
        return decisions
    
    async def _decision_b_roas_budget(self, db: AsyncSession) -> List[Dict[str, Any]]:
        """
        Decision B: ROAS-based budget scaling.
        
        Lógica:
        - ROAS > 3: Subir 20-40%
        - ROAS 1.5-3: Mantener
        - ROAS < 1.5: Bajar 20-40% o pausar
        """
        decisions = []
        
        # STUB: Simulamos ROAS de algunos adsets
        adsets_roas = [
            {"adset_id": "23847656789012350", "roas": 4.2, "current_budget": 100.0},
            {"adset_id": "23847656789012351", "roas": 2.5, "current_budget": 150.0},
            {"adset_id": "23847656789012352", "roas": 1.2, "current_budget": 200.0},
        ]
        
        for adset_data in adsets_roas:
            adset_id = adset_data["adset_id"]
            roas = adset_data["roas"]
            current_budget = adset_data["current_budget"]
            
            if roas > 3.0:
                # Scale up 30%
                new_budget = current_budget * 1.3
                decisions.append({
                    "type": "roas_scaling",
                    "action": "scale_up_30",
                    "entity_type": "adset",
                    "entity_id": adset_id,
                    "metadata": {
                        "roas": roas,
                        "old_budget": current_budget,
                        "new_budget": new_budget,
                        "reason": "High ROAS > 3.0",
                    },
                })
                
                self._log_action(
                    step="roas_decision",
                    action="scale_up_30",
                    input_snapshot={"roas": roas, "current_budget": current_budget},
                    output_snapshot={"new_budget": new_budget},
                    success=True,
                    entity_type="adset",
                    entity_id=adset_id,
                )
                
            elif roas < 1.5:
                # Scale down 30% or pause
                if current_budget > 50:
                    new_budget = current_budget * 0.7
                    decisions.append({
                        "type": "roas_scaling",
                        "action": "scale_down_30",
                        "entity_type": "adset",
                        "entity_id": adset_id,
                        "metadata": {
                            "roas": roas,
                            "old_budget": current_budget,
                            "new_budget": new_budget,
                            "reason": "Low ROAS < 1.5",
                        },
                    })
                else:
                    # Pause if budget already low
                    decisions.append({
                        "type": "roas_scaling",
                        "action": "pause_adset",
                        "entity_type": "adset",
                        "entity_id": adset_id,
                        "metadata": {
                            "roas": roas,
                            "reason": "Low ROAS < 1.5 and low budget",
                        },
                    })
                
                self._log_action(
                    step="roas_decision",
                    action="scale_down_30",
                    input_snapshot={"roas": roas, "current_budget": current_budget},
                    output_snapshot={"action": "scale_down" if current_budget > 50 else "pause"},
                    success=True,
                    entity_type="adset",
                    entity_id=adset_id,
                )
        
        return decisions
    
    async def _decision_c_spike_handling(self, db: AsyncSession) -> List[Dict[str, Any]]:
        """
        Decision C: Spike detection and handling.
        
        Lógica:
        - Positive spike + ROAS > 2: boost +15%
        - Negative spike: reduce -10% o pausar
        """
        decisions = []
        
        # STUB: Simulamos 1 positive spike
        spike = {
            "adset_id": "23847656789012353",
            "spike_type": "positive",
            "roas": 3.5,
            "current_budget": 120.0,
        }
        
        if spike["spike_type"] == "positive" and spike["roas"] > 2.0:
            new_budget = spike["current_budget"] * 1.15
            decisions.append({
                "type": "spike_handling",
                "action": "boost_15",
                "entity_type": "adset",
                "entity_id": spike["adset_id"],
                "metadata": {
                    "spike_type": "positive",
                    "roas": spike["roas"],
                    "old_budget": spike["current_budget"],
                    "new_budget": new_budget,
                },
            })
            
            self._log_action(
                step="spike_decision",
                action="boost_15",
                input_snapshot=spike,
                output_snapshot={"new_budget": new_budget},
                success=True,
                entity_type="adset",
                entity_id=spike["adset_id"],
            )
        
        return decisions
    
    async def _decision_d_creative_fatigue(self, db: AsyncSession) -> List[Dict[str, Any]]:
        """
        Decision D: Creative fatigue detection.
        
        Lógica:
        - Si CTR baja 30% vs media 7 días
        - Marcar creative como fatigado
        - Generar variante nueva
        """
        decisions = []
        
        # STUB: Simulamos 1 creative con fatiga
        creative = {
            "ad_id": "23847656789012354",
            "creative_id": "23847656789012355",
            "current_ctr": 2.1,
            "avg_ctr_7d": 3.2,
        }
        
        ctr_drop = (creative["avg_ctr_7d"] - creative["current_ctr"]) / creative["avg_ctr_7d"]
        
        if ctr_drop >= 0.30:  # 30% drop
            decisions.append({
                "type": "creative_fatigue",
                "action": "generate_variant",
                "entity_type": "ad",
                "entity_id": creative["ad_id"],
                "metadata": {
                    "creative_id": creative["creative_id"],
                    "current_ctr": creative["current_ctr"],
                    "avg_ctr_7d": creative["avg_ctr_7d"],
                    "ctr_drop_pct": ctr_drop * 100,
                    "variant_type": "reorder_fragments",
                },
            })
            
            self._log_action(
                step="fatigue_detection",
                action="generate_variant",
                input_snapshot=creative,
                output_snapshot={"ctr_drop_pct": ctr_drop * 100},
                success=True,
                entity_type="ad",
                entity_id=creative["ad_id"],
            )
        
        return decisions
    
    async def _step_3_api_actions(
        self,
        db: AsyncSession,
        decisions: List[Dict[str, Any]],
        mode: str
    ) -> List[Dict[str, Any]]:
        """
        STEP 3: Ejecuta acciones en Meta API.
        
        Acciones:
        - update_budget
        - pause_ad/adset
        - create_new_ad_variant
        - publish_winner_ad
        - sync_insights
        """
        logger.info(f"🚀 STEP 3: API Actions (mode={mode})")
        
        results = []
        
        for decision in decisions:
            try:
                action_type = decision["action"]
                entity_type = decision["entity_type"]
                entity_id = decision["entity_id"]
                
                if mode == "stub":
                    # Stub mode: simulate success
                    result = await self._execute_stub_action(decision)
                else:
                    # Live mode: real API calls
                    result = await self._execute_live_action(decision)
                
                results.append(result)
                
                self._log_action(
                    step="api_action",
                    action=action_type,
                    input_snapshot=decision,
                    output_snapshot=result,
                    success=result.get("success", True),
                    entity_type=entity_type,
                    entity_id=entity_id,
                )
                
            except Exception as e:
                logger.error(f"Error executing action {decision['action']}: {e}")
                self._log_action(
                    step="api_action",
                    action=decision["action"],
                    input_snapshot=decision,
                    output_snapshot={},
                    success=False,
                    error_message=str(e),
                    entity_type=decision.get("entity_type"),
                    entity_id=decision.get("entity_id"),
                )
                results.append({"success": False, "error": str(e)})
        
        logger.info(f"🚀 Executed {len(results)} actions")
        
        return results
    
    async def _execute_stub_action(self, decision: Dict[str, Any]) -> Dict[str, Any]:
        """Ejecuta acción en modo stub (simulado)"""
        action = decision["action"]
        
        # Simulate success
        return {
            "success": True,
            "mode": "stub",
            "action": action,
            "entity_id": decision.get("entity_id"),
            "message": f"Stub: {action} executed successfully",
        }
    
    async def _execute_live_action(self, decision: Dict[str, Any]) -> Dict[str, Any]:
        """Ejecuta acción en modo live (real Meta API)"""
        action = decision["action"]
        entity_type = decision["entity_type"]
        entity_id = decision["entity_id"]
        metadata = decision.get("metadata", {})
        
        # TODO: Implement real Meta API calls
        # For now, return stub response
        return {
            "success": True,
            "mode": "live",
            "action": action,
            "entity_id": entity_id,
            "message": f"Live: {action} executed (TODO: implement real API call)",
        }
    
    async def _step_4_finalize(
        self,
        db: AsyncSession,
        actions_results: List[Dict[str, Any]]
    ):
        """
        STEP 4: Finalizar y persistir logs.
        """
        logger.info("📝 STEP 4: Finalize Logging")
        
        # Save all action logs to database
        for log in self.action_logs:
            log.cycle_run_id = self.current_run.id
            db.add(log)
        
        await db.commit()
        
        logger.info(f"📝 Saved {len(self.action_logs)} action logs")
    
    def _log_action(
        self,
        step: str,
        action: str,
        input_snapshot: Dict[str, Any],
        output_snapshot: Dict[str, Any],
        success: bool,
        error_message: str = None,
        entity_type: str = None,
        entity_id: str = None,
    ):
        """
        Registra una acción en el log interno.
        """
        log = MetaCycleActionLogModel(
            step=step,
            action=action,
            input_snapshot=input_snapshot,
            output_snapshot=output_snapshot,
            success=success,
            error_message=error_message,
            entity_type=entity_type,
            entity_id=entity_id,
        )
        self.action_logs.append(log)
