# Dashboard AI Integration Module

**PASO 8.0** - Integración AI Global Worker → Dashboard

Este módulo proporciona endpoints optimizados para el Dashboard que consumen datos del AI Global Worker y los formatean para consumo del frontend.

## Arquitectura

```
dashboard_ai_integration/
├── __init__.py          # Exports del módulo
├── router.py            # Endpoints FastAPI
├── serializers.py       # Serialización compacta
├── formatter.py         # Formatters derivados
└── README.md            # Este archivo
```

## Endpoints

### 1. GET `/dashboard/ai-integration/last`

Retorna el último output de reasoning del AI Worker en formato dashboard.

**Autenticación:** admin, manager

**Response:**
```json
{
  "reasoning_id": "uuid",
  "timestamp": "2025-11-23T10:30:00Z",
  "execution_time_ms": 1500,
  "health_card": {
    "score": 75,
    "status": "healthy",
    "status_label": "Healthy",
    "top_issue": "No issues detected",
    "color": "green",
    "overall_health": "System operating normally"
  },
  "recommendations_cards": [
    {
      "category": "content",
      "priority": "high",
      "title": "Increase publishing frequency",
      "description": "Current cadence is below optimal...",
      "full_description": "Full text...",
      "impact": "high",
      "effort": "medium",
      "reasoning": "Analysis shows...",
      "badge_color": "orange"
    }
  ],
  "actions_summary": {
    "total_steps": 3,
    "estimated_duration": "2 hours",
    "risk_level": "low",
    "automated": true,
    "objective": "Optimize publishing schedule",
    "risk_badge_color": "green",
    "steps": [...]
  },
  "raw": {
    "summary": {...},
    "snapshot": {...}
  }
}
```

**Códigos de estado:**
- `200` - Success
- `404` - No AI reasoning available yet
- `401` - Unauthorized
- `403` - Forbidden (insufficient permissions)

---

### 2. GET `/dashboard/ai-integration/run`

Trigger manual de AI reasoning con retorno inmediato en formato dashboard.

**Autenticación:** admin, manager

**Response:** Mismo formato que `/last`

**Códigos de estado:**
- `200` - Success
- `500` - AI reasoning failed
- `401` - Unauthorized
- `403` - Forbidden

**Uso:**
```bash
curl -X GET "http://localhost:8000/dashboard/ai-integration/run" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

### 3. GET `/dashboard/ai-integration/history`

Historial de ejecuciones de AI reasoning (STUB).

**Autenticación:** admin, manager

**Response:**
```json
[]
```

**Estado:** STUB - Implementación futura almacenará outputs en DB.

---

## Módulos

### `serializers.py`

Funciones de serialización compacta:

- **`serialize_ai_reasoning_compact()`** - Serializa AIReasoningOutput completo
- **`serialize_summary()`** - Serializa AISummary
- **`serialize_recommendation()`** - Serializa AIRecommendation
- **`serialize_action_plan()`** - Serializa AIActionPlan
- **`serialize_snapshot_minimal()`** - Serializa SystemSnapshot (mínimo)

### `formatter.py`

Funciones que generan formatos derivados:

- **`generate_health_card()`** - Card con score, status, color, top issue
  - Score 0-40: "critical" (red)
  - Score 40-70: "warning" (yellow)
  - Score 70-100: "healthy" (green)

- **`generate_recommendations_cards()`** - Lista resumida de recomendaciones
  - Incluye badge_color basado en priority
  - Trunca descriptions largas (150 chars)

- **`generate_actions_summary()`** - Resumen del action plan
  - Total steps
  - Duración estimada
  - Risk level con badge color

- **`generate_full_dashboard_response()`** - Response completo (usado por endpoints)

---

## Integración con AI Global Worker

Este módulo **NO ejecuta reasoning**, solo formatea outputs existentes.

**Flujo:**
1. AI Global Worker genera `AIReasoningOutput` cada N minutos (background loop)
2. Output se almacena en memoria (`runner.py` → `_last_reasoning`)
3. Dashboard llama `/dashboard/ai-integration/last` para obtener datos formateados
4. Dashboard puede llamar `/dashboard/ai-integration/run` para trigger manual

**Dependencias:**
- `app.ai_global_worker.runner.get_last_reasoning()` - Obtiene último reasoning
- `app.ai_global_worker.collector.collect_system_snapshot()` - Recolecta snapshot
- `app.ai_global_worker.reasoning.run_full_reasoning()` - Ejecuta reasoning

---

## Testing

Ver `backend/tests/test_dashboard_ai_integration.py` para tests completos.

Tests incluidos:
1. `test_ai_last_endpoint_ok` - Endpoint GET /last funciona
2. `test_ai_run_endpoint_ok` - Endpoint GET /run funciona
3. `test_ai_history_empty` - Endpoint GET /history retorna []
4. `test_ai_summary_formatter_ok` - Formatter genera health_card correcto
5. `test_ai_recommendations_formatter_ok` - Formatter genera recommendations_cards

---

## Uso en Frontend

```typescript
// Obtener último reasoning
const response = await fetch('/dashboard/ai-integration/last', {
  headers: { Authorization: `Bearer ${token}` }
});
const data = await response.json();

// Renderizar health card
<HealthCard 
  score={data.health_card.score}
  status={data.health_card.status}
  color={data.health_card.color}
  topIssue={data.health_card.top_issue}
/>

// Renderizar recommendations
{data.recommendations_cards.map(rec => (
  <RecommendationCard
    key={rec.title}
    priority={rec.priority}
    title={rec.title}
    description={rec.description}
    badgeColor={rec.badge_color}
  />
))}

// Trigger manual
const runAI = async () => {
  const response = await fetch('/dashboard/ai-integration/run', {
    headers: { Authorization: `Bearer ${token}` }
  });
  return await response.json();
};
```

---

## Roadmap Future

**PASO 8.1 (no implementado aún):**
- Database storage de reasoning outputs
- Endpoint /history con paginación
- Trend analysis (health score over time)
- Comparación entre runs
- Export a CSV/PDF

**PASO 8.2 (no implementado aún):**
- WebSocket notifications para nuevos reasoning outputs
- Real-time health score updates
- Alert thresholds configurables

---

## Notas de Implementación

1. **Sin Autenticación Local:** Los endpoints delegan autenticación a `require_role()` del módulo `app.auth`.

2. **Formato de Timestamp:** Todos los timestamps se serializan a ISO 8601 strings.

3. **Health Score Logic:**
   - Critical (red): 0-39
   - Warning (yellow): 40-69
   - Healthy (green): 70-100

4. **Priority Badge Colors:**
   - critical → red
   - high → orange
   - medium → yellow
   - low → blue

5. **Risk Badge Colors:**
   - high → red
   - medium → yellow
   - low → green

---

## Autor

Implementado en **PASO 8.0** - Noviembre 2025
