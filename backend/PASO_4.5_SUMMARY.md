# PASO 4.5: Auto-Publisher Intelligence Layer (APIL)

## 🎯 Resumen Ejecutivo

El **Auto-Publisher Intelligence Layer (APIL)** es una capa de inteligencia que opera **antes del scheduler**, tomando decisiones inteligentes sobre cuándo, cómo y con qué prioridad programar publicaciones. APIL no modifica la lógica del scheduler existente, sino que actúa como una capa superior que crea `PublishLogModel` con `status="scheduled"` de manera inteligente.

**Estado:** ✅ COMPLETADO  
**Tests:** 10/10 PASSING  
**Integración:** No invasiva, compatible con scheduler y worker existentes

---

## 📐 Arquitectura General

```
┌─────────────────────────────────────────────────────────────────┐
│                    PUBLISHING INTELLIGENCE LAYER                 │
│                              (APIL)                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  1. PRIORITY CALCULATION                                         │
│     ├─ Visual Score (40%)                                        │
│     ├─ Engagement Score (30%)                                    │
│     ├─ Predicted Virality (20%)                                  │
│     ├─ Campaign Weight (10%)                                     │
│     └─ Delay Penalty (bonus for old clips)                       │
│                                                                   │
│  2. GLOBAL FORECAST                                              │
│     ├─ Slots disponibles por plataforma                          │
│     ├─ Nivel de saturación (low/medium/high)                     │
│     ├─ Next available slot                                       │
│     └─ Risk assessment                                           │
│                                                                   │
│  3. AUTO-SLOTTING INTELIGENTE                                    │
│     ├─ Calcula prioridad del clip                                │
│     ├─ Consulta forecast                                         │
│     ├─ Selecciona mejor slot                                     │
│     ├─ Detecta y resuelve conflictos                             │
│     └─ Crea PublishLogModel (status="scheduled")                 │
│                                                                   │
│  4. CONFLICT RESOLUTION                                          │
│     ├─ Compara prioridades                                       │
│     ├─ Higher priority wins                                      │
│     ├─ Lower priority shifted to next slot                       │
│     └─ Ledger events: conflict_detected, conflict_resolved       │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    PUBLISHING SCHEDULER (4.4)                    │
│  - Lee logs con status="scheduled"                               │
│  - Respeta ventanas horarias                                     │
│  - Aplica MIN_GAP_MINUTES                                        │
│  - scheduler_tick(): scheduled → pending                         │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    PUBLISHING WORKER (4.2)                       │
│  - Procesa logs pending → published                              │
│  - Interactúa con plataformas                                    │
│  - Retry logic (4.3)                                             │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🧮 Fórmula de Prioridad

### Priority Calculation Formula

```python
priority = (visual_score * 0.4) +
           (engagement_score * 0.3) +
           (predicted_virality * 0.2) +
           (campaign_weight * 0.1) +
           delay_penalty

# Todos los componentes normalizados a escala 0-100
# Priority final: 0-100 (capped)
```

### Componentes Detallados

#### 1. **Visual Score** (40% contribution)
- **Fuente:** `Clip.visual_score` (0-100)
- **Peso:** 0.4
- **Ejemplo:** Visual score 85 → Contribución 34.0 puntos

#### 2. **Engagement Score** (30% contribution)
- **Fuente:** `Clip.params['engagement_score']` (0-100)
- **Peso:** 0.3
- **Simulación:** Obtenido de metadata o analytics
- **Ejemplo:** Engagement 70 → Contribución 21.0 puntos

#### 3. **Predicted Virality** (20% contribution)
- **Cálculo:** `base_virality = visual_score * 0.6`
- **Multiplicadores por plataforma:**
  - TikTok: 1.3x (favorece contenido viral)
  - Instagram: 1.1x
  - YouTube: 1.0x
- **Peso:** 0.2
- **Ejemplo:** TikTok, visual 80 → virality 62.4 → Contribución 12.5 puntos

#### 4. **Campaign Weight** (10% contribution)
- **Fuente:** `sum(Campaign.budget_cents)` asociadas al clip
- **Normalización:** `min(100, (budget_cents / 50000) * 100)`
  - $100 budget = 50 points
  - $500 budget = 100 points
- **Peso:** 0.1
- **Ejemplo:** Budget $500 → weight 100 → Contribución 10.0 puntos

#### 5. **Delay Penalty** (bonus addition)
- **Objetivo:** Clips antiguos reciben prioridad para evitar staleness
- **Escalas:**
  - 0-24h: 0 puntos
  - 24-48h: +5 puntos
  - 48-72h: +10 puntos
  - 72h+: +20 puntos (máximo boost)
- **Ejemplo:** Clip de 80h → +20 puntos

### Ejemplos de Prioridad

**Ejemplo 1: Clip Premium Reciente**
```json
{
  "visual_score": 90,
  "engagement_score": 85,
  "predicted_virality": 65,
  "campaign_weight": 100,
  "delay_penalty": 0,
  "priority": 87.0
}
```
Cálculo: (90*0.4) + (85*0.3) + (65*0.2) + (100*0.1) + 0 = 36 + 25.5 + 13 + 10 + 0 = **84.5**

**Ejemplo 2: Clip Viejo (Stale)**
```json
{
  "visual_score": 50,
  "engagement_score": 40,
  "predicted_virality": 35,
  "campaign_weight": 0,
  "delay_penalty": 20,
  "priority": 47.0
}
```
Cálculo: (50*0.4) + (40*0.3) + (35*0.2) + (0*0.1) + 20 = 20 + 12 + 7 + 0 + 20 = **59.0**

---

## 📊 Forecast Global

### Estructura de Response

```json
{
  "forecast_date": "2024-01-15T14:30:00Z",
  "instagram": {
    "platform": "instagram",
    "next_slot": "2024-01-15T18:00:00Z",
    "slots_remaining_today": 3,
    "risk": "low",
    "scheduled_count": 2,
    "window_start_hour": 18,
    "window_end_hour": 23,
    "min_gap_minutes": 60
  },
  "tiktok": {
    "platform": "tiktok",
    "next_slot": "2024-01-15T16:30:00Z",
    "slots_remaining_today": 8,
    "risk": "medium",
    "scheduled_count": 8,
    "window_start_hour": 16,
    "window_end_hour": 24,
    "min_gap_minutes": 30
  },
  "youtube": {
    "platform": "youtube",
    "next_slot": "2024-01-15T17:00:00Z",
    "slots_remaining_today": 1,
    "risk": "high",
    "scheduled_count": 4,
    "window_start_hour": 17,
    "window_end_hour": 22,
    "min_gap_minutes": 90
  }
}
```

### Cálculo de Slots

**Fórmula:**
```
max_slots_per_day = window_duration_minutes / min_gap_minutes
slots_remaining = max_slots_per_day - scheduled_count
```

**Ejemplos:**
- **Instagram:** (23-18) * 60 / 60 = 5 slots max/day
- **TikTok:** (24-16) * 60 / 30 = 16 slots max/day
- **YouTube:** (22-17) * 60 / 90 = 3 slots max/day

### Risk Levels

| Utilization | Risk Level | Description |
|-------------|------------|-------------|
| < 50%       | `low`      | Plenty of slots available |
| 50% - 80%   | `medium`   | Moderate saturation |
| > 80%       | `high`     | High saturation, limited slots |

---

## 🔄 Auto-Slotting Inteligente

### Flujo Completo

```
┌──────────────────────┐
│  POST /auto-schedule │
│  {clip_id, platform} │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────────┐
│ 1. Calculate Priority    │
│    priority = f(clip)    │
└──────────┬───────────────┘
           │
           ▼
┌──────────────────────────┐
│ 2. Get Forecast          │
│    forecast = global()   │
└──────────┬───────────────┘
           │
           ▼
┌──────────────────────────┐
│ 3. Select Best Slot      │
│    slot = forecast.next  │
└──────────┬───────────────┘
           │
           ▼
┌──────────────────────────┐
│ 4. Check Conflicts       │
│    existing_logs?        │
└──────────┬───────────────┘
           │
           ├─YES─► Resolve by Priority
           │       ├─ Higher wins → shift lower
           │       └─ Lower loses → shift to next
           │
           ▼
┌──────────────────────────┐
│ 5. Create PublishLog     │
│    status="scheduled"    │
│    scheduled_by="auto_   │
│      intelligence"       │
└──────────┬───────────────┘
           │
           ▼
┌──────────────────────────┐
│ 6. Log Ledger Events     │
│    - auto_schedule_      │
│      created             │
│    - conflict_* (if any) │
└──────────────────────────┘
```

### Request/Response Examples

**Request:**
```bash
curl -X POST http://localhost:8000/publishing/intelligence/auto-schedule \
  -H "Content-Type: application/json" \
  -d '{
    "clip_id": "clip_abc123",
    "platform": "instagram",
    "social_account_id": "acc_xyz789"
  }'
```

**Response (Sin Conflicto):**
```json
{
  "publish_log_id": "log_def456",
  "clip_id": "clip_abc123",
  "platform": "instagram",
  "scheduled_for": "2024-01-15T20:00:00Z",
  "priority": 75.5,
  "conflict_info": {
    "detected": false
  },
  "reason": "Scheduled with priority 75.5"
}
```

**Response (Con Conflicto Resuelto):**
```json
{
  "publish_log_id": "log_ghi789",
  "clip_id": "clip_abc123",
  "platform": "instagram",
  "scheduled_for": "2024-01-15T20:00:00Z",
  "priority": 85.0,
  "conflict_info": {
    "detected": true,
    "conflicting_log_id": "log_old123",
    "resolution": "Higher priority (85.0 > 45.0). Conflicting log shifted.",
    "original_slot": "2024-01-15T20:00:00Z",
    "shifted_slot": "2024-01-15T20:00:00Z"
  },
  "reason": "Scheduled with priority 85.0. Higher priority (85.0 > 45.0). Conflicting log shifted."
}
```

---

## ⚔️ Conflict Resolution

### Algoritmo de Resolución

```python
def resolve_conflict(proposed_time, proposed_priority):
    # 1. Find conflicting logs within MIN_GAP window
    conflicts = find_logs_near(proposed_time, ± MIN_GAP_MINUTES)
    
    if no_conflicts:
        return ConflictInfo(detected=False)
    
    # 2. Get conflict priority from metadata
    conflict_priority = conflict_log.metadata['priority']
    
    # 3. Compare priorities
    if proposed_priority > conflict_priority:
        # WE WIN: Shift conflicting log to next slot
        new_slot = find_next_slot(after=proposed_time + MIN_GAP)
        conflict_log.scheduled_for = new_slot
        
        log_event("schedule_conflict_detected")
        log_event("schedule_conflict_resolved")
        
        return ConflictInfo(
            detected=True,
            resolution="Higher priority wins",
            shifted_slot=proposed_time  # We keep our slot
        )
    else:
        # WE LOSE: Find next slot for us
        new_slot = find_next_slot(after=proposed_time + MIN_GAP)
        
        log_event("schedule_conflict_detected")
        
        return ConflictInfo(
            detected=True,
            resolution="Lower priority shifted",
            shifted_slot=new_slot  # We move to next slot
        )
```

### Ledger Events

**1. auto_schedule_created**
```json
{
  "event_type": "auto_schedule_created",
  "entity_type": "publish_log",
  "entity_id": "log_abc123",
  "metadata": {
    "clip_id": "clip_xyz",
    "platform": "instagram",
    "scheduled_for": "2024-01-15T20:00:00Z",
    "priority": 75.5,
    "conflict_detected": false
  }
}
```

**2. schedule_conflict_detected**
```json
{
  "event_type": "schedule_conflict_detected",
  "entity_type": "publish_log",
  "entity_id": "log_conflicted",
  "metadata": {
    "original_slot": "2024-01-15T20:00:00Z",
    "new_slot": "2024-01-15T21:00:00Z",
    "reason": "Lower priority, shifted by higher priority request"
  }
}
```

**3. schedule_conflict_resolved**
```json
{
  "event_type": "schedule_conflict_resolved",
  "entity_type": "publish_log",
  "entity_id": "log_conflicted",
  "metadata": {
    "shifted_to": "2024-01-15T21:00:00Z",
    "conflict_priority": 45.0,
    "winner_priority": 85.0
  }
}
```

---

## 📡 API Endpoints

### 1. POST /publishing/intelligence/auto-schedule

**Descripción:** Auto-programa un clip usando inteligencia.

**Request:**
```json
{
  "clip_id": "string",
  "platform": "instagram" | "tiktok" | "youtube",
  "social_account_id": "string (optional)",
  "force_slot": "datetime (optional)"
}
```

**Response:** `AutoScheduleResponse`

**Ejemplo:**
```bash
curl -X POST /publishing/intelligence/auto-schedule \
  -d '{"clip_id":"abc","platform":"instagram"}'
```

---

### 2. GET /publishing/intelligence/forecast

**Descripción:** Obtiene forecast global de todas las plataformas.

**Response:** `GlobalForecast`

**Ejemplo:**
```bash
curl -X GET /publishing/intelligence/forecast
```

---

### 3. GET /publishing/intelligence/priority/{clip_id}

**Descripción:** Calcula prioridad de un clip específico.

**Parámetros:**
- `clip_id`: ID del clip (path)
- `platform`: Plataforma (query, default="instagram")

**Response:** `PriorityCalculation`

**Ejemplo:**
```bash
curl -X GET /publishing/intelligence/priority/abc123?platform=tiktok
```

---

## 🧪 Tests Implementados

### Suite Completa (10 Tests)

#### **Priority Calculation Tests (5)**
1. ✅ `test_priority_calculation_basic` - Cálculo básico de prioridad
2. ✅ `test_priority_higher_visual_score` - Mayor visual score → mayor prioridad
3. ✅ `test_priority_delay_penalty_boost` - Clips viejos reciben boost
4. ✅ `test_priority_campaign_weight` - Campañas grandes aumentan prioridad
5. ✅ `test_priority_virality_estimation` - Virality varía por plataforma

#### **Forecast Tests (3)**
6. ✅ `test_forecast_returns_valid_structure` - Estructura válida para 3 plataformas
7. ✅ `test_forecast_calculates_slots_remaining` - Cálculo correcto de slots
8. ✅ `test_forecast_risk_levels` - Risk levels (low/medium/high)

#### **Auto-Schedule Tests (2)**
9. ✅ `test_auto_schedule_creates_log` - Crea PublishLogModel con status=scheduled
10. ✅ `test_auto_schedule_uses_forecast_slot` - Usa slot del forecast

**Total: 10/10 PASSING** ✅

### Ejecución de Tests

```bash
cd /workspaces/stakazo/backend
source .venv/bin/activate
pytest tests/test_publishing_intelligence.py -v
```

**Resultado:**
```
============= 10 passed, 205 warnings in 1.77s =============
```

---

## 🔗 Integración con Sistema Existente

### No Modifica Componentes Previos

APIL es **completamente no invasivo**:

- ✅ **Scheduler (4.4):** Sin cambios. Continúa procesando logs `scheduled`
- ✅ **Worker (4.2):** Sin cambios. Continúa procesando logs `pending`
- ✅ **Retries (4.3):** Sin cambios. Continúa reintentando `failed`
- ✅ **Webhooks (4.3):** Sin cambios. Continúa recibiendo confirmaciones

### Flujo Integrado Completo

```
USER → APIL → PublishLog (scheduled) → Scheduler → PublishLog (pending) → Worker → Platform → Webhook
  ↓                                         ↓                                 ↓
Priority                               Tick Process                      Retry Logic
Calculation                            (scheduler_tick)                  (on failure)
  ↓                                         ↓                                 ↓
Forecast                               Respeta ventanas                  Max 3 retries
  ↓                                    Respeta MIN_GAP                        ↓
Auto-Slot                                                              Reconciliation
  ↓
Conflict
Resolution
```

### Interacción con Ledger

APIL agrega 3 nuevos event_types al ledger:

1. `auto_schedule_created` - Cuando APIL crea un log
2. `schedule_conflict_detected` - Cuando detecta conflicto
3. `schedule_conflict_resolved` - Cuando resuelve conflicto

Estos eventos son **adicionales** a los existentes del scheduler:
- `publish_scheduled_created`
- `publish_scheduled_adjusted`
- `publish_scheduled_enqueued`

---

## 📦 Archivos Creados

```
app/publishing_intelligence/
├── __init__.py              # Exports del módulo
├── models.py                # Pydantic schemas (7 modelos)
├── intelligence.py          # Lógica core (450+ líneas)
└── router.py                # FastAPI endpoints (3 rutas)

tests/
└── test_publishing_intelligence.py  # Suite de tests (10 tests)

docs/
└── PASO_4.5_SUMMARY.md      # Esta documentación
```

### Modificaciones

```
app/main.py
├── Import: from app.publishing_intelligence.router import router as intelligence_router
└── Include: app.include_router(intelligence_router, prefix="/publishing/intelligence")
```

---

## 🚀 Deployment & Usage

### 1. Uso Manual (API)

```bash
# Calcular prioridad de un clip
curl GET /publishing/intelligence/priority/clip_123?platform=instagram

# Ver forecast global
curl GET /publishing/intelligence/forecast

# Auto-programar clip
curl -X POST /publishing/intelligence/auto-schedule \
  -d '{"clip_id":"clip_123","platform":"instagram"}'
```

### 2. Uso Programático (Python)

```python
from app.publishing_intelligence import auto_schedule_clip, get_global_forecast

# Auto-schedule
result = await auto_schedule_clip(
    db=db,
    clip_id="clip_123",
    platform="instagram"
)

print(f"Scheduled at {result.scheduled_for} with priority {result.priority}")

# Get forecast
forecast = await get_global_forecast(db)
print(f"Instagram next slot: {forecast.instagram.next_slot}")
print(f"Risk: {forecast.instagram.risk}")
```

### 3. Integración con Rule Engine

```python
# En el rule engine, reemplazar scheduler directo por APIL:

# ANTES (4.4):
await schedule_publication(db, clip_id, platform, scheduled_for)

# AHORA (4.5):
await auto_schedule_clip(db, clip_id, platform)  # APIL decide cuándo
```

### 4. Integración con Campaign Orchestrator

```python
# El campaign orchestrator puede usar APIL para publicaciones inteligentes:

for clip in campaign_clips:
    result = await auto_schedule_clip(
        db=db,
        clip_id=clip.id,
        platform=campaign.target_platform
    )
    # APIL maneja prioridades y conflictos automáticamente
```

---

## 📈 Métricas y Monitoreo

### Queries SQL Útiles

**1. Ver todas las publicaciones auto-programadas:**
```sql
SELECT id, clip_id, platform, scheduled_for, 
       metadata->>'priority' as priority,
       status
FROM publish_logs
WHERE scheduled_by = 'auto_intelligence'
ORDER BY scheduled_for;
```

**2. Analizar distribución de prioridades:**
```sql
SELECT 
    platform,
    AVG(CAST(metadata->>'priority' AS FLOAT)) as avg_priority,
    MIN(CAST(metadata->>'priority' AS FLOAT)) as min_priority,
    MAX(CAST(metadata->>'priority' AS FLOAT)) as max_priority
FROM publish_logs
WHERE scheduled_by = 'auto_intelligence'
GROUP BY platform;
```

**3. Detectar conflictos resueltos:**
```sql
SELECT event_type, entity_id, metadata
FROM ledger
WHERE event_type IN ('schedule_conflict_detected', 'schedule_conflict_resolved')
ORDER BY created_at DESC
LIMIT 20;
```

---

## 🔮 Mejoras Futuras

### Fase 2 (Opcional)

1. **Machine Learning Integration**
   - Entrenar modelo de virality con datos históricos
   - Predicción de engagement basada en ML

2. **Account Intelligence**
   - Detectar cuenta principal vs satélites
   - Priorizar cuenta principal automáticamente

3. **Time Zone Awareness**
   - Ajustar ventanas según timezone de audiencia
   - Optimizar horarios por geolocalización

4. **A/B Testing**
   - Comparar performance de auto-schedule vs manual
   - Optimizar pesos de fórmula de prioridad

5. **Smart Batching**
   - Agrupar clips similares
   - Distribuir contenido diverso a lo largo del día

6. **Dynamic Window Adjustment**
   - Aprender mejores ventanas horarias por plataforma
   - Ajustar según performance histórica

---

## ✅ Conclusión

PASO 4.5 **COMPLETADO**:

- ✅ Módulo `publishing_intelligence/` implementado
- ✅ Prioridad dinámica con 5 componentes
- ✅ Forecast global para 3 plataformas
- ✅ Auto-slotting inteligente
- ✅ Resolución de conflictos por prioridad
- ✅ 3 API endpoints funcionales
- ✅ 10/10 tests passing
- ✅ Integración no invasiva con scheduler y worker
- ✅ Documentación completa

**APIL está listo para producción.** 🚀
