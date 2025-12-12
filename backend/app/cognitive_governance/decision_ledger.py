"""
SPRINT 14 - Decision Ledger (Ledger Cognitivo de Decisiones)

Objetivo:
Registrar toda decisión crítica o estándar tomada por el Orchestrator con contexto completo.

Características:
- Inmutable: Una vez registrado, no se modifica
- Auditable: Exportable a Dashboard (Sprint 13)
- Completo: Incluye inputs, alternativas, reasoning, confianza, riesgo
- Transversal: Integrado con todos los módulos

Estructura de decisión:
{
  "decision_id": "DEC-2025-05-01-014",
  "actor": "Orchestrator",
  "decision_type": "CONTENT_BOOST",
  "inputs": ["ML", "SatelliteEngine", "RulesEngine"],
  "alternatives_considered": ["IG_Reel_008", "YT_Short_021"],
  "chosen": "YT_Video_014",
  "reasoning": ["Retention +12%", "Near breakout", "Low identity risk"],
  "confidence": 0.83,
  "risk_score": 0.21,
  "validated_by": "Gemini_3.0",
  "timestamp": "2025-05-01T14:22:10Z"
}

Requisitos:
✔ Obligatorio para decisiones STANDARD, CRITICAL, STRUCTURAL
✔ Inmutable (append-only)
✔ Auditable
✔ Exportable a Sprint 13 Dashboard
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from typing import List, Dict, Any, Optional
import json
import csv
from pathlib import Path
import hashlib


class DecisionType(Enum):
    """Tipos de decisiones rastreadas"""
    # Content decisions
    CONTENT_BOOST = "content_boost"
    CONTENT_SUPPRESS = "content_suppress"
    CONTENT_SCHEDULE = "content_schedule"
    
    # Account decisions
    ACCOUNT_ACTIVATION = "account_activation"
    ACCOUNT_PAUSE = "account_pause"
    ACCOUNT_WARMUP = "account_warmup"
    
    # Scaling decisions
    SCALE_UP = "scale_up"
    SCALE_DOWN = "scale_down"
    SCALE_HOLD = "scale_hold"
    
    # Risk decisions
    RISK_MITIGATION = "risk_mitigation"
    EMERGENCY_STOP = "emergency_stop"
    
    # Structural decisions
    STRATEGY_CHANGE = "strategy_change"
    POLICY_UPDATE = "policy_update"
    SYSTEM_RECONFIGURATION = "system_reconfiguration"


@dataclass
class DecisionRecord:
    """
    Registro inmutable de una decisión del Orchestrator
    """
    # Identificación
    decision_id: str
    actor: str  # Quién tomó la decisión (ej: "Orchestrator", "Human", "AutomatedAgent")
    decision_type: DecisionType
    timestamp: datetime
    
    # Contexto de entrada
    inputs: List[str]  # Fuentes consultadas: ["ML", "SatelliteEngine", "RulesEngine"]
    context: Dict[str, Any]  # Contexto completo de la decisión
    
    # Proceso decisional
    alternatives_considered: List[str]  # Opciones evaluadas
    chosen: str  # Opción seleccionada
    reasoning: List[str]  # Razonamientos detrás de la elección
    
    # Métricas de confianza
    confidence: float  # 0.0 - 1.0
    risk_score: float  # 0.0 - 1.0
    expected_impact: Optional[Dict[str, float]] = None  # ej: {"engagement": +0.12, "risk": -0.05}
    
    # Validación
    validated_by: Optional[str] = None  # ej: "Gemini_3.0", "GPT-4", "Human"
    validation_confidence: Optional[float] = None
    
    # Metadata
    tags: List[str] = field(default_factory=list)
    notes: Optional[str] = None
    reversible: bool = True
    execution_status: str = "pending"  # pending, executed, failed, reversed
    
    # Audit trail
    hash: Optional[str] = field(default=None, init=False)
    
    def __post_init__(self):
        """Generate immutable hash for the record"""
        if self.hash is None:
            content = f"{self.decision_id}{self.actor}{self.decision_type.value}{self.timestamp.isoformat()}"
            self.hash = hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        data['decision_type'] = self.decision_type.value
        data['timestamp'] = self.timestamp.isoformat()
        return data
    
    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict(), indent=2)
    
    def is_critical(self) -> bool:
        """Check if this is a critical decision"""
        critical_types = {
            DecisionType.EMERGENCY_STOP,
            DecisionType.STRATEGY_CHANGE,
            DecisionType.POLICY_UPDATE,
            DecisionType.SYSTEM_RECONFIGURATION,
        }
        return self.decision_type in critical_types or self.risk_score > 0.7
    
    def is_reversible(self) -> bool:
        """Check if this decision can be reversed"""
        return self.reversible and self.execution_status in ["pending", "executed"]


class DecisionLedger:
    """
    Ledger inmutable de todas las decisiones del sistema
    
    Características:
    - Append-only (solo agregar, no modificar)
    - Persistencia en JSON + CSV
    - Búsqueda por tipo, actor, timestamp
    - Exportación a Dashboard (Sprint 13)
    - Integración con Audit Log
    """
    
    def __init__(self, storage_path: str = "./storage/cognitive_governance"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.ledger_file = self.storage_path / "decision_ledger.jsonl"
        self.csv_export_file = self.storage_path / "decision_ledger.csv"
        
        # In-memory cache (últimas 1000 decisiones)
        self._cache: List[DecisionRecord] = []
        self._cache_limit = 1000
        
        # Estadísticas
        self.total_decisions = 0
        self.decisions_by_type: Dict[DecisionType, int] = {}
        self.decisions_by_actor: Dict[str, int] = {}
        
        # Load existing ledger
        self._load_ledger()
    
    def record_decision(self, decision: DecisionRecord) -> str:
        """
        Registrar una nueva decisión en el ledger
        
        Returns:
            decision_id: ID único de la decisión
        """
        # Validate
        if not decision.decision_id:
            decision.decision_id = self._generate_decision_id()
        
        # Append to file (inmutable)
        with open(self.ledger_file, 'a') as f:
            f.write(decision.to_json() + '\n')
        
        # Update cache
        self._cache.append(decision)
        if len(self._cache) > self._cache_limit:
            self._cache.pop(0)
        
        # Update stats
        self.total_decisions += 1
        self.decisions_by_type[decision.decision_type] = \
            self.decisions_by_type.get(decision.decision_type, 0) + 1
        self.decisions_by_actor[decision.actor] = \
            self.decisions_by_actor.get(decision.actor, 0) + 1
        
        return decision.decision_id
    
    def get_decision(self, decision_id: str) -> Optional[DecisionRecord]:
        """Retrieve a specific decision by ID"""
        # Check cache first
        for decision in reversed(self._cache):
            if decision.decision_id == decision_id:
                return decision
        
        # Search in file
        with open(self.ledger_file, 'r') as f:
            for line in f:
                data = json.loads(line)
                if data['decision_id'] == decision_id:
                    return self._dict_to_decision(data)
        
        return None
    
    def get_recent_decisions(self, limit: int = 50) -> List[DecisionRecord]:
        """Get most recent decisions"""
        return list(reversed(self._cache[-limit:]))
    
    def get_decisions_by_type(
        self, 
        decision_type: DecisionType,
        limit: Optional[int] = None
    ) -> List[DecisionRecord]:
        """Get decisions by type"""
        results = [d for d in self._cache if d.decision_type == decision_type]
        if limit:
            results = results[-limit:]
        return results
    
    def get_decisions_by_actor(
        self, 
        actor: str,
        limit: Optional[int] = None
    ) -> List[DecisionRecord]:
        """Get decisions by actor"""
        results = [d for d in self._cache if d.actor == actor]
        if limit:
            results = results[-limit:]
        return results
    
    def get_critical_decisions(self, hours: int = 24) -> List[DecisionRecord]:
        """Get all critical decisions in last N hours"""
        cutoff = datetime.now().timestamp() - (hours * 3600)
        return [
            d for d in self._cache 
            if d.is_critical() and d.timestamp.timestamp() > cutoff
        ]
    
    def get_decisions_by_timerange(
        self, 
        start: datetime,
        end: datetime
    ) -> List[DecisionRecord]:
        """Get decisions within a time range"""
        return [
            d for d in self._cache 
            if start <= d.timestamp <= end
        ]
    
    def export_to_csv(self, output_path: Optional[str] = None) -> str:
        """
        Export ledger to CSV for analysis
        
        Returns:
            path: Path to exported CSV file
        """
        output_path = output_path or str(self.csv_export_file)
        
        with open(output_path, 'w', newline='') as f:
            writer = csv.writer(f)
            
            # Header
            writer.writerow([
                'decision_id', 'timestamp', 'actor', 'decision_type',
                'chosen', 'confidence', 'risk_score', 'validated_by',
                'execution_status', 'hash'
            ])
            
            # Data from cache
            for decision in self._cache:
                writer.writerow([
                    decision.decision_id,
                    decision.timestamp.isoformat(),
                    decision.actor,
                    decision.decision_type.value,
                    decision.chosen,
                    decision.confidence,
                    decision.risk_score,
                    decision.validated_by or 'none',
                    decision.execution_status,
                    decision.hash
                ])
        
        return output_path
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get ledger statistics"""
        return {
            'total_decisions': self.total_decisions,
            'decisions_by_type': {
                k.value: v for k, v in self.decisions_by_type.items()
            },
            'decisions_by_actor': self.decisions_by_actor,
            'cache_size': len(self._cache),
            'critical_decisions_24h': len(self.get_critical_decisions(24)),
            'avg_confidence': sum(d.confidence for d in self._cache) / len(self._cache) if self._cache else 0,
            'avg_risk_score': sum(d.risk_score for d in self._cache) / len(self._cache) if self._cache else 0,
        }
    
    def mark_executed(self, decision_id: str) -> bool:
        """Mark a decision as executed"""
        decision = self.get_decision(decision_id)
        if decision:
            decision.execution_status = "executed"
            return True
        return False
    
    def mark_failed(self, decision_id: str, reason: str = "") -> bool:
        """Mark a decision as failed"""
        decision = self.get_decision(decision_id)
        if decision:
            decision.execution_status = "failed"
            if reason and decision.notes:
                decision.notes += f" | Failed: {reason}"
            elif reason:
                decision.notes = f"Failed: {reason}"
            return True
        return False
    
    def mark_reversed(self, decision_id: str, reason: str = "") -> bool:
        """Mark a decision as reversed"""
        decision = self.get_decision(decision_id)
        if decision and decision.is_reversible():
            decision.execution_status = "reversed"
            if reason and decision.notes:
                decision.notes += f" | Reversed: {reason}"
            elif reason:
                decision.notes = f"Reversed: {reason}"
            return True
        return False
    
    def _generate_decision_id(self) -> str:
        """Generate unique decision ID"""
        now = datetime.now()
        count = self.total_decisions + 1
        return f"DEC-{now.strftime('%Y-%m-%d')}-{count:04d}"
    
    def _load_ledger(self):
        """Load existing ledger from file"""
        if not self.ledger_file.exists():
            return
        
        with open(self.ledger_file, 'r') as f:
            for line in f:
                try:
                    data = json.loads(line)
                    decision = self._dict_to_decision(data)
                    self._cache.append(decision)
                    self.total_decisions += 1
                    self.decisions_by_type[decision.decision_type] = \
                        self.decisions_by_type.get(decision.decision_type, 0) + 1
                    self.decisions_by_actor[decision.actor] = \
                        self.decisions_by_actor.get(decision.actor, 0) + 1
                except Exception as e:
                    print(f"Error loading decision: {e}")
        
        # Keep only last N in cache
        if len(self._cache) > self._cache_limit:
            self._cache = self._cache[-self._cache_limit:]
    
    def _dict_to_decision(self, data: Dict[str, Any]) -> DecisionRecord:
        """Convert dictionary to DecisionRecord"""
        data['decision_type'] = DecisionType(data['decision_type'])
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return DecisionRecord(**data)


# Helper function for quick decision recording
def record_decision(
    actor: str,
    decision_type: DecisionType,
    inputs: List[str],
    alternatives: List[str],
    chosen: str,
    reasoning: List[str],
    confidence: float,
    risk_score: float,
    context: Optional[Dict[str, Any]] = None,
    validated_by: Optional[str] = None,
    ledger: Optional[DecisionLedger] = None
) -> str:
    """
    Helper function to quickly record a decision
    
    Returns:
        decision_id
    """
    if ledger is None:
        ledger = DecisionLedger()
    
    decision = DecisionRecord(
        decision_id="",  # Will be generated
        actor=actor,
        decision_type=decision_type,
        timestamp=datetime.now(),
        inputs=inputs,
        context=context or {},
        alternatives_considered=alternatives,
        chosen=chosen,
        reasoning=reasoning,
        confidence=confidence,
        risk_score=risk_score,
        validated_by=validated_by
    )
    
    return ledger.record_decision(decision)
