# Meta Campaigns Auto-Pilot (AutoPublisher) - PASO 10.8

Sistema automatizado de creación, testeo A/B, selección de ganador y publicación de campañas en Meta (Instagram/Facebook).

## Arquitectura

```
┌─────────────────────────────────────────────────────────────┐
│                   AutoPublisher System                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  1. Request → Orchestrator                                  │
│  2. Orchestrator → Executor (create campaigns/adsets/ads)  │
│  3. Executor → MetaAdsClient (stub/live)                   │
│  4. ABTestManager → Launch variants                         │
│  5. Wait embargo period                                     │
│  6. Collect insights → MetaInsightsCollector                │
│  7. ABTestManager → Analyze & select winner                │
│  8. BudgetOptimizer → Scale winner budget                   │
│  9. Executor → Publish final campaign                       │
│  10. Pause losing variants                                  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Endpoints

### POST /meta/autopilot/run
Ejecuta un AutoPublisher run manualmente.

**Permisos:** admin, manager

**Request:**
```json
{
  "meta_account_id": "uuid",
  "campaign_name": "Test Campaign",
  "objective": "CONVERSIONS",
  "ab_test_config": {
    "strategy": "creative_split",
    "variants_count": 2,
    "test_budget_per_variant": 50.0,
    "test_duration_hours": 24,
    "winner_criteria": "roas"
  },
  "targeting_config": {
    "countries": ["ES", "PE"],
    "age_min": 18,
    "age_max": 65,
    "placements": ["instagram_feed"]
  },
  "budget_config": {
    "total_budget": 500.0,
    "scaling_factor": 2.0
  },
  "creative_ids": ["uuid1", "uuid2"],
  "headlines": ["Headline A", "Headline B"],
  "primary_texts": ["Text A", "Text B"],
  "require_human_approval": true
}
```

**Response:**
```json
{
  "run_id": "uuid",
  "status": "completed",
  "campaign_ids": ["uuid1", "uuid2"],
  "winner_selection": {
    "winner_variant_id": "...",
    "winner_name": "Test Campaign - Variant A",
    "winner_metrics": {
      "spend": 50.0,
      "roas": 3.5,
      "conversions": 45
    },
    "improvement_percentage": 25.5
  },
  "overall_roas": 2.8,
  "logs": ["..."]
}
```

### POST /meta/autopilot/schedule
Programa un run para ejecución futura.

**Permisos:** manager

### GET /meta/autopilot/status/{run_id}
Obtiene estado de un run.

**Permisos:** admin, manager

### POST /meta/autopilot/publish-winner
Aprueba y publica el ganador de un A/B test.

**Permisos:** operator, manager, admin

## Variables de Entorno

```bash
# AutoPublisher
AUTO_PUBLISHER_ENABLED=true
META_API_MODE=stub  # o "live"
META_DEFAULT_AD_ACCOUNT_ID=act_123456789
AUTO_PUBLISHER_MAX_CONCURRENT_RUNS=5

# Meta API (para modo live)
META_ACCESS_TOKEN=your_token_here

# Database
DATABASE_URL=postgresql+asyncpg://...

# Auth
SECRET_KEY=your_secret
```

## Flujo de Uso

### 1. Stub Mode (Testing Local)

```bash
cd /workspaces/stakazo/backend

# Configurar modo stub
export AUTO_PUBLISHER_ENABLED=true
export META_API_MODE=stub

# Ejecutar tests
pytest tests/test_meta_autopublisher.py -v

# Iniciar backend
uvicorn app.main:app --reload
```

### 2. Request Manual

```bash
curl -X POST "http://localhost:8000/meta/autopilot/run" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d @request_example.json
```

### 3. Verificar Estado

```bash
curl "http://localhost:8000/meta/autopilot/status/{run_id}" \
  -H "Authorization: Bearer $TOKEN"
```

## Componentes

### orchestrator.py
Coordina el flujo completo end-to-end.

### executor.py
Tareas idempotentes para crear campaigns/adsets/ads con rollback.

### ab_flow.py
Gestión de A/B testing y selección de ganadores con significancia estadística.

### optimizer.py
Integración con ROAS Engine para escalado de presupuestos.

### monitor.py
Health checks y métricas del sistema.

### router.py
Endpoints REST con RBAC.

## Integraciones

- **PASO 10.1:** Meta Models (database)
- **PASO 10.2:** MetaAdsClient (stub/live)
- **PASO 10.7:** Meta Insights Collector
- **PASO 10.5:** ROAS Engine (optimizer)
- **Publishing Queue:** Para upload físico de creativos
- **AI Global Worker:** Supervisión y recomendaciones

## Estados de Run

- `PENDING`: Iniciando
- `CREATING_CAMPAIGNS`: Creando variantes
- `AB_TESTING`: Test A/B en curso
- `ANALYZING_RESULTS`: Analizando métricas
- `SELECTING_WINNER`: Seleccionando ganador
- `WAITING_APPROVAL`: Esperando aprobación humana
- `SCALING_BUDGET`: Escalando presupuesto
- `PUBLISHING_FINAL`: Publicando campaña final
- `COMPLETED`: Completado exitosamente
- `FAILED`: Falló con errores
- `CANCELLED`: Cancelado manualmente

## Seguridad

- RBAC por endpoint (admin/manager/operator)
- Credenciales encriptadas (PASO 5.1)
- Validación de presupuestos
- Límites de rate en Meta API
- Require human approval flag

## Testing

```bash
# Unit tests
pytest tests/test_meta_autopublisher.py -k test_orchestrator

# Integration tests  
pytest tests/test_meta_autopublisher.py -k test_integration

# Con coverage
pytest tests/test_meta_autopublisher.py --cov=app.meta_autopublisher
```

## Troubleshooting

### Error: "AutoPublisher is disabled"
Solución: `export AUTO_PUBLISHER_ENABLED=true`

### Error: "Meta account not found"
Verificar que `meta_account_id` existe en DB.

### Error: "Insufficient budget"
El `total_budget` debe ser >= `test_budget_per_variant * variants_count`

## Próximos Pasos

1. ✅ Implementación stub-first (Fase A)
2. ⏳ Modo live con OAuth tokens (Fase B)
3. ⏳ Storage S3/GCS para creativos
4. ⏳ Notificaciones Telegram/Email
5. ⏳ Dashboard UI components

## Soporte

Ver logs en: `/var/log/autopublisher.log`

Consultas: sistemaproyectomunidal@gmail.com
