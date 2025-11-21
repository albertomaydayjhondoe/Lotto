# Publishing Scheduler Module

Módulo para programación de publicaciones futuras con ventanas horarias y separación mínima entre posts.

## 🏗️ Arquitectura

```
┌─────────────────────────────────────────────────────────────┐
│                   SCHEDULER WORKFLOW                         │
└─────────────────────────────────────────────────────────────┘

1. REQUEST → POST /publishing/schedule
   ├─ Validar clip existe
   ├─ Validar social_account existe
   ├─ Validar platform match
   └─ Aplicar reglas de scheduling:
      ├─ Ventana horaria (18-23h Instagram, 16-24h TikTok, etc.)
      ├─ Gap mínimo (60min Instagram, 30min TikTok, 90min YouTube)
      └─ Ajuste automático si necesario

2. CREATION → PublishLogModel
   ├─ status = "scheduled"
   ├─ schedule_type = "scheduled"
   ├─ scheduled_for = tiempo ajustado
   ├─ scheduled_window_end = fin de ventana
   └─ scheduled_by = "manual"|"rule_engine"|"campaign_orchestrator"

3. TICK → POST /publishing/scheduler/tick (cron cada minuto)
   ├─ Buscar logs con status="scheduled" y scheduled_for <= now
   ├─ Cambiar status a "pending"
   ├─ Encolar para procesamiento inmediato
   └─ Registrar evento: publish_scheduled_enqueued

4. PROCESSING → Worker normal
   └─ Procesa logs con status="pending" como siempre
```

## ⚙️ Configuración

### Ventanas Horarias (por plataforma)

```python
PLATFORM_WINDOWS = {
    "instagram": {"start_hour": 18, "end_hour": 23},  # 18:00-23:00 (5 horas)
    "tiktok": {"start_hour": 16, "end_hour": 24},     # 16:00-00:00 (8 horas)
    "youtube": {"start_hour": 17, "end_hour": 22}     # 17:00-22:00 (5 horas)
}
```

**Lógica:**
- Si `scheduled_for` cae FUERA de ventana → ajustar al inicio de ventana
- Si cae ANTES de start_hour → mover a start_hour mismo día
- Si cae DESPUÉS de end_hour → mover a start_hour día siguiente

### Gaps Mínimos (por plataforma)

```python
MIN_GAP_MINUTES = {
    "instagram": 60,  # 1 hora entre posts
    "tiktok": 30,     # 30 minutos entre posts
    "youtube": 90     # 1.5 horas entre posts
}
```

**Lógica:**
- Buscar posts existentes en mismo platform + social_account
- Si distancia < MIN_GAP → push forward scheduled_for
- Re-validar que sigue dentro de ventana después del ajuste

## 📊 Modelo de Datos

### PublishLogModel (nuevos campos)

```python
schedule_type = Column(String(50), default="immediate")
    # "immediate": publicación inmediata (default)
    # "scheduled": publicación programada

scheduled_for = Column(DateTime, nullable=True)
    # Cuándo publicar (UTC)

scheduled_window_end = Column(DateTime, nullable=True)
    # Fin de ventana (opcional)

scheduled_by = Column(String(100), nullable=True)
    # Quién programó: "manual", "rule_engine", "campaign_orchestrator"
```

## 🔌 API Endpoints

### POST /publishing/schedule

Programa una publicación futura.

**Request:**
```json
{
  "clip_id": "clip_abc123",
  "platform": "instagram",
  "social_account_id": "acc_xyz789",
  "scheduled_for": "2025-01-15T20:00:00Z",
  "scheduled_window_end": "2025-01-15T22:00:00Z",
  "scheduled_by": "manual"
}
```

**Response (éxito):**
```json
{
  "publish_log_id": "log_def456",
  "status": "scheduled",
  "reason": "Adjusted 5min forward to respect 60min gap",
  "scheduled_for": "2025-01-15T20:05:00Z",
  "scheduled_window_end": "2025-01-15T22:00:00Z"
}
```

**Response (rechazo):**
```json
{
  "publish_log_id": "",
  "status": "rejected",
  "reason": "Clip not found: clip_abc123"
}
```

### GET /publishing/schedule/{clip_id}

Lista todas las publicaciones programadas para un clip.

**Response:**
```json
[
  {
    "id": "log_def456",
    "clip_id": "clip_abc123",
    "platform": "instagram",
    "social_account_id": "acc_xyz789",
    "status": "scheduled",
    "schedule_type": "scheduled",
    "scheduled_for": "2025-01-15T20:05:00Z",
    "scheduled_window_end": "2025-01-15T22:00:00Z",
    "scheduled_by": "manual",
    "created_at": "2025-01-14T10:00:00Z",
    "updated_at": "2025-01-14T10:00:00Z"
  }
]
```

### POST /publishing/scheduler/tick?dry_run=false

Ejecuta el tick del scheduler (mover logs de "scheduled" → "pending").

**Query params:**
- `dry_run`: bool (default=False) - Si true, solo cuenta sin modificar

**Response:**
```json
{
  "moved": 3,
  "dry_run": false,
  "log_ids": ["log_def456", "log_ghi789", "log_jkl012"]
}
```

## 📝 Eventos Ledger

### 1. publish_scheduled_created

Se registra cuando se crea un log programado.

```json
{
  "event_type": "publish_scheduled_created",
  "entity_type": "publish_log",
  "entity_id": "log_def456",
  "metadata": {
    "clip_id": "clip_abc123",
    "platform": "instagram",
    "social_account_id": "acc_xyz789",
    "scheduled_for": "2025-01-15T20:00:00Z",
    "scheduled_window_end": "2025-01-15T22:00:00Z",
    "scheduled_by": "manual",
    "status": "scheduled"
  }
}
```

### 2. publish_scheduled_adjusted

Se registra cuando el tiempo fue ajustado (ventana o gap).

```json
{
  "event_type": "publish_scheduled_adjusted",
  "entity_type": "publish_log",
  "entity_id": "log_def456",
  "metadata": {
    "clip_id": "clip_abc123",
    "platform": "instagram",
    "original_time": "2025-01-15T20:00:00Z",
    "adjusted_time": "2025-01-15T20:05:00Z",
    "reason": "Adjusted 60min forward to respect minimum gap"
  }
}
```

### 3. publish_scheduled_enqueued

Se registra cuando el scheduler mueve un log a "pending".

```json
{
  "event_type": "publish_scheduled_enqueued",
  "entity_type": "publish_log",
  "entity_id": "log_def456",
  "metadata": {
    "clip_id": "clip_abc123",
    "platform": "instagram",
    "social_account_id": "acc_xyz789",
    "scheduled_for": "2025-01-15T20:05:00Z",
    "enqueued_at": "2025-01-15T20:05:00Z"
  }
}
```

## 🚀 Deployment

### Cron Job (recomendado)

```bash
# /etc/crontab
* * * * * curl -X POST http://localhost:8000/publishing/scheduler/tick
```

### APScheduler (alternativo)

```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()
scheduler.add_job(
    scheduler_tick_job,
    'interval',
    minutes=1,
    args=[db]
)
scheduler.start()
```

## 🧪 Testing

Ver `tests/test_publishing_scheduler.py` para ejemplos completos.

**Casos de test incluidos:**
- ✅ Creación de logs scheduled
- ✅ Validación de clip/account
- ✅ Respeto de ventanas horarias
- ✅ Aplicación de gaps mínimos
- ✅ Scheduler tick (scheduled → pending)
- ✅ Dry run mode
- ✅ Endpoints API

## 📈 Monitoreo

### Query: Logs programados pendientes

```sql
SELECT id, clip_id, platform, scheduled_for, status
FROM publish_logs
WHERE schedule_type = 'scheduled'
  AND status = 'scheduled'
  AND scheduled_for > NOW()
ORDER BY scheduled_for ASC;
```

### Query: Logs encolados hoy

```sql
SELECT COUNT(*) as enqueued_today
FROM ledger_events
WHERE event_type = 'publish_scheduled_enqueued'
  AND DATE(created_at) = CURRENT_DATE;
```

## 🔮 Future Enhancements

1. **Timezone support**: Permitir especificar timezone por cuenta
2. **Recurring schedules**: Soporte para publicaciones recurrentes
3. **Priority queues**: Diferentes prioridades de publicación
4. **Smart scheduling**: ML para optimizar horarios automáticamente
5. **Batch operations**: Programar múltiples clips a la vez
6. **Calendar view**: Visualización de calendario de publicaciones

---

**Version:** 1.0.0  
**Last Updated:** 2025-11-21
