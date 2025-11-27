# Meta Ads Full Autonomous Cycle (PASO 10.11)

## 🎯 Objetivo

Integrar todos los módulos Meta Ads (10.1-10.10) en un **ciclo autónomo end-to-end** que opera 24/7 optimizando campañas automáticamente.

## 📋 Índice

1. [Arquitectura](#arquitectura)
2. [Flujo del Ciclo](#flujo-del-ciclo)
3. [Decisiones Automáticas](#decisiones-automáticas)
4. [API Endpoints](#api-endpoints)
5. [Configuración](#configuración)
6. [Modo STUB vs LIVE](#modo-stub-vs-live)
7. [Ejemplos](#ejemplos)
8. [Monitoreo](#monitoreo)
9. [Troubleshooting](#troubleshooting)

---

## Arquitectura

```
┌─────────────────────────────────────────────────────────────┐
│          Meta Ads Full Autonomous Cycle (10.11)             │
│                  Every 30 Minutes                            │
└─────────────────────────────────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        ▼                  ▼                  ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│   STEP 1     │→→│   STEP 2     │→→│   STEP 3     │
│  Collection  │  │  Decisions   │  │ API Actions  │
└──────────────┘  └──────────────┘  └──────────────┘
        │                  │                  │
        ▼                  ▼                  ▼
┌─────────────────────────────────────────────────────┐
│              Integrations (10.1-10.10)               │
│                                                      │
│  • Meta Models (10.1)                               │
│  • Meta Client (10.2)                               │
│  • Orchestrator (10.3)                              │
│  • A/B Testing (10.4)                               │
│  • ROAS Engine (10.5)                               │
│  • Insights Collector (10.7)                        │
│  • Spike Manager (10.9)                             │
│  • Creative Variants (10.10)                        │
└─────────────────────────────────────────────────────┘
                           │
                           ▼
                  ┌────────────────┐
                  │ PostgreSQL DB  │
                  │  Cycle Logs    │
                  └────────────────┘
```

---

## Flujo del Ciclo

### STEP 1: Data Collection (Recolección)

Carga datos de múltiples fuentes:

1. **Campañas activas** (Meta Models 10.1)
2. **Insights recientes** (Insights Collector 10.7)
3. **Métricas ROAS** (ROAS Engine 10.5)
4. **A/B Tests activos** (A/B Manager 10.4)
5. **Spikes detectados** (Spike Manager 10.9)

**Output:** Stats snapshot con métricas consolidadas.

### STEP 2: Automated Decisions (Decisiones)

Toma 4 tipos de decisiones:

#### Decision A: A/B Test Winner Selection

- **Condición:** Test > 48h + impresiones > 1000
- **Acción:**
  - Publicar winner
  - Pausar loser

#### Decision B: ROAS-based Budget Scaling

- **ROAS > 3.0:** Subir presupuesto 20-40%
- **ROAS 1.5-3.0:** Mantener
- **ROAS < 1.5:** Bajar 20-40% o pausar

#### Decision C: Spike Handling

- **Positive spike + ROAS > 2:** Boost +15%
- **Negative spike:** Reduce -10% o pausar

#### Decision D: Creative Fatigue Detection

- **CTR baja 30% vs media 7 días:**
  - Marcar creative como fatigado
  - Generar variante nueva (Creative Variants 10.10)
  - Cambiar: fragmentos, títulos, música

### STEP 3: API Actions (Ejecución)

Ejecuta acciones vía MetaAdsClient (10.2):

- `update_budget()`
- `pause_ad()`
- `create_new_ad_variant()`
- `publish_winner_ad()`
- `sync_insights()`

**Modo:**
- **STUB:** Simula acciones (sin API real)
- **LIVE:** Ejecuta en Meta API real

### STEP 4: Logging & Persistence

Guarda en DB:
- Cycle run completo
- Action logs detallados
- Stats snapshot
- Errores (si los hay)

---

## Decisiones Automáticas

### Tabla de Decisiones

| Tipo | Condición | Acción | Prioridad |
|------|-----------|--------|-----------|
| A/B Winner | Test > 48h + impressions > 1K | Publish winner, pause loser | Alta |
| ROAS High | ROAS > 3.0 | Scale up 20-40% | Alta |
| ROAS Low | ROAS < 1.5 | Scale down 20-40% or pause | Alta |
| Positive Spike | Spike + ROAS > 2 | Boost +15% | Media |
| Negative Spike | Spike detected | Reduce -10% or pause | Alta |
| Creative Fatigue | CTR drop 30% vs 7d avg | Generate new variant | Media |

---

## API Endpoints

### POST /meta/full-cycle/run

Ejecuta ciclo manual.

**RBAC:** admin, manager

**Request:**
```json
{
  "mode": "stub"  // "stub" or "live"
}
```

**Response:**
```json
{
  "cycle_run_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "success",
  "duration_ms": 2456,
  "stats_snapshot": {
    "campaigns_active": 10,
    "adsets_active": 50,
    "ads_active": 200,
    "total_spend_today": 1500.50,
    "avg_roas": 3.2,
    "actions_taken": 8
  },
  "message": "Cycle executed successfully in 2456ms"
}
```

### GET /meta/full-cycle/last

Obtiene el último ciclo ejecutado.

**RBAC:** admin, manager

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "started_at": "2025-11-27T10:00:00Z",
  "finished_at": "2025-11-27T10:02:30Z",
  "duration_ms": 150000,
  "status": "success",
  "steps_executed": [
    "step_1_collection",
    "step_2_decisions",
    "step_3_api_actions",
    "step_4_finalize"
  ],
  "errors": [],
  "stats_snapshot": {
    "campaigns_active": 10,
    "actions_taken": 8
  },
  "triggered_by": "scheduler",
  "mode": "stub"
}
```

### GET /meta/full-cycle/log/{cycle_run_id}

Obtiene logs detallados de un ciclo.

**RBAC:** admin, manager

**Response:**
```json
[
  {
    "id": 1,
    "cycle_run_id": "550e8400-e29b-41d4-a716-446655440000",
    "step": "ab_decision",
    "action": "publish_winner",
    "input_snapshot": {
      "test_duration_hours": 72,
      "impressions": 1500
    },
    "output_snapshot": {
      "winner": "23847656789012345",
      "loser": "23847656789012346"
    },
    "success": true,
    "error_message": null,
    "entity_type": "ad",
    "entity_id": "23847656789012345",
    "created_at": "2025-11-27T10:01:15Z"
  }
]
```

### GET /meta/full-cycle/history?limit=50

Lista últimos N ciclos.

**RBAC:** admin, manager

**Response:** Array de cycle runs.

### POST /meta/full-cycle/debug/step

Ejecuta un step individual (debug).

**RBAC:** admin only

**Request:**
```json
{
  "step": "collection",  // "collection", "decisions", "api_actions", "finalize"
  "mode": "stub"
}
```

---

## Configuración

### Variables de Entorno

```python
# backend/app/core/config.py

META_API_MODE: str = "stub"  # "stub" or "live"
META_CYCLE_ENABLED: bool = True
META_CYCLE_INTERVAL_MINUTES: int = 30
META_CYCLE_AUTO_START: bool = True
```

### Activar en `main.py`

```python
from app.meta_full_cycle.scheduler import start_meta_cycle_scheduler, stop_meta_cycle_scheduler

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    
    # Start Meta Cycle Scheduler
    meta_cycle_task = None
    if settings.META_CYCLE_ENABLED:
        meta_cycle_task = await start_meta_cycle_scheduler()
    
    yield
    
    # Shutdown
    if meta_cycle_task:
        await stop_meta_cycle_scheduler(meta_cycle_task)
```

---

## Modo STUB vs LIVE

### STUB Mode (Default)

- ✅ Seguro para desarrollo/testing
- ✅ No hace llamadas reales a Meta API
- ✅ Usa datos sintéticos
- ✅ Simula todas las acciones
- ⚠️ No afecta campañas reales

**Cuándo usar:**
- Development
- Testing
- Staging
- CI/CD pipelines

### LIVE Mode

- ⚠️ Ejecuta acciones REALES en Meta API
- ⚠️ Modifica presupuestos reales
- ⚠️ Pausa/activa ads reales
- ⚠️ Requiere credenciales válidas
- ⚠️ Puede incurrir en costos

**Requisitos para LIVE:**
1. Meta API credentials válidas
2. Permisos: `ads_management`, `ads_read`
3. Presupuesto disponible
4. Rate limiting configurado
5. Alertas de monitoring activas

**Activación:**
```bash
# En .env
META_API_MODE=live
META_CYCLE_ENABLED=true
```

---

## Ejemplos

### Ejecutar Ciclo Manual

```bash
curl -X POST "http://localhost:8000/meta/full-cycle/run" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"mode": "stub"}'
```

### Ver Último Ciclo

```bash
curl -X GET "http://localhost:8000/meta/full-cycle/last" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Ver Logs de un Ciclo

```bash
curl -X GET "http://localhost:8000/meta/full-cycle/log/550e8400-e29b-41d4-a716-446655440000" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Ver Historial

```bash
curl -X GET "http://localhost:8000/meta/full-cycle/history?limit=20" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## Monitoreo

### Métricas Clave

| Métrica | Descripción | Umbral |
|---------|-------------|--------|
| Cycle Duration | Duración del ciclo | < 5 min |
| Success Rate | % de ciclos exitosos | > 95% |
| Actions Taken | Acciones ejecutadas por ciclo | 5-20 |
| API Errors | Errores de Meta API | < 5% |

### Logs

```bash
# Ver logs del scheduler
tail -f logs/meta_cycle.log

# Buscar errores
grep "ERROR" logs/meta_cycle.log

# Contar ciclos exitosos
grep "Cycle completed successfully" logs/meta_cycle.log | wc -l
```

### Alertas Recomendadas

1. **Cycle Failed** → Slack/Email
2. **Duration > 10 min** → Warning
3. **No cycles in 1 hour** → Critical
4. **API Error Rate > 10%** → Warning
5. **Budget change > $1000** → Info (LIVE mode)

---

## Troubleshooting

### Problema: Ciclo no se ejecuta

**Causa:** Scheduler no iniciado

**Solución:**
```python
# Verificar en main.py
if settings.META_CYCLE_ENABLED:
    meta_cycle_task = await start_meta_cycle_scheduler()
```

### Problema: Errores de permisos

**Causa:** Usuario sin rol admin/manager

**Solución:**
```sql
UPDATE users SET role = 'manager' WHERE username = 'tu_usuario';
```

### Problema: Ciclo tarda mucho

**Causa:** Muchas campañas activas

**Solución:**
- Optimizar queries DB
- Aumentar workers
- Reducir ventana de análisis

### Problema: Acciones no se aplican en LIVE

**Causa:** Credenciales Meta inválidas

**Solución:**
```bash
# Verificar credenciales
META_APP_ID=xxx
META_APP_SECRET=xxx
META_ACCESS_TOKEN=xxx
```

---

## Roadmap (Fase B - LIVE)

### Implementaciones Pendientes

- [ ] Rate limiting Meta API
- [ ] Retry logic con exponential backoff
- [ ] Webhook de confirmación de acciones
- [ ] Dashboard UI para monitoring
- [ ] Alertas Telegram/Email
- [ ] ML model para decisiones predictivas
- [ ] Multi-account support
- [ ] Budget cap por campaña
- [ ] Approval workflow para acciones críticas

---

## Seguridad

### Recomendaciones LIVE Mode

1. **Budget Limits:**
   - Configurar `MAX_DAILY_BUDGET_PER_ADSET`
   - Configurar `MAX_TOTAL_DAILY_SPEND`

2. **Approval Workflow:**
   - Acciones > $500 → Requieren aprobación
   - Pausas masivas → Requieren aprobación

3. **Rollback:**
   - Mantener snapshot de presupuestos pre-cambio
   - Implementar endpoint `/rollback/{cycle_id}`

4. **Audit Log:**
   - Todos los cambios en DB
   - Retention: 90 días

---

## Contacto y Soporte

**Equipo:** AI Platform Team  
**Slack:** #meta-ads-automation  
**Docs:** https://docs.stakazo.com/full-cycle

---

**Versión:** 1.0.0  
**Fecha:** 2025-11-27  
**Autor:** PASO 10.11 Implementation
