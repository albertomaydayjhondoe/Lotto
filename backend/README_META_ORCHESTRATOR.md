# Meta Ads Orchestrator - PASO 10.3

## 📦 Overview

Meta Ads Orchestrator coordina la creación completa de campañas publicitarias en Meta (Facebook/Instagram) integrando todos los componentes del sistema:

- **PASO 10.1**: Modelos de base de datos (MetaCampaign, MetaAdset, MetaAd, etc.)
- **PASO 10.2**: Cliente de API Meta Ads (stub mode)
- **PASO 10.3**: Capa de orquestación (este módulo)

## 🏗️ Architecture

```
POST /meta/orchestrate/run
    ↓
MetaAdsOrchestrator.orchestrate_campaign()
    ↓
1. Validate Clip exists in DB
2. Get MetaAdsClient for social_account_id
3. Create Campaign → Adset → Ad → Creative
4. Persist all entities to database
5. Sync insights from Meta API
6. Return OrchestrationResult
```

## 📡 API Endpoints

### POST /meta/orchestrate/run

Ejecuta la orquestación completa de una campaña de Meta Ads.

**Request Body:**
```json
{
  "social_account_id": "uuid",
  "clip_id": "uuid",
  "campaign_name": "Summer Sale 2025",
  "campaign_objective": "OUTCOME_SALES",
  "daily_budget_cents": 10000,
  "creative_title": "Amazing Product",
  "creative_description": "Get 50% off",
  "landing_url": "https://example.com/sale",
  "targeting": {
    "age_min": 18,
    "age_max": 65,
    "genders": [1, 2]
  },
  "optimization_goal": "LINK_CLICKS",
  "auto_publish": false
}
```

**Response (200):**
```json
{
  "request_id": "uuid",
  "social_account_id": "uuid",
  "clip_id": "uuid",
  "overall_success": true,
  "started_at": "2025-11-25T15:00:00Z",
  "completed_at": "2025-11-25T15:00:05Z",
  "duration_seconds": 5.2,
  "campaign_creation": {
    "campaign_db_id": 123,
    "campaign_meta_id": "META_CAMPAIGN_abc123",
    "adset_db_id": 124,
    "adset_meta_id": "META_ADSET_xyz789",
    "ad_db_id": 125,
    "ad_meta_id": "META_AD_def456",
    "creative_db_id": 126,
    "creative_meta_id": "META_CREATIVE_ghi789",
    "success": true,
    "error": null
  },
  "insights_sync": {
    "insights_synced": 7,
    "date_range_start": "2025-11-18",
    "date_range_end": "2025-11-25",
    "success": true,
    "error": null
  },
  "errors": []
}
```

**Authorization:** Requires `admin` or `manager` role (RBAC enforced).

### POST /meta/orchestrate/sync-insights/{social_account_id}

Sincroniza insights para todas las campañas de una cuenta social.

**Response (200):**
```json
{
  "message": "Insights sync initiated for account {id}",
  "status": "queued"
}
```

## 🧪 Tests

### Running Tests

```bash
# All orchestrator tests (simplified without DB fixtures)
pytest tests/test_meta_orchestrator_simple.py -v

# Expected: 6/6 passing
```

### Test Coverage

1. **test_orchestrator_validate_clip_fails_if_not_found**: Validates clip existence check
2. **test_orchestrator_has_action_queue**: Tests action queue functionality
3. **test_orchestration_request_model**: Validates Pydantic request model
4. **test_orchestrator_instantiation**: Tests orchestrator creation
5. **test_orchestrate_campaign_returns_result**: Tests full orchestration flow
6. **test_orchestrator_respects_budget**: Validates budget parameter handling

## 💾 Database Persistence

All entities created during orchestration are persisted to PostgreSQL:

```sql
-- Created in order:
1. MetaCampaignModel (campaign_id, name, objective, status)
2. MetaAdsetModel (adset_id, campaign_db_id, targeting, budget)
3. MetaCreativeModel (creative_id, video_id, thumbnail_url)
4. MetaAdModel (ad_id, adset_db_id, creative_id, status)
5. MetaAdInsightsModel (impressions, clicks, spend, date_start)
```

Transaction handling:
- `await db.commit()` on success
- `await db.rollback()` on error
- Atomicity guaranteed per orchestration

## 🔧 Configuration

### Environment Variables

```bash
# Meta Ads client mode
META_ADS_MODE=stub  # or "live" for production

# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/stakazo
```

### Default Values

```python
max_retries = 3
retry_delay_seconds = 2
```

## 📝 Usage Example

```python
from app.meta_ads_orchestrator import MetaAdsOrchestrator, OrchestrationRequest
from app.core.database import get_db

# Create request
request = OrchestrationRequest(
    social_account_id=social_account_id,
    clip_id=clip_id,
    campaign_name="Black Friday 2025",
    campaign_objective="OUTCOME_SALES",
    daily_budget_cents=50000,  # $500/day
    creative_title="Limited Time Offer",
    creative_description="Save 70% on select items",
    landing_url="https://shop.example.com/black-friday",
    targeting={
        "age_min": 25,
        "age_max": 54,
        "genders": [1, 2],
        "geo_locations": {"countries": ["US", "CA"]},
        "interests": [{"id": "12345", "name": "Shopping"}]
    },
    optimization_goal="CONVERSIONS",
    auto_publish=True  # Creates as ACTIVE instead of PAUSED
)

# Execute orchestration
async with get_db() as db:
    orchestrator = MetaAdsOrchestrator(db)
    result = await orchestrator.orchestrate_campaign(request)
    
    if result.overall_success:
        print(f"Campaign created: {result.campaign_creation.campaign_meta_id}")
        print(f"Synced {result.insights_sync.insights_synced} insights")
    else:
        print(f"Errors: {result.errors}")
```

## 🔒 Security

- **RBAC**: Only `admin` and `manager` roles can orchestrate campaigns
- **Input Validation**: All requests validated with Pydantic models
- **Error Handling**: Exceptions caught and returned in `errors` array
- **Transaction Safety**: Database rollback on any failure

## 🚀 Next Steps

### PASO 10.4: Advanced Features (Future)
- Batch campaign creation
- A/B testing automation
- Budget optimization algorithms
- Scheduled campaign activation
- Real-time performance alerts

### Integration Points
- **Publishing Engine**: Trigger campaign creation from clip publication
- **Analytics Dashboard**: Display orchestration metrics
- **Alerting System**: Notify on campaign failures

## 📚 Dependencies

```python
# Core
FastAPI >= 0.104.0
Pydantic >= 2.5.0
SQLAlchemy >= 2.0.0

# Integrations
app.meta_ads_client  # PASO 10.2
app.models.database  # PASO 10.1
app.core.auth       # RBAC
```

## ✅ Status

- **Implementation**: Complete (PASO 10.3)
- **Tests**: 6/6 passing
- **Mode**: STUB only (no real Meta API calls yet)
- **RBAC**: Enforced (admin/manager only)
- **Documentation**: Complete

---

**Last Updated**: 2025-11-25
**Author**: sistemaproyectomunidal
**Commit**: 8b9f6a2
