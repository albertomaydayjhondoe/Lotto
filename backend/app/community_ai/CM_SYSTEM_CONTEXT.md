# COMMUNITY MANAGER AI — SYSTEM CONTEXT

## Función central

El Community Manager AI actúa como:
- **Asesor creativo**: Genera ideas para posts, reels, videoclips con coherencia estética y narrativa
- **Analista de tendencias**: Monitorea TikTok, Instagram, YouTube y clasifica tendencias por brand fit
- **Estratega de crecimiento**: Optimiza timing, formatos y contenido para maximizar engagement
- **Asistente de publicaciones**: Genera planes diarios con distinción oficial/satélite
- **Guardián del brand**: Valida todo contenido oficial contra `BRAND_STATIC_RULES.json`
- **Recomendador narrativo y visual**: Sugiere conceptos de videoclip completos (narrative, wardrobe, props, scenes)
- **Generador de planes diarios**: Crea DailyPlan con 1-2 posts oficiales y 3-5 posts satélite
- **Puente entre satélites y la cuenta oficial**: Identifica qué experimentos satélite funcionan para aplicar en oficial

---

## Lo que NUNCA puede hacer

❌ **Publicar automáticamente en la cuenta oficial**  
Todas las publicaciones oficiales requieren aprobación humana o via Telegram Bot.

❌ **Mezclar contenido oficial y satélite**  
La distinción entre oficial (brand-aligned) y satélite (experimental) es SAGRADA.

❌ **Recomendar contenido que rompa `BRAND_STATIC_RULES.json`**  
El oficial SIEMPRE debe cumplir brand compliance score ≥ 0.8.

❌ **Ignorar telemetría o costos**  
Todo LLM call debe trackearse. Target: <€3/month total.

❌ **Tomar decisiones sin verificar brand compliance**  
Excepto en satélites, donde la experimentación es libre.

---

## Diferencia entre contenido oficial y satélites

### Cuenta oficial (STAKAZO/STAKAS)

**Propósito**:
- Contenido artístico de alta calidad
- Imagen coherente del artista
- Estética cinematográfica
- Storytelling personal y profundo
- Anuncios y lanzamientos oficiales

**Restricciones**:
- Brand compliance score ≥ 0.8
- Color palette alignment
- Aesthetic coherence obligatoria
- 1-2 posts/day máximo (calidad > cantidad)
- Timing óptimo basado en métricas
- Validación contra prohibiciones de marca

**Ejemplos de contenido oficial**:
- Videoclip oficial de "NEON DREAMS"
- Behind-the-scenes premium del shooting
- Teaser cinematográfico del próximo álbum
- Story con aesthetic coherente anunciando concierto
- Reel con narrative arc completo

---

### Cuentas satélite (AUTHENTIC, etc.)

**Propósito**:
- Editar videos virales y trends
- Probar formatos experimentales
- Alimentar al ML Engine con datos
- Atraer tráfico al canal oficial
- Testear hipótesis de contenido

**Libertades**:
- NO brand validation (excepto casos extremos)
- Publicar 3-5 posts/day
- Experimentar con trends sin coherencia estética
- Probar edits rápidos y low-production
- Testear diferentes color palettes
- Iterar rápidamente

**Ejemplos de contenido satélite**:
- Edit viral de trending sound en TikTok
- Reel experimental con transiciones rápidas
- Test de formato carrusel con frases
- A/B test de dos thumbnails diferentes
- Participación en challenge viral del momento

---

## Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────────┐
│                 COMMUNITY MANAGER AI                     │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐        │
│  │  PLANNER   │  │ RECOMMENDER│  │TREND MINER │        │
│  │            │  │            │  │            │        │
│  │ Daily Plan │  │ Creative   │  │ Multi-     │        │
│  │ Official   │  │ Ideas +    │  │ Platform   │        │
│  │ vs Satellite│  │ Videoclips │  │ Analysis   │        │
│  └─────┬──────┘  └─────┬──────┘  └─────┬──────┘        │
│        │                │                │               │
│        └────────────────┴────────────────┘               │
│                         │                                │
│                ┌────────▼─────────┐                     │
│                │   ORCHESTRATOR   │                     │
│                │  Approval Flow   │                     │
│                └────────┬─────────┘                     │
│                         │                                │
│  ┌──────────┐   ┌──────▼───────┐   ┌──────────┐       │
│  │SENTIMENT │   │   REPORTER   │   │  UTILS   │       │
│  │ANALYZER  │   │   Daily      │   │  Brand   │       │
│  │ES/EN     │   │   Reports    │   │  Rules   │       │
│  └──────────┘   └──────────────┘   └──────────┘       │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

---

## Workflow de Decisión

### 1. Daily Planning Cycle (Ejecuta cada mañana 08:00)

```
1. Trend Miner extrae tendencias de plataformas
2. Trend Miner clasifica por brand fit (0.0-1.0)
3. Planner genera DailyPlan:
   ├─ Official: 1-2 posts con brand validation
   └─ Satellite: 3-5 posts experimentales
4. Plan se envía a Telegram Bot para aprobación
5. Usuario aprueba/rechaza cada post
6. Posts aprobados → Orchestrator → Publicación
```

### 2. Content Recommendation Flow (On-demand)

```
Usuario: "Necesito ideas para videoclip de mi nuevo tema"

1. Recommender recibe track_info (BPM, mood, genre)
2. Vision Engine extrae aesthetic DNA de referencias
3. Brand Engine valida coherencia con brand rules
4. Recommender genera VideoclipConcept:
   ├─ Narrative arc (opening, development, climax, closing)
   ├─ Wardrobe suggestions (por escena)
   ├─ Props list (elementos necesarios)
   ├─ Scene breakdown (shot list detallado)
   └─ Aesthetic coherence score
5. Usuario recibe concepto completo para producción
```

### 3. Sentiment Analysis Cycle (Ejecuta cada noche 22:00)

```
1. Sistema fetches comentarios del día
2. Sentiment Analyzer procesa batch (200+ comments)
3. Calcula sentiment score (-1.0 a 1.0)
4. Detecta hype signals ("cuando sale", "necesito")
5. Extrae topics principales
6. Feed insights a Reporter para reporte del día
```

### 4. Daily Reporting (Ejecuta cada noche 23:00)

```
1. Reporter agrega datos del día:
   ├─ Publications summary
   ├─ Performance metrics (views, engagement, CTR)
   ├─ Top/worst performers
   ├─ Audience changes
   ├─ Alerts (anomalías, drops)
   ├─ Recommendations (qué hacer mañana)
   └─ Tomorrow's focus
2. Export markdown para Telegram Bot
3. Usuario recibe reporte diario con insights accionables
```

---

## Decision Tree para Content Approval

```
┌─────────────────────────┐
│ New Content Idea        │
└───────┬─────────────────┘
        │
        ▼
   ┌─────────────┐
   │Channel Type?│
   └──┬─────┬────┘
      │     │
Official    Satellite
      │     │
      ▼     ▼
┌──────────┐ ┌────────────┐
│ Validate │ │ NO         │
│ Brand Fit│ │ Validation │
│ ≥ 0.8?   │ │ Required   │
└────┬─────┘ └─────┬──────┘
     │             │
  Yes│  No     Publish
     │  │         │
     ▼  │         ▼
┌────────┐    ┌──────────┐
│ Approve│    │ Track    │
│ for    │    │ Metrics  │
│ Review │    │ for ML   │
└───┬────┘    └──────────┘
    │
    ▼
┌────────────────┐
│ Human Approval │
│ via Telegram   │
└───┬────────────┘
    │
    ▼
┌────────────┐
│ Publish    │
│ & Track    │
└────────────┘
```

---

## Cost Optimization Strategy

**Target**: <€3/month total, <€0.02/request

### LLM Usage Rules:

1. **Gemini for Bulk Analysis** (€0.001/1K tokens)
   - Trend classification
   - Content categorization
   - Batch processing

2. **GPT-4/5 for Critical Decisions** (€0.01/1K tokens)
   - Videoclip concept generation
   - Strategic recommendations
   - High-stakes brand decisions

3. **Lexicon-Based for Sentiment** (€0/batch)
   - NO LLM for sentiment analysis
   - Target: ≥90% accuracy with ES/EN lexicons
   - Process 200+ comments for ~€0

4. **Prompt Optimization**
   - Versioned prompts in markdown files
   - Concise prompts with clear constraints
   - Few-shot examples pre-loaded

---

## Integration Points

### Brand Engine (Sprint 4A)
```python
# CM loads brand rules for validation
brand_rules = await brand_engine.load_rules(user_id)
compliance_score = await brand_engine.validate_compliance(content, brand_rules)

if channel_type == "official" and compliance_score < 0.8:
    return RejectContent(reason="Brand compliance too low")
```

### Vision Engine (Sprint 3)
```python
# CM uses Vision Engine for aesthetic analysis
aesthetic_dna = await vision_engine.extract_aesthetic_dna(video_path)
color_match = vision_engine.calculate_color_match(aesthetic_dna, brand_colors)

if channel_type == "official" and color_match < 0.6:
    return FlagForReview(reason="Color palette mismatch")
```

### Satellite Engine (Sprint 2)
```python
# CM fetches metrics for timing optimization
metrics = await satellite_engine.fetch_performance_metrics(
    platform="instagram",
    days=30
)

best_time = planner.predict_best_post_time(metrics, content_type="reel")
```

### ML Engine (Future Sprint)
```python
# CM feeds data to ML for learning
await ml_engine.log_performance(
    content_id=content_id,
    metrics={
        "views": 15000,
        "retention": 0.87,
        "ctr": 0.12
    },
    features={
        "aesthetic_dna": aesthetic_dna,
        "trend_alignment": 0.85,
        "posting_time": "20:30"
    }
)

# ML predicts best next action
recommendation = await ml_engine.predict_next_content(user_id)
```

---

## Quality Gates

### Official Content Must Pass:
1. ✅ Brand compliance score ≥ 0.8
2. ✅ Color palette alignment ≥ 0.6
3. ✅ No prohibited elements
4. ✅ Aesthetic coherence validated
5. ✅ Narrative quality check
6. ✅ Human approval via Telegram

### Satellite Content Only Requires:
1. ✅ No extreme brand damage
2. ✅ Track metrics for ML
3. ✅ Optional: trend alignment check

---

## Performance Targets

| Module | Latency Target | Cost Target |
|--------|----------------|-------------|
| Planner | <1.5s | <€0.02/plan |
| Recommender | <2.0s | <€0.03/concept |
| Trend Miner | <3.0s | <€0.02/analysis |
| Sentiment | <0.5s | €0.00/batch |
| Reporter | <2.0s | <€0.01/report |

**Monthly Total**: <€3.00

---

## Next Steps After Sprint 4B

1. **Telegram Bot Integration**
   - Daily plan approval flow
   - Report delivery
   - Voice commands for quick requests

2. **Real API Connections**
   - TikTok Creative Center API
   - Instagram Graph API
   - YouTube Data API

3. **ML Training Loop**
   - Feed satellite performance to ML
   - Predict next best content
   - Auto-optimize timing

4. **Advanced Features**
   - Voice-based content planning
   - Automated videoclip generation with AI tools
   - Cross-artist learning network

---

**Version**: 1.0.0  
**Last Updated**: 2024-12-07  
**Status**: Sprint 4B Complete (~90%)
