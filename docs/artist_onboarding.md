# Artist Onboarding System - Sprint 4C

## Overview

The Artist Onboarding System is the **foundational configuration sprint** that captures an artist's complete identity and automatically generates brand rules, satellite channel rules, and content strategy. This system ensures the entire STAKAZO platform operates with perfect understanding of the artist's aesthetic, values, and content boundaries.

**Critical Purpose**: Distinguish PERFECTLY between Official (brand-aligned) and Satellite (experimental) content channels.

---

## 🎯 System Objectives

1. **Capture Artist Identity**: 50-question comprehensive interrogation covering visual, narrative, musical, and strategic preferences
2. **Auto-Generate Brand Rules**: Transform questionnaire answers into `brand_static_rules.json` for Official channel validation
3. **Configure Satellite Rules**: Generate `satellite_rules.json` for experimental channels with clear prohibitions
4. **Define Content Strategy**: Create `content_strategy.json` with posting schedules, content mix, and KPI priorities
5. **Prepare ML Integration**: Artist profile embeddings for future ML Engine training

---

## 📋 Questionnaire Structure

### 10 Sections | 50 Questions | 45 Minutes

The onboarding questionnaire (`onboarding_questions.json`) is structured into 10 thematic sections:

### **Section 1: Visual Identity** (10 questions) - CRITICAL
Captures the artist's visual DNA: colors, camera work, lighting, scenes, editing preferences.

**Key Questions**:
- q1: Allowed color palette (3-5 colors)
- q2: Forbidden colors
- q3: Visual style keywords (dark, cyberpunk, neon, etc.)
- q4-q5: Camera styles and lighting preferences
- q6-q7: Scene preferences (allowed/forbidden)
- q8-q9: Editing styles (allowed/forbidden)
- q10: Top 5 visual references (films, videos, artists)

**Example (Stakazo)**:
```json
{
  "q1_color_palette": ["#8B44FF", "#0A0A0A", "#1A1A2E", "#16213E", "#E94560"],
  "q3_visual_style": ["oscuro", "futurista", "cyberpunk", "neon", "urbano"],
  "q5_lighting_preference": ["high_contrast", "low_key", "neon_lights"]
}
```

### **Section 2: Brand Tone** (5 questions) - CRITICAL
Defines the artist's emotional palette, personality, and uniqueness.

**Key Questions**:
- q11: Emotional tone to transmit (intensity, mystery, power)
- q12: Emotions to avoid (superficial happiness, weakness)
- q13: Brand personality (5 keywords)
- q14: Artist uniqueness statement (200 words)
- q15: Artist inspirations (5-10 names)

### **Section 3: Music Context** (5 questions) - HIGH
Captures musical genres, moods, vocal style, and lyrical themes.

**Key Questions**:
- q16: Genres (trap, electronic, experimental)
- q17: Moods (dark, intense, introspective)
- q18: Vocal style (autotuned, melodic, layered)
- q19-q20: Lyrical themes (allowed/forbidden)

### **Section 4: Fashion Identity** (4 questions) - HIGH
Defines wardrobe style, accessories, and fashion aesthetic.

**Key Questions**:
- q21-q22: Wardrobe (allowed/forbidden)
- q23: Key accessories (masks, glasses, jewelry)
- q24: Fashion aesthetic keywords

### **Section 5: Narrative & Storytelling** (4 questions) - HIGH
Captures story types, themes, and storytelling style.

**Key Questions**:
- q25: Story types to tell (rise from underground, personal struggle)
- q26: Repeatable themes (night, city, ascent)
- q27: Narratives to avoid
- q28: Storytelling visual style (cinematic, symbolic)

### **Section 6: Official vs Satellite** (6 questions) - CRITICAL ⚠️

**THE MOST IMPORTANT SECTION** - Defines the boundary between brand-aligned official content and experimental satellite content.

**Key Questions**:
- q29: Official content types (videoclips, teasers, premium BTS)
- q30: Official forbidden content (generic viral, incoherent trends)
- q31: Satellite content types (viral edits, AI videos, GTA clips, anime edits)
- q32: Satellite rules (NO show real artist, NO mix official aesthetic, YES experiment freely)
- q33: Quality threshold official (default: 8/10)
- q34: Quality threshold satellite (default: 5/10)

**Example (Stakazo)**:
```json
{
  "q29_official_content_types": [
    "videoclips_oficiales",
    "teasers_cinematicos",
    "behind_scenes_premium"
  ],
  "q31_satellite_content_types": [
    "edits_virales",
    "IA_videos",
    "GTA_edits",
    "anime_edits",
    "trends_populares"
  ],
  "q32_satellite_rules": [
    "NO_mostrar_artista_real",
    "NO_mezclar_estetica_oficial",
    "SI_experimentar_libremente",
    "SI_usar_IA"
  ],
  "q33_quality_threshold_official": 8,
  "q34_quality_threshold_satellite": 5
}
```

### **Section 7: Audience Targeting** (4 questions) - HIGH
Defines target demographics, characteristics, and engagement drivers.

**Key Questions**:
- q35: Target age range (default: 16-28)
- q36: Audience characteristics (urban, tech-savvy, gamers)
- q37: Engagement drivers (unique aesthetic, cinematography)
- q38: Content consumption platforms

### **Section 8: Content Strategy** (6 questions) - HIGH
Defines posting frequency, timing, experimentation tolerance.

**Key Questions**:
- q39: Official posting frequency (default: 5 posts/week)
- q40: Satellite posting frequency (default: 15 posts/week)
- q41: Optimal posting times
- q42: Content mix percentages
- q43: Experimentation tolerance (1-10 scale)
- q44: Trend adoption speed (1-10 scale)

### **Section 9: Platform Guidelines** (3 questions) - MEDIUM
Platform-specific strategies for Instagram, TikTok, YouTube.

### **Section 10: Metrics Priorities** (3 questions) - MEDIUM
Defines KPI priorities, success definition, failure tolerance.

**Key Questions**:
- q48: Primary KPIs ranked (retention_rate, engagement_rate, views, shares)
- q49: Success definition (150 words)
- q50: Failure tolerance threshold (1-10)

---

## 🤖 Auto-Generation Process

### Step 1: Complete Questionnaire
Artist completes 50-question onboarding, responses stored in `onboarding_answers.json`.

### Step 2: Generate Brand Rules
**Generator**: `brand_generator.py`
**Input**: `onboarding_answers.json`
**Output**: `brand_static_rules.json`

**Transformation Logic**:
- Visual Identity → `visual_rules` (color palette, camera, lighting, scenes, editing, wardrobe)
- Brand Tone → `artist_identity` (personality, emotions, uniqueness)
- Music Context → `music_context` (genres, moods, vocal style)
- Narrative → `content_boundaries.narrative_rules`
- Official Content → `content_boundaries.official_content`
- Platform Guidelines → `platform_guidelines`
- Metrics → `metrics_priorities`

**Key Sections Generated**:
```json
{
  "artist_identity": { ... },
  "visual_rules": {
    "color_palette": {
      "allowed": ["#8B44FF", "#0A0A0A", ...],
      "signature_color": "#8B44FF",
      "color_match_threshold": 0.6
    },
    "scenes": { "allowed": [...], "forbidden": [...] }
  },
  "content_boundaries": {
    "brand_compliance_threshold": 0.8,
    "aesthetic_coherence_threshold": 0.7
  },
  "quality_standards": {
    "minimum_quality_score": 8,
    "validation_gates": { ... }
  }
}
```

### Step 3: Generate Satellite Rules
**Generator**: `satellite_generator.py`
**Input**: `onboarding_answers.json`
**Output**: `satellite_rules.json`

**Transformation Logic**:
- Satellite Content Types → `content_rules.allowed_content_types`
- Satellite Rules (q32) → `prohibitions` + `freedoms`
- Quality Threshold Satellite → `quality_standards.minimum_quality_score`
- Posting Frequency Satellite → `posting_strategy.frequency`

**Key Sections Generated**:
```json
{
  "philosophy": {
    "purpose": "Experimental testing ground for trends",
    "relationship_to_official": "Completely separate - NO brand validation"
  },
  "prohibitions": {
    "absolute_prohibitions": [
      "NO_mostrar_artista_real",
      "NO_mezclar_estetica_oficial",
      "NO_usar_vestuario_oficial"
    ]
  },
  "freedoms": {
    "creative_freedoms": [
      "SI_experimentar_libremente",
      "SI_usar_IA",
      "SI_contenido_edgy"
    ],
    "no_validation_required": [
      "brand_compliance_check",
      "color_palette_validation",
      "aesthetic_coherence_check"
    ]
  },
  "quality_standards": {
    "minimum_quality_score": 5,
    "quality_philosophy": "Good enough to test, not necessarily polished"
  }
}
```

### Step 4: Generate Content Strategy
**Generator**: `strategy_generator.py`
**Input**: `onboarding_answers.json`
**Output**: `content_strategy.json`

**Transformation Logic**:
- Posting Frequency → `official_channel.posting_schedule` + `satellite_channels.posting_schedule`
- Content Mix → `content_mix.official_mix` + `content_mix.satellite_mix`
- Optimal Times → `timing_optimization.optimal_posting_times`
- Platform Strategies → `platform_strategies` (Instagram, TikTok, YouTube)
- KPIs → `kpi_framework.primary_kpis`

**Key Sections Generated**:
```json
{
  "official_channel": {
    "posting_schedule": {
      "posts_per_week": 5,
      "rhythm": "consistent_quality"
    },
    "content_calendar": {
      "weekly_structure": {
        "monday": "teaser_or_preview",
        "friday": "high_production_reel"
      }
    }
  },
  "satellite_channels": {
    "posting_schedule": {
      "posts_per_week": 15,
      "rhythm": "rapid_iteration"
    }
  },
  "timing_optimization": {
    "optimal_posting_times": ["20:00", "21:30", "23:00"]
  },
  "kpi_framework": {
    "primary_kpis": ["retention_rate", "engagement_rate", "views"]
  }
}
```

---

## 🔀 Official vs Satellite Distinction

### Official Channel (Brand-Aligned)

**Philosophy**: Quality over quantity - every post must meet brand standards.

**Content Types**:
- Videoclips oficiales
- Teasers cinematográficos
- Behind the scenes premium
- Anuncios de lanzamientos
- Reels alta producción
- Contenido narrativo

**Quality Standards**:
- Minimum quality: 8/10
- Brand compliance: ≥0.8
- Aesthetic coherence: ≥0.7
- Color palette match: ≥0.6
- Narrative depth: Required

**Posting Frequency**: 5 posts/week (1-2 per day)

**Validation Gates**:
1. Color palette validation
2. Brand compliance check
3. Aesthetic coherence check
4. Narrative alignment check
5. Quality threshold gate (≥8/10)

**Example Official Post**:
```json
{
  "type": "teaser_cinematico",
  "quality_score": 9.2,
  "brand_compliance": 0.89,
  "color_palette_match": 0.78,
  "aesthetic_coherence": 0.85,
  "validation": "APPROVED"
}
```

### Satellite Channels (Experimental)

**Philosophy**: Rapid iteration and learning - volume enables discovery.

**Content Types**:
- Edits virales
- AI videos
- Clips de series/películas con música overlay
- GTA edits
- Anime edits
- Contenido experimental
- Trends populares
- Format testing

**Quality Standards**:
- Minimum quality: 5/10
- Brand compliance: NOT required
- Aesthetic coherence: NOT required
- Color palette: NOT enforced
- Watchability: Baseline only

**Posting Frequency**: 15 posts/week (3-5 per day)

**Validation Gates**: NONE (except legal compliance)

**Absolute Prohibitions**:
- ❌ NO mostrar artista real (face, body, recognizable features)
- ❌ NO mezclar estética oficial (no purple neon, no brand colors)
- ❌ NO usar vestuario oficial (no artist's wardrobe)

**Creative Freedoms**:
- ✅ SI experimentar libremente (unlimited format testing)
- ✅ SI usar IA (AI-generated content fully allowed)
- ✅ SI contenido edgy (experimental, controversial content)

**Example Satellite Post**:
```json
{
  "type": "GTA_edit",
  "quality_score": 6.1,
  "brand_compliance": null,
  "validation": "APPROVED (no brand check required)",
  "prohibition_check": "PASS (no artist shown, no official aesthetic)"
}
```

---

## 🔧 Integration with System Modules

### Community Manager AI

**CM Planner** (`planner.py`):
- Loads `brand_static_rules.json` at initialization
- Uses `content_strategy.json` for daily planning
- Applies Official vs Satellite distinction in content recommendations
- Enforces posting frequency limits (5 official, 15 satellite)

**CM Recommender** (`content_recommender.py`):
- Uses `brand_static_rules.json` for brand-aligned recommendations
- Uses `satellite_rules.json` for experimental content ideas
- Filters recommendations based on channel type

**CM Trend Miner** (`trend_miner.py`):
- Scores trends with brand fit (official) vs viral potential (satellite)
- Recommends trends to official only if brand_fit_score ≥0.7
- All trends eligible for satellite testing

**CM Reporter** (`daily_reporter.py`):
- Tracks Official vs Satellite metrics separately
- Reports brand compliance scores for official content
- Identifies winning patterns in satellite for official application

### Vision Engine

**Aesthetic Extractor**:
- Uses `visual_rules.color_palette` for color validation
- Uses `visual_rules.scenes` for scene classification
- Uses `visual_rules.wardrobe` for fashion validation

**Content Validator**:
- Applies `quality_standards.validation_gates` for official content
- Bypasses validation for satellite content (except prohibitions)

### Brand Engine

**Rules Builder**:
- Onboarding system auto-generates initial rules
- Brand Engine can refine rules based on performance data
- Periodic review and adjustment recommended (quarterly)

---

## 📊 Usage Examples

### Example 1: Generate All Configuration Files

```bash
cd /workspaces/stakazo/backend/app/community_ai/onboarding

# Step 1: Complete questionnaire (manual or via API)
# Creates: onboarding_answers.json

# Step 2: Generate brand rules
python brand_generator.py onboarding_answers.json ../brand/brand_static_rules.json

# Step 3: Generate satellite rules
python satellite_generator.py onboarding_answers.json ../brand/satellite_rules.json

# Step 4: Generate content strategy
python strategy_generator.py onboarding_answers.json ../brand/content_strategy.json
```

**Output**:
```
✅ Brand rules generated: ../brand/brand_static_rules.json
   - Artist: Stakazo
   - Sections: 9
   - Signature color: #8B44FF
   - Quality threshold: 8/10

✅ Satellite rules generated: ../brand/satellite_rules.json
   - Channel type: satellite
   - Quality threshold: 5/10
   - Posts per week: 15
   - Prohibitions: 3

✅ Content strategy generated: ../brand/content_strategy.json
   - Official posts/week: 5
   - Satellite posts/week: 15
   - Primary KPIs: 6
```

### Example 2: Load Rules in CM Planner

```python
from backend.app.community_ai.planner import CommunityManagerPlanner
from pathlib import Path
import json

# Load brand rules
brand_rules_path = Path("backend/app/community_ai/brand/brand_static_rules.json")
with open(brand_rules_path) as f:
    brand_rules = json.load(f)

# Load content strategy
strategy_path = Path("backend/app/community_ai/brand/content_strategy.json")
with open(strategy_path) as f:
    content_strategy = json.load(f)

# Initialize planner with rules
planner = CommunityManagerPlanner(
    brand_rules=brand_rules,
    content_strategy=content_strategy
)

# Generate daily plan
daily_plan = await planner.generate_daily_plan(
    date="2024-12-07",
    channel_type="official"  # or "satellite"
)
```

### Example 3: Validate Official Content

```python
from backend.app.vision_engine.aesthetic_extractor import AestheticExtractor
import json

# Load brand rules
with open("backend/app/community_ai/brand/brand_static_rules.json") as f:
    brand_rules = json.load(f)

# Extract aesthetic from video
extractor = AestheticExtractor(brand_rules=brand_rules)
aesthetic = await extractor.extract(video_path="teaser_v1.mp4")

# Validate against brand rules
validation_result = {
    "quality_score": aesthetic["quality_score"],  # Must be ≥8
    "brand_compliance": aesthetic["brand_compliance"],  # Must be ≥0.8
    "color_match": aesthetic["color_palette_match"],  # Must be ≥0.6
    "aesthetic_coherence": aesthetic["aesthetic_coherence"],  # Must be ≥0.7
}

# Decision
if all([
    validation_result["quality_score"] >= brand_rules["quality_standards"]["minimum_quality_score"],
    validation_result["brand_compliance"] >= brand_rules["content_boundaries"]["brand_compliance_threshold"],
    validation_result["color_match"] >= brand_rules["visual_rules"]["color_palette"]["color_match_threshold"],
    validation_result["aesthetic_coherence"] >= brand_rules["content_boundaries"]["aesthetic_coherence_threshold"]
]):
    print("✅ APPROVED for Official Channel")
else:
    print("❌ REJECTED - Does not meet official standards")
    print("💡 Consider posting to Satellite Channel instead")
```

---

## 🎓 Best Practices

### 1. Questionnaire Completion

- **Time Investment**: Set aside 45-60 minutes for quality responses
- **Be Specific**: Avoid generic answers ("good quality" → "high contrast neon lighting")
- **Visual References**: Provide specific examples (films, videos, artists)
- **Honesty**: Accurately describe preferences, not aspirations
- **Review**: Double-check Section 6 (Official vs Satellite) - most critical

### 2. Brand Rules Maintenance

- **Quarterly Review**: Review and adjust rules every 3 months
- **Performance-Driven**: Update based on what actually works
- **Document Changes**: Track rule changes and reasons
- **A/B Testing**: Test rule variations in satellite before applying to official

### 3. Satellite Channel Management

- **Respect Prohibitions**: NEVER violate the 3 absolute prohibitions
- **Track Learnings**: Document what works in satellite for official application
- **Rapid Iteration**: Don't overthink satellite content - post and learn
- **Data Collection**: Ensure all satellite metrics are tracked for ML

### 4. Content Strategy Adaptation

- **Monitor KPIs Weekly**: Track primary KPIs every week
- **Adjust Monthly**: Make strategy adjustments monthly based on data
- **Seasonal Awareness**: Adjust posting times and frequency for seasons/holidays
- **Platform Evolution**: Stay updated on platform algorithm changes

---

## 🚨 Common Pitfalls

### ❌ DON'T:
- Mix official aesthetic in satellite content
- Show real artist in satellite channels
- Apply brand validation to satellite
- Post satellite content to official channel
- Ignore the 3 absolute prohibitions
- Make knee-jerk strategy changes based on 1-2 posts

### ✅ DO:
- Maintain clear separation between official and satellite
- Track all metrics for both channels
- Use satellite as testing ground for official
- Review and adjust strategy based on data
- Respect brand rules for official content
- Experiment freely in satellite (within prohibitions)

---

## 📈 Success Metrics

### System-Level Success

- **Brand Coherence**: Official content maintains ≥0.8 brand compliance
- **Learning Velocity**: Satellite identifies 2+ winning patterns per month
- **Strategy Effectiveness**: Official content meets KPI targets 80% of the time
- **Separation Quality**: Zero instances of prohibited content in satellite

### Content Performance

**Official Channel**:
- Retention rate >70%
- Engagement rate >5%
- Brand compliance >0.8
- Aesthetic coherence >0.7

**Satellite Channels**:
- 15 posts/week maintained
- 3+ winning patterns identified per month
- ML data collection 100% complete
- Zero prohibition violations

---

## 🔄 Integration Timeline

### Sprint 4C Deliverables (COMPLETE)

- [x] `onboarding_questions.json` - 50-question structured questionnaire
- [x] `onboarding_answers.json` - Example Stakazo responses
- [x] `brand_generator.py` - Auto-generate brand rules
- [x] `satellite_generator.py` - Auto-generate satellite rules
- [x] `strategy_generator.py` - Auto-generate content strategy
- [x] `brand_static_rules.json` - Generated for Stakazo
- [x] `satellite_rules.json` - Generated for Stakazo
- [x] `content_strategy.json` - Generated for Stakazo
- [x] `docs/artist_onboarding.md` - This documentation

### Next Steps (Sprint 5 Integration)

- [ ] Integrate brand_static_rules.json with Rules Engine
- [ ] Implement real-time validation API endpoints
- [ ] Create onboarding UI for artists
- [ ] Build ML embeddings pipeline
- [ ] Implement performance monitoring dashboard

---

## 📞 Support & Troubleshooting

### Generator Errors

**Error**: "File not found: onboarding_answers.json"
- **Solution**: Ensure answers file exists in same directory as generator

**Error**: "Missing required fields in answers"
- **Solution**: Validate answers file has all 50 question IDs (q1-q50)

**Error**: "Invalid JSON format"
- **Solution**: Check JSON syntax, ensure proper escaping

### Validation Issues

**Issue**: Official content failing brand compliance
- **Check**: Review `visual_rules.color_palette` - is content using allowed colors?
- **Check**: Review `content_boundaries.brand_compliance_threshold` - may need adjustment

**Issue**: Satellite content being rejected
- **Check**: Are you violating the 3 absolute prohibitions?
- **Check**: Is quality_score ≥5? Even satellite has minimum standards

---

## 🎬 Conclusion

The Artist Onboarding System is the **foundational configuration layer** that enables STAKAZO to operate with the artist's real identity. By completing the 50-question questionnaire, the system automatically generates comprehensive rules that govern Official channel validation, Satellite channel experimentation, and content strategy execution.

**Key Takeaway**: Perfect Official vs Satellite separation is achieved through:
1. Clear prohibitions in satellite (NO show artist, NO mix aesthetic)
2. Strict validation gates for official (brand compliance ≥0.8, quality ≥8/10)
3. Separate posting strategies (5/week official, 15/week satellite)
4. Learning pipeline (satellite patterns → official application)

With onboarding complete, the system is ready to create content that is **authentically aligned with the artist's vision** while maintaining **creative freedom for experimentation and learning**.
