# SocialSyncLedger

Sistema completo de auditoría y trazabilidad para el orquestador.

## 🎯 Objetivo

Registrar **absolutamente todas las acciones importantes** del sistema de forma estructurada, consultable y trazable para:

- El worker pueda aprender del histórico
- Los handlers puedan mejorar lógica más adelante
- Las campañas puedan optimizarse
- El sistema pueda detectar anomalías
- La IA externa (GPT/E2B) entienda el contexto completo

## 🏗️ Arquitectura

```
backend/app/ledger/
├── __init__.py          # Exports principales
├── models.py            # LedgerEvent SQLAlchemy model
├── service.py           # Service layer con log_event(), etc.
├── ledger.py            # Lógica principal del ledger
└── README.md            # Este archivo
```

## 📊 Modelo de Datos

### Tabla: `ledger_events`

| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | UUID | Primary key |
| timestamp | DateTime | Timestamp UTC del evento |
| event_type | String(100) | Tipo de evento (video_uploaded, job_created, etc.) |
| entity_type | String(50) | Tipo de entidad (video_asset, job, clip, etc.) |
| entity_id | String(255) | ID de la entidad relacionada |
| metadata | JSON | Datos adicionales del evento |
| severity | Enum | INFO, WARN, ERROR |
| worker_id | String(100) | ID del worker que procesó (opcional) |
| job_id | UUID | ID del job relacionado (opcional) |
| clip_id | UUID | ID del clip relacionado (opcional) |

### Índices

- `timestamp` - Para queries por rango de fechas
- `event_type` - Para filtrar por tipo de evento
- `entity_type, entity_id` - Para buscar eventos de una entidad específica
- `job_id` - Para rastrear todos los eventos de un job
- `clip_id` - Para rastrear todos los eventos de un clip

## 🔄 Tipos de Eventos

### Eventos de Video
- `video_uploaded` - Video subido al sistema
- `video_validated` - Video validado correctamente
- `video_processing_started` - Inicio de procesamiento
- `video_processing_failed` - Fallo en procesamiento

### Eventos de Job
- `job_created` - Job creado
- `job_processing_started` - Job comenzó a procesarse
- `job_processing_completed` - Job completado exitosamente
- `job_processing_failed` - Job falló
- `job_retry_scheduled` - Job marcado para reintento

### Eventos de Clip
- `clip_created` - Clip generado
- `clip_variant_generated` - Variante de clip creada
- `clip_published` - Clip publicado en plataforma

### Eventos de Campaña
- `campaign_created` - Campaña creada
- `campaign_started` - Campaña iniciada
- `campaign_paused` - Campaña pausada
- `campaign_completed` - Campaña completada

### Eventos de Sistema
- `worker_started` - Worker iniciado
- `worker_stopped` - Worker detenido
- `health_check_failed` - Health check falló

## 📝 API del Service Layer

### `log_event()`

```python
async def log_event(
    db: AsyncSession,
    event_type: str,
    entity_type: str,
    entity_id: str,
    metadata: dict = None,
    severity: str = "INFO",
    worker_id: str = None,
    job_id: str = None,
    clip_id: str = None
) -> Optional[LedgerEvent]
```

Registra un evento genérico en el ledger.

**Parámetros**:
- `event_type`: Tipo de evento (ej: "video_uploaded")
- `entity_type`: Tipo de entidad (ej: "video_asset")
- `entity_id`: ID de la entidad
- `metadata`: Datos adicionales (opcional)
- `severity`: INFO, WARN, ERROR (default: INFO)
- `worker_id`: ID del worker (opcional)
- `job_id`: UUID del job relacionado (opcional)
- `clip_id`: UUID del clip relacionado (opcional)

**Returns**: LedgerEvent o None si falla

**Comportamiento**: Nunca lanza excepciones, solo loggea errores.

### `log_job_event()`

```python
async def log_job_event(
    db: AsyncSession,
    job_id: str,
    event_type: str,
    metadata: dict = None,
    severity: str = "INFO"
) -> Optional[LedgerEvent]
```

Registra un evento relacionado con un job.

### `log_clip_event()`

```python
async def log_clip_event(
    db: AsyncSession,
    clip_id: str,
    event_type: str,
    metadata: dict = None,
    severity: str = "INFO"
) -> Optional[LedgerEvent]
```

Registra un evento relacionado con un clip.

## 🔌 Integraciones

### 1. Upload Endpoint (`api/upload.py`)

```python
# Después de crear video_asset
await log_event(
    db=db,
    event_type="video_uploaded",
    entity_type="video_asset",
    entity_id=str(video_asset.id),
    metadata={
        "filename": file.filename,
        "size": file_size,
        "content_type": file.content_type
    }
)
```

### 2. Job Creation (`api/jobs.py`)

```python
# Después de crear job
await log_job_event(
    db=db,
    job_id=str(job.id),
    event_type="job_created",
    metadata={"job_type": job.job_type}
)
```

### 3. Worker Processing (`worker/worker.py`)

```python
# Al iniciar procesamiento
await log_job_event(
    db=db,
    job_id=str(job.id),
    event_type="job_processing_started"
)

# Al completar
await log_job_event(
    db=db,
    job_id=str(job.id),
    event_type="job_processing_completed",
    metadata={"result": result}
)

# Al fallar
await log_job_event(
    db=db,
    job_id=str(job.id),
    event_type="job_processing_failed",
    metadata={"error": str(e)},
    severity="ERROR"
)
```

### 4. Cut Analysis Handler (`worker/handlers/cut_analysis.py`)

```python
# Por cada clip creado
await log_clip_event(
    db=db,
    clip_id=str(clip.id),
    event_type="clip_created",
    metadata={
        "video_asset_id": str(video_asset.id),
        "start_ms": clip.start_ms,
        "end_ms": clip.end_ms,
        "visual_score": clip.visual_score
    }
)
```

## 🔍 Endpoint de Consulta

### `GET /debug/ledger/recent`

Query params:
- `limit` (int): Número de eventos a retornar (default: 50, max: 500)

Response:
```json
{
  "events": [
    {
      "id": "uuid",
      "timestamp": "2025-11-20T10:30:00Z",
      "event_type": "clip_created",
      "entity_type": "clip",
      "entity_id": "uuid",
      "metadata": {...},
      "severity": "INFO",
      "job_id": "uuid",
      "clip_id": "uuid"
    }
  ],
  "total": 150,
  "limit": 50
}
```

## 🛡️ Garantías del Sistema

### 1. Never Break Flow
- Todas las funciones del ledger son fail-safe
- Si falla el registro, solo se loggea el error
- Nunca se lanza excepción al caller

### 2. Structured Logging
- Usa el módulo `app.core.logging`
- Formato: `[INFO] [app.ledger.service] Event logged | extra={...}`

### 3. Performance
- Inserts asíncronos (no bloquean)
- Índices optimizados para queries frecuentes
- Commit manejado por el caller (no auto-commit)

### 4. Data Integrity
- UUID auto-generados
- Timestamp UTC automático
- Validación de severity enum

## 📈 Casos de Uso Futuros

### 1. Análisis de Rendimiento
```sql
-- Jobs más lentos
SELECT job_id, 
       MAX(timestamp) - MIN(timestamp) as duration
FROM ledger_events
WHERE event_type IN ('job_processing_started', 'job_processing_completed')
GROUP BY job_id
ORDER BY duration DESC;
```

### 2. Tasa de Error
```sql
-- Tasa de fallo por tipo de job
SELECT metadata->>'job_type' as job_type,
       COUNT(CASE WHEN event_type = 'job_processing_failed' THEN 1 END) as failures,
       COUNT(CASE WHEN event_type = 'job_processing_completed' THEN 1 END) as successes
FROM ledger_events
WHERE event_type IN ('job_processing_failed', 'job_processing_completed')
GROUP BY job_type;
```

### 3. Timeline de Entidad
```sql
-- Todos los eventos de un video específico
SELECT *
FROM ledger_events
WHERE entity_type = 'video_asset' 
  AND entity_id = 'uuid'
ORDER BY timestamp;
```

### 4. Detección de Anomalías
```python
# Clips que fallaron en publicación
failed_clips = await get_events_by_type(
    db,
    event_type="clip_published",
    severity="ERROR",
    since=datetime.now() - timedelta(days=7)
)
```

## 🧪 Testing

Ver `tests/test_ledger.py` para tests completos:
- `test_log_event_basic` - Log básico funciona
- `test_log_job_event_creates_entry` - Job events se registran
- `test_log_clip_event_creates_entry` - Clip events se registran
- `test_ledger_endpoint_returns_recent_items` - Endpoint retorna datos
- `test_ledger_graceful_failure_does_not_break_flow` - Falla gracefully

## 🔐 Seguridad y Privacy

- No almacenar información sensible en metadata
- Los datos del ledger son append-only (no modificar eventos pasados)
- Considerar retención de datos (ej: 90 días)

## 📚 Referencias

- OpenAPI spec: `/openapi/orquestador_openapi.yaml`
- Logging: `app/core/logging.py`
- Database models: `app/models/database.py`

---

**Última actualización**: 20 de Noviembre, 2025  
**Versión**: 1.0
