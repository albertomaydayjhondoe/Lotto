"""
Test Config
Tests para configuración y límites de coste.
"""

import pytest
import os
from app.content_engine.config import ContentEngineConfig


def test_config_defaults():
    """Test: Config con valores por defecto."""
    config = ContentEngineConfig()
    
    assert config.llm_model == "gpt-4o-mini"
    assert config.llm_temperature == 0.7
    assert config.max_cost_per_request == 0.05
    assert config.max_monthly_cost == 10.0
    assert config.enable_telemetry is True


def test_config_custom_values():
    """Test: Config con valores personalizados."""
    config = ContentEngineConfig(
        llm_model="gpt-4",
        max_cost_per_request=0.10,
        max_daily_cost=2.0
    )
    
    assert config.llm_model == "gpt-4"
    assert config.max_cost_per_request == 0.10
    assert config.max_daily_cost == 2.0


def test_config_from_env(monkeypatch):
    """Test: Config se carga desde env vars."""
    monkeypatch.setenv("CONTENT_ENGINE_LLM_MODEL", "gpt-4-turbo")
    monkeypatch.setenv("CONTENT_ENGINE_MAX_DAILY_COST", "5.0")
    
    config = ContentEngineConfig.from_env()
    
    assert config.llm_model == "gpt-4-turbo"
    assert config.max_daily_cost == 5.0


def test_get_cost_limits():
    """Test: Método get_cost_limits retorna dict correcto."""
    config = ContentEngineConfig(
        max_cost_per_request=0.10,
        max_daily_cost=2.0,
        max_monthly_cost=15.0
    )
    
    limits = config.get_cost_limits()
    
    assert limits["per_request"] == 0.10
    assert limits["daily"] == 2.0
    assert limits["monthly"] == 15.0


def test_temperature_validation():
    """Test: Temperature fuera de rango falla."""
    with pytest.raises(ValueError):
        ContentEngineConfig(llm_temperature=3.0)  # > 2.0


def test_confidence_threshold_validation():
    """Test: Confidence threshold fuera de rango falla."""
    with pytest.raises(ValueError):
        ContentEngineConfig(min_confidence_threshold=1.5)  # > 1.0
