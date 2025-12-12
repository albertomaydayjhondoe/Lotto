"""
Rules Loader v2 - Load and merge rule files for Sprint 5

Handles loading and merging of:
- base_rules.json (system-wide)
- brand_static_rules.json (from artist onboarding)
- satellite_rules.json (experimental channels)
- content_strategy.json (posting strategy)
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from enum import Enum
from pydantic import BaseModel, Field


class RulePriority(str, Enum):
    """Rule priority levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class RuleType(str, Enum):
    """Types of rules."""
    BRAND_COMPLIANCE = "brand_compliance"
    QUALITY_GATE = "quality_gate"
    SATELLITE_PROHIBITION = "satellite_prohibition"
    COST_GUARD = "cost_guard"
    SAFETY_CHECK = "safety_check"


class DecisionRule(BaseModel):
    """Individual decision rule."""
    rule_id: str
    rule_type: RuleType
    priority: RulePriority
    name: str
    description: str
    conditions: Dict[str, Any]
    actions: List[str]
    enabled: bool = True


class MergedRuleSet(BaseModel):
    """Merged rules from all sources."""
    version: str = "1.0.0"
    rules: List[DecisionRule]
    brand_config: Dict[str, Any] = Field(default_factory=dict)
    satellite_config: Dict[str, Any] = Field(default_factory=dict)
    strategy_config: Dict[str, Any] = Field(default_factory=dict)


class RulesLoaderV2:
    """Load and merge rules for autonomous decision making."""
    
    def __init__(self, base_dir: Path):
        self.base_dir = Path(base_dir)
        self.rules_dir = self.base_dir / "rules_engine" / "rules"
        self.brand_dir = self.base_dir / "community_ai" / "brand"
    
    def load_base_rules(self) -> List[DecisionRule]:
        """Load base system rules."""
        base_path = self.rules_dir / "base_rules.json"
        
        if not base_path.exists():
            return []
        
        with open(base_path) as f:
            data = json.load(f)
        
        rules = []
        for rule_data in data.get("rules", []):
            rule = DecisionRule(
                rule_id=rule_data["rule_id"],
                rule_type=RuleType(rule_data["type"]),
                priority=RulePriority(rule_data["priority"]),
                name=rule_data["name"],
                description=rule_data["description"],
                conditions=rule_data["conditions"],
                actions=rule_data["actions"]
            )
            rules.append(rule)
        
        return rules
    
    def load_brand_config(self) -> Dict[str, Any]:
        """Load brand static rules from onboarding."""
        brand_path = self.brand_dir / "brand_static_rules.json"
        
        if not brand_path.exists():
            return {}
        
        with open(brand_path) as f:
            return json.load(f)
    
    def load_satellite_config(self) -> Dict[str, Any]:
        """Load satellite rules."""
        satellite_path = self.brand_dir / "satellite_rules.json"
        
        if not satellite_path.exists():
            return {}
        
        with open(satellite_path) as f:
            return json.load(f)
    
    def load_strategy_config(self) -> Dict[str, Any]:
        """Load content strategy."""
        strategy_path = self.brand_dir / "content_strategy.json"
        
        if not strategy_path.exists():
            return {}
        
        with open(strategy_path) as f:
            return json.load(f)
    
    def load_and_merge(self) -> MergedRuleSet:
        """Load all rules and configs, return merged ruleset."""
        rules = self.load_base_rules()
        brand_config = self.load_brand_config()
        satellite_config = self.load_satellite_config()
        strategy_config = self.load_strategy_config()
        
        # Add brand compliance rules
        if brand_config:
            quality_std = brand_config.get("quality_standards", {})
            if quality_std:
                rule = DecisionRule(
                    rule_id="brand_quality_official",
                    rule_type=RuleType.QUALITY_GATE,
                    priority=RulePriority.HIGH,
                    name="Official Quality Gate",
                    description="Enforce official channel quality",
                    conditions={
                        "channel": "official",
                        "min_quality": quality_std.get("official_channel", {}).get("minimum_quality_score", 8)
                    },
                    actions=["reject_if_below_threshold"]
                )
                rules.append(rule)
        
        # Add satellite prohibitions
        if satellite_config:
            prohibitions = satellite_config.get("prohibitions", {})
            for prohibition in prohibitions.get("absolute_prohibitions", []):
                rule = DecisionRule(
                    rule_id=f"satellite_prohibition_{prohibition}",
                    rule_type=RuleType.SATELLITE_PROHIBITION,
                    priority=RulePriority.CRITICAL,
                    name=f"Satellite: {prohibition}",
                    description=f"Enforce {prohibition}",
                    conditions={"channel": "satellite", "check": prohibition},
                    actions=["reject"]
                )
                rules.append(rule)
        
        return MergedRuleSet(
            rules=rules,
            brand_config=brand_config,
            satellite_config=satellite_config,
            strategy_config=strategy_config
        )
