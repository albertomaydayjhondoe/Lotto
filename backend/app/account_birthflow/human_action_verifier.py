"""
SPRINT 12.1 - Human-Assisted Warm-Up Scheduler
Module: Human Action Verifier

Verifica que el humano ejecutó las acciones requeridas correctamente:
- Tiempo mínimo cumplido
- Intervalos naturales
- Comportamiento no mecánico
- Diversidad de acciones
- Estabilidad de fingerprint
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import statistics


@dataclass
class HumanActionVerifierConfig:
    """Configuration for human action verifier"""
    
    min_session_duration: int = 120  # 2 minutes
    max_session_duration: int = 1800  # 30 minutes
    min_action_interval: int = 15  # 15 seconds
    max_action_interval: int = 300  # 5 minutes
    min_unique_actions: int = 2  # At least 2 types
    max_identical_intervals: int = 3  # Max repeating intervals
    risk_reduction_on_pass: float = -0.05
    risk_increase_on_fail: float = +0.10
    enabled: bool = True


@dataclass
class VerificationResult:
    """Result of task completion verification"""
    
    account_id: str
    task_id: str
    verification_passed: bool
    time_spent_seconds: int
    detected_actions: List[str]
    action_diversity_score: float  # 0-1
    interval_variance: float  # Higher = more natural
    mechanical_score: float  # 0-1 (lower = more human)
    risk_adjustment: float  # +/- risk change
    issues: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        """Convert to dict"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data


class HumanActionVerifier:
    """
    Verifies that human executed warmup tasks correctly.
    NO automation - only verification of human actions.
    """
    
    def __init__(self, config: Optional[HumanActionVerifierConfig] = None):
        self.config = config or HumanActionVerifierConfig()
        self.verification_history: Dict[str, List[VerificationResult]] = {}
    
    def verify_task_completion(
        self,
        account_id: str,
        task_id: str,
        session_start: datetime,
        session_end: datetime,
        actions: List[Dict],  # [{type, timestamp}, ...]
        fingerprint_data: Optional[Dict] = None
    ) -> VerificationResult:
        """
        Verify task completion by human.
        
        Checks:
        1. Time spent (min/max)
        2. Action diversity
        3. Interval analysis
        4. Mechanical detection
        5. Fingerprint stability (optional)
        """
        
        issues = []
        warnings = []
        
        # 1. Time check
        time_spent = int((session_end - session_start).total_seconds())
        
        if time_spent < self.config.min_session_duration:
            issues.append(f"Session too short: {time_spent}s < {self.config.min_session_duration}s")
        
        if time_spent > self.config.max_session_duration:
            warnings.append(f"Session very long: {time_spent}s")
        
        # 2. Action diversity
        action_types = set(a["type"] for a in actions)
        unique_actions = len(action_types)
        
        if unique_actions < self.config.min_unique_actions:
            issues.append(f"Too few action types: {unique_actions} < {self.config.min_unique_actions}")
        
        action_diversity_score = min(unique_actions / 5.0, 1.0)  # Max 5 types
        
        # 3. Interval analysis
        if len(actions) >= 2:
            intervals = []
            sorted_actions = sorted(actions, key=lambda x: x["timestamp"])
            
            for i in range(1, len(sorted_actions)):
                delta = (sorted_actions[i]["timestamp"] - sorted_actions[i-1]["timestamp"]).total_seconds()
                intervals.append(delta)
            
            # Check for too fast actions
            too_fast = [i for i in intervals if i < self.config.min_action_interval]
            if too_fast:
                issues.append(f"Actions too fast: {len(too_fast)} intervals < {self.config.min_action_interval}s")
            
            # Check for mechanical patterns (identical intervals)
            if len(intervals) >= self.config.max_identical_intervals:
                interval_counts = {}
                for interval in intervals:
                    rounded = round(interval, 0)
                    interval_counts[rounded] = interval_counts.get(rounded, 0) + 1
                
                max_repeats = max(interval_counts.values())
                if max_repeats > self.config.max_identical_intervals:
                    issues.append(f"Mechanical pattern detected: {max_repeats} identical intervals")
            
            # Calculate variance (higher = more natural)
            if len(intervals) > 1:
                try:
                    mean = statistics.mean(intervals)
                    stdev = statistics.stdev(intervals)
                    cv = stdev / mean if mean > 0 else 0  # Coefficient of variation
                    interval_variance = cv
                    mechanical_score = 1.0 - min(cv / 0.5, 1.0)  # Normalize
                    
                    # If CV too low, it's mechanical
                    if cv < 0.2:
                        warnings.append(f"Low variance (CV={cv:.2f}), might be mechanical")
                except:
                    interval_variance = 0.5
                    mechanical_score = 0.5
            else:
                interval_variance = 0.5
                mechanical_score = 0.5
        else:
            interval_variance = 0.5
            mechanical_score = 0.5
            warnings.append("Too few actions for interval analysis")
        
        # 4. Fingerprint stability (optional)
        if fingerprint_data:
            # Check if fingerprint is stable
            # (Implementation would check canvas, audio, WebGL consistency)
            pass
        
        # Determine pass/fail
        verification_passed = len(issues) == 0
        
        # Risk adjustment
        if verification_passed:
            risk_adjustment = self.config.risk_reduction_on_pass
        else:
            risk_adjustment = self.config.risk_increase_on_fail
        
        # Create result
        result = VerificationResult(
            account_id=account_id,
            task_id=task_id,
            verification_passed=verification_passed,
            time_spent_seconds=time_spent,
            detected_actions=list(action_types),
            action_diversity_score=action_diversity_score,
            interval_variance=interval_variance,
            mechanical_score=mechanical_score,
            risk_adjustment=risk_adjustment,
            issues=issues,
            warnings=warnings
        )
        
        # Store in history
        if account_id not in self.verification_history:
            self.verification_history[account_id] = []
        self.verification_history[account_id].append(result)
        
        return result
    
    def quick_verify(
        self,
        account_id: str,
        task_id: str,
        time_spent_seconds: int
    ) -> VerificationResult:
        """Quick verification (only time check)"""
        
        issues = []
        if time_spent_seconds < self.config.min_session_duration:
            issues.append(f"Session too short: {time_spent_seconds}s")
        
        verification_passed = len(issues) == 0
        risk_adjustment = (
            self.config.risk_reduction_on_pass if verification_passed
            else self.config.risk_increase_on_fail
        )
        
        result = VerificationResult(
            account_id=account_id,
            task_id=task_id,
            verification_passed=verification_passed,
            time_spent_seconds=time_spent_seconds,
            detected_actions=[],
            action_diversity_score=0.0,
            interval_variance=0.0,
            mechanical_score=0.0,
            risk_adjustment=risk_adjustment,
            issues=issues,
            warnings=["Quick verification only"]
        )
        
        if account_id not in self.verification_history:
            self.verification_history[account_id] = []
        self.verification_history[account_id].append(result)
        
        return result
    
    def get_verification_history(
        self,
        account_id: str,
        limit: Optional[int] = None
    ) -> List[VerificationResult]:
        """Get verification history for account"""
        history = self.verification_history.get(account_id, [])
        if limit:
            return history[-limit:]
        return history
    
    def get_success_rate(self, account_id: str) -> float:
        """Get verification success rate"""
        history = self.verification_history.get(account_id, [])
        if not history:
            return 0.0
        
        passed = sum(1 for v in history if v.verification_passed)
        return passed / len(history)
    
    def get_average_mechanical_score(self, account_id: str) -> float:
        """Get average mechanical score"""
        history = self.verification_history.get(account_id, [])
        if not history:
            return 0.0
        
        scores = [v.mechanical_score for v in history if v.mechanical_score > 0]
        return statistics.mean(scores) if scores else 0.0
    
    def get_cumulative_risk_adjustment(self, account_id: str) -> float:
        """Get cumulative risk adjustment for account"""
        history = self.verification_history.get(account_id, [])
        return sum(v.risk_adjustment for v in history)


# ============================================================================
# TEST HELPERS
# ============================================================================

def create_mock_verification_result(
    account_id: str,
    task_id: str,
    passed: bool = True
) -> VerificationResult:
    """Create mock verification result for testing"""
    return VerificationResult(
        account_id=account_id,
        task_id=task_id,
        verification_passed=passed,
        time_spent_seconds=300 if passed else 30,
        detected_actions=["scroll", "like", "comment"] if passed else ["like"],
        action_diversity_score=0.6 if passed else 0.2,
        interval_variance=0.35 if passed else 0.05,
        mechanical_score=0.20 if passed else 0.80,
        risk_adjustment=-0.05 if passed else +0.10,
        issues=[] if passed else ["Too short session"],
        warnings=[]
    )


import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


# ============================================================================
# CONFIG
# ============================================================================

@dataclass
class HumanActionVerifierConfig:
    """Configuración del verificador"""
    
    # Time thresholds
    min_session_duration: int = 120  # 2 min minimum
    max_session_duration: int = 1800  # 30 min maximum
    
    # Interval checks
    min_action_interval: int = 15  # 15s minimum between actions
    max_action_interval: int = 300  # 5min maximum (not too slow)
    
    # Behavioral checks
    min_unique_actions: int = 2  # At least 2 different action types
    max_identical_intervals: int = 3  # Max 3 identical intervals = bot-like
    
    # Fingerprint stability
    check_fingerprint_consistency: bool = True
    allow_minor_fingerprint_changes: bool = True  # OS updates, etc.
    
    # Risk adjustments
    risk_reduction_on_pass: float = 0.05  # -0.05 per successful verification
    risk_increase_on_fail: float = 0.10  # +0.10 per failed verification


# ============================================================================
# VERIFICATION RESULT
# ============================================================================

@dataclass
class VerificationResult:
    """Resultado de verificación"""
    
    account_id: str
    task_id: str
    verification_passed: bool
    
    # Timing
    time_spent_seconds: int
    session_start: datetime
    session_end: datetime
    
    # Actions detected
    detected_actions: List[str]
    action_count: int
    action_diversity_score: float  # 0-1
    
    # Behavioral
    interval_variance: float  # 0-1 (higher = more natural)
    mechanical_score: float  # 0-1 (lower = less mechanical)
    
    # Risk
    risk_adjustment: float  # Positive = increase, negative = decrease
    
    # Details
    issues: List[str]
    warnings: List[str]
    metadata: Dict
    
    def to_dict(self) -> Dict:
        return {
            "account_id": self.account_id,
            "task_id": self.task_id,
            "verification_passed": self.verification_passed,
            "time_spent": f"{self.time_spent_seconds}s",
            "detected_actions": self.detected_actions,
            "action_count": self.action_count,
            "action_diversity_score": self.action_diversity_score,
            "interval_variance": self.interval_variance,
            "mechanical_score": self.mechanical_score,
            "risk_adjustment": self.risk_adjustment,
            "issues": self.issues,
            "warnings": self.warnings
        }


# ============================================================================
# HUMAN ACTION VERIFIER
# ============================================================================

class HumanActionVerifier:
    """
    Verificador de acciones humanas.
    
    Responsabilidades:
    - Verificar tiempo de sesión
    - Analizar intervalos entre acciones
    - Detectar comportamiento mecánico
    - Verificar diversidad de acciones
    - Ajustar risk score
    
    NO ejecuta acciones - solo verifica.
    """
    
    def __init__(self, config: Optional[HumanActionVerifierConfig] = None):
        self.config = config or HumanActionVerifierConfig()
        
        # Verification history
        self._verification_history: Dict[str, List[VerificationResult]] = {}
        
        logger.info("HumanActionVerifier initialized")
    
    # ========================================================================
    # PUBLIC API - VERIFICATION
    # ========================================================================
    
    def verify_task_completion(
        self,
        account_id: str,
        task_id: str,
        session_start: datetime,
        session_end: datetime,
        actions_performed: List[Dict],  # [{"type": "like", "timestamp": dt}, ...]
        fingerprint_data: Optional[Dict] = None
    ) -> VerificationResult:
        """
        Verifica que la tarea fue completada correctamente.
        
        Args:
            account_id: ID de la cuenta
            task_id: ID de la tarea
            session_start: Inicio de la sesión
            session_end: Fin de la sesión
            actions_performed: Lista de acciones con timestamps
            fingerprint_data: Datos de fingerprint (opcional)
        
        Returns:
            VerificationResult con resultado detallado
        """
        issues = []
        warnings = []
        
        # 1. Check time spent
        time_spent = int((session_end - session_start).total_seconds())
        
        if time_spent < self.config.min_session_duration:
            issues.append(f"Session too short: {time_spent}s < {self.config.min_session_duration}s")
        
        if time_spent > self.config.max_session_duration:
            warnings.append(f"Session very long: {time_spent}s > {self.config.max_session_duration}s")
        
        # 2. Check action count and diversity
        action_types = [a["type"] for a in actions_performed]
        unique_actions = set(action_types)
        
        if len(unique_actions) < self.config.min_unique_actions:
            issues.append(f"Low action diversity: only {len(unique_actions)} type(s)")
        
        action_diversity = len(unique_actions) / 5.0  # Max 5 types
        
        # 3. Check intervals
        interval_variance = 0.0
        mechanical_score = 0.0
        
        if len(actions_performed) >= 2:
            intervals = []
            for i in range(1, len(actions_performed)):
                prev_ts = actions_performed[i-1]["timestamp"]
                curr_ts = actions_performed[i]["timestamp"]
                interval = (curr_ts - prev_ts).total_seconds()
                intervals.append(interval)
            
            # Check interval variance
            mean_interval = sum(intervals) / len(intervals)
            variance = sum((x - mean_interval) ** 2 for x in intervals) / len(intervals)
            std_dev = variance ** 0.5
            cv = std_dev / mean_interval if mean_interval > 0 else 0
            
            interval_variance = min(1.0, cv)
            
            # Check for mechanical patterns
            if cv < 0.2:  # Very low variance = mechanical
                issues.append(f"Intervals too regular (CV={cv:.2f})")
                mechanical_score = 1.0 - cv
            else:
                mechanical_score = max(0.0, 1.0 - cv)
            
            # Check for too fast intervals
            too_fast = [i for i in intervals if i < self.config.min_action_interval]
            if too_fast:
                issues.append(f"{len(too_fast)} action(s) too fast (< {self.config.min_action_interval}s)")
            
            # Check for identical intervals
            identical_count = max(intervals.count(i) for i in set(intervals))
            if identical_count > self.config.max_identical_intervals:
                issues.append(f"{identical_count} identical intervals detected (bot-like)")
        
        # 4. Check fingerprint stability (if provided)
        if self.config.check_fingerprint_consistency and fingerprint_data:
            stability_ok = self._check_fingerprint_stability(account_id, fingerprint_data)
            if not stability_ok:
                warnings.append("Fingerprint inconsistency detected")
        
        # 5. Determine pass/fail
        verification_passed = len(issues) == 0
        
        # 6. Calculate risk adjustment
        if verification_passed:
            risk_adjustment = -self.config.risk_reduction_on_pass
        else:
            risk_adjustment = self.config.risk_increase_on_fail
        
        # Create result
        result = VerificationResult(
            account_id=account_id,
            task_id=task_id,
            verification_passed=verification_passed,
            time_spent_seconds=time_spent,
            session_start=session_start,
            session_end=session_end,
            detected_actions=list(unique_actions),
            action_count=len(actions_performed),
            action_diversity_score=action_diversity,
            interval_variance=interval_variance,
            mechanical_score=mechanical_score,
            risk_adjustment=risk_adjustment,
            issues=issues,
            warnings=warnings,
            metadata={"fingerprint_checked": fingerprint_data is not None}
        )
        
        # Store result
        if account_id not in self._verification_history:
            self._verification_history[account_id] = []
        self._verification_history[account_id].append(result)
        
        if verification_passed:
            logger.info(f"✅ Verification passed for {account_id} (task {task_id})")
        else:
            logger.warning(f"❌ Verification failed for {account_id}: {', '.join(issues)}")
        
        return result
    
    def quick_verify(
        self,
        account_id: str,
        task_id: str,
        time_spent_seconds: int,
        action_count: int
    ) -> bool:
        """
        Verificación rápida (solo tiempo y cantidad).
        
        Returns:
            True si pasa verificación básica
        """
        if time_spent_seconds < self.config.min_session_duration:
            return False
        
        if action_count < 2:
            return False
        
        return True
    
    def get_verification_history(
        self,
        account_id: str
    ) -> List[VerificationResult]:
        """Obtiene historial de verificaciones"""
        return self._verification_history.get(account_id, [])
    
    def get_success_rate(self, account_id: str) -> float:
        """
        Calcula tasa de éxito en verificaciones.
        
        Returns:
            Porcentaje 0.0-1.0
        """
        history = self._verification_history.get(account_id, [])
        if not history:
            return 0.0
        
        passed = len([r for r in history if r.verification_passed])
        return passed / len(history)
    
    def get_average_mechanical_score(self, account_id: str) -> float:
        """
        Calcula mechanical score promedio.
        
        Returns:
            Score 0.0-1.0 (lower = more human-like)
        """
        history = self._verification_history.get(account_id, [])
        if not history:
            return 0.5  # Default
        
        scores = [r.mechanical_score for r in history]
        return sum(scores) / len(scores)
    
    def get_cumulative_risk_adjustment(self, account_id: str) -> float:
        """
        Calcula ajuste de riesgo acumulado.
        
        Returns:
            Ajuste total (positive = increase, negative = decrease)
        """
        history = self._verification_history.get(account_id, [])
        return sum(r.risk_adjustment for r in history)
    
    # ========================================================================
    # INTERNAL - FINGERPRINT CHECKING
    # ========================================================================
    
    def _check_fingerprint_stability(
        self,
        account_id: str,
        current_fingerprint: Dict
    ) -> bool:
        """
        Verifica estabilidad del fingerprint.
        
        Returns:
            True si es estable
        """
        # TODO: Implement actual fingerprint comparison
        # For now, always return True
        return True


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def create_mock_verification_result(
    account_id: str,
    task_id: str,
    passed: bool = True
) -> VerificationResult:
    """Helper para crear resultado de verificación de prueba"""
    
    now = datetime.now()
    
    return VerificationResult(
        account_id=account_id,
        task_id=task_id,
        verification_passed=passed,
        time_spent_seconds=240,
        session_start=now - timedelta(minutes=4),
        session_end=now,
        detected_actions=["scroll", "like", "comment"],
        action_count=5,
        action_diversity_score=0.6,
        interval_variance=0.45,
        mechanical_score=0.15,
        risk_adjustment=-0.05 if passed else 0.10,
        issues=[] if passed else ["Test failure"],
        warnings=[],
        metadata={}
    )


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    "HumanActionVerifierConfig",
    "VerificationResult",
    "HumanActionVerifier",
    "create_mock_verification_result",
]
