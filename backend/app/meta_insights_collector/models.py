# backend/app/meta_insights_collector/models.py

from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class InsightMetrics(BaseModel):
    """Métricas básicas de insights."""
    spend: float = Field(0.0, ge=0, description="Gasto en USD")
    impressions: int = Field(0, ge=0, description="Número de impresiones")
    clicks: int = Field(0, ge=0, description="Número de clicks")
    conversions: int = Field(0, ge=0, description="Número de conversiones")
    revenue: float = Field(0.0, ge=0, description="Ingresos en USD")
    ctr: float = Field(0.0, ge=0, description="Click-through rate (%)")
    cpc: float = Field(0.0, ge=0, description="Costo por click (USD)")
    roas: float = Field(0.0, ge=0, description="Return on ad spend")
    frequency: float = Field(0.0, ge=0, description="Frecuencia promedio")
    reach: Optional[int] = Field(None, ge=0, description="Alcance único")
    unique_clicks: Optional[int] = Field(None, ge=0, description="Clicks únicos")
    cost_per_conversion: Optional[float] = Field(None, ge=0, description="Costo por conversión (USD)")


class InsightResponse(BaseModel):
    """Respuesta de insight individual."""
    id: str = Field(..., description="ID del insight")
    entity_id: str = Field(..., description="ID de la entidad (campaign/adset/ad)")
    entity_type: str = Field(..., description="Tipo de entidad")
    date_start: datetime = Field(..., description="Fecha de inicio del período")
    date_end: datetime = Field(..., description="Fecha de fin del período")
    metrics: InsightMetrics = Field(..., description="Métricas del insight")
    created_at: datetime = Field(..., description="Fecha de creación del registro")
    updated_at: datetime = Field(..., description="Fecha de última actualización")


class InsightTimeline(BaseModel):
    """Timeline de insights para una entidad."""
    entity_id: str = Field(..., description="ID de la entidad")
    entity_type: str = Field(..., description="Tipo de entidad") 
    entity_name: Optional[str] = Field(None, description="Nombre de la entidad")
    date_range: Dict[str, str] = Field(..., description="Rango de fechas consultado")
    insights: List[InsightResponse] = Field(..., description="Lista de insights")
    total_insights: int = Field(..., description="Total de insights disponibles")
    
    # Métricas agregadas
    total_spend: float = Field(0.0, description="Gasto total del período")
    total_impressions: int = Field(0, description="Impresiones totales")
    total_clicks: int = Field(0, description="Clicks totales")
    total_conversions: int = Field(0, description="Conversiones totales") 
    total_revenue: float = Field(0.0, description="Ingresos totales")
    avg_ctr: float = Field(0.0, description="CTR promedio")
    avg_cpc: float = Field(0.0, description="CPC promedio")
    avg_roas: float = Field(0.0, description="ROAS promedio")


class CampaignInsightsOverview(BaseModel):
    """Vista general de insights de campaña."""
    campaign_id: str = Field(..., description="ID de la campaña")
    campaign_name: str = Field(..., description="Nombre de la campaña")
    status: str = Field(..., description="Estado de la campaña")
    
    # Insights de la campaña
    campaign_insights: InsightTimeline = Field(..., description="Insights de la campaña")
    
    # Resumen de adsets
    adsets_count: int = Field(0, description="Número de adsets")
    adsets_active: int = Field(0, description="Adsets activos")
    adsets_paused: int = Field(0, description="Adsets pausados")
    
    # Resumen de ads
    ads_count: int = Field(0, description="Número de ads")
    ads_active: int = Field(0, description="Ads activos")
    ads_paused: int = Field(0, description="Ads pausados")
    
    # Métricas top level
    performance_summary: Dict[str, Any] = Field(
        default_factory=dict,
        description="Resumen de performance"
    )


class AdsetInsightsOverview(BaseModel):
    """Vista general de insights de adset."""
    adset_id: str = Field(..., description="ID del adset")
    adset_name: str = Field(..., description="Nombre del adset")
    campaign_id: str = Field(..., description="ID de la campaña padre")
    campaign_name: str = Field(..., description="Nombre de la campaña")
    status: str = Field(..., description="Estado del adset")
    
    # Insights del adset
    adset_insights: InsightTimeline = Field(..., description="Insights del adset")
    
    # Resumen de ads
    ads_count: int = Field(0, description="Número de ads en el adset")
    ads_active: int = Field(0, description="Ads activos")
    ads_paused: int = Field(0, description="Ads pausados")
    
    # Configuración del adset
    targeting_summary: Optional[Dict[str, Any]] = Field(
        None,
        description="Resumen de targeting"
    )
    budget_info: Optional[Dict[str, Any]] = Field(
        None,
        description="Información de presupuesto"
    )


class AdInsightsOverview(BaseModel):
    """Vista general de insights de ad."""
    ad_id: str = Field(..., description="ID del ad")
    ad_name: str = Field(..., description="Nombre del ad")
    adset_id: str = Field(..., description="ID del adset padre")
    adset_name: str = Field(..., description="Nombre del adset")
    campaign_id: str = Field(..., description="ID de la campaña")
    campaign_name: str = Field(..., description="Nombre de la campaña")
    status: str = Field(..., description="Estado del ad")
    
    # Insights del ad
    ad_insights: InsightTimeline = Field(..., description="Insights del ad")
    
    # Información del creative
    creative_info: Optional[Dict[str, Any]] = Field(
        None,
        description="Información del creative"
    )
    
    # Comparación con peers
    peer_comparison: Optional[Dict[str, Any]] = Field(
        None,
        description="Comparación con otros ads del mismo adset"
    )


class SyncEntityReport(BaseModel):
    """Reporte de sincronización por tipo de entidad."""
    processed: int = Field(0, description="Entidades procesadas")
    success: int = Field(0, description="Sincronizaciones exitosas")
    errors: int = Field(0, description="Errores encontrados")
    skipped: int = Field(0, description="Entidades saltadas")


class SyncReport(BaseModel):
    """Reporte completo de sincronización."""
    sync_id: str = Field(..., description="ID único de la sincronización")
    sync_timestamp: datetime = Field(..., description="Timestamp de inicio")
    sync_type: str = Field(..., description="Tipo de sincronización (manual/scheduled)")
    mode: str = Field(..., description="Modo de operación (stub/live)")
    
    # Configuración de sincronización
    date_range: Dict[str, str] = Field(..., description="Rango de fechas sincronizado")
    days_back: int = Field(..., description="Días hacia atrás sincronizados")
    
    # Reportes por entidad
    campaigns: SyncEntityReport = Field(..., description="Reporte de campañas")
    adsets: SyncEntityReport = Field(..., description="Reporte de adsets") 
    ads: SyncEntityReport = Field(..., description="Reporte de ads")
    
    # Métricas generales
    total_duration_seconds: float = Field(..., description="Duración total en segundos")
    total_api_calls: int = Field(0, description="Total de llamadas a API")
    rate_limit_hits: int = Field(0, description="Veces que se alcanzó rate limit")
    
    # Errores y warnings
    errors: List[str] = Field(default_factory=list, description="Lista de errores")
    warnings: List[str] = Field(default_factory=list, description="Lista de warnings")
    
    # Estado final
    success: bool = Field(..., description="Si la sincronización fue exitosa")
    completion_percentage: float = Field(
        0.0, 
        ge=0, 
        le=100, 
        description="Porcentaje de completitud"
    )


class InsightsOverviewResponse(BaseModel):
    """Respuesta del endpoint de overview general."""
    timestamp: datetime = Field(..., description="Timestamp de la consulta")
    date_range: Dict[str, str] = Field(..., description="Rango de fechas consultado")
    
    # Contadores generales
    total_campaigns: int = Field(0, description="Total de campañas")
    active_campaigns: int = Field(0, description="Campañas activas")
    total_adsets: int = Field(0, description="Total de adsets")
    active_adsets: int = Field(0, description="Adsets activos")
    total_ads: int = Field(0, description="Total de ads")
    active_ads: int = Field(0, description="Ads activos")
    
    # Métricas agregadas globales
    global_metrics: InsightMetrics = Field(..., description="Métricas globales agregadas")
    
    # Top performers
    top_campaigns: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Top 5 campañas por ROAS"
    )
    top_adsets: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Top 5 adsets por ROAS" 
    )
    top_ads: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Top 5 ads por ROAS"
    )
    
    # Estado de sincronización
    last_sync: Optional[Dict[str, Any]] = Field(
        None,
        description="Información de la última sincronización"
    )
    
    # Alertas y notificaciones
    alerts: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Alertas activas (bajo rendimiento, etc.)"
    )


class ManualSyncRequest(BaseModel):
    """Request para sincronización manual."""
    days_back: int = Field(7, ge=1, le=30, description="Días hacia atrás a sincronizar")
    force: bool = Field(False, description="Forzar sincronización aunque haya una reciente")
    entity_ids: Optional[List[str]] = Field(
        None,
        description="IDs específicos a sincronizar (si no se especifica, sincroniza todo)"
    )
    entity_type: Optional[str] = Field(
        None,
        description="Tipo de entidad a sincronizar (campaign/adset/ad)"
    )


class InsightsQueryParams(BaseModel):
    """Parámetros de consulta para insights."""
    days_back: int = Field(30, ge=1, le=365, description="Días hacia atrás")
    limit: int = Field(100, ge=1, le=1000, description="Límite de resultados")
    offset: int = Field(0, ge=0, description="Offset para paginación")
    order_by: str = Field("date_start", description="Campo para ordenar")
    order_desc: bool = Field(True, description="Orden descendente")
    include_metrics: bool = Field(True, description="Incluir métricas calculadas")
    
    
class ErrorResponse(BaseModel):
    """Respuesta de error estándar."""
    error: str = Field(..., description="Mensaje de error")
    error_code: str = Field(..., description="Código de error")
    timestamp: datetime = Field(..., description="Timestamp del error")
    details: Optional[Dict[str, Any]] = Field(None, description="Detalles adicionales")