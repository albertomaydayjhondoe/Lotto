# Meta Creative Optimizer (PASO 10.16)

## 🎯 Objetivo

Capa de integración completa que conecta todos los módulos Meta Ads en un sistema de decisión creativa autónoma. Selecciona el "Creative Winner of the Day", asigna roles, decide recombinaciones y escala presupuestos automáticamente.

## 🏗️ Arquitectura

```
┌─────────────────────────────────────────────────────────────────┐
│                  META CREATIVE OPTIMIZER                          │
│                     (PASO 10.16)                                  │
└──────────────┬──────────────────────────────────┬────────────────┘
               │                                  │
               ▼                                  ▼
    ┌──────────────────────┐         ┌───────────────────────┐
    │  Unified Data        │         │  Decision Pipeline    │
    │  Collector           │         │                       │
    └──────────┬───────────┘         └─────────┬─────────────┘
               │                               │
      ┌────────┴─────────┐            ┌────────┴────────┐
      │                  │            │                  │
      ▼                  ▼            ▼                  ▼
┌──────────┐      ┌──────────┐  ┌──────────┐    ┌──────────┐
│ PASO 10.15│      │ PASO 10.7│  │  Winner  │    │ Decision │
│ Creative  │      │ Insights │  │ Selector │    │  Engine  │
│ Analyzer  │      │Collector │  │          │    │          │
└──────────┘      └──────────┘  └──────────┘    └──────────┘
      │                  │            │                │
      ▼                  ▼            │                │
┌──────────┐      ┌──────────┐       │                │
│ PASO 10.5│      │ PASO 10.12│      │                │
│   ROAS   │      │ Targeting│       │                │
│  Engine  │      │Optimizer │       │                │
└──────────┘      └──────────┘       │                │
      │                  │            │                │
      ▼                  ▼            ▼                ▼
┌──────────┐      ┌──────────┐  ┌────────────────────────┐
│ PASO 10.9│      │Other Data│  │   Orchestration        │
│  Spike   │      │ Sources  │  │   Client               │
│ Manager  │      │          │  │   (PASO 10.3)          │
└──────────┘      └──────────┘  └─────────┬──────────────┘
                                           │
                                           ▼
                                  ┌─────────────────┐
                                  │   Meta Ads API  │
                                  │   Publishing    │
                                  └─────────────────┘
```

## 🔄 Pipeline de Decisión

### 1. Data Collection Phase
```python
UnifiedDataCollector
├── Collect from Creative Analyzer (10.15)
│   ├── overall_score (0-100)
│   ├── fatigue_score, is_fatigued
│   └── performance/engagement/completion scores
├── Collect from Insights (10.7)
│   ├── CTR, CVR, CPC, CPM, ROAS
│   └── impressions, clicks, conversions, spend
├── Collect from ROAS Engine (10.5)
│   ├── roas_efficiency
│   └── roas_trend (improving/stable/declining)
├── Collect from Targeting (10.12)
│   ├── target_score
│   ├── best_segments
│   └── frequency_cap
└── Collect from Spike Manager (10.9)
    ├── has_spike
    └── spike_severity
```

### 2. Winner Selection Phase
```python
WinnerSelector
├── Filter candidates (non-fatigued, score > 50)
├── Calculate composite score (weighted)
│   ├── overall_score: 30%
│   ├── ROAS: 25%
│   ├── conversions: 20%
│   ├── CTR: 10%
│   ├── CVR: 10%
│   └── freshness: 5%
├── Sort by composite score
├── Select winner + runner-up
└── Generate reasoning
```

### 3. Decision Making Phase
```python
CreativeDecisionEngine
├── Assign role to each creative
│   ├── WINNER: Top performer
│   ├── TEST: Good potential
│   ├── FATIGUE: Needs refresh
│   ├── ARCHIVE: Retire
│   └── PENDING: Not evaluated
├── Determine actions
│   ├── PROMOTE (winner)
│   ├── SCALE_BUDGET (high ROAS)
│   ├── REDUCE_BUDGET (low performance)
│   ├── GENERATE_VARIANTS (fatigued)
│   ├── RECOMBINE (fragment optimization)
│   ├── PAUSE (severe fatigue)
│   └── ARCHIVE (retire)
├── Calculate priority (1-5)
├── Decide budget changes
└── Decide variant generation
```

### 4. Orchestration Phase
```python
OrchestrationClient (PASO 10.3)
├── publish_winner()
│   └── Publish winning creative to Meta
├── update_budget()
│   └── Scale budget up/down
└── create_ab_test()
    └── Create A/B test for variants
```

## 📊 Algoritmo de Scoring

### Composite Score Calculation
```
Composite = (overall_score × 0.30) +
            (ROAS × 20 × 0.25) +
            (conversions / 10 × 0.20) +
            (CTR × 20 × 0.10) +
            (CVR × 12.5 × 0.10) +
            ((100 - days_active) × 0.05)

Range: 0-100
```

### Role Assignment Logic
- **WINNER**: `is_winner=True` (selected by WinnerSelector)
- **FATIGUE**: `is_fatigued=True`
- **ARCHIVE**: `overall_score < 50`
- **TEST**: All others with potential
- **PENDING**: Not yet evaluated

### Action Determination
| Role    | Condition                    | Actions                                  |
|---------|------------------------------|------------------------------------------|
| WINNER  | Always                       | PROMOTE                                  |
| WINNER  | ROAS > 4.0                   | PROMOTE + SCALE_BUDGET                   |
| FATIGUE | overall_score > 40           | GENERATE_VARIANTS + RECOMBINE            |
| FATIGUE | overall_score ≤ 40           | PAUSE                                    |
| ARCHIVE | Always                       | ARCHIVE + REDUCE_BUDGET                  |
| TEST    | ROAS > 3.0 && score > 70     | SCALE_BUDGET                             |

## 🗃️ Database Models

### 1. MetaCreativeDecisionModel
Almacena decisiones de optimización para cada creative.

**Campos principales:**
- `assigned_role`: winner/test/fatigue/archive/pending
- `recommended_actions`: List[OptimizationAction]
- `priority`: 1-5 (1=highest)
- `confidence`: high/medium/low
- `current_budget` / `recommended_budget`
- `should_generate_variants` / `should_recombine`
- `execution_status`: pending/in_progress/completed/failed

**Índices:** 6 índices compuestos para queries rápidas

### 2. MetaCreativeWinnerLogModel
Log histórico de selecciones de ganadores.

**Campos principales:**
- `winner_score`: Composite score
- `overall_score`, `roas`, `ctr`, `cvr`
- `runner_up_creative_id` / `runner_up_score`
- `is_current_winner`: Flag para ganador actual
- `days_as_winner`: Días como ganador
- `replaced_at` / `replaced_by_id`: Tracking de reemplazos

**Índices:** 5 índices para historial y queries actuales

### 3. MetaCreativeOptimizationAuditModel
Audit log de ciclos de optimización completos.

**Campos principales:**
- `campaigns_processed` / `creatives_processed`
- `winners_selected` / `decisions_made`
- Breakdown de decisiones: `winners_count`, `testers_count`, `fatigued_count`, `archived_count`
- Breakdown de acciones: `promote_count`, `scale_budget_count`, `generate_variants_count`, etc.
- Budget impact: `total_budget_change`, `budget_scale_ups`, `budget_scale_downs`
- Integration tracking: `orchestrator_calls`, `orchestrator_successes`, `orchestrator_failures`

**Índices:** 5 índices para análisis de performance

## 🔌 API Endpoints

### GET `/meta/creative-optimizer/status`
Obtiene estado actual del optimizador.

**Response:**
```json
{
  "status": "operational",
  "last_run": "2025-11-27T10:00:00Z",
  "total_campaigns": 5,
  "total_creatives": 42,
  "current_winner_count": 5,
  "pending_decisions": 3
}
```

### POST `/meta/creative-optimizer/run`
Ejecuta ciclo completo de optimización.

**Request:**
```json
{
  "campaign_ids": ["uuid1", "uuid2"],
  "force": false,
  "mode": "stub"
}
```

**Response:**
```json
{
  "optimization_id": "uuid",
  "campaigns_processed": 2,
  "creatives_processed": 15,
  "winners_selected": 2,
  "decisions_made": 15,
  "processing_time_ms": 450
}
```

### GET `/meta/creative-optimizer/winner?campaign_id=uuid`
Obtiene ganador actual de campaña.

**Response:**
```json
{
  "campaign_id": "uuid",
  "creative_id": "uuid",
  "selected_at": "2025-11-27T10:00:00Z",
  "overall_score": 85.0,
  "roas": 4.5,
  "days_as_winner": 3,
  "confidence": "high"
}
```

### POST `/meta/creative-optimizer/promote/{creative_id}`
Promueve manualmente un creative a ganador (admin only).

**Request:**
```json
{
  "force": true,
  "reason": "Manual override for campaign X"
}
```

### GET `/meta/creative-optimizer/recommendations`
Obtiene todas las recomendaciones de optimización.

**Response:**
```json
{
  "total": 8,
  "high_priority": 3,
  "recommendations": [
    {
      "creative_id": "uuid",
      "recommendation_type": "generate_variants",
      "priority": 1,
      "confidence": "high",
      "estimated_impact": 15.0
    }
  ]
}
```

## ⚙️ Configuration

```python
# settings.py
CREATIVE_OPTIMIZER_ENABLED = True
CREATIVE_OPTIMIZER_INTERVAL_HOURS = 24
CREATIVE_OPTIMIZER_MODE = "stub"  # or "live"

# Scoring weights (customizable)
OPTIMIZER_WEIGHTS = {
    "overall_score": 0.30,
    "roas": 0.25,
    "conversions": 0.20,
    "ctr": 0.10,
    "cvr": 0.10,
    "freshness": 0.05
}
```

## 🔗 Integraciones

### PASO 10.15 - Creative Analyzer
- `overall_score`, `performance_score`, `engagement_score`
- `is_fatigued`, `fatigue_score`, `fatigue_level`

### PASO 10.7 - Insights Collector
- `ctr`, `cvr`, `cpc`, `cpm`, `roas`
- `impressions`, `clicks`, `conversions`, `spend`

### PASO 10.5 - ROAS Engine
- `roas_efficiency` (0-100 score)
- `roas_trend` (improving/stable/declining)

### PASO 10.12 - Targeting Optimizer
- `target_score` (0-100)
- `best_segments` (demographic/geographic)
- `frequency_cap`

### PASO 10.9 - Spike Manager
- `has_spike` (boolean)
- `spike_severity` (minor/moderate/severe)

### PASO 10.3 - Meta Orchestrator
- `publish_winner()` - Publica ganador
- `update_budget()` - Escala presupuesto
- `create_ab_test()` - Crea A/B tests

## 📝 TODOs para Modo LIVE

1. **UnifiedDataCollector:**
   - Implementar queries reales a DB de cada módulo
   - Cache de datos con TTL configurable
   - Batch queries para performance

2. **DecisionEngine:**
   - Guardar decisiones en `MetaCreativeDecisionModel`
   - Query previous_role desde DB
   - Tracking de ejecución de acciones

3. **WinnerSelector:**
   - Persistir en `MetaCreativeWinnerLogModel`
   - Actualizar `is_current_winner` flags
   - Tracking de `days_as_winner`

4. **OrchestrationClient:**
   - Integración real con PASO 10.3
   - Retry logic para API calls
   - Error handling y rollback

5. **Scheduler:**
   - Persist audit logs en `MetaCreativeOptimizationAuditModel`
   - Email notifications de resultados
   - Slack/webhook integrations

6. **Testing:**
   - Integration tests con DB real
   - E2E tests del pipeline completo
   - Load testing para volumen

## 🧪 Testing

```bash
# Run all tests
pytest tests/test_meta_creative_optimizer.py -v

# Run specific test
pytest tests/test_meta_creative_optimizer.py::test_full_optimization_pipeline -v
```

**Test Coverage:**
- Data collection (unified + multi-source)
- Winner selection (algorithm + filtering)
- Decision engine (roles + actions + budget)
- Orchestration (publish + budget + A/B test)
- Full pipeline (end-to-end)

## 📦 Deployment

### 1. Run Migration
```bash
alembic upgrade head
```

### 2. Environment Variables
```bash
export CREATIVE_OPTIMIZER_ENABLED=true
export CREATIVE_OPTIMIZER_INTERVAL_HOURS=24
export CREATIVE_OPTIMIZER_MODE=stub
```

### 3. Start Service
```bash
uvicorn app.main:app --reload
```

### 4. Verify Health
```bash
curl http://localhost:8000/meta/creative-optimizer/health-check
```

## 📊 Monitoring

### Key Metrics
- `optimization_cycles_completed`: Total runs
- `winners_selected_total`: Total winners
- `decisions_made_total`: Total decisions
- `orchestrations_executed_total`: Total API calls
- `processing_time_avg_ms`: Average duration

### Alerts
- Winner not selected in 48h
- High orchestration failure rate (>10%)
- Processing time >5s
- No decisions made in cycle

## 🎯 Version

**Version:** 1.0.0  
**Mode:** STUB (100% functional)  
**LIVE Mode:** TODOs prepared for production integration

---

**Integration Status:**
- ✅ PASO 10.15 (Creative Analyzer)
- ✅ PASO 10.7 (Insights Collector)
- ✅ PASO 10.5 (ROAS Engine)
- ✅ PASO 10.12 (Targeting Optimizer)
- ✅ PASO 10.9 (Spike Manager)
- 🔄 PASO 10.3 (Orchestrator) - STUB ready, LIVE TODOs
