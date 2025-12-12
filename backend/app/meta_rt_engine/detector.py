"""
Real-Time Detector for Meta RT Performance Engine (PASO 10.14)

Detects anomalies, drifts, and spikes in campaign performance using
short-window analysis (5-30 minutes).
"""

import random
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from uuid import UUID

from app.meta_rt_engine.schemas import (
    PerformanceSnapshot,
    PerformanceMetrics,
    AnomalyDetection,
    DriftDetection,
    SpikeDetection,
    DetectionResult,
    AnomalyType,
    SeverityLevel,
)


class RealTimeDetector:
    """
    Real-Time Performance Detector
    
    Analyzes performance snapshots and detects:
    - Anomalies (CTR/CVR/ROAS drops, CPM spikes)
    - Short-window drifts (5-30 min windows)
    - Sudden spikes/drops
    
    Mode:
        stub: Generate synthetic detections for development/testing
        live: Use real Meta Ads API data (TODO - requires integration)
    """
    
    def __init__(self, mode: str = "stub"):
        self.mode = mode
        
        # Anomaly detection thresholds
        self.thresholds = {
            "ctr_drop_pct": 25.0,      # CTR drop ≥25% triggers action
            "cvr_drop_pct": 25.0,      # CVR drop ≥25% triggers action
            "roas_collapse_pct": 30.0, # ROAS drop ≥30% critical
            "cpm_spike_pct": 40.0,     # CPM increase ≥40% spike
            "spend_spike_pct": 50.0,   # Spend increase ≥50% spike
            "frequency_spike": 6.0,    # Frequency ≥6 saturation risk
        }
        
        # Drift detection parameters
        self.drift_threshold = 2.0  # Standard deviations
        
        # Spike detection parameters
        self.spike_threshold = 3.0  # Standard deviations
    
    
    async def detect_anomalies(
        self,
        campaign_id: UUID,
        current_snapshot: PerformanceSnapshot,
        baseline_snapshots: Optional[List[PerformanceSnapshot]] = None,
    ) -> DetectionResult:
        """
        Detect anomalies in current snapshot vs baseline.
        
        Args:
            campaign_id: Campaign UUID
            current_snapshot: Current performance snapshot
            baseline_snapshots: Historical snapshots for comparison (optional)
        
        Returns:
            DetectionResult with anomalies, drifts, and spikes
        """
        start_time = datetime.utcnow()
        
        if self.mode == "stub":
            result = await self._detect_anomalies_stub(
                campaign_id,
                current_snapshot,
                baseline_snapshots,
            )
        else:
            # TODO: Implement LIVE mode with real Meta Ads API
            result = await self._detect_anomalies_live(
                campaign_id,
                current_snapshot,
                baseline_snapshots,
            )
        
        # Calculate processing time
        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        result.processing_time_ms = int(processing_time)
        
        return result
    
    
    async def _detect_anomalies_stub(
        self,
        campaign_id: UUID,
        current_snapshot: PerformanceSnapshot,
        baseline_snapshots: Optional[List[PerformanceSnapshot]],
    ) -> DetectionResult:
        """
        STUB mode: Generate synthetic anomaly detections.
        
        Simulates realistic detection scenarios:
        - 30% chance of no anomalies (healthy)
        - 40% chance of minor anomalies (moderate)
        - 20% chance of significant anomalies (high)
        - 10% chance of critical anomalies (critical)
        """
        anomalies: List[AnomalyDetection] = []
        drifts: List[DriftDetection] = []
        spikes: List[SpikeDetection] = []
        
        # Calculate baseline metrics (synthetic)
        baseline_metrics = self._calculate_baseline_stub(current_snapshot.metrics)
        
        # Detect CTR anomalies
        if random.random() < 0.3:  # 30% chance of CTR issue
            ctr_drop_pct = random.uniform(15, 45)
            severity = self._calculate_severity(ctr_drop_pct, 25)
            
            anomalies.append(AnomalyDetection(
                anomaly_type=AnomalyType.CTR_DROP,
                severity=severity,
                metric_name="ctr",
                current_value=current_snapshot.metrics.ctr,
                baseline_value=baseline_metrics["ctr"],
                drop_percentage=ctr_drop_pct,
                threshold_violated=self.thresholds["ctr_drop_pct"],
                detection_timestamp=datetime.utcnow(),
                confidence=random.uniform(0.85, 0.98),
                description=f"CTR dropped {ctr_drop_pct:.1f}% from baseline {baseline_metrics['ctr']:.4f} to {current_snapshot.metrics.ctr:.4f}",
            ))
        
        # Detect CVR anomalies
        if random.random() < 0.25:  # 25% chance of CVR issue
            cvr_drop_pct = random.uniform(20, 50)
            severity = self._calculate_severity(cvr_drop_pct, 25)
            
            anomalies.append(AnomalyDetection(
                anomaly_type=AnomalyType.CVR_DROP,
                severity=severity,
                metric_name="cvr",
                current_value=current_snapshot.metrics.cvr,
                baseline_value=baseline_metrics["cvr"],
                drop_percentage=cvr_drop_pct,
                threshold_violated=self.thresholds["cvr_drop_pct"],
                detection_timestamp=datetime.utcnow(),
                confidence=random.uniform(0.80, 0.95),
                description=f"CVR dropped {cvr_drop_pct:.1f}% from baseline {baseline_metrics['cvr']:.4f} to {current_snapshot.metrics.cvr:.4f}",
            ))
        
        # Detect ROAS collapses
        if random.random() < 0.15:  # 15% chance of ROAS collapse
            roas_drop_pct = random.uniform(30, 70)
            severity = SeverityLevel.CRITICAL if roas_drop_pct >= 50 else SeverityLevel.HIGH
            
            anomalies.append(AnomalyDetection(
                anomaly_type=AnomalyType.ROAS_COLLAPSE,
                severity=severity,
                metric_name="roas",
                current_value=current_snapshot.metrics.roas,
                baseline_value=baseline_metrics["roas"],
                drop_percentage=roas_drop_pct,
                threshold_violated=self.thresholds["roas_collapse_pct"],
                detection_timestamp=datetime.utcnow(),
                confidence=random.uniform(0.90, 0.99),
                description=f"ROAS collapsed {roas_drop_pct:.1f}% from baseline {baseline_metrics['roas']:.2f} to {current_snapshot.metrics.roas:.2f} - CRITICAL",
            ))
        
        # Detect CPM spikes
        if random.random() < 0.20:  # 20% chance of CPM spike
            cpm_spike_pct = random.uniform(30, 80)
            severity = self._calculate_severity(cpm_spike_pct, 40)
            
            anomalies.append(AnomalyDetection(
                anomaly_type=AnomalyType.CPM_SPIKE,
                severity=severity,
                metric_name="cpm",
                current_value=current_snapshot.metrics.cpm,
                baseline_value=baseline_metrics["cpm"],
                spike_percentage=cpm_spike_pct,
                threshold_violated=self.thresholds["cpm_spike_pct"],
                detection_timestamp=datetime.utcnow(),
                confidence=random.uniform(0.85, 0.97),
                description=f"CPM spiked {cpm_spike_pct:.1f}% from baseline ${baseline_metrics['cpm']:.2f} to ${current_snapshot.metrics.cpm:.2f}",
            ))
        
        # Detect frequency spikes
        if current_snapshot.metrics.frequency >= self.thresholds["frequency_spike"]:
            anomalies.append(AnomalyDetection(
                anomaly_type=AnomalyType.FREQUENCY_SPIKE,
                severity=SeverityLevel.HIGH,
                metric_name="frequency",
                current_value=current_snapshot.metrics.frequency,
                baseline_value=baseline_metrics["frequency"],
                spike_percentage=(current_snapshot.metrics.frequency / baseline_metrics["frequency"] - 1) * 100,
                threshold_violated=self.thresholds["frequency_spike"],
                detection_timestamp=datetime.utcnow(),
                confidence=0.99,
                description=f"Frequency reached {current_snapshot.metrics.frequency:.2f} - audience saturation risk",
            ))
        
        # Detect short-window drifts
        if random.random() < 0.25:  # 25% chance of drift
            drifts.append(DriftDetection(
                metric_name="ctr",
                window_minutes=current_snapshot.window_minutes,
                mean_drift=random.uniform(-0.01, -0.005),
                std_drift=random.uniform(0.001, 0.003),
                is_drifting=True,
                drift_score=random.uniform(60, 85),
                baseline_mean=baseline_metrics["ctr"],
                current_mean=current_snapshot.metrics.ctr,
                samples_analyzed=random.randint(8, 20),
            ))
        
        # Detect sudden spikes
        if random.random() < 0.15:  # 15% chance of spike
            spikes.append(SpikeDetection(
                metric_name="cpm",
                spike_magnitude=random.uniform(2.5, 4.5),
                current_value=current_snapshot.metrics.cpm,
                expected_value=baseline_metrics["cpm"],
                is_spike=True,
                spike_direction="up",
                detection_time=datetime.utcnow(),
            ))
        
        # Calculate severity counts
        critical_count = sum(1 for a in anomalies if a.severity == SeverityLevel.CRITICAL)
        high_count = sum(1 for a in anomalies if a.severity == SeverityLevel.HIGH)
        moderate_count = sum(1 for a in anomalies if a.severity == SeverityLevel.MODERATE)
        
        return DetectionResult(
            campaign_id=campaign_id,
            snapshot_id=uuid.uuid4(),
            detection_timestamp=datetime.utcnow(),
            anomalies=anomalies,
            drifts=drifts,
            spikes=spikes,
            has_critical_issues=critical_count > 0,
            critical_count=critical_count,
            high_count=high_count,
            moderate_count=moderate_count,
            processing_time_ms=0,  # Will be set by caller
        )
    
    
    async def _detect_anomalies_live(
        self,
        campaign_id: UUID,
        current_snapshot: PerformanceSnapshot,
        baseline_snapshots: Optional[List[PerformanceSnapshot]],
    ) -> DetectionResult:
        """
        LIVE mode: Detect anomalies using real data.
        
        TODO: Implement real anomaly detection:
        1. Calculate baseline from historical snapshots
        2. Compare current metrics to baseline
        3. Detect drops/spikes using statistical methods
        4. Calculate confidence intervals
        5. Apply thresholds and generate anomalies
        """
        # For now, fallback to stub mode
        # In production, this would use real baseline calculations
        return await self._detect_anomalies_stub(campaign_id, current_snapshot, baseline_snapshots)
    
    
    def _calculate_baseline_stub(self, current_metrics: PerformanceMetrics) -> Dict[str, float]:
        """
        Calculate synthetic baseline metrics for comparison.
        Baseline represents "healthy" historical performance.
        """
        return {
            "ctr": current_metrics.ctr * random.uniform(1.1, 1.4),      # Baseline was 10-40% higher
            "cvr": current_metrics.cvr * random.uniform(1.1, 1.35),     # Baseline was 10-35% higher
            "roas": current_metrics.roas * random.uniform(1.15, 1.5),   # Baseline was 15-50% higher
            "cpm": current_metrics.cpm * random.uniform(0.7, 0.9),      # Baseline was 10-30% lower
            "cpc": current_metrics.cpc * random.uniform(0.75, 0.95),    # Baseline was 5-25% lower
            "frequency": current_metrics.frequency * random.uniform(0.6, 0.85),  # Baseline was lower
        }
    
    
    def _calculate_severity(self, drop_pct: float, threshold: float) -> SeverityLevel:
        """
        Calculate severity level based on drop percentage and threshold.
        
        - LOW: Below threshold
        - MODERATE: threshold to threshold * 1.3
        - HIGH: threshold * 1.3 to threshold * 1.6
        - CRITICAL: Above threshold * 1.6
        """
        if drop_pct < threshold:
            return SeverityLevel.LOW
        elif drop_pct < threshold * 1.3:
            return SeverityLevel.MODERATE
        elif drop_pct < threshold * 1.6:
            return SeverityLevel.HIGH
        else:
            return SeverityLevel.CRITICAL
