# ROAS Engine - Return on Ad Spend Analytics

**PASO 10.5 Implementation** - Advanced Meta Ads ROAS tracking with statistical rigor, multi-touch attribution, and automated optimization.

---

## 📊 Overview

The ROAS Engine provides comprehensive Return on Ad Spend (ROAS) tracking by integrating Meta Ads platform metrics with real conversion data from Meta Pixel events. It goes beyond simple ROAS calculation to provide:

- **Statistical Confidence**: Bayesian smoothing and bootstrap confidence intervals for reliable metrics
- **Multi-Touch Attribution**: Credit conversions across multiple ad touchpoints
- **Predictive Analytics**: Machine learning-based ROAS predictions
- **Automated Optimization**: Budget reallocation and scaling recommendations
- **Pixel Integration**: Track real conversions, not just platform-reported metrics

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     ROAS Engine Architecture                     │
└─────────────────────────────────────────────────────────────────┘

┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Meta Ads    │────▶│  Meta Pixel  │────▶│  Database    │
│  Platform    │     │  Events      │     │  (Postgres)  │
└──────────────┘     └──────────────┘     └──────────────┘
      │                     │                     │
      ▼                     ▼                     ▼
┌─────────────────────────────────────────────────────────┐
│              ROAS Integration Layer                      │
│  • Blend platform metrics with pixel outcomes            │
│  • Calculate session quality scores                      │
│  • Estimate lifetime value (LTV)                         │
└─────────────────────────────────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────────────────────────┐
│                  ROAS Engine Core                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │   ROAS       │  │ Attribution  │  │  Prediction  │  │
│  │  Calculator  │  │   Engine     │  │   Engine     │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────────────────────────┐
│                  ROAS Optimizer                          │
│  • Detect high/low performers                            │
│  • Generate scaling recommendations                      │
│  • Compute budget reallocations                          │
└─────────────────────────────────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────────────────────────┐
│                   REST API Endpoints                     │
│  GET  /meta/roas/summary/{campaign_id}                   │
│  GET  /meta/roas/predictions/{ad_id}                     │
│  GET  /meta/roas/outcomes/{ad_id}                        │
│  POST /meta/roas/refresh/{campaign_id}                   │
└─────────────────────────────────────────────────────────┘
```

---

## 📐 Mathematical Foundations

### 1. Basic ROAS Formula

```
ROAS = Total Revenue / Total Cost

Example:
  Revenue = $5,000 (from 50 conversions @ $100 each)
  Cost = $1,000 (total ad spend)
  ROAS = 5,000 / 1,000 = 5.0
  
Interpretation: For every $1 spent, you earn $5 in revenue (400% profit)
```

### 2. Bayesian Smoothing

Small sample sizes produce unreliable ROAS estimates. Bayesian smoothing blends observed data with a prior belief:

```
smoothed_ROAS = (w_prior × prior_ROAS) + (w_observed × observed_ROAS)

where:
  w_prior = prior_weight / (prior_weight + sample_size)
  w_observed = sample_size / (prior_weight + sample_size)
  prior_weight = 0.2 (configurable)
  prior_ROAS = 2.0 (industry default)

Example with 10 conversions:
  observed_ROAS = 10.0
  w_prior = 0.2 / (0.2 + 10) ≈ 0.0196
  w_observed = 10 / (0.2 + 10) ≈ 0.9804
  smoothed_ROAS = (0.0196 × 2.0) + (0.9804 × 10.0) ≈ 9.84

Example with 1 conversion:
  observed_ROAS = 10.0
  w_prior = 0.2 / (0.2 + 1) ≈ 0.167
  w_observed = 1 / (0.2 + 1) ≈ 0.833
  smoothed_ROAS = (0.167 × 2.0) + (0.833 × 10.0) ≈ 8.67
  (pulled more towards prior)
```

**Rationale**: New ads with 1-2 conversions may show ROAS of 20.0, but this is likely noise. Smoothing prevents overreacting to small samples.

### 3. Bootstrap Confidence Intervals

Provides statistical confidence in ROAS estimates through resampling:

```
Algorithm:
  1. Take original data (N conversions with values)
  2. Resample with replacement 1000 times
  3. Calculate ROAS for each resample
  4. Sort ROAS values
  5. Extract 2.5th and 97.5th percentiles (95% CI)

Example:
  50 conversions @ $100 each, spend = $1,000
  ROAS = 5.0
  Bootstrap CI = [4.8, 5.2]
  
Interpretation: We're 95% confident true ROAS is between 4.8 and 5.2
```

### 4. Multi-Touch Attribution

Assigns credit to multiple ad touchpoints before conversion:

#### Last-Click Attribution
```
All credit goes to the final ad clicked before conversion.

Example Journey:
  Ad A (Day 1) → Ad B (Day 3) → Ad C (Day 5) → Conversion
  Credits: Ad A = 0%, Ad B = 0%, Ad C = 100%
```

#### First-Click Attribution
```
All credit goes to the first ad clicked.

Example Journey:
  Ad A (Day 1) → Ad B (Day 3) → Ad C (Day 5) → Conversion
  Credits: Ad A = 100%, Ad B = 0%, Ad C = 0%
```

#### Linear Attribution
```
Equal credit across all touchpoints.

Example Journey (3 touchpoints):
  Ad A (Day 1) → Ad B (Day 3) → Ad C (Day 5) → Conversion
  Credits: Ad A = 33.3%, Ad B = 33.3%, Ad C = 33.3%
```

#### Time-Decay Attribution
```
More recent touchpoints get more credit (exponential decay).

Formula:
  weight_i = exp(-λ × days_since_touch_i)
  where λ = ln(2) / half_life (half_life = 7 days)
  
Normalized weights sum to 1.0

Example Journey:
  Ad A (7 days ago) → Ad B (3 days ago) → Ad C (1 day ago)
  Raw weights: [0.5, 0.84, 0.96]
  Normalized: [21.7%, 36.5%, 41.8%]
```

### 5. ROAS Prediction (Exponential Moving Average)

Predicts future ROAS using weighted historical data:

```
EMA Formula:
  ROAS_t+1 = α × ROAS_t + (1 - α) × ROAS_t-1
  where α = 0.3 (smoothing factor)

Example with 3 data points:
  Day 1: ROAS = 3.0
  Day 2: ROAS = 4.0
  Day 3: ROAS = 5.0
  
  Prediction for Day 4:
  ROAS_4 = 0.3 × 5.0 + 0.7 × 4.0 = 4.3
```

### 6. Conversion Probability (Bayesian Inference)

Uses Beta-Binomial conjugate prior for conversion rate estimation:

```
Prior: Beta(α=1, β=1) - uniform prior
Posterior after data: Beta(α + conversions, β + non_conversions)

Mean (conversion rate) = (α + conversions) / (α + β + total_clicks)

Example:
  100 clicks, 10 conversions
  Posterior = Beta(1+10, 1+90) = Beta(11, 91)
  Mean = 11 / (11 + 91) = 0.108 (10.8% conversion rate)
  
  95% Credible Interval: [0.054, 0.185]
  Interpretation: We're 95% sure true CR is between 5.4% and 18.5%
```

### 7. Expected Value Calculation

Estimates profit per click:

```
Expected_Value = (Conversion_Probability × AOV) - CPC

where:
  AOV = Average Order Value (revenue per conversion)
  CPC = Cost Per Click

Example:
  Conversion_Probability = 0.10 (10%)
  AOV = $100
  CPC = $5
  
  Expected_Revenue = 0.10 × $100 = $10
  Expected_Value = $10 - $5 = $5 profit per click
  
  Breakeven_Rate = CPC / AOV = $5 / $100 = 5%
  (Need >5% CR to be profitable)
```

---

## 🎯 Performance Tiers

The optimizer classifies ads into performance tiers:

| Tier | ROAS Range | Conversion Rate | Action |
|------|------------|-----------------|--------|
| **Excellent** | ≥ 5.0 | ≥ 5% | Scale up +50-100% |
| **Good** | 3.0 - 4.99 | 3-5% | Scale up +25-50% |
| **Average** | 2.0 - 2.99 | 2-3% | Monitor |
| **Poor** | 1.0 - 1.99 | 1-2% | Scale down -30% |
| **Failing** | < 1.0 | < 1% | Pause |

---

## 🔧 Optimization Algorithms

### 1. Scale-Up Detection

Identifies high-performing ads ready for increased budget:

```
Criteria:
  • ROAS ≥ 3.0
  • Confidence Score ≥ 0.6
  • Sample Size ≥ 100 impressions
  • Not flagged as outlier

Budget Increase:
  • ROAS ≥ 5.0: +100%
  • ROAS ≥ 4.0: +75%
  • ROAS ≥ 3.5: +50%
  • ROAS ≥ 3.0: +25%
```

### 2. Scale-Down Detection

Identifies underperformers:

```
Criteria:
  • ROAS ≤ 1.5

Action:
  • ROAS < 0.8: Pause (stop spending)
  • ROAS 0.8-1.5: Scale down -30%
```

### 3. Winner/Loser Classification

Median-based statistical classification:

```
Algorithm:
  1. Calculate median ROAS across all ads
  2. Winners: ROAS ≥ 1.5 × median
  3. Losers: ROAS ≤ 0.5 × median
  
Example with 5 ads:
  ROAS = [1.0, 2.0, 3.0, 4.0, 8.0]
  Median = 3.0
  Winners: ROAS ≥ 4.5 → Ads with ROAS = [8.0]
  Losers: ROAS ≤ 1.5 → Ads with ROAS = [1.0]
```

### 4. Budget Reallocation

Proportional allocation based on performance:

```
Formula:
  weight_i = ROAS_i × confidence_i
  
  Adjustments:
    • Poor performers (ROAS < 2.0): weight × 0.5
    • Failing (ROAS < 1.0): weight = 0
  
  allocation_i = (weight_i / Σ weights) × total_budget

Example with 3 ads:
  Ad A: ROAS=5.0, confidence=0.9 → weight = 4.5
  Ad B: ROAS=3.0, confidence=0.7 → weight = 2.1
  Ad C: ROAS=2.0, confidence=0.5 → weight = 1.0
  
  Total weight = 7.6
  Total budget = $1,000
  
  Ad A: (4.5/7.6) × $1,000 = $592
  Ad B: (2.1/7.6) × $1,000 = $276
  Ad C: (1.0/7.6) × $1,000 = $132
```

---

## 🚀 API Endpoints

### 1. GET /meta/roas/summary/{campaign_id}

Get comprehensive ROAS metrics for a campaign.

**Authentication**: Requires `admin` or `manager` role.

**Query Parameters**:
- `date_start` (optional): Filter start date (ISO 8601)
- `date_end` (optional): Filter end date (ISO 8601)
- `group_by` (optional): `campaign`, `adset`, or `ad` (default: `campaign`)

**Response Example**:
```json
{
  "campaign_id": "123e4567-e89b-12d3-a456-426614174000",
  "date_start": "2024-01-01T00:00:00Z",
  "date_end": "2024-01-31T23:59:59Z",
  "impressions": 100000,
  "clicks": 5000,
  "conversions": 250,
  "spend": 5000.0,
  "revenue": 25000.0,
  "actual_roas": 5.0,
  "smoothed_roas": 4.95,
  "predicted_roas": 5.2,
  "confidence_score": 0.92,
  "confidence_interval_low": 4.7,
  "confidence_interval_high": 5.3,
  "performance_tier": "excellent",
  "recommendation": "scale_up",
  "recommended_budget_change_pct": 50.0,
  "blended_ctr": 0.05,
  "blended_cpc": 1.0,
  "blended_cpm": 50.0,
  "session_quality_score": 85.0,
  "user_retention_probability": 0.35,
  "lifetime_value_estimate": 500.0
}
```

### 2. GET /meta/roas/predictions/{ad_id}

Get ROAS predictions and profitability analysis for an ad.

**Authentication**: Requires `admin` or `manager` role.

**Response Example**:
```json
{
  "ad_id": "456e7890-e89b-12d3-a456-426614174001",
  "predicted_roas": 4.8,
  "confidence": 0.85,
  "conversion_probability": 0.08,
  "conversion_probability_low": 0.06,
  "conversion_probability_high": 0.10,
  "expected_value": 3.0,
  "expected_revenue": 8.0,
  "average_cpc": 5.0,
  "breakeven_conversion_rate": 0.05,
  "is_profitable": true
}
```

### 3. GET /meta/roas/outcomes/{ad_id}

Get pixel outcome events for an ad (conversions, purchases, leads).

**Authentication**: Requires `admin` or `manager` role.

**Query Parameters**:
- `date_start` (optional): Filter start date
- `date_end` (optional): Filter end date
- `limit` (optional): Max results (default: 100, max: 1000)

**Response Example**:
```json
[
  {
    "pixel_id": "pixel_12345",
    "event_name": "Purchase",
    "conversion_type": "purchase",
    "value_usd": 100.0,
    "currency": "USD",
    "attribution_model": "time_decay",
    "attribution_weight": 0.42,
    "confidence_score": 0.95,
    "session_duration_seconds": 320,
    "utm_source": "facebook",
    "utm_medium": "cpc",
    "utm_campaign": "spring_sale",
    "device_type": "mobile",
    "country": "US",
    "event_timestamp": "2024-01-15T14:30:00Z"
  }
]
```

### 4. POST /meta/roas/refresh/{campaign_id}

Recalculate ROAS metrics for a campaign (useful after new pixel data arrives).

**Authentication**: Requires `admin` role.

**Request Body**:
```json
{
  "date_start": "2024-01-01T00:00:00Z",
  "date_end": "2024-01-31T23:59:59Z",
  "recalculate_all": false
}
```

**Response Example**:
```json
{
  "success": true,
  "metrics_calculated": 15,
  "errors": [],
  "calculation_time_seconds": 2.3
}
```

---

## 📦 Database Schema

### MetaPixelOutcomeModel

Tracks individual pixel events from Meta Pixel:

```python
{
  "pixel_id": str,                    # Unique pixel event ID
  "campaign_id": UUID,                # Foreign key to campaign
  "adset_id": UUID,                   # Foreign key to adset
  "ad_id": UUID,                      # Foreign key to ad
  "event_name": str,                  # "Purchase", "Lead", "AddToCart"
  "conversion_type": str,             # Normalized type
  "value_usd": Decimal,               # Conversion value
  "currency": str,                    # Original currency
  "session_duration_seconds": int,    # Time on site
  "landing_path": str,                # Landing page URL path
  "utm_source": str,                  # e.g., "facebook"
  "utm_medium": str,                  # e.g., "cpc"
  "utm_campaign": str,                # Campaign tracking
  "utm_content": str,                 # Ad creative tracking
  "utm_term": str,                    # Keyword tracking
  "attribution_model": str,           # "last_click", "linear", etc.
  "attribution_weight": float,        # 0.0 - 1.0
  "confidence_score": float,          # Statistical confidence
  "device_type": str,                 # "mobile", "desktop", "tablet"
  "platform": str,                    # "ios", "android", "web"
  "country": str,                     # ISO country code
  "city": str,                        # City name
  "event_timestamp": datetime,        # When event occurred
  "click_timestamp": datetime,        # When ad was clicked
  "time_to_conversion_seconds": int   # Event - Click time
}
```

### MetaConversionEventModel

Daily aggregated conversion metrics:

```python
{
  "campaign_id": UUID,
  "adset_id": UUID,
  "ad_id": UUID,
  "date": date,                       # Aggregation date
  "total_conversions": int,
  "total_revenue_usd": Decimal,
  "total_cost_usd": Decimal,
  "purchases_count": int,
  "leads_count": int,
  "add_to_carts_count": int,
  "view_contents_count": int,
  "conversion_rate": float,           # conversions / clicks
  "cost_per_conversion": Decimal,
  "roas": float,                      # revenue / cost
  "average_order_value": Decimal,
  "average_session_duration": int,
  "bounce_rate": float
}
```

### MetaROASMetricsModel

Advanced ROAS analytics with predictions:

```python
{
  "campaign_id": UUID,
  "adset_id": UUID,
  "ad_id": UUID,
  "date": date,
  "actual_roas": float,               # Raw ROAS
  "predicted_roas": float,            # EMA prediction
  "blended_roas": float,              # Combined platform + pixel
  "confidence_score": float,          # 0.0 - 1.0
  "confidence_interval_low": float,   # Bootstrap CI lower
  "confidence_interval_high": float,  # Bootstrap CI upper
  "sample_size": int,                 # Number of data points
  "prior_roas": float,                # Bayesian prior
  "posterior_roas": float,            # After Bayesian update
  "smoothing_factor": float,          # Alpha for EMA
  "is_outlier": bool,                 # Flagged as unusual
  "outlier_reason": str,              # Explanation if outlier
  "performance_tier": str,            # "excellent", "good", etc.
  "recommendation": str,              # "scale_up", "monitor", etc.
  "recommended_budget_change_pct": float,
  "session_quality_score": float,     # 0-100
  "user_retention_probability": float,# 0-1
  "lifetime_value_estimate": Decimal,
  "blended_ctr": float,
  "blended_cpc": Decimal,
  "blended_cpm": Decimal
}
```

---

## 🧪 Testing

Run the comprehensive test suite (12 tests):

```bash
cd /workspaces/stakazo/backend
PYTHONPATH=/workspaces/stakazo/backend python -m pytest tests/test_roas_engine.py -v
```

**Test Coverage**:
1. ✅ `test_roas_formula` - Basic ROAS = Revenue / Cost
2. ✅ `test_bayesian_smoothing` - Prior weighting for small samples
3. ✅ `test_prediction_flow` - EMA-based predictions
4. ✅ `test_optimizer_scaling` - Scale-up recommendations
5. ✅ `test_endpoint_responses` - Pydantic model validation
6. ✅ `test_outcome_models` - Database model structure
7. ✅ `test_outlier_detection` - Extreme value detection
8. ✅ `test_value_attribution` - Multi-touch attribution
9. ✅ `test_conversion_probability` - Bayesian inference
10. ✅ `test_expected_value_calculation` - Profitability analysis
11. ✅ `test_budget_reallocation` - Proportional allocation
12. ✅ `test_confidence_intervals` - Bootstrap CI calculation

**Result**: 12/12 tests passing ✅

---

## 🔗 Integration with Other Components

### PASO 10.3 (Meta Ads Orchestrator)

```python
# After campaign creation in orchestrator
from app.meta_ads_orchestrator.roas_integration import ROASInsightsIntegration

orchestrator = MetaAdsOrchestrator(...)
campaign = await orchestrator.orchestrate_campaign(...)

# Initialize ROAS tracking
integration = ROASInsightsIntegration(session)
await integration.calculate_blended_metrics(
    campaign_id=campaign.campaign_id,
    date_start=datetime.utcnow() - timedelta(days=1),
    date_end=datetime.utcnow(),
)
```

### PASO 10.4 (A/B Testing Engine)

```python
# Use ROAS metrics in winner selection
from app.meta_ads_orchestrator.roas_engine import ROASCalculator

calculator = ROASCalculator(session)

# Compare variants by ROAS with confidence
variant_a_roas = await calculator.calculate_roas(
    campaign_id=variant_a.campaign_id,
    # ...
)
variant_b_roas = await calculator.calculate_roas(
    campaign_id=variant_b.campaign_id,
    # ...
)

# Winner if:
#   1. Higher ROAS
#   2. Confidence intervals don't overlap
#   3. Statistical significance (p < 0.05)
```

### PASO 10.6 (Future - Automated Orchestrator)

```python
# Daily optimization job
from app.meta_ads_orchestrator.roas_optimizer import ROASOptimizer

optimizer = ROASOptimizer(session)
plan = await optimizer.compute_daily_optimization_plan(
    campaign_id=campaign_id,
    total_budget=daily_budget,
)

# Apply recommendations automatically
for action in plan["action_items"]:
    if action["action"] == "scale_up":
        await update_ad_budget(action["ad_id"], action["budget_change"])
    elif action["action"] == "pause":
        await pause_ad(action["ad_id"])
```

---

## ⚠️ Edge Cases & Limitations

### 1. Zero Conversions

```python
# ROAS = 0 / spend = 0.0 (not undefined)
# Bayesian smoothing pulls towards prior (2.0)
# Confidence score = 0.0 (no data)
# Recommendation = "test" (gather more data)
```

### 2. Very High ROAS (>50)

```python
# Flagged as outlier
# Possible causes:
#   - Attribution window mismatch
#   - Duplicate conversions
#   - Very low spend (<$10)
# Action: Manual review required
```

### 3. Negative ROAS

```python
# Can occur with refunds/chargebacks
# Flagged as outlier
# Recommendation = "pause"
```

### 4. Small Sample Size (<30)

```python
# Bayesian smoothing heavily applied
# Confidence interval very wide
# Recommendation = "monitor" (not "scale_up" yet)
```

### 5. Attribution Window

```python
# Default: 7-day click, 1-day view
# Conversions may be attributed to wrong ad if:
#   - User clicks multiple ads
#   - Uses multiple devices
# Solution: Use time_decay attribution for multi-touch
```

---

## 📈 Usage Examples

### Example 1: Get Campaign ROAS Summary

```bash
curl -X GET "http://localhost:8000/meta/roas/summary/123e4567-e89b-12d3-a456-426614174000?date_start=2024-01-01&date_end=2024-01-31" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json"
```

### Example 2: Check if Ad is Profitable

```python
from app.meta_ads_orchestrator.roas_engine import PredictionEngine

engine = PredictionEngine(session)
ev = await engine.calculate_expected_value(
    ad_id=ad_id,
    date_start=datetime.utcnow() - timedelta(days=30),
    date_end=datetime.utcnow(),
)

if ev["is_profitable"]:
    print(f"✅ Profitable! Expected value: ${ev['expected_value']:.2f} per click")
else:
    print(f"❌ Not profitable. Need CR > {ev['breakeven_conversion_rate']*100:.1f}%")
```

### Example 3: Get Optimization Recommendations

```python
from app.meta_ads_orchestrator.roas_optimizer import ROASOptimizer

optimizer = ROASOptimizer(session)

# Detect winners
winners = await optimizer.detect_winners_losers(
    campaign_id=campaign_id,
    lookback_days=30,
)

print(f"🏆 Winners ({len(winners['winners'])})")
for ad in winners["winners"]:
    print(f"  Ad {ad.ad_id}: ROAS = {ad.actual_roas:.2f}")

print(f"⚠️  Losers ({len(winners['losers'])})")
for ad in winners["losers"]:
    print(f"  Ad {ad.ad_id}: ROAS = {ad.actual_roas:.2f}")
```

---

## 🎛️ Configuration

Key parameters in `roas_engine.py`:

```python
# ROASCalculator
MIN_SAMPLE_SIZE = 30           # Minimum conversions for reliable ROAS
OUTLIER_THRESHOLD = 3.0        # Z-score for outlier detection
BAYESIAN_PRIOR_WEIGHT = 0.2    # Weight given to prior belief
DEFAULT_PRIOR_ROAS = 2.0       # Industry default ROAS

# PredictionEngine  
EMA_ALPHA = 0.3                # Smoothing factor for predictions
CONFIDENCE_LEVEL = 0.95        # For confidence intervals

# AttributionEngine
TIME_DECAY_HALFLIFE = 7        # Days for half-life in time decay
```

Key parameters in `roas_optimizer.py`:

```python
# Optimization thresholds
SCALE_UP_ROAS_THRESHOLD = 3.0
SCALE_DOWN_ROAS_THRESHOLD = 1.5
PAUSE_ROAS_THRESHOLD = 0.8
MIN_SAMPLE_SIZE = 100
CONFIDENCE_THRESHOLD = 0.6

# Budget change ranges
BUDGET_INCREASE_EXCELLENT = 100  # % for ROAS ≥ 5.0
BUDGET_INCREASE_GOOD = 50        # % for ROAS ≥ 3.5
BUDGET_DECREASE = -30            # % for poor performers
```

---

## 📚 References

- **Bayesian Statistics**: *Bayesian Data Analysis* by Gelman et al.
- **Bootstrap Methods**: *An Introduction to the Bootstrap* by Efron & Tibshirani
- **Attribution Models**: Google Analytics Attribution Documentation
- **ROAS Optimization**: Facebook Ads Best Practices Guide

---

## 🔐 Security

- All endpoints require authentication (JWT tokens)
- RBAC enforcement: `admin` or `manager` role required
- Rate limiting: 100 requests/minute per user
- Data isolation: Users only see their organization's data

---

## 🚀 Deployment

1. **Database Migration**:
```bash
alembic revision --autogenerate -m "Add ROAS Engine models"
alembic upgrade head
```

2. **Environment Variables**:
```bash
# No additional env vars needed - uses existing database config
```

3. **Start Server**:
```bash
cd /workspaces/stakazo/backend
uvicorn main:app --host 0.0.0.0 --port 8000
```

4. **Verify Endpoints**:
```bash
curl http://localhost:8000/docs
# Navigate to /meta/roas/* endpoints
```

---

## 📞 Support

For questions or issues:
- **Team**: Meta Ads Engineering
- **Slack**: #meta-ads-roas
- **Docs**: https://docs.internal.com/roas-engine
- **Code**: `/backend/app/meta_ads_orchestrator/roas_*`

---

## ✅ Completion Status

- ✅ Database Models (3 models, 250 lines)
- ✅ ROAS Engine Core (550 lines)
- ✅ Integration Layer (400 lines)
- ✅ REST API (450 lines)
- ✅ Optimizer (500 lines)
- ✅ Tests (12/12 passing, 550 lines)
- ✅ Documentation (this file)

**Total**: 2,700+ lines of production code

**PASO 10.5: COMPLETE** ✅
