"""
Content Engine Configuration
Configuración centralizada con cost limits y timeouts.
"""

import os
from typing import Dict, Any
from pydantic import BaseModel, Field


class ContentEngineConfig(BaseModel):
    """Configuración del Content Engine con límites de coste y recursos."""
    
    # LLM Configuration
    llm_model: str = Field(
        default="gpt-4o-mini",
        description="Modelo LLM por defecto (optimizado para coste)"
    )
    llm_temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    llm_max_tokens: int = Field(default=500, le=2000)
    llm_timeout: int = Field(default=30, description="Timeout en segundos")
    
    # Cost Limits (EUR)
    max_cost_per_request: float = Field(
        default=0.05,
        description="Coste máximo por request en EUR"
    )
    max_daily_cost: float = Field(
        default=1.50,
        description="Coste máximo diario en EUR"
    )
    max_monthly_cost: float = Field(
        default=10.0,
        description="Coste máximo mensual en EUR (Sprint 1 target)"
    )
    
    # Rate Limits
    max_requests_per_minute: int = Field(default=10)
    max_requests_per_hour: int = Field(default=100)
    
    # Feature Flags
    enable_video_analysis: bool = Field(default=True)
    enable_trend_analysis: bool = Field(default=True)
    enable_hook_generation: bool = Field(default=True)
    enable_caption_generation: bool = Field(default=True)
    
    # Telemetry
    enable_telemetry: bool = Field(default=True)
    telemetry_sample_rate: float = Field(default=1.0, ge=0.0, le=1.0)
    
    # Prompts versioning
    prompt_version: str = Field(default="1.0.0")
    prompt_base_path: str = Field(default="app/prompts/content_engine")
    
    # Validation
    min_confidence_threshold: float = Field(
        default=0.6,
        ge=0.0,
        le=1.0,
        description="Umbral mínimo de confianza para outputs"
    )
    
    class Config:
        env_prefix = "CONTENT_ENGINE_"
        
    @classmethod
    def from_env(cls) -> "ContentEngineConfig":
        """Carga configuración desde variables de entorno."""
        return cls(
            llm_model=os.getenv("CONTENT_ENGINE_LLM_MODEL", "gpt-4o-mini"),
            llm_temperature=float(os.getenv("CONTENT_ENGINE_LLM_TEMPERATURE", "0.7")),
            llm_max_tokens=int(os.getenv("CONTENT_ENGINE_LLM_MAX_TOKENS", "500")),
            max_cost_per_request=float(os.getenv("CONTENT_ENGINE_MAX_COST_PER_REQUEST", "0.05")),
            max_daily_cost=float(os.getenv("CONTENT_ENGINE_MAX_DAILY_COST", "1.50")),
            max_monthly_cost=float(os.getenv("CONTENT_ENGINE_MAX_MONTHLY_COST", "10.0")),
        )
    
    def get_cost_limits(self) -> Dict[str, float]:
        """Retorna diccionario con límites de coste."""
        return {
            "per_request": self.max_cost_per_request,
            "daily": self.max_daily_cost,
            "monthly": self.max_monthly_cost,
        }


# Instancia global de configuración
config = ContentEngineConfig.from_env()
