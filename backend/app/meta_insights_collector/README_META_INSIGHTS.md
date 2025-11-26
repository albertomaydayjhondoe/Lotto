# Meta Insights Collector - PASO 10.7

## Descripción

El Meta Insights Collector es un sistema completo para la recolección, persistencia y análisis de insights de Meta Ads (Facebook/Instagram). Proporciona sincronización automática y manual de métricas de campañas, adsets y anuncios individuales.

## Arquitectura del Sistema

### Componentes Principales

```
app/meta_insights_collector/
├── collector.py      # Lógica de recolección de insights
├── scheduler.py      # Programador de sincronización automática  
├── models.py         # Modelos Pydantic para responses
├── router.py         # Endpoints REST API
└── README_META_INSIGHTS.md
```

### Dashboard Integration

```
dashboard/lib/meta_insights/
├── api.ts           # Funciones de API y tipos TypeScript
└── hooks.ts         # React Query hooks personalizados
```

## Flujo de Sincronización

### 1. Sincronización Automática

```python
# El scheduler ejecuta cada 30 minutos:
1. Obtiene campañas activas de la BD
2. Para cada campaña:
   - Recolecta insights de la campaña
   - Obtiene adsets de la campaña
   - Para cada adset: recolecta insights + obtiene ads
   - Para cada ad: recolecta insights
3. Persiste todo evitando duplicados por (entity_id, date_start)
4. Maneja rate limits con retry automático
5. Genera reporte detallado
```

### 2. Sincronización Manual

```python
# Endpoint POST /meta/insights/sync-now
- Permite sincronización inmediata
- Configurable: días hacia atrás, entidades específicas  
- Retorna reporte completo con métricas
```

### 3. Persistencia Inteligente

```sql
-- Evita duplicados con constraint único
UNIQUE(campaign_id, adset_id, ad_id, date_start, entity_type)

-- Actualiza registros existentes en lugar de crear duplicados
UPDATE insights SET spend=?, impressions=?, ... WHERE id=?
```

## Endpoints API

### GET /meta/insights/overview
**Permisos:** `analytics:read`, `manager`, `admin`

Vista general de todos los insights con métricas agregadas.

**Respuesta:**
```json
{
  "timestamp": "2024-01-01T12:00:00Z",
  "date_range": {"start": "...", "end": "..."},
  "total_campaigns": 25,
  "active_campaigns": 20,
  "global_metrics": {
    "spend": 15750.50,
    "impressions": 1500000,
    "clicks": 45000,
    "conversions": 1200,
    "revenue": 28500.00,
    "ctr": 3.0,
    "cpc": 0.35,
    "roas": 1.81
  },
  "top_campaigns": [...],
  "last_sync": {...},
  "alerts": [...]
}
```

### GET /meta/insights/campaign/{campaign_id}
**Permisos:** `analytics:read`, `manager`, `admin`

Insights detallados de una campaña específica.

**Parámetros:**
- `campaign_id`: ID de la campaña
- `days`: Días hacia atrás (default: 30)

**Respuesta:**
```json
{
  "campaign_id": "123456789",
  "campaign_name": "Holiday Sale 2024",
  "status": "ACTIVE",
  "campaign_insights": {
    "entity_id": "123456789",
    "entity_type": "campaign", 
    "insights": [...],
    "total_spend": 2500.00,
    "avg_roas": 2.15
  },
  "adsets_count": 5,
  "ads_count": 15,
  "performance_summary": {
    "efficiency_score": 85.5
  }
}
```

### GET /meta/insights/adset/{adset_id}
**Permisos:** `analytics:read`, `manager`, `admin`

Insights de un adset con información de targeting.

### GET /meta/insights/ad/{ad_id}  
**Permisos:** `analytics:read`, `manager`, `admin`

Insights de un anuncio con comparación de peers.

### GET /meta/insights/recent-insights/{entity_id}
**Permisos:** `analytics:read`, `manager`, `admin`

Timeline de insights recientes para cualquier entidad.

**Parámetros:**
- `entity_id`: ID de la entidad
- `entity_type`: `campaign` | `adset` | `ad`
- `days`: Días hacia atrás (default: 30)

### POST /meta/insights/sync-now
**Permisos:** `admin`, `manager`

Ejecuta sincronización manual inmediata.

**Request:**
```json
{
  "days_back": 7,
  "force": false,
  "entity_ids": ["123", "456"],
  "entity_type": "campaign"
}
```

**Response:**
```json
{
  "sync_id": "uuid-here",
  "sync_timestamp": "2024-01-01T12:00:00Z",
  "sync_type": "manual",
  "mode": "stub",
  "campaigns": {"processed": 10, "success": 9, "errors": 1},
  "adsets": {"processed": 45, "success": 43, "errors": 2},
  "ads": {"processed": 180, "success": 175, "errors": 5},
  "total_duration_seconds": 125.6,
  "success": true,
  "errors": ["Campaign XYZ: Rate limit exceeded"]
}
```

## Configuración

### Variables de Entorno

```bash
# Modo de operación
META_INSIGHTS_MODE=stub  # "stub" | "live"

# Configuración del scheduler
INSIGHTS_SYNC_INTERVAL_MINUTES=30
INSIGHTS_SYNC_ENABLED=true

# Configuración de rate limits
META_API_RATE_LIMIT_RETRY_DELAY=60
META_API_MAX_RETRIES=3

# Configuración de datos
INSIGHTS_MAX_DAYS_BACK=365
INSIGHTS_DEFAULT_BATCH_SIZE=5
```

### Configuración en Base de Datos

```sql
-- Tabla principal de insights (ya existe)
CREATE TABLE meta_ad_insights (
    id VARCHAR(36) PRIMARY KEY,
    campaign_id VARCHAR(36),
    adset_id VARCHAR(36), 
    ad_id VARCHAR(36),
    entity_type VARCHAR(20) NOT NULL,
    date_start DATETIME NOT NULL,
    date_end DATETIME NOT NULL,
    spend DECIMAL(10,2),
    impressions INT,
    clicks INT,
    conversions INT,
    revenue DECIMAL(10,2),
    ctr DECIMAL(5,2),
    cpc DECIMAL(5,2),
    roas DECIMAL(5,2),
    frequency DECIMAL(5,2),
    reach INT,
    unique_clicks INT,
    cost_per_conversion DECIMAL(10,2),
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    UNIQUE KEY unique_insight (campaign_id, adset_id, ad_id, date_start, entity_type)
);

-- Índices para optimizar consultas
CREATE INDEX idx_insights_entity_date ON meta_ad_insights(entity_type, date_start);
CREATE INDEX idx_insights_campaign_date ON meta_ad_insights(campaign_id, date_start);
CREATE INDEX idx_insights_adset_date ON meta_ad_insights(adset_id, date_start);
CREATE INDEX idx_insights_ad_date ON meta_ad_insights(ad_id, date_start);
```

## Modos de Operación

### Modo STUB (Desarrollo/Testing)
```python
# Genera datos realistas pero ficticios
collector = MetaInsightsCollector(mode="stub")

# Los datos son consistentes por hash del ID
campaign_123_insights = {
    "spend": 1250.75,  # Siempre igual para campaign_123
    "impressions": 15000,
    "roas": 1.72,
    # ... más métricas
}
```

### Modo LIVE (Producción)
```python
# TODO: Implementar con Facebook Marketing API
collector = MetaInsightsCollector(mode="live")

# Requerirá:
# - Access token de Meta
# - Configuración de app ID
# - Manejo de rate limits reales
# - Procesamiento de respuestas de API real
```

## Errores Comunes y Soluciones

### 1. Error de Rate Limit
```
Error: MetaRateLimitError: Too many requests
Solución: El sistema espera automáticamente 60s y reintenta
```

### 2. Error de Autenticación
```
Error: 401 Unauthorized
Solución: Verificar permisos RBAC del usuario
```

### 3. Error de Entidad No Encontrada
```
Error: 404 Campaign not found
Solución: Verificar que el ID existe en la BD
```

### 4. Error de Sincronización
```
Error: Sync failed: Connection timeout
Solución: Reintentar manualmente, verificar conectividad
```

### 5. Error de Duplicados
```
Error: Duplicate key error
Solución: Sistema maneja automáticamente, actualiza registro existente
```

## Cómo Activar Live Mode

### 1. Configurar Credenciales de Meta

```bash
# .env
META_APP_ID=your_app_id
META_APP_SECRET=your_app_secret
META_ACCESS_TOKEN=your_access_token
META_INSIGHTS_MODE=live
```

### 2. Implementar Cliente Real

```python
# app/meta_ads_client/client.py
class MetaAdsClient:
    async def get_campaign_insights(self, campaign_id, date_start, date_end):
        # TODO: Implementar con facebook_business SDK
        from facebook_business.adobjects.campaign import Campaign
        from facebook_business.adobjects.adsinsights import AdsInsights
        
        campaign = Campaign(campaign_id)
        insights = campaign.get_insights(
            fields=[
                AdsInsights.Field.spend,
                AdsInsights.Field.impressions,
                AdsInsights.Field.clicks,
                # ... más fields
            ],
            params={
                'time_range': {
                    'since': date_start.strftime('%Y-%m-%d'),
                    'until': date_end.strftime('%Y-%m-%d')
                }
            }
        )
        return insights[0] if insights else {}
```

### 3. Configurar Rate Limits

```python
# app/meta_insights_collector/collector.py
class MetaInsightsCollector:
    async def _handle_rate_limit(self, retry_count: int = 0):
        if retry_count >= 3:
            raise MetaRateLimitError("Max retries exceeded")
        
        await asyncio.sleep(60 * (retry_count + 1))  # Backoff exponencial
```

### 4. Testing en Live Mode

```python
# Empezar con sincronización limitada
sync_request = {
    "days_back": 1,  # Solo 1 día
    "entity_ids": ["campaign_id_test"],
    "entity_type": "campaign"
}

# Monitorear logs para rate limits
tail -f logs/meta_insights.log | grep "rate_limit"
```

## Performance y Escalabilidad

### Optimizaciones Implementadas

1. **Batch Processing**: Procesa campañas en lotes de 5
2. **Asyncio Parallel**: Usa `asyncio.gather` para paralelización  
3. **Connection Pooling**: Reutiliza conexiones de BD
4. **Query Optimization**: Índices en columnas consultadas frecuentemente
5. **Rate Limit Handling**: Backoff automático y retry
6. **Memory Management**: Procesamiento streaming, no carga todo en memoria

### Métricas de Performance

```python
# Tiempo estimado para sincronización completa:
# - 100 campañas × 5 adsets × 3 ads = 1,500 entidades
# - En paralelo (batch=5): ~15-20 minutos en modo stub
# - En modo live: 45-60 minutos (por rate limits)
```

## Monitoreo y Alertas

### Logs Estructurados
```python
logger.info("Sync completed", extra={
    "campaigns": 25,
    "duration_seconds": 125.6,
    "errors": 2,
    "mode": "stub"
})
```

### Métricas Clave a Monitorear
- Duración de sincronización
- Tasa de errores por entidad
- Rate limit hits por hora
- Cobertura de datos (% entidades sincronizadas)
- Latencia de endpoints API

### Alertas Recomendadas
- Sincronización falló > 2 veces seguidas
- Duración > 2x promedio histórico  
- Rate limits > 10 por hora
- Errors > 5% del total de entidades

## Roadmap Futuro

### Versión 2.0
- [ ] Modo hybrid (stub + live para testing)
- [ ] Agregaciones pre-calculadas para dashboard
- [ ] Alertas automáticas por performance
- [ ] Export de datos a CSV/Excel
- [ ] Comparaciones período vs período
- [ ] Forecasting básico con ML

### Versión 3.0  
- [ ] Streaming real-time de insights
- [ ] Integración con Google Ads
- [ ] Dashboard widgets personalizables
- [ ] API GraphQL para queries complejas
- [ ] Data warehouse integration

---

## Testing

Ejecutar tests completos:
```bash
pytest tests/test_meta_insights_collector.py -v
```

Tests incluidos:
- ✅ `test_collect_insights_ok`
- ✅ `test_persist_insights_no_duplicates`
- ✅ `test_sync_scheduler_runs`
- ✅ `test_overview_endpoint_ok`
- ✅ `test_campaign_endpoint_ok`
- ✅ `test_ad_endpoint_ok`  
- ✅ `test_rbac_protection`

## Soporte

Para problemas o preguntas:
1. Revisar logs en `logs/meta_insights.log`
2. Verificar estado del scheduler: `GET /meta/insights/overview`
3. Ejecutar sincronización manual para diagnosticar
4. Verificar permisos RBAC del usuario