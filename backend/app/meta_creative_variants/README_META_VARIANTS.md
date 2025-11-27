**# Meta Ads Creative Variants Engine (PASO 10.10)

## 🎯 Objetivo

El **Creative Variants Engine** genera automáticamente múltiples variantes creativas para campañas de Meta Ads mediante combinaciones inteligentes de video, texto y thumbnails. Diseñado para maximizar el A/B testing y optimización de anuncios.

## 📋 Índice

1. [Arquitectura](#arquitectura)
2. [Componentes](#componentes)
3. [Flujo Completo](#flujo-completo)
4. [Ejemplos de Uso](#ejemplos-de-uso)
5. [API Endpoints](#api-endpoints)
6. [Modelos de Datos](#modelos-de-datos)
7. [Configuración](#configuración)
8. [Testing](#testing)
9. [Modo STUB vs LIVE](#modo-stub-vs-live)
10. [Limitaciones y TODOs](#limitaciones-y-todos)

---

## Arquitectura

```
┌─────────────────────────────────────────────────────────────┐
│          Meta Ads Creative Variants Engine                   │
│                    (PASO 10.10)                              │
└─────────────────────────────────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        ▼                  ▼                  ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  Extractor   │→→│  Generator   │→→│   Uploader   │
│              │  │              │  │              │
│  - Clips     │  │  - Video 3-7 │  │  - Meta API  │
│  - Textos    │  │  - Texto 3-10│  │  - Creative  │
│  - Metadata  │  │  - Thumb 3-6 │  │  - Ad        │
└──────────────┘  └──────────────┘  └──────────────┘
        │                  │                  │
        └──────────────────┼──────────────────┘
                           ▼
                  ┌────────────────┐
                  │  Engine Core   │
                  │                │
                  │  5-20 Variants │
                  └────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        ▼                  ▼                  ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  PostgreSQL  │  │  Meta Ads    │  │  Scheduler   │
│   Database   │  │     API      │  │  (cada 6h)   │
└──────────────┘  └──────────────┘  └──────────────┘
```

---

## Componentes

### 1. **Extractor** (`extractor.py`)

Extrae material creativo desde clips existentes.

**Funciones:**
- `extract_from_clip(clip_id)` → Material completo
- `extract_video_fragments(clip_id, count)` → Fragmentos temporales
- `extract_text_templates(clip_id, count)` → Plantillas de texto
- `extract_thumbnail_points(clip_id, count)` → Timestamps óptimos

**Output:**
```python
{
    "clip_metadata": {...},
    "video_asset": {"url": "...", "duration": 30.0},
    "text_content": {"title": "...", "description": "..."},
    "keywords": ["tecnología", "innovación"],
    "hashtags": ["#tech", "#innovation"],
    "scenes": [{"start": 0.0, "end": 10.0, ...}]
}
```

### 2. **Generator** (`generator.py`)

Genera variantes de cada componente.

**Video Variants (3-7):**
- Fragmentos de distintas duraciones (6s, 10s, 15s, full)
- Crop ratios: 1:1, 9:16, 4:5, 16:9
- Speed: 0.9x, 1.0x, 1.1x
- Mute on/off
- Subtítulos on/off

**Text Variants (3-10):**
- Plantillas con emojis, urgencia, beneficios
- Headlines (max 40 chars)
- Primary text (max 125 chars)
- CTA types: learn_more, shop_now, sign_up, etc.

**Thumbnail Variants (3-6):**
- Freeze frames en momentos clave
- Overlays de texto
- Crop ratios matching con video

**Permutación:**
```
video_variants × text_variants × thumbnail_variants
    ↓
Selección inteligente de Top N (5-20)
Prioridad: crop_ratio matching, formato vertical, subtítulos
```

### 3. **Uploader** (`uploader.py`)

Sube creatives a Meta Ads API.

**Proceso:**
1. Upload video → `video_id`
2. Upload thumbnail → `thumbnail_url`
3. Create creative → `creative_id`
4. Create ad → `ad_id`

**Modos:**
- **STUB**: Genera IDs ficticios (testing)
- **LIVE**: Upload real a Meta Ads API

### 4. **Engine** (`engine.py`)

Motor completo de generación.

**Workflow:**
```
1. extract_from_clip()
2. generate_video_variants()
3. generate_text_variants()
4. generate_thumbnail_variants()
5. generate_creative_combinations()
6. persist_variants() [DB]
7. upload_creative() [Meta API] (opcional)
```

### 5. **Scheduler** (`scheduler.py`)

Background task cada **6 horas**.

**Lógica:**
- Detecta campañas activas con < X creatives
- Genera nuevas variantes automáticamente
- Sube si presupuesto > threshold

### 6. **Router** (`router.py`)

REST API con 6 endpoints.

---

## Flujo Completo

### Generación Manual

```bash
# 1. Generar 10 variantes desde clip
curl -X POST "http://localhost:8000/meta/creative-variants/generate/clip_123" \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "clip_id": "clip_123",
    "campaign_id": "23847656789012340",
    "num_variants": 10,
    "video_variants_count": 5,
    "text_variants_count": 5,
    "thumbnail_variants_count": 4,
    "auto_upload": false,
    "dry_run": false
  }'

# Response:
{
  "success": true,
  "total_variants": 10,
  "variants": [...],
  "video_variants_generated": 5,
  "text_variants_generated": 5,
  "thumbnail_variants_generated": 4,
  "generation_time_seconds": 2.34
}
```

### Upload Individual

```bash
# 2. Subir variante específica
curl -X POST "http://localhost:8000/meta/creative-variants/upload/variant_abc123" \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "variant_id": "variant_abc123",
    "campaign_id": "23847656789012340",
    "adset_id": "23847656789012345",
    "ad_account_id": "act_123456789"
  }'

# Response:
{
  "success": true,
  "variant_id": "variant_abc123",
  "meta_creative_id": "23847656789012400",
  "meta_ad_id": "23847656789012401"
}
```

### Upload Masivo

```bash
# 3. Subir 5-20 variantes de golpe
curl -X POST "http://localhost:8000/meta/creative-variants/bulk-upload/23847656789012340" \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "campaign_id": "23847656789012340",
    "adset_id": "23847656789012345",
    "ad_account_id": "act_123456789",
    "variant_ids": ["var_1", "var_2", "var_3", ...],
    "max_parallel": 3
  }'

# Response:
{
  "success": true,
  "uploaded_count": 18,
  "failed_count": 2,
  "results": [...],
  "upload_time_seconds": 12.45
}
```

---

## API Endpoints

| Método | Ruta | Rol | Descripción |
|--------|------|-----|-------------|
| POST | `/generate/{clip_id}` | admin, manager | Genera variantes automáticas |
| GET | `/list/{campaign_id}` | admin, manager, operator | Lista variantes de campaña |
| POST | `/upload/{variant_id}` | admin, manager | Sube variante individual |
| POST | `/bulk-upload/{campaign_id}` | admin | Sube 5-20 variantes |
| POST | `/regenerate/{variant_id}` | admin, manager | Regenera componentes |
| DELETE | `/archive/{variant_id}` | admin | Marca como archivada |
| GET | `/health` | público | Health check |

---

## Modelos de Datos

### SQLAlchemy Models

**MetaCreativeVariantModel**
- `variant_id` (PK)
- `campaign_id`, `adset_id`
- `video_variant_id` (FK)
- `text_variant_id` (FK)
- `thumbnail_variant_id` (FK)
- `status`: draft, generated, uploaded, active, paused, archived
- `meta_creative_id`, `meta_ad_id`
- `impressions`, `clicks`, `spend`, `ctr`

**MetaCreativeVariantVideoModel**
- `variant_id` (PK)
- `clip_id`
- `start_time`, `end_time`, `duration`
- `crop_ratio`, `speed`, `muted`, `subtitles_enabled`
- `file_url`

**MetaCreativeVariantTextModel**
- `variant_id` (PK)
- `headline`, `primary_text`, `description`
- `cta_type`, `cta_text`
- `language`, `keywords`, `hashtags`

**MetaCreativeVariantThumbnailModel**
- `variant_id` (PK)
- `source_type`: freeze_frame, extract_frame, overlay
- `timestamp`, `has_text_overlay`, `overlay_text`
- `crop_ratio`, `file_url`

### Pydantic Schemas

Ver `schemas.py` para tipos completos:
- `VideoVariant`
- `TextVariant`
- `ThumbnailVariant`
- `CreativeVariant`
- `GenerateVariantsRequest/Response`
- `UploadVariantRequest/Response`
- `BulkUploadRequest/Response`

---

## Configuración

### Variables de Entorno

```bash
# Meta API Mode
META_API_MODE=stub  # stub | live

# Creative Variants
CREATIVE_VARIANTS_ENABLED=true
CREATIVE_VARIANTS_SCHEDULER_INTERVAL_HOURS=6
CREATIVE_VARIANTS_MAX_VARIANTS=20
CREATIVE_VARIANTS_MIN_VARIANTS=5

# Meta Ad Account
META_DEFAULT_AD_ACCOUNT_ID=act_123456789
```

### Activación en `main.py`

```python
from app.meta_creative_variants.router import router as creative_variants_router

app.include_router(
    creative_variants_router,
    prefix="/meta/creative-variants",
    tags=["meta_creative_variants"]
)
```

---

## Testing

### Tests Incluidos

`test_meta_creative_variants.py` (12 tests):

1. `test_generate_video_variants` ✅
2. `test_generate_text_variants` ✅
3. `test_generate_thumbnail_variants` ✅
4. `test_generate_creative_combinations` ✅
5. `test_upload_creative_stub` ✅
6. `test_upload_creative_live` ⏳
7. `test_bulk_upload` ✅
8. `test_generate_variants_endpoint` ✅
9. `test_list_variants_endpoint` ✅
10. `test_upload_endpoint` ✅
11. `test_regenerate_endpoint` ✅
12. `test_archive_endpoint` ✅

### Ejecutar Tests

```bash
cd backend
pytest tests/test_meta_creative_variants.py -v
```

---

## Modo STUB vs LIVE

### STUB Mode (Testing)

**Características:**
- No hace llamadas reales a Meta API
- Genera IDs ficticios
- No crea archivos de video/thumbnail
- Material extraído es sintético

**Activación:**
```bash
export META_API_MODE=stub
```

### LIVE Mode (Producción)

**Requisitos:**
- ✅ Meta API Access Token válido
- ✅ Ad Account ID configurado
- ✅ Permisos: `ads_management`, `ads_read`
- ✅ Storage (S3/GCS) para videos/thumbnails

**Activación:**
```bash
export META_API_MODE=live
export META_ACCESS_TOKEN=your_token_here
export META_DEFAULT_AD_ACCOUNT_ID=act_123456789
```

**Proceso LIVE:**
1. Extract: Lee clips reales desde DB
2. Generate: Procesa videos con FFmpeg
3. Upload: Sube a storage (S3)
4. Create Creative: Llama a Meta Ads API
5. Persist: Guarda en DB con IDs reales

---

## Limitaciones y TODOs

### Limitaciones Actuales

❌ **Scene Detection:** Usa división simple en 3 escenas (no AI real)  
❌ **Text Generation:** Plantillas fijas (no LLM)  
❌ **Video Processing:** No hay edición real (FFmpeg pendiente)  
❌ **Thumbnail Extraction:** No hay extracción de frames real  
❌ **Performance Tracking:** No se actualizan métricas desde Insights

### TODOs para Modo LIVE

**Alta Prioridad:**
- [ ] Integrar FFmpeg para edición de video real
- [ ] Implementar extracción de frames para thumbnails
- [ ] Conectar con S3/GCS para storage
- [ ] Integrar AI para scene detection
- [ ] Conectar con LLM para text generation

**Media Prioridad:**
- [ ] Background sync de métricas desde Insights
- [ ] Dashboard UI para preview de variantes
- [ ] A/B testing automático entre variantes
- [ ] Alertas cuando variante tiene bajo CTR

**Baja Prioridad:**
- [ ] Multi-idioma automático
- [ ] Generación de captions con IA
- [ ] Soporte para TikTok/YouTube Ads

---

## Integraciones

Este módulo se integra con:

- **Meta Ads API Client** (PASO 10.2) → Upload de creatives
- **Insights Collector** (PASO 10.7) → Métricas de performance
- **ROAS Engine** (PASO 10.5) → Validación de ROI
- **A/B Tester** (PASO 10.4) → Testing de variantes
- **Orchestrator** (PASO 10.3) → Flujos automatizados

---

## Diagramas

### Flujo de Generación

```
Clip Input
    │
    ▼
Extractor
    │
    ├─→ Video Fragments (5)
    ├─→ Text Templates (5)
    └─→ Thumbnail Points (4)
    │
    ▼
Generator
    │
    ├─→ Video Variants (5) × Crop × Speed × Mute
    ├─→ Text Variants (5) × CTA × Language
    └─→ Thumbnail Variants (4) × Overlay × Crop
    │
    ▼
Permutation Engine
    │
    └─→ 5×5×4 = 100 combinations
         │
         └─→ Select Top 10 (score-based)
              │
              ▼
         10 Creative Variants
              │
              ├─→ Persist to DB
              │
              └─→ Upload to Meta API (optional)
```

---

## Contacto y Soporte

**Equipo:** AI Platform Team  
**Slack:** #meta-ads-automation  
**Docs:** https://docs.stakazo.com/creative-variants

---

**Versión:** 1.0.0  
**Fecha:** 2025-11-26  
**Autor:** PASO 10.10 Implementation
