# Meta Creative Analyzer (PASO 10.15)

## Objetivo
Sistema autónomo que analiza creativos, detecta fatiga, genera variantes y ofrece sugerencias automáticas.

## Componentes

### 1. Creative Intelligence Core
- **Scoring unificado** (0-100):
  - Performance (40%): CTR, CVR, ROAS
  - Engagement (30%): Engagement rate, clicks
  - Completion (20%): Video completion rates
  - Efficiency (10%): CPC, CPM

### 2. Fatigue Detector
- **Detección**: Drop ≥30% en CTR/CVR vs baseline
- **Niveles**: healthy, mild, moderate, severe, critical
- **Score**: 0-100 (combinado con días activos, impressions)

### 3. Variant Generator
- **Cambios**: copy, title, thumbnail, fragment_order
- **Estrategias**: conservative, balanced, aggressive
- **Output**: 5-10 variantes con estimated improvement

### 4. Recombination Engine
- Extrae mejores fragmentos (intro, body, cta)
- Recombina para generar nuevas variantes

## API Endpoints

- `POST /meta/creative/analyze/{creative_id}` - Analizar creative
- `GET /meta/creative/health/{creative_id}` - Health status
- `POST /meta/creative/recombine/{creative_id}` - Recombinar variantes
- `POST /meta/creative/refresh-all` - Refresh fatigados
- `GET /meta/creative/recommendations` - Obtener recomendaciones

## Integraciones
- PASO 10.5 (ROAS Engine)
- PASO 10.11 (Full Cycle)
- PASO 10.12 (Targeting)
- PASO 10.14 (RT Engine)

**Versión:** 1.0.0 | **Modo:** STUB funcional, LIVE TODOs preparados
