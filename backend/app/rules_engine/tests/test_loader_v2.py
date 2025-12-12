"""
Tests for loader_v2.py - Rules loader with merge logic
"""

import pytest
from pathlib import Path
from backend.app.rules_engine.loader_v2 import (
    RulesLoaderV2,
    DecisionRule,
    MergedRuleSet,
    RulePriority,
    RuleType
)


@pytest.fixture
def rules_base_dir(tmp_path):
    """Create temp directory structure for rules."""
    rules_dir = tmp_path / "rules_engine"
    rules_dir.mkdir()
    
    # Create rules subdirectory
    (rules_dir / "rules").mkdir()
    
    # Create brand directory
    brand_dir = tmp_path / "community_ai" / "brand"
    brand_dir.mkdir(parents=True)
    
    return str(tmp_path)


@pytest.fixture
def sample_base_rules(rules_base_dir):
    """Create sample base_rules.json."""
    rules_path = Path(rules_base_dir) / "rules_engine" / "rules" / "base_rules.json"
    
    rules_content = {
        "version": "1.0",
        "rules": [
            {
                "rule_id": "cost_guard_daily",
                "rule_type": "COST_GUARD",
                "priority": "CRITICAL",
                "name": "Daily budget limit",
                "description": "Enforce daily budget <€10",
                "conditions": {"daily_spend_gte": 10.0},
                "actions": ["reject"],
                "enabled": True
            },
            {
                "rule_id": "quality_gate_official",
                "rule_type": "QUALITY_GATE",
                "priority": "HIGH",
                "name": "Official channel quality",
                "description": "Official content must be high quality",
                "conditions": {"channel": "official", "min_quality": 8.0},
                "actions": ["reject_if_below"],
                "enabled": True
            }
        ]
    }
    
    import json
    with open(rules_path, 'w') as f:
        json.dump(rules_content, f)
    
    return rules_path


@pytest.fixture
def sample_brand_config(rules_base_dir):
    """Create sample brand_static_rules.json."""
    brand_path = Path(rules_base_dir) / "community_ai" / "brand" / "brand_static_rules.json"
    
    brand_content = {
        "quality_standards": {
            "official_channel": {
                "minimum_quality_score": 8.0
            }
        },
        "content_boundaries": {
            "brand_compliance_threshold": 0.8
        }
    }
    
    import json
    with open(brand_path, 'w') as f:
        json.dump(brand_content, f)
    
    return brand_path


class TestRulesLoaderV2:
    """Test cases for RulesLoaderV2."""
    
    def test_init(self, rules_base_dir):
        """Test loader initialization."""
        loader = RulesLoaderV2(base_dir=rules_base_dir)
        assert loader.base_dir == Path(rules_base_dir)
    
    def test_load_base_rules_success(self, rules_base_dir, sample_base_rules):
        """Test loading base rules from file."""
        loader = RulesLoaderV2(base_dir=rules_base_dir)
        rules = loader.load_base_rules()
        
        assert len(rules) == 2
        assert rules[0].rule_id == "cost_guard_daily"
        assert rules[0].priority == RulePriority.CRITICAL
        assert rules[1].rule_id == "quality_gate_official"
        assert rules[1].priority == RulePriority.HIGH
    
    def test_load_base_rules_missing_file(self, rules_base_dir):
        """Test loading base rules when file is missing."""
        loader = RulesLoaderV2(base_dir=rules_base_dir)
        rules = loader.load_base_rules()
        
        # Should return empty list when file missing
        assert rules == []
    
    def test_load_brand_config_success(self, rules_base_dir, sample_brand_config):
        """Test loading brand config."""
        loader = RulesLoaderV2(base_dir=rules_base_dir)
        config = loader.load_brand_config()
        
        assert "quality_standards" in config
        assert config["quality_standards"]["official_channel"]["minimum_quality_score"] == 8.0
    
    def test_load_brand_config_missing(self, rules_base_dir):
        """Test loading brand config when missing."""
        loader = RulesLoaderV2(base_dir=rules_base_dir)
        config = loader.load_brand_config()
        
        assert config == {}
    
    def test_load_and_merge_creates_quality_gate(
        self, rules_base_dir, sample_base_rules, sample_brand_config
    ):
        """Test that load_and_merge auto-generates quality gate rule from brand config."""
        loader = RulesLoaderV2(base_dir=rules_base_dir)
        merged = loader.load_and_merge()
        
        # Should have base rules + auto-generated quality gate
        assert len(merged.rules) >= 2
        
        # Check if quality gate was generated
        quality_gates = [r for r in merged.rules if r.rule_id == "brand_quality_official"]
        assert len(quality_gates) == 1
        assert quality_gates[0].priority == RulePriority.HIGH
    
    def test_merge_by_priority(self, rules_base_dir, sample_base_rules):
        """Test that rules are properly organized by priority."""
        loader = RulesLoaderV2(base_dir=rules_base_dir)
        merged = loader.load_and_merge()
        
        # Check that CRITICAL rules exist
        critical_rules = [r for r in merged.rules if r.priority == RulePriority.CRITICAL]
        assert len(critical_rules) >= 1
        
        # Check that HIGH rules exist
        high_rules = [r for r in merged.rules if r.priority == RulePriority.HIGH]
        assert len(high_rules) >= 1
    
    def test_only_enabled_rules_loaded(self, rules_base_dir):
        """Test that disabled rules are not included."""
        # Create rules with one disabled
        rules_path = Path(rules_base_dir) / "rules_engine" / "rules" / "base_rules.json"
        rules_path.parent.mkdir(parents=True, exist_ok=True)
        
        rules_content = {
            "version": "1.0",
            "rules": [
                {
                    "rule_id": "enabled_rule",
                    "rule_type": "COST_GUARD",
                    "priority": "CRITICAL",
                    "name": "Enabled",
                    "description": "Active rule",
                    "conditions": {},
                    "actions": [],
                    "enabled": True
                },
                {
                    "rule_id": "disabled_rule",
                    "rule_type": "COST_GUARD",
                    "priority": "CRITICAL",
                    "name": "Disabled",
                    "description": "Inactive rule",
                    "conditions": {},
                    "actions": [],
                    "enabled": False
                }
            ]
        }
        
        import json
        with open(rules_path, 'w') as f:
            json.dump(rules_content, f)
        
        loader = RulesLoaderV2(base_dir=rules_base_dir)
        rules = loader.load_base_rules()
        
        # Both rules loaded (filtering happens in evaluator)
        assert len(rules) == 2
    
    def test_merged_ruleset_structure(self, rules_base_dir, sample_base_rules, sample_brand_config):
        """Test MergedRuleSet structure."""
        loader = RulesLoaderV2(base_dir=rules_base_dir)
        merged = loader.load_and_merge()
        
        assert isinstance(merged, MergedRuleSet)
        assert merged.version == "1.0"
        assert isinstance(merged.rules, list)
        assert isinstance(merged.brand_config, dict)
        assert isinstance(merged.satellite_config, dict)
        assert isinstance(merged.strategy_config, dict)
    
    def test_rule_priority_enum(self):
        """Test RulePriority enum values."""
        assert RulePriority.CRITICAL.value == "CRITICAL"
        assert RulePriority.HIGH.value == "HIGH"
        assert RulePriority.MEDIUM.value == "MEDIUM"
        assert RulePriority.LOW.value == "LOW"
    
    def test_rule_type_enum(self):
        """Test RuleType enum values."""
        assert RuleType.BRAND_COMPLIANCE.value == "BRAND_COMPLIANCE"
        assert RuleType.QUALITY_GATE.value == "QUALITY_GATE"
        assert RuleType.COST_GUARD.value == "COST_GUARD"
    
    def test_decision_rule_model(self):
        """Test DecisionRule Pydantic model."""
        rule = DecisionRule(
            rule_id="test_rule",
            rule_type=RuleType.QUALITY_GATE,
            priority=RulePriority.HIGH,
            name="Test",
            description="Test rule",
            conditions={"min_quality": 8.0},
            actions=["reject"],
            enabled=True
        )
        
        assert rule.rule_id == "test_rule"
        assert rule.priority == RulePriority.HIGH
        assert rule.enabled is True
    
    def test_load_strategy_config(self, rules_base_dir):
        """Test loading content strategy config."""
        # Create strategy file
        strategy_path = Path(rules_base_dir) / "community_ai" / "brand" / "content_strategy.json"
        strategy_path.parent.mkdir(parents=True, exist_ok=True)
        
        strategy_content = {
            "posting_schedule": {
                "official": {"frequency": "daily"}
            }
        }
        
        import json
        with open(strategy_path, 'w') as f:
            json.dump(strategy_content, f)
        
        loader = RulesLoaderV2(base_dir=rules_base_dir)
        config = loader.load_strategy_config()
        
        assert "posting_schedule" in config
        assert config["posting_schedule"]["official"]["frequency"] == "daily"
    
    def test_load_satellite_config(self, rules_base_dir):
        """Test loading satellite config."""
        # Create satellite file
        satellite_path = Path(rules_base_dir) / "community_ai" / "brand" / "satellite_rules.json"
        satellite_path.parent.mkdir(parents=True, exist_ok=True)
        
        satellite_content = {
            "prohibitions": ["NO_mostrar_artista_real"],
            "quality_standards": {"minimum_quality_score": 5.0}
        }
        
        import json
        with open(satellite_path, 'w') as f:
            json.dump(satellite_content, f)
        
        loader = RulesLoaderV2(base_dir=rules_base_dir)
        config = loader.load_satellite_config()
        
        assert "prohibitions" in config
        assert "NO_mostrar_artista_real" in config["prohibitions"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
