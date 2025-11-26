"""
Spike Detector Engine para Meta Budget SPIKE Manager.
Detecta picos de rendimiento/gasto usando análisis estadístico.
"""

import statistics
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy.orm import Session

from app.core.config import settings
from app.meta_budget_spike.models import (
    MetricsSnapshot,
    RiskLevel,
    ScaleAction,
    SpikeDetectionResult,
    SpikeType,
)
from app.meta_insights_collector.collector import MetaInsightsCollector


class SpikeDetector:
    """
    Motor de detección de spikes usando:
    - Z-Score dinámico
    - Rolling averages (1h, 6h, 24h)
    - Percentile-based detection
    - Cuadrantes de riesgo
    """

    def __init__(self, db: Session):
        self.db = db
        self.insights_collector = MetaInsightsCollector(db)
        
        # Umbrales configurables
        self.z_score_threshold = 2.0  # 2 desviaciones estándar
        self.percentile_high = 90  # p90
        self.percentile_low = 10   # p10
        
        # Ventanas temporales
        self.window_1h = timedelta(hours=1)
        self.window_6h = timedelta(hours=6)
        self.window_24h = timedelta(hours=24)

    async def detect_spike(
        self,
        adset_id: str,
        campaign_id: str | None = None,
    ) -> SpikeDetectionResult:
        """
        Detecta spike en un adset específico.
        
        Proceso:
        1. Obtener métricas actuales
        2. Obtener métricas históricas (rolling windows)
        3. Calcular Z-Scores
        4. Calcular percentiles
        5. Clasificar spike (positive/negative/risk)
        6. Calcular risk_score y stability_score
        7. Recomendar acción
        """
        
        # STUB MODE: Generar métricas sintéticas
        if settings.META_API_MODE == "stub":
            return self._generate_stub_detection(adset_id, campaign_id)
        
        # LIVE MODE: Lógica real
        current_metrics = await self._get_current_metrics(adset_id)
        historical_metrics = await self._get_historical_metrics(adset_id)
        
        if not historical_metrics:
            # Sin datos históricos, no podemos detectar spikes
            return SpikeDetectionResult(
                adset_id=adset_id,
                campaign_id=campaign_id,
                spike_detected=False,
                risk_level=RiskLevel.LOW,
                current_metrics=current_metrics,
                risk_score=0.0,
                stability_score=100.0,
                reason="No hay datos históricos suficientes",
                recommended_action=ScaleAction.MAINTAIN,
            )
        
        # Calcular Z-Scores
        z_scores = self._calculate_z_scores(current_metrics, historical_metrics)
        
        # Calcular percentiles
        percentiles = self._calculate_percentiles(current_metrics, historical_metrics)
        
        # Clasificar spike
        spike_type, risk_level = self._classify_spike(
            current_metrics, z_scores, percentiles
        )
        
        # Calcular scores
        risk_score = self._calculate_risk_score(current_metrics, z_scores)
        stability_score = self._calculate_stability_score(z_scores)
        
        # Recomendar acción
        recommended_action = self._recommend_action(
            spike_type, risk_level, risk_score, current_metrics
        )
        
        # Calcular promedio histórico
        historical_avg = self._calculate_historical_avg(historical_metrics)
        
        # Generar razón
        reason = self._generate_reason(
            spike_type, risk_level, z_scores, current_metrics, historical_avg
        )
        
        return SpikeDetectionResult(
            adset_id=adset_id,
            campaign_id=campaign_id,
            spike_detected=spike_type is not None,
            spike_type=spike_type,
            risk_level=risk_level,
            current_metrics=current_metrics,
            historical_avg=historical_avg,
            z_scores=z_scores,
            percentiles=percentiles,
            risk_score=risk_score,
            stability_score=stability_score,
            reason=reason,
            recommended_action=recommended_action,
        )

    def _calculate_z_scores(
        self,
        current: MetricsSnapshot,
        historical: list[MetricsSnapshot],
    ) -> dict[str, float]:
        """Calcula Z-Score para cada métrica."""
        z_scores = {}
        
        metrics_to_check = [
            "cpm", "cpc", "ctr", "roas", "conversion_rate", 
            "frequency", "spend_rate"
        ]
        
        for metric in metrics_to_check:
            current_val = getattr(current, metric)
            if current_val is None:
                continue
                
            historical_vals = [
                getattr(m, metric) for m in historical 
                if getattr(m, metric) is not None
            ]
            
            if len(historical_vals) < 2:
                continue
            
            mean = statistics.mean(historical_vals)
            stdev = statistics.stdev(historical_vals)
            
            if stdev > 0:
                z_scores[metric] = (current_val - mean) / stdev
            else:
                z_scores[metric] = 0.0
        
        return z_scores

    def _calculate_percentiles(
        self,
        current: MetricsSnapshot,
        historical: list[MetricsSnapshot],
    ) -> dict[str, float]:
        """Calcula percentil de cada métrica actual vs histórico."""
        percentiles = {}
        
        metrics_to_check = [
            "cpm", "cpc", "ctr", "roas", "conversion_rate",
            "frequency", "spend_rate"
        ]
        
        for metric in metrics_to_check:
            current_val = getattr(current, metric)
            if current_val is None:
                continue
                
            historical_vals = [
                getattr(m, metric) for m in historical
                if getattr(m, metric) is not None
            ]
            
            if not historical_vals:
                continue
            
            # Contar cuántos valores históricos son menores que el actual
            count_lower = sum(1 for v in historical_vals if v < current_val)
            percentile = (count_lower / len(historical_vals)) * 100
            percentiles[metric] = percentile
        
        return percentiles

    def _classify_spike(
        self,
        current: MetricsSnapshot,
        z_scores: dict[str, float],
        percentiles: dict[str, float],
    ) -> tuple[SpikeType | None, RiskLevel]:
        """
        Clasifica el spike en:
        - POSITIVE: Métricas mejoran (CTR, ROAS up, CPC/CPM down)
        - NEGATIVE: Métricas empeoran (CTR, ROAS down, CPC/CPM up)
        - RISK: Gasto alto pero métricas malas
        """
        
        # Métricas positivas (mayor es mejor)
        positive_metrics = ["ctr", "roas", "conversion_rate"]
        # Métricas negativas (menor es mejor)
        negative_metrics = ["cpm", "cpc", "frequency"]
        
        positive_score = 0
        negative_score = 0
        
        # Analizar Z-Scores
        for metric, z in z_scores.items():
            if abs(z) < self.z_score_threshold:
                continue  # No es spike significativo
                
            if metric in positive_metrics:
                if z > 0:  # Aumentó → bueno
                    positive_score += abs(z)
                else:  # Disminuyó → malo
                    negative_score += abs(z)
            elif metric in negative_metrics:
                if z < 0:  # Disminuyó → bueno
                    positive_score += abs(z)
                else:  # Aumentó → malo
                    negative_score += abs(z)
        
        # Detectar spike de RIESGO (gasto alto pero métricas malas)
        spend_spike = z_scores.get("spend_rate", 0) > self.z_score_threshold
        bad_roas = current.roas is not None and current.roas < 1.0
        bad_ctr = current.ctr is not None and current.ctr < 0.01  # <1%
        
        if spend_spike and (bad_roas or bad_ctr):
            return SpikeType.RISK, RiskLevel.HIGH
        
        # Clasificar basado en score
        if positive_score > negative_score and positive_score > 2:
            risk_level = RiskLevel.LOW if positive_score > 4 else RiskLevel.MEDIUM
            return SpikeType.POSITIVE, risk_level
        elif negative_score > positive_score and negative_score > 2:
            risk_level = RiskLevel.HIGH if negative_score > 4 else RiskLevel.MEDIUM
            return SpikeType.NEGATIVE, risk_level
        else:
            # No spike significativo
            return None, RiskLevel.LOW

    def _calculate_risk_score(
        self,
        current: MetricsSnapshot,
        z_scores: dict[str, float],
    ) -> float:
        """
        Calcula score de riesgo (0-100).
        Mayor score = mayor riesgo.
        """
        risk = 0.0
        
        # Factores de riesgo
        if current.roas is not None and current.roas < 0.5:
            risk += 30
        elif current.roas is not None and current.roas < 1.0:
            risk += 15
        
        if current.ctr is not None and current.ctr < 0.005:  # <0.5%
            risk += 20
        
        if current.frequency is not None and current.frequency > 3.0:
            risk += 15
        
        # Z-Scores altos en métricas negativas
        if z_scores.get("cpm", 0) > 2:
            risk += 10
        if z_scores.get("cpc", 0) > 2:
            risk += 10
        
        return min(risk, 100.0)

    def _calculate_stability_score(self, z_scores: dict[str, float]) -> float:
        """
        Calcula score de estabilidad (0-100).
        Mayor score = más estable (menos volatilidad).
        """
        if not z_scores:
            return 100.0
        
        # Promedio de Z-Scores absolutos
        avg_z = statistics.mean([abs(z) for z in z_scores.values()])
        
        # Convertir a score de estabilidad
        # Z=0 → 100%, Z=3 → 0%
        stability = max(0, 100 - (avg_z * 33.33))
        return stability

    def _recommend_action(
        self,
        spike_type: SpikeType | None,
        risk_level: RiskLevel,
        risk_score: float,
        current: MetricsSnapshot,
    ) -> ScaleAction:
        """Recomienda acción de escalado basado en spike detectado."""
        
        if spike_type == SpikeType.POSITIVE:
            # Escalar up según risk level
            if risk_level == RiskLevel.LOW:
                return ScaleAction.SCALE_UP_50
            elif risk_level == RiskLevel.MEDIUM:
                return ScaleAction.SCALE_UP_30
            else:
                return ScaleAction.SCALE_UP_10
        
        elif spike_type == SpikeType.NEGATIVE:
            # Escalar down según risk level
            if risk_level == RiskLevel.HIGH:
                return ScaleAction.SCALE_DOWN_40
            elif risk_level == RiskLevel.MEDIUM:
                return ScaleAction.SCALE_DOWN_20
            else:
                return ScaleAction.SCALE_DOWN_10
        
        elif spike_type == SpikeType.RISK:
            # Pausar inmediatamente
            return ScaleAction.PAUSE
        
        else:
            # Sin spike → mantener
            return ScaleAction.MAINTAIN

    def _calculate_historical_avg(
        self, historical: list[MetricsSnapshot]
    ) -> MetricsSnapshot:
        """Calcula promedio de métricas históricas."""
        if not historical:
            return MetricsSnapshot()
        
        def avg(metric: str) -> float | None:
            vals = [getattr(m, metric) for m in historical if getattr(m, metric) is not None]
            return statistics.mean(vals) if vals else None
        
        return MetricsSnapshot(
            cpm=avg("cpm"),
            cpc=avg("cpc"),
            ctr=avg("ctr"),
            roas=avg("roas"),
            conversion_rate=avg("conversion_rate"),
            frequency=avg("frequency"),
            spend_rate=avg("spend_rate"),
            impressions=int(avg("impressions") or 0),
            clicks=int(avg("clicks") or 0),
            conversions=int(avg("conversions") or 0),
            spend=avg("spend"),
            revenue=avg("revenue"),
        )

    def _generate_reason(
        self,
        spike_type: SpikeType | None,
        risk_level: RiskLevel,
        z_scores: dict[str, float],
        current: MetricsSnapshot,
        historical_avg: MetricsSnapshot,
    ) -> str:
        """Genera razón en lenguaje natural del spike detectado."""
        
        if spike_type is None:
            return "No se detectó spike significativo. Métricas estables."
        
        reasons = []
        
        if spike_type == SpikeType.POSITIVE:
            reasons.append("📈 Spike POSITIVO detectado:")
            if z_scores.get("roas", 0) > 2:
                reasons.append(f"  • ROAS aumentó a {current.roas:.2f} (avg: {historical_avg.roas:.2f})")
            if z_scores.get("ctr", 0) > 2:
                reasons.append(f"  • CTR aumentó a {current.ctr:.2%} (avg: {historical_avg.ctr:.2%})")
        
        elif spike_type == SpikeType.NEGATIVE:
            reasons.append("📉 Spike NEGATIVO detectado:")
            if z_scores.get("roas", 0) < -2:
                reasons.append(f"  • ROAS cayó a {current.roas:.2f} (avg: {historical_avg.roas:.2f})")
            if z_scores.get("cpc", 0) > 2:
                reasons.append(f"  • CPC aumentó a ${current.cpc:.2f} (avg: ${historical_avg.cpc:.2f})")
        
        elif spike_type == SpikeType.RISK:
            reasons.append("⚠️ Spike de RIESGO detectado:")
            reasons.append(f"  • Gasto elevado: ${current.spend:.2f}")
            if current.roas and current.roas < 1.0:
                reasons.append(f"  • ROAS bajo: {current.roas:.2f}")
            if current.ctr and current.ctr < 0.01:
                reasons.append(f"  • CTR bajo: {current.ctr:.2%}")
        
        reasons.append(f"Nivel de riesgo: {risk_level.value.upper()}")
        
        return "\n".join(reasons)

    async def _get_current_metrics(self, adset_id: str) -> MetricsSnapshot:
        """Obtiene métricas actuales del adset (últimas 1h)."""
        # TODO: Integrar con MetaInsightsCollector
        pass

    async def _get_historical_metrics(
        self, adset_id: str
    ) -> list[MetricsSnapshot]:
        """Obtiene métricas históricas (últimas 24h)."""
        # TODO: Integrar con MetaInsightsCollector
        pass

    def _generate_stub_detection(
        self, adset_id: str, campaign_id: str | None
    ) -> SpikeDetectionResult:
        """Genera detección sintética para STUB mode."""
        import random
        
        # Generar métricas actuales aleatorias
        current = MetricsSnapshot(
            cpm=random.uniform(5, 20),
            cpc=random.uniform(0.5, 3.0),
            ctr=random.uniform(0.005, 0.05),
            roas=random.uniform(0.5, 4.0),
            conversion_rate=random.uniform(0.01, 0.10),
            frequency=random.uniform(1.0, 4.0),
            spend_rate=random.uniform(10, 100),
            impressions=random.randint(1000, 50000),
            clicks=random.randint(50, 2000),
            conversions=random.randint(5, 200),
            spend=random.uniform(50, 500),
            revenue=random.uniform(100, 2000),
        )
        
        # Generar métricas históricas (similares pero con variación)
        historical = MetricsSnapshot(
            cpm=current.cpm * random.uniform(0.8, 1.2),
            cpc=current.cpc * random.uniform(0.8, 1.2),
            ctr=current.ctr * random.uniform(0.8, 1.2),
            roas=current.roas * random.uniform(0.8, 1.2),
            conversion_rate=current.conversion_rate * random.uniform(0.8, 1.2),
            frequency=current.frequency * random.uniform(0.8, 1.2),
            spend_rate=current.spend_rate * random.uniform(0.8, 1.2),
        )
        
        # Generar Z-Scores aleatorios
        z_scores = {
            "cpm": random.uniform(-3, 3),
            "cpc": random.uniform(-3, 3),
            "ctr": random.uniform(-3, 3),
            "roas": random.uniform(-3, 3),
            "conversion_rate": random.uniform(-3, 3),
            "frequency": random.uniform(-3, 3),
            "spend_rate": random.uniform(-3, 3),
        }
        
        # Determinar spike basado en Z-Scores
        max_z = max(abs(z) for z in z_scores.values())
        
        if max_z > 2.5:
            # Spike significativo
            if z_scores["roas"] > 2:
                spike_type = SpikeType.POSITIVE
                risk_level = RiskLevel.LOW
                action = ScaleAction.SCALE_UP_30
            elif z_scores["roas"] < -2:
                spike_type = SpikeType.NEGATIVE
                risk_level = RiskLevel.HIGH
                action = ScaleAction.SCALE_DOWN_20
            else:
                spike_type = SpikeType.RISK
                risk_level = RiskLevel.MEDIUM
                action = ScaleAction.MAINTAIN
            spike_detected = True
        else:
            spike_type = None
            spike_detected = False
            risk_level = RiskLevel.LOW
            action = ScaleAction.MAINTAIN
        
        risk_score = random.uniform(0, 100)
        stability_score = random.uniform(50, 100)
        
        reason = f"STUB MODE: Spike {'detectado' if spike_detected else 'no detectado'}"
        
        return SpikeDetectionResult(
            adset_id=adset_id,
            campaign_id=campaign_id,
            spike_detected=spike_detected,
            spike_type=spike_type,
            risk_level=risk_level,
            current_metrics=current,
            historical_avg=historical,
            z_scores=z_scores,
            percentiles={k: random.uniform(0, 100) for k in z_scores.keys()},
            risk_score=risk_score,
            stability_score=stability_score,
            reason=reason,
            recommended_action=action,
        )
