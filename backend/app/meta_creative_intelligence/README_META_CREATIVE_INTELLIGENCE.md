# Meta Creative Intelligence & Lifecycle System (PASO 10.13)

## 🎯 Objetivo

Sistema completo de **inteligencia creativa autónoma** que integra 5 subsistemas críticos para el análisis, optimización y gestión del ciclo de vida de creatividades publicitarias.

## 📋 Índice

1. [Arquitectura](#arquitectura)
2. [Subsistemas](#subsistemas)
3. [API Endpoints](#api-endpoints)
4. [Modo STUB vs LIVE](#modo-stub-vs-live)
5. [Integración](#integración)
6. [Ejemplos](#ejemplos)
7. [Troubleshooting](#troubleshooting)

---

## Arquitectura

```
┌─────────────────────────────────────────────────────────────────┐
│       Meta Creative Intelligence & Lifecycle System              │
│                       (PASO 10.13)                               │
└─────────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌───────────────┐    ┌──────────────┐    ┌──────────────────┐
│  1. Visual    │    │ 2. Variant   │    │ 3. Winner Engine │
│    Analyzer   │    │   Generator  │    │   (ROAS/CTR/CVR) │
│  (YOLO/CV)    │    │ (5-10 vars)  │    │                  │
└───────────────┘    └──────────────┘    └──────────────────┘
        │                     │                     │
        ▼                     ▼                     ▼
┌───────────────┐    ┌──────────────┐
│ 4. Thumbnail  │    │ 5. Lifecycle │
│   Generator   │    │   Manager    │
│ (Auto frames) │    │  (Fatigue)   │
└───────────────┘    └──────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │  PostgreSQL DB   │
                    │   5 Tables       │
                    └──────────────────┘
```

---

## Subsistemas

### 1. Visual Analyzer (Creative Intelligence Layer)

**Objetivo:** Analizar videos con computer vision para extraer insights.

**Capacidades:**
- **Object Detection:** Detecta objetos (persons, cars, phones, etc.)
- **Face Detection:** Detecta rostros + emoción + edad + género
- **Text OCR:** Extrae texto visible en pantalla
- **Visual Scoring:** Score 0-100 basado en:
  - Rostros (30%)
  - Acción/Movimiento (25%)
  - Texto (15%)
  - Color/Vibrancia (15%)
  - Composición (15%)
- **Fragment Extraction:** Identifica fragmentos con alto potencial de engagement

**STUB Mode:** Genera detecciones sintéticas realistas  
**LIVE Mode:** TODO - Integrar YOLO v8+, face_recognition, EasyOCR

### 2. Variant Generator

**Objetivo:** Generar 5-10 variantes automáticas de cada video.

**Transformaciones:**
1. **Reorder Fragments:** Cambia orden de segmentos (hook_first, climax_middle, reversed, best_segments_only)
2. **Subtitles:** Añade subtítulos automáticos (bottom, top, karaoke)
3. **Overlays:** Texto dinámico (CTAs, discounts, urgency, brand)
4. **Music:** Cambia música de fondo (STUB only)
5. **Duration:** Ajusta velocidad o recorta (speed_up, slow_down, trim)

**STUB Mode:** Simula generación  
**LIVE Mode:** TODO - Integrar FFmpeg, Whisper (transcripción)

### 3. Winner Engine (Publication Winner Selection)

**Objetivo:** Seleccionar el creative ganador para Instagram basado en performance real.

**Criterios:**
- **ROAS** (40%): Return on Ad Spend
- **CTR** (25%): Click-Through Rate
- **CVR** (20%): Conversion Rate
- **View Depth** (15%): % de video visto

**Fórmula:**
```
Winner Score = (ROAS_norm * 0.40) + (CTR_norm * 0.25) + 
               (CVR_norm * 0.20) + (ViewDepth * 0.15)

Normalización:
- ROAS: 0-5 → 0-100
- CTR: 0-5% → 0-100
- CVR: 0-8% → 0-100
- ViewDepth: 0-100% → 0-100
```

**Integraciones:**
- ROAS Engine (10.5)
- A/B Testing (10.4)
- Targeting Optimizer (10.12)

**STUB Mode:** Genera métricas sintéticas  
**LIVE Mode:** TODO - Consultar MetaInsightsCollector, ROASEngine

### 4. Thumbnail Generator (Auto-Thumbnailing)

**Objetivo:** Generar thumbnail automático seleccionando el mejor frame.

**Heurísticas:**
- **Rostros:** Máxima prioridad (+30 score)
- **Acción:** Prioridad media (+15 score)
- **Texto:** Prioridad baja (+5 score, penalizar si avoid_text)

**Proceso:**
1. Extraer N candidatos (frames)
2. Evaluar cada frame según heurísticas
3. Seleccionar frame con mayor score
4. Generar URL del thumbnail

**STUB Mode:** Selección sintética  
**LIVE Mode:** TODO - OpenCV frame extraction, face detection

### 5. Lifecycle Manager (Creative Fatigue Detection)

**Objetivo:** Detectar fatiga de creatividades y gestionar renovación automática.

**Fatigue Score (0-100):**
```
Score = (CTR_drop * 40%) + (CVR_drop * 30%) + 
        (Engagement_drop * 20%) + (Frequency_saturation * 10%)

Criterios:
- CTR drop ≥30% vs. baseline → Fatiga
- CVR drop ≥25% vs. baseline → Fatiga
- Frequency ≥5 imp/user → Saturación
- Days active >14 → Mayor riesgo
```

**Estrategias de Renovación:**
1. **generate_variant:** Crear variante del mismo base
2. **replace_entirely:** Reemplazar con creative nuevo
3. **refresh_targeting:** Cambiar targeting sin tocar creative

**STUB Mode:** Simula tendencias de métricas  
**LIVE Mode:** TODO - Consultar MetaInsightsCollector con ventanas temporales

---

## API Endpoints

### POST /meta/creative-intelligence/analyze

Analiza un video con CV.

**Request:**
```json
{
  "video_asset_id": "uuid",
  "mode": "stub",
  "detect_objects": true,
  "detect_faces": true,
  "detect_text": true,
  "extract_fragments": true,
  "max_fragments": 5
}
```

**Response:**
```json
{
  "analysis_id": "uuid",
  "video_asset_id": "uuid",
  "mode": "stub",
  "objects": [
    {"label": "person", "confidence": 0.95, "bbox": [x1, y1, x2, y2], "frame_number": 120}
  ],
  "faces": [
    {"confidence": 0.97, "bbox": [...], "frame_number": 150, "emotion": "happy", "age_range": "18-25"}
  ],
  "texts": [
    {"text": "OFERTA 50%", "confidence": 0.88, "bbox": [...], "frame_number": 200}
  ],
  "scoring": {
    "overall_score": 82.5,
    "face_score": 90.0,
    "action_score": 75.0,
    "text_score": 60.0,
    "color_score": 85.0,
    "composition_score": 80.0,
    "engagement_potential": 85.0
  },
  "fragments": [
    {"start_frame": 30, "end_frame": 90, "duration_seconds": 2.5, "score": 88.0, "reason": "Contains 2 face(s)"}
  ],
  "processing_time_ms": 1250,
  "created_at": "2025-11-27T12:00:00Z"
}
```

### POST /meta/creative-intelligence/generate-variants

Genera variantes de un video.

**Request:**
```json
{
  "video_asset_id": "uuid",
  "analysis_id": "uuid",
  "config": {
    "reorder_fragments": true,
    "add_subtitles": true,
    "add_overlays": true,
    "vary_music": false,
    "vary_duration": true,
    "min_variants": 5,
    "max_variants": 10
  },
  "mode": "stub"
}
```

**Response:**
```json
{
  "generation_id": "uuid",
  "video_asset_id": "uuid",
  "variants": [
    {
      "variant_number": 1,
      "changes": {
        "reorder": {"strategy": "hook_first", "fragments_reordered": 3},
        "subtitles": {"style": "bottom", "language": "es"},
        "overlays": {"total_overlays": 2}
      },
      "duration_seconds": 25.5,
      "estimated_score": 78.5,
      "asset_url": "https://cdn.example.com/variants/uuid/variant_1.mp4"
    }
  ],
  "total_variants": 8,
  "processing_time_ms": 2100,
  "created_at": "2025-11-27T12:05:00Z"
}
```

### POST /meta/creative-intelligence/select-winner

Selecciona el creative ganador.

**Request:**
```json
{
  "campaign_id": "uuid",
  "candidate_asset_ids": ["uuid1", "uuid2", "uuid3"],
  "criteria_weights": {
    "roas": 0.40,
    "ctr": 0.25,
    "cvr": 0.20,
    "view_depth": 0.15
  },
  "min_impressions": 1000
}
```

**Response:**
```json
{
  "selection_id": "uuid",
  "campaign_id": "uuid",
  "winner_asset_id": "uuid1",
  "winner_score": 85.2,
  "runner_up_asset_id": "uuid2",
  "runner_up_score": 78.1,
  "all_scores": {
    "uuid1": 85.2,
    "uuid2": 78.1,
    "uuid3": 72.5
  },
  "reasoning": "Selected as winner with weighted score of 85.2/100. Key strengths: Excellent ROAS of 3.85 (weight: 40%); Strong CTR of 3.52% (weight: 25%); Based on 12,450 impressions, 438 clicks, 85 conversions.",
  "performance_summary": {
    "total_candidates": 3,
    "qualified_candidates": 3,
    "winner_roas": 3.85,
    "winner_ctr": 0.0352,
    "winner_cvr": 0.0194,
    "winner_view_depth": 0.68,
    "winner_impressions": 12450,
    "winner_spend": 124.50,
    "score_margin": 7.1
  },
  "created_at": "2025-11-27T12:10:00Z"
}
```

### POST /meta/creative-intelligence/generate-thumbnail

Genera thumbnail automático.

**Request:**
```json
{
  "video_asset_id": "uuid",
  "analysis_id": "uuid",
  "max_candidates": 5,
  "prefer_faces": true,
  "prefer_action": true,
  "avoid_text": false,
  "mode": "stub"
}
```

**Response:**
```json
{
  "thumbnail_id": "uuid",
  "video_asset_id": "uuid",
  "selected_frame": 145,
  "selected_timestamp": 4.83,
  "thumbnail_url": "https://cdn.example.com/thumbnails/uuid/frame_145.jpg",
  "candidates": [
    {"frame_number": 145, "timestamp_seconds": 4.83, "score": 92.5, "has_face": true, "has_action": true, "has_text": false},
    {"frame_number": 78, "timestamp_seconds": 2.60, "score": 85.0, "has_face": true, "has_action": false, "has_text": false}
  ],
  "reasoning": "Selected frame 145 at 4.8s with score 92.5/100. Features: contains face(s), shows action/movement. Configuration: prioritizing faces, prioritizing action.",
  "created_at": "2025-11-27T12:15:00Z"
}
```

### GET /meta/creative-intelligence/check-fatigue/{creative_id}

Detecta fatiga de un creative.

**Response:**
```json
{
  "creative_id": "uuid",
  "is_fatigued": true,
  "fatigue_score": 72.5,
  "metrics_trend": {
    "days_active": 28,
    "impressions_total": 145000,
    "baseline_ctr": 0.0385,
    "recent_ctr": 0.0252,
    "ctr_drop_pct": 34.5,
    "baseline_cvr": 0.0220,
    "recent_cvr": 0.0168,
    "cvr_drop_pct": 23.6,
    "avg_frequency": 4.8
  },
  "recommendation": "HIGH FATIGUE - Generate new variant or refresh targeting. Performance declining significantly after 28 days.",
  "days_active": 28,
  "impressions_total": 145000
}
```

### POST /meta/creative-intelligence/renew-creative

Renueva un creative fatigado.

**Request:**
```json
{
  "creative_id": "uuid",
  "strategy": "generate_variant",
  "auto_apply": false
}
```

**Response:**
```json
{
  "renewal_id": "uuid",
  "creative_id": "uuid",
  "strategy": "generate_variant",
  "new_creative_id": "uuid_new",
  "actions_taken": [
    "Generated new variant from same base video",
    "Paused fatigued creative",
    "Activated new variant"
  ],
  "success": true,
  "message": "New variant created: uuid_new and automatically applied",
  "created_at": "2025-11-27T12:20:00Z"
}
```

### POST /meta/creative-intelligence/run

Ejecuta orchestrator completo.

**Request:**
```json
{
  "video_asset_ids": ["uuid1", "uuid2"],
  "enable_analysis": true,
  "enable_variants": true,
  "enable_thumbnails": true,
  "enable_lifecycle_check": true,
  "mode": "stub"
}
```

**Response:**
```json
{
  "run_id": "uuid",
  "video_assets_processed": 2,
  "analyses_completed": 2,
  "variants_generated": 16,
  "thumbnails_created": 2,
  "fatigues_detected": 1,
  "duration_ms": 8500,
  "summary": {
    "analysis_results": [...],
    "variant_results": [...],
    "thumbnail_results": [...],
    "lifecycle_results": [...]
  },
  "created_at": "2025-11-27T12:25:00Z"
}
```

### GET /meta/creative-intelligence/health

Health check.

**Response:**
```json
{
  "status": "healthy",
  "subsystems": {
    "visual_analyzer": "ok",
    "variant_generator": "ok",
    "winner_engine": "ok",
    "thumbnail_generator": "ok",
    "lifecycle_manager": "ok"
  },
  "timestamp": "2025-11-27T12:30:00Z"
}
```

---

## Modo STUB vs LIVE

### STUB Mode (Default)

✅ **Completamente funcional** para desarrollo y testing  
✅ Genera datos sintéticos realistas  
✅ Sin dependencias externas (YOLO, FFmpeg, etc.)  
✅ Respuestas rápidas (<2s)  

**Cuándo usar:**
- Development
- Testing
- CI/CD
- Demos
- Staging

### LIVE Mode

⚠️ **En desarrollo** - Requiere integraciones adicionales  

**TODOs pendientes:**
1. **Visual Analyzer LIVE:**
   - Integrar YOLO v8+ (Ultralytics)
   - Integrar face_recognition (dlib)
   - Integrar EasyOCR / Tesseract

2. **Variant Generator LIVE:**
   - Integrar FFmpeg para edición de video
   - Integrar Whisper para transcripción
   - Biblioteca de músicas royalty-free

3. **Winner Engine LIVE:**
   - Consultar MetaInsightsCollector (10.7)
   - Consultar ROASEngine (10.5)
   - Consultar MetaABTestingModel (10.4)

4. **Thumbnail Generator LIVE:**
   - OpenCV para frame extraction
   - face_recognition para detección

5. **Lifecycle Manager LIVE:**
   - Consultar MetaInsightsCollector con ventanas temporales
   - Integrar con MetaFullCycle (10.11) para auto-renewal

---

## Integración

### Con Otros Módulos Meta

```python
# PASO 10.5 - ROAS Engine
from app.meta_ads_orchestrator.roas_engine import ROASEngine

roas_engine = ROASEngine(db)
roas_data = await roas_engine.get_roas_for_asset(asset_id)

# PASO 10.7 - Insights Collector
from app.meta_insights_collector.collector import MetaInsightsCollector

insights_collector = MetaInsightsCollector(mode="live")
insights = await insights_collector.get_insights_for_asset(asset_id)

# PASO 10.11 - Full Cycle
from app.meta_full_cycle.cycle import MetaFullCycleManager

cycle = MetaFullCycleManager()
await cycle.run_cycle(db, triggered_by="creative_intelligence")
```

### Scheduler en main.py

```python
from app.meta_creative_intelligence.scheduler import (
    start_creative_intelligence_scheduler,
    stop_creative_intelligence_scheduler
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    ci_task = await start_creative_intelligence_scheduler(
        interval_hours=12,
        mode="stub"
    )
    
    yield
    
    # Shutdown
    await stop_creative_intelligence_scheduler(ci_task)
```

---

## Ejemplos de Uso

### Flujo Completo

```python
from app.meta_creative_intelligence.orchestrator import MetaCreativeIntelligenceOrchestrator

orchestrator = MetaCreativeIntelligenceOrchestrator(mode="stub")

result = await orchestrator.run(
    db=db,
    video_asset_ids=[video_id_1, video_id_2],
    enable_analysis=True,
    enable_variants=True,
    enable_thumbnails=True,
    enable_lifecycle_check=True,
)

print(f"Processed {result.video_assets_processed} videos")
print(f"Generated {result.variants_generated} variants")
print(f"Detected {result.fatigues_detected} fatigued creatives")
```

### Solo Análisis Visual

```python
from app.meta_creative_intelligence.visual_analyzer import VisualAnalyzer

analyzer = VisualAnalyzer(mode="stub")

result = await analyzer.analyze(
    video_asset_id=video_id,
    detect_objects=True,
    detect_faces=True,
    detect_text=True,
    extract_fragments=True,
)

print(f"Overall score: {result.scoring.overall_score}")
print(f"Found {len(result.faces)} faces")
print(f"Extracted {len(result.fragments)} fragments")
```

---

## Troubleshooting

### Error: "No candidates meet minimum impressions threshold"

**Causa:** Ningún creative tiene suficientes impresiones para análisis  
**Solución:** Reducir `min_impressions` en WinnerSelectionRequest

### Error: "LIVE mode not implemented yet"

**Causa:** Intentando usar LIVE mode sin integraciones  
**Solución:** Usar `mode="stub"` o implementar TODOs pendientes

### Fatigue Score siempre bajo

**Causa:** Métricas sintéticas en STUB mode  
**Solución:** En LIVE mode, conectar con MetaInsightsCollector real

### Variantes con scores similares

**Causa:** Generación sintética en STUB mode  
**Solución:** Normal en STUB - en LIVE, usar análisis real para diferenciar

---

## Monitoreo

### Métricas Clave

| Métrica | Descripción | Umbral |
|---------|-------------|--------|
| Analysis Duration | Tiempo de análisis por video | < 5s (STUB), < 30s (LIVE) |
| Variants Generated | Variantes por video | 5-10 |
| Fatigue Detection Rate | % creatives fatigados | 10-30% |
| Winner Score Margin | Diferencia winner vs runner-up | > 5 puntos |

---

## Roadmap (Fase B - LIVE)

- [ ] Integrar YOLO v8+ para object detection
- [ ] Integrar face_recognition para face detection
- [ ] Integrar EasyOCR para text extraction
- [ ] Integrar FFmpeg para video editing
- [ ] Integrar Whisper para subtitling
- [ ] Conectar con MetaInsightsCollector (10.7)
- [ ] Conectar con ROASEngine (10.5)
- [ ] Auto-renewal integration con FullCycle (10.11)
- [ ] Dashboard UI para resultados
- [ ] Alertas automáticas de fatiga

---

**Versión:** 1.0.0  
**Fecha:** 2025-11-27  
**Autor:** PASO 10.13 Implementation
