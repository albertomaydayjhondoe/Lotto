"""
SPRINT 14 - Decision Classifier (Clasificador de Tipos de Decisión)

Objetivo:
Clasificar decisiones en 4 niveles según criticidad y requerimientos de gobernanza.

Niveles:
1️⃣ MICRO → auto, sin ledger
2️⃣ STANDARD → ledger obligatorio
3️⃣ CRITICAL → simulación + Gemini 3.0
4️⃣ STRUCTURAL → decisión humana obligatoria + Gemini

Esto da:
- Velocidad (MICRO decisions no bloquean)
- Seguridad (CRITICAL+ validado)
- Flexibilidad (niveles configurables)
- Gobernanza total (STRUCTURAL requiere humano)

Integración:
- Orchestrator (consulta clasificación antes de decidir)
- Decision Ledger (STANDARD+ van al ledger)
- Risk Simulation (CRITICAL+ requieren simulación)
- Supervisor Layer (CRITICAL+ requieren validación LLM)
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Any, Optional


class DecisionLevel(Enum):
    """
    Niveles de clasificación de decisiones
    """
    MICRO = "micro"  # Auto, sin ledger, sin simulación
    STANDARD = "standard"  # Ledger obligatorio, sin simulación
    CRITICAL = "critical"  # Ledger + simulación + Gemini 3.0
    STRUCTURAL = "structural"  # Ledger + simulación + Gemini + humano obligatorio


@dataclass
class ClassificationResult:
    """
    Resultado de clasificación de una decisión
    """
    level: DecisionLevel
    requires_ledger: bool
    requires_simulation: bool
    requires_llm_validation: bool
    requires_human_approval: bool
    
    # Justificación
    reasoning: List[str]
    risk_factors: List[str]
    
    # Umbrales aplicados
    risk_threshold: float
    impact_threshold: float
    
    # Metadata
    confidence: float = 1.0
    
    def get_summary(self) -> str:
        """Get human-readable summary"""
        return f"Level: {self.level.value.upper()} | " \
               f"Ledger: {self.requires_ledger} | " \
               f"Simulation: {self.requires_simulation} | " \
               f"LLM: {self.requires_llm_validation} | " \
               f"Human: {self.requires_human_approval}"
    
    def is_auto_executable(self) -> bool:
        """Check if decision can be executed automatically"""
        return not self.requires_human_approval


class DecisionClassifier:
    """
    Clasificador de decisiones según criticidad
    
    Características:
    - Clasificación rápida (< 50ms)
    - Reglas configurables
    - 4 niveles de criticidad
    - Integración con todo el sistema
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Umbrales para clasificación
        self.micro_max_risk = self.config.get('micro_max_risk', 0.2)
        self.standard_max_risk = self.config.get('standard_max_risk', 0.5)
        self.critical_max_risk = self.config.get('critical_max_risk', 0.75)
        
        self.micro_max_impact = self.config.get('micro_max_impact', 0.1)
        self.standard_max_impact = self.config.get('standard_max_impact', 0.3)
        
        # Reglas forzadas (sobrescriben umbrales)
        self.forced_critical_actions = set(self.config.get('forced_critical', [
            'emergency_stop',
            'mass_account_activation',
            'policy_override'
        ]))
        
        self.forced_structural_actions = set(self.config.get('forced_structural', [
            'strategy_change',
            'system_reconfiguration',
            'kill_switch_activation'
        ]))
        
        # Estadísticas
        self.classifications_count = {
            DecisionLevel.MICRO: 0,
            DecisionLevel.STANDARD: 0,
            DecisionLevel.CRITICAL: 0,
            DecisionLevel.STRUCTURAL: 0
        }
    
    def classify_decision(
        self,
        decision_type: str,
        estimated_risk: float,
        estimated_impact: float,
        context: Optional[Dict[str, Any]] = None
    ) -> ClassificationResult:
        """
        Clasificar una decisión según criticidad
        
        Args:
            decision_type: Tipo de decisión (ej: "content_boost", "account_activation")
            estimated_risk: Riesgo estimado (0.0 - 1.0)
            estimated_impact: Impacto estimado (0.0 - 1.0)
            context: Contexto adicional {
                'accounts_affected': int,
                'irreversible': bool,
                'financial_impact': float,
                'platform_risk': str,
                ...
            }
        
        Returns:
            ClassificationResult con nivel y requerimientos
        """
        context = context or {}
        
        # Reglas forzadas (overrides)
        if decision_type in self.forced_structural_actions:
            return self._create_structural_result(decision_type, estimated_risk, estimated_impact, context)
        
        if decision_type in self.forced_critical_actions:
            return self._create_critical_result(decision_type, estimated_risk, estimated_impact, context)
        
        # Factores adicionales del contexto
        accounts_affected = context.get('accounts_affected', 1)
        irreversible = context.get('irreversible', False)
        financial_impact = context.get('financial_impact', 0.0)
        
        # Factores de riesgo identificados
        risk_factors = []
        
        if estimated_risk > 0.7:
            risk_factors.append(f"High risk score: {estimated_risk:.2f}")
        if estimated_impact > 0.5:
            risk_factors.append(f"High impact: {estimated_impact:.2f}")
        if accounts_affected > 10:
            risk_factors.append(f"Many accounts affected: {accounts_affected}")
        if irreversible:
            risk_factors.append("Action is irreversible")
        if financial_impact > 1000:
            risk_factors.append(f"High financial impact: ${financial_impact:.0f}")
        
        # Clasificación por niveles
        
        # STRUCTURAL: Decisiones de máxima criticidad
        if (estimated_risk > self.critical_max_risk or
            estimated_impact > 0.7 or
            accounts_affected > 50 or
            irreversible and estimated_risk > 0.5 or
            financial_impact > 5000):
            
            result = self._create_structural_result(decision_type, estimated_risk, estimated_impact, context)
            result.risk_factors = risk_factors
            self.classifications_count[DecisionLevel.STRUCTURAL] += 1
            return result
        
        # CRITICAL: Alta criticidad, requiere simulación + LLM
        if (estimated_risk > self.standard_max_risk or
            estimated_impact > self.standard_max_impact or
            accounts_affected > 5 or
            irreversible or
            financial_impact > 500):
            
            result = self._create_critical_result(decision_type, estimated_risk, estimated_impact, context)
            result.risk_factors = risk_factors
            self.classifications_count[DecisionLevel.CRITICAL] += 1
            return result
        
        # STANDARD: Criticidad media, requiere ledger
        if (estimated_risk > self.micro_max_risk or
            estimated_impact > self.micro_max_impact or
            accounts_affected > 1):
            
            result = self._create_standard_result(decision_type, estimated_risk, estimated_impact, context)
            result.risk_factors = risk_factors
            self.classifications_count[DecisionLevel.STANDARD] += 1
            return result
        
        # MICRO: Baja criticidad, no requiere nada especial
        result = self._create_micro_result(decision_type, estimated_risk, estimated_impact, context)
        result.risk_factors = risk_factors
        self.classifications_count[DecisionLevel.MICRO] += 1
        return result
    
    def _create_micro_result(
        self,
        decision_type: str,
        risk: float,
        impact: float,
        context: Dict[str, Any]
    ) -> ClassificationResult:
        """Create MICRO level classification"""
        return ClassificationResult(
            level=DecisionLevel.MICRO,
            requires_ledger=False,
            requires_simulation=False,
            requires_llm_validation=False,
            requires_human_approval=False,
            reasoning=[
                "Low risk and low impact",
                "Single account affected",
                "Reversible action",
                "Standard operation"
            ],
            risk_factors=[],
            risk_threshold=self.micro_max_risk,
            impact_threshold=self.micro_max_impact,
            confidence=1.0
        )
    
    def _create_standard_result(
        self,
        decision_type: str,
        risk: float,
        impact: float,
        context: Dict[str, Any]
    ) -> ClassificationResult:
        """Create STANDARD level classification"""
        reasoning = [
            "Moderate risk or impact",
            "Requires audit trail",
            "Standard governance applies"
        ]
        
        if risk > self.micro_max_risk:
            reasoning.append(f"Risk above MICRO threshold: {risk:.2f}")
        if impact > self.micro_max_impact:
            reasoning.append(f"Impact above MICRO threshold: {impact:.2f}")
        
        return ClassificationResult(
            level=DecisionLevel.STANDARD,
            requires_ledger=True,
            requires_simulation=False,
            requires_llm_validation=False,
            requires_human_approval=False,
            reasoning=reasoning,
            risk_factors=[],
            risk_threshold=self.standard_max_risk,
            impact_threshold=self.standard_max_impact,
            confidence=1.0
        )
    
    def _create_critical_result(
        self,
        decision_type: str,
        risk: float,
        impact: float,
        context: Dict[str, Any]
    ) -> ClassificationResult:
        """Create CRITICAL level classification"""
        reasoning = [
            "High risk or high impact",
            "Requires pre-simulation",
            "Requires LLM validation (Gemini 3.0)",
            "Full audit trail mandatory"
        ]
        
        if risk > self.standard_max_risk:
            reasoning.append(f"Risk exceeds STANDARD threshold: {risk:.2f}")
        if impact > self.standard_max_impact:
            reasoning.append(f"Impact exceeds STANDARD threshold: {impact:.2f}")
        if context.get('irreversible'):
            reasoning.append("Action is irreversible")
        if context.get('accounts_affected', 0) > 5:
            reasoning.append(f"Multiple accounts affected: {context['accounts_affected']}")
        
        return ClassificationResult(
            level=DecisionLevel.CRITICAL,
            requires_ledger=True,
            requires_simulation=True,
            requires_llm_validation=True,
            requires_human_approval=False,
            reasoning=reasoning,
            risk_factors=[],
            risk_threshold=self.critical_max_risk,
            impact_threshold=0.5,
            confidence=1.0
        )
    
    def _create_structural_result(
        self,
        decision_type: str,
        risk: float,
        impact: float,
        context: Dict[str, Any]
    ) -> ClassificationResult:
        """Create STRUCTURAL level classification"""
        reasoning = [
            "MAXIMUM CRITICALITY",
            "Structural/strategic decision",
            "Requires human approval",
            "Requires LLM validation",
            "Requires pre-simulation",
            "Full audit trail mandatory",
            "Irreversible or high-consequence action"
        ]
        
        if risk > self.critical_max_risk:
            reasoning.append(f"CRITICAL risk level: {risk:.2f}")
        if impact > 0.7:
            reasoning.append(f"MAJOR impact: {impact:.2f}")
        if context.get('accounts_affected', 0) > 50:
            reasoning.append(f"MASS operation: {context['accounts_affected']} accounts")
        if context.get('financial_impact', 0) > 5000:
            reasoning.append(f"HIGH financial impact: ${context['financial_impact']:.0f}")
        if decision_type in self.forced_structural_actions:
            reasoning.append(f"Action '{decision_type}' is ALWAYS structural")
        
        return ClassificationResult(
            level=DecisionLevel.STRUCTURAL,
            requires_ledger=True,
            requires_simulation=True,
            requires_llm_validation=True,
            requires_human_approval=True,
            reasoning=reasoning,
            risk_factors=[],
            risk_threshold=1.0,  # Max
            impact_threshold=1.0,  # Max
            confidence=1.0
        )
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get classifier statistics"""
        total = sum(self.classifications_count.values())
        
        return {
            'total_classifications': total,
            'by_level': {
                level.value: count 
                for level, count in self.classifications_count.items()
            },
            'distribution': {
                level.value: count / total if total > 0 else 0
                for level, count in self.classifications_count.items()
            },
            'thresholds': {
                'micro_max_risk': self.micro_max_risk,
                'standard_max_risk': self.standard_max_risk,
                'critical_max_risk': self.critical_max_risk
            }
        }
    
    def update_thresholds(
        self,
        micro_max_risk: Optional[float] = None,
        standard_max_risk: Optional[float] = None,
        critical_max_risk: Optional[float] = None
    ):
        """Update classification thresholds"""
        if micro_max_risk is not None:
            self.micro_max_risk = micro_max_risk
        if standard_max_risk is not None:
            self.standard_max_risk = standard_max_risk
        if critical_max_risk is not None:
            self.critical_max_risk = critical_max_risk


# Helper functions

def quick_classify(
    decision_type: str,
    risk: float,
    impact: float
) -> DecisionLevel:
    """
    Quick classification without full result
    
    Returns:
        DecisionLevel
    """
    classifier = DecisionClassifier()
    result = classifier.classify_decision(decision_type, risk, impact)
    return result.level


def requires_simulation(classification: ClassificationResult) -> bool:
    """Check if classification requires simulation"""
    return classification.requires_simulation


def requires_human_approval(classification: ClassificationResult) -> bool:
    """Check if classification requires human approval"""
    return classification.requires_human_approval
