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

## 🎯 A/B Testing & Auto-Publish (PASO 10.4)

### Overview

El sistema de A/B testing permite comparar múltiples variantes de creativos publicitarios y seleccionar automáticamente el "ganador" basándose en métricas de rendimiento. El ganador puede ser publicado automáticamente en redes sociales.

### Architecture

```
1. Create A/B Test → Multiple variants (2+) assigned to campaign
2. Run Test → Collect metrics (CTR, CPC, ROAS, engagement)
3. Evaluate → Statistical test (chi-square) + composite score
4. Select Winner → Based on ROAS (50%) + CTR (30%) + CPC (20%)
5. Auto-Publish → Create PublishLog → Publishing queue
```

### API Endpoints

#### POST /meta/orchestrate/ab

Crea un nuevo A/B test para una campaña.

**Request:**
```json
{
  "campaign_id": "uuid",
  "test_name": "Black Friday Creative Test",
  "variants": [
    {"clip_id": "uuid-1", "ad_id": "uuid-ad-1"},
    {"clip_id": "uuid-2", "ad_id": "uuid-ad-2"}
  ],
  "metrics": ["ctr", "cpc", "roas", "engagement"],
  "min_impressions": 1000,
  "min_duration_hours": 48
}
```

**Response (201):**
```json
{
  "id": "ab-test-uuid",
  "campaign_id": "campaign-uuid",
  "test_name": "Black Friday Creative Test",
  "status": "active",
  "variants": [...],
  "metrics": ["ctr", "cpc", "roas", "engagement"],
  "start_time": "2025-11-25T10:00:00Z",
  "min_impressions": 1000,
  "min_duration_hours": 48
}
```

**curl Example:**
```bash
curl -X POST http://localhost:8000/meta/orchestrate/ab \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "campaign_id": "550e8400-e29b-41d4-a716-446655440000",
    "test_name": "Summer Sale Test",
    "variants": [
      {"clip_id": "clip-uuid-1", "ad_id": "ad-uuid-1"},
      {"clip_id": "clip-uuid-2", "ad_id": "ad-uuid-2"}
    ],
    "metrics": ["ctr", "cpc", "engagement"],
    "min_impressions": 1000,
    "min_duration_hours": 48
  }'
```

#### GET /meta/orchestrate/ab/{ab_test_id}

Obtiene detalles de un A/B test.

**Response (200):**
```json
{
  "id": "ab-test-uuid",
  "campaign_id": "campaign-uuid",
  "test_name": "Black Friday Creative Test",
  "status": "completed",
  "variants": [...],
  "winner_clip_id": "uuid-1",
  "winner_ad_id": "uuid-ad-1",
  "winner_decided_at": "2025-11-27T14:30:00Z",
  "metrics_snapshot": [
    {
      "clip_id": "uuid-1",
      "impressions": 5000,
      "clicks": 250,
      "ctr": 5.0,
      "cpc": 2.0,
      "roas": 4.5
    },
    {
      "clip_id": "uuid-2",
      "impressions": 5000,
      "clicks": 150,
      "ctr": 3.0,
      "cpc": 2.5,
      "roas": 3.2
    }
  ],
  "statistical_results": {
    "chi2": 125.5,
    "p_value": 0.001,
    "significant": true,
    "confidence": "95%"
  },
  "published_to_social": true,
  "publish_log_id": "publish-log-uuid"
}
```

#### POST /meta/orchestrate/ab/{ab_test_id}/evaluate

Evalúa un A/B test y selecciona un ganador.

**Request:**
```json
{
  "force": false
}
```

**Response (200):**
```json
{
  "success": true,
  "winner_clip_id": "uuid-1",
  "winner_ad_id": "uuid-ad-1",
  "metrics_snapshot": [...],
  "statistical_results": {
    "chi2": 125.5,
    "p_value": 0.001,
    "significant": true
  },
  "composite_scores": {
    "uuid-1": 4.35,
    "uuid-2": 3.12
  }
}
```

**Embargo Rules:**
- Minimum duration: 48 hours (configurable)
- Minimum impressions: 1,000 per variant (configurable)
- Status: `needs_more_data` if rules not met

**curl Example:**
```bash
curl -X POST http://localhost:8000/meta/orchestrate/ab/{test-id}/evaluate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"force": false}'
```

#### POST /meta/orchestrate/ab/{ab_test_id}/publish-winner

Publica el ganador del A/B test en redes sociales.

**Request:**
```json
{
  "social_account_id": "social-account-uuid"
}
```

**Response (200):**
```json
{
  "success": true,
  "publish_log_id": "publish-log-uuid",
  "clip_id": "winner-clip-uuid",
  "social_account_id": "social-account-uuid",
  "status": "pending",
  "message": "Winner queued for publishing"
}
```

**curl Example:**
```bash
curl -X POST http://localhost:8000/meta/orchestrate/ab/{test-id}/publish-winner \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"social_account_id": "account-uuid"}'
```

#### POST /meta/orchestrate/ab/{ab_test_id}/archive

Archiva un A/B test.

**Response (200):**
```json
{
  "id": "ab-test-uuid",
  "status": "archived",
  "message": "A/B test archived successfully"
}
```

### Winner Selection Algorithm

**Composite Score Formula:**
```
score = (ROAS × 0.5) + (CTR × 0.3) + (normalized_CPC × 0.2)
```

- **ROAS (50% weight)**: Return on Ad Spend - most important for ROI
- **CTR (30% weight)**: Click-Through Rate - engagement indicator
- **CPC (20% weight)**: Cost Per Click - efficiency metric (inverted, lower is better)

### Statistical Evaluation

**Chi-Square Test:**
- Tests statistical significance between variants
- 95% confidence level (p-value < 0.05)
- Applied to CTR comparison

**Example:**
```python
Variant A: 5,000 impressions, 250 clicks (5% CTR)
Variant B: 5,000 impressions, 150 clicks (3% CTR)

Chi-square = 125.5, p-value = 0.001
Result: Statistically significant difference
```

### Database Schema

**MetaAbTestModel:**
```sql
CREATE TABLE meta_ab_tests (
    id UUID PRIMARY KEY,
    campaign_id UUID REFERENCES meta_campaigns(id),
    test_name VARCHAR(255),
    variants JSON,  -- List of {clip_id, ad_id}
    metrics JSON,   -- ["ctr", "cpc", "roas"]
    status VARCHAR(50),  -- active, evaluating, completed, archived, needs_more_data
    winner_clip_id UUID,
    winner_ad_id UUID,
    winner_decided_at TIMESTAMP,
    metrics_snapshot JSON,
    statistical_results JSON,
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    min_impressions INTEGER DEFAULT 1000,
    min_duration_hours INTEGER DEFAULT 48,
    published_to_social INTEGER DEFAULT 0,
    publish_log_id UUID REFERENCES publish_logs(id),
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

### Integration with Publishing Engine

When a winner is selected and published:

1. **Create PublishLog** with status `pending`
2. **Queue for Publishing** - Will be picked up by publishing queue worker
3. **Metadata** includes:
   - `ab_test_id`: Reference to the A/B test
   - `source`: "ab_test_winner"
   - `winner_metrics`: Snapshot of winning metrics

### Complete Workflow Example

```python
# 1. Create campaign with orchestrator
orchestration_result = await orchestrator.orchestrate_campaign(request)
campaign_id = orchestration_result.campaign_creation.campaign_db_id

# 2. Create A/B test with 2 variants
ab_test = await create_ab_test(
    db=db,
    campaign_id=campaign_id,
    test_name="Holiday Sale Test",
    variants=[
        {"clip_id": clip_1, "ad_id": ad_1},
        {"clip_id": clip_2, "ad_id": ad_2},
    ],
    metrics=["ctr", "cpc", "roas"],
    min_impressions=1000,
    min_duration_hours=48,
)

# 3. Wait for test to run (48+ hours, 1000+ impressions)
# ... ads run and collect metrics ...

# 4. Evaluate and select winner
result = await evaluate_ab_test(
    db=db,
    ab_test_id=ab_test.id,
    force=False,
)

if result["success"]:
    print(f"Winner: {result['winner_clip_id']}")
    print(f"Composite scores: {result['composite_scores']}")
    
    # 5. Auto-publish winner to Instagram
    publish_result = await publish_winner(
        db=db,
        ab_test_id=ab_test.id,
        social_account_id=instagram_account_id,
    )
    
    print(f"Published: {publish_result['publish_log_id']}")
```

### Tests (9/9 passing)

```bash
pytest tests/test_meta_orchestrator_ab.py -v
```

**Test Coverage:**
1. ✅ `test_create_ab_test_success` - Create A/B test
2. ✅ `test_create_ab_test_requires_two_variants` - Validation
3. ✅ `test_evaluate_ab_test_insufficient_duration` - Embargo rules (duration)
4. ✅ `test_evaluate_ab_test_insufficient_impressions` - Embargo rules (impressions)
5. ✅ `test_evaluate_ab_test_selects_winner` - Winner selection
6. ✅ `test_publish_winner_creates_publish_log` - Auto-publish
7. ✅ `test_archive_ab_test` - Archiving
8. ✅ `test_ab_test_evaluator_chi_square` - Statistical test
9. ✅ `test_ab_test_evaluator_metrics` - Metric calculations

### Security

- **RBAC**: All A/B testing endpoints require `admin` or `manager` role
- **Validation**: Pydantic models validate all inputs
- **Atomicity**: Database transactions with rollback on error
- **Idempotency**: Publishing winner checks `published_to_social` flag

## 📚 Dependencies

```python
# Core
FastAPI >= 0.104.0
Pydantic >= 2.5.0
SQLAlchemy >= 2.0.0

# Statistical
scipy >= 1.16.0
numpy >= 2.3.0

# Integrations
app.meta_ads_client  # PASO 10.2
app.models.database  # PASO 10.1
app.core.auth       # RBAC
```

## ✅ Status

- **Implementation**: Complete (PASO 10.3 + 10.4)
- **Tests**: 
  - Orchestrator: 6/6 passing
  - A/B Testing: 9/9 passing
  - **Total: 15/15 passing** ✅
- **Mode**: STUB only (no real Meta API calls yet)
- **RBAC**: Enforced (admin/manager only)
- **Documentation**: Complete
- **A/B Testing**: Full statistical evaluation + auto-publish

---

**Last Updated**: 2025-11-25
**Author**: sistemaproyectomunidal
**Commit**: [pending]
