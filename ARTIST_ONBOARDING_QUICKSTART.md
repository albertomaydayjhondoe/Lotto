# Artist Onboarding - Quick Start Guide

## 🚀 5-Minute Quick Start

### Option 1: Use Orchestrator (Recommended)

```bash
cd /workspaces/stakazo/backend/app/community_ai/onboarding

# Run complete onboarding
python onboarding_orchestrator.py onboarding_answers.json ../brand/
```

**Output**: All 3 configuration files generated + validation report

### Option 2: Run Generators Individually

```bash
cd /workspaces/stakazo/backend/app/community_ai/onboarding

# Generate brand rules
python brand_generator.py onboarding_answers.json ../brand/brand_static_rules.json

# Generate satellite rules
python satellite_generator.py onboarding_answers.json ../brand/satellite_rules.json

# Generate content strategy
python strategy_generator.py onboarding_answers.json ../brand/content_strategy.json
```

---

## 📋 Questionnaire Structure

### 10 Sections | 50 Questions | 45 Minutes

1. **Visual Identity** (10 Q) - Colors, camera, lighting, scenes, editing
2. **Brand Tone** (5 Q) - Emotions, personality, uniqueness
3. **Music Context** (5 Q) - Genres, moods, vocal style
4. **Fashion Identity** (4 Q) - Wardrobe, accessories, aesthetic
5. **Narrative** (4 Q) - Story types, themes, style
6. **Official vs Satellite** (6 Q) ⚠️ **CRITICAL** - Content types, rules, quality
7. **Audience** (4 Q) - Demographics, engagement drivers
8. **Content Strategy** (6 Q) - Posting frequency, timing, experimentation
9. **Platform Guidelines** (3 Q) - Instagram, TikTok, YouTube
10. **Metrics** (3 Q) - KPIs, success definition, failure tolerance

---

## 🎯 Key Questions to Focus On

### Section 6: Official vs Satellite (MOST CRITICAL)

**q29**: What content goes on OFFICIAL channel?
- Videoclips, teasers, premium BTS, high-production reels

**q30**: What content is FORBIDDEN on official?
- Generic viral, incoherent trends, low-quality edits

**q31**: What content goes on SATELLITE channels?
- Viral edits, AI videos, GTA clips, anime edits, trends

**q32**: Rules for satellite content?
- ❌ NO_mostrar_artista_real
- ❌ NO_mezclar_estetica_oficial
- ❌ NO_usar_vestuario_oficial
- ✅ SI_experimentar_libremente
- ✅ SI_usar_IA
- ✅ SI_contenido_edgy

**q33**: Quality threshold for official? (1-10)
- Default: 8/10

**q34**: Quality threshold for satellite? (1-10)
- Default: 5/10

---

## 🔀 Official vs Satellite at a Glance

| Aspect | Official | Satellite |
|--------|----------|-----------|
| **Quality** | ≥8/10 | ≥5/10 |
| **Brand Check** | Required (≥0.8) | NOT required |
| **Aesthetic** | Must match | Can differ |
| **Artist Shown** | Yes | NO ❌ |
| **Posts/Week** | 5 (1-2/day) | 15 (3-5/day) |
| **Content** | Videoclips, teasers, BTS | Edits, AI, GTA, trends |
| **Validation** | 5 gates | NONE (except prohibitions) |
| **Purpose** | Brand-aligned, quality | Experimentation, learning |

---

## 📂 Generated Files

### 1. brand_static_rules.json (~12 KB)

**Sections**:
- `artist_identity`: Personality, emotions, uniqueness
- `visual_rules`: Color palette, scenes, editing, wardrobe
- `content_boundaries`: Official content, narrative rules, thresholds
- `platform_guidelines`: Posting schedule, Instagram/TikTok/YouTube strategies
- `music_context`: Genres, moods, vocal style
- `brand_signature`: Visual DNA, recognizability elements
- `quality_standards`: Minimum scores, validation gates
- `metrics_priorities`: KPIs, success definition

**Key Values**:
- Signature color: First color from q1
- Quality threshold: q33 (default: 8)
- Brand compliance: 0.8
- Aesthetic coherence: 0.7
- Color match: 0.6

### 2. satellite_rules.json (~10 KB)

**Sections**:
- `philosophy`: Purpose, objectives, key principles
- `content_rules`: Allowed types, categories, sources
- `prohibitions`: 3 absolute NO rules
- `freedoms`: 3 creative SI rules
- `quality_standards`: Minimum 5/10, baseline only
- `posting_strategy`: 15 posts/week, rapid iteration
- `experimentation_rules`: Testing framework, trend adoption
- `ml_learning_rules`: Data collection, pattern discovery

**Key Values**:
- Quality threshold: q34 (default: 5)
- Posts/week: q40 (default: 15)
- Prohibitions: 3 (NO artist, NO aesthetic, NO wardrobe)
- Validation gates: NONE

### 3. content_strategy.json (~14 KB)

**Sections**:
- `official_channel`: Posting schedule, content calendar, quality requirements
- `satellite_channels`: Posting schedule, iteration cycles, channel allocation
- `content_mix`: Official/satellite breakdown, balance rules
- `timing_optimization`: Optimal times, activity windows, seasonal adjustments
- `platform_strategies`: Instagram, TikTok, YouTube specific guidelines
- `kpi_framework`: Primary KPIs, definitions, success criteria
- `experimentation_guidelines`: Testing framework, approval rules
- `adaptation_rules`: Performance triggers, trend adaptation, learning integration

**Key Values**:
- Official posts/week: q39 (default: 5)
- Satellite posts/week: q40 (default: 15)
- Optimal times: q41 (default: [20:00, 21:30, 23:00])
- Primary KPIs: q48 (default: [retention_rate, engagement_rate, views, shares])

---

## 🔧 Integration Examples

### Load in CM Planner

```python
from pathlib import Path
import json

# Load brand rules
brand_rules_path = Path("backend/app/community_ai/brand/brand_static_rules.json")
with open(brand_rules_path) as f:
    brand_rules = json.load(f)

# Access rules
signature_color = brand_rules["brand_signature"]["visual_dna"]["signature_color"]
quality_threshold = brand_rules["quality_standards"]["official_channel"]["minimum_quality_score"]
brand_compliance = brand_rules["content_boundaries"]["brand_compliance_threshold"]

print(f"Signature: {signature_color}")  # #8B44FF
print(f"Quality: {quality_threshold}")  # 8
print(f"Compliance: {brand_compliance}")  # 0.8
```

### Load in Vision Engine

```python
# Load visual rules
visual_rules = brand_rules["visual_rules"]

# Color validation
allowed_colors = visual_rules["color_palette"]["allowed"]
color_match_threshold = visual_rules["color_palette"]["color_match_threshold"]

# Scene validation
allowed_scenes = visual_rules["scenes"]["allowed"]
forbidden_scenes = visual_rules["scenes"]["forbidden"]
```

### Check Satellite Prohibitions

```python
# Load satellite rules
satellite_rules_path = Path("backend/app/community_ai/brand/satellite_rules.json")
with open(satellite_rules_path) as f:
    satellite_rules = json.load(f)

# Get prohibitions
prohibitions = satellite_rules["prohibitions"]["absolute_prohibitions"]
# ["NO_mostrar_artista_real", "NO_mezclar_estetica_oficial", "NO_usar_vestuario_oficial"]

# Check if content violates prohibitions
def validate_satellite_content(content):
    if "artist_shown" in content and content["artist_shown"]:
        return False, "Violates: NO_mostrar_artista_real"
    
    if "uses_official_aesthetic" in content and content["uses_official_aesthetic"]:
        return False, "Violates: NO_mezclar_estetica_oficial"
    
    return True, "APPROVED"
```

---

## ✅ Validation Checklist

Before deploying configurations:

### Questionnaire
- [ ] All 50 questions answered
- [ ] Section 6 (Official vs Satellite) carefully reviewed
- [ ] Quality thresholds realistic (official: 8, satellite: 5)
- [ ] Posting frequencies achievable (official: 5/week, satellite: 15/week)

### Brand Rules
- [ ] Signature color correct
- [ ] Allowed colors list complete
- [ ] Forbidden scenes accurately captured
- [ ] Brand compliance threshold reasonable (0.8)

### Satellite Rules
- [ ] 3 prohibitions present and enforced
- [ ] Content types list complete
- [ ] Quality threshold not too high (≤6)
- [ ] Posting frequency realistic for rapid iteration

### Content Strategy
- [ ] Posting times match audience activity
- [ ] Content mix percentages sum to 100%
- [ ] KPI priorities ranked correctly
- [ ] Platform strategies specific to each platform

---

## 🚨 Common Mistakes to Avoid

### ❌ DON'T:
1. Mix official aesthetic in satellite content
2. Set satellite quality threshold too high (>6)
3. Apply brand validation to satellite
4. Show real artist in satellite channels
5. Set unrealistic posting frequencies
6. Ignore Section 6 (Official vs Satellite)

### ✅ DO:
1. Keep official and satellite completely separate
2. Be specific in visual preferences (not "good quality")
3. Provide real examples in Section 1 (q10)
4. Set realistic posting frequencies for your capacity
5. Review generated rules before deployment
6. Test with actual content before full rollout

---

## 📞 Quick Help

### "How do I complete the questionnaire?"

Edit `onboarding_answers.json` directly with your responses. Use `onboarding_questions.json` as reference for question types and options.

### "What if I'm not sure about a question?"

Use defaults provided in questions. Can always regenerate rules later with updated answers.

### "Can I change rules after generation?"

Yes! Edit generated JSON files directly, or update `onboarding_answers.json` and regenerate.

### "How do I test generated rules?"

Use orchestrator: `python onboarding_orchestrator.py answers.json output_dir/`

It validates questionnaire, generates all files, and reports any issues.

---

## 📚 Full Documentation

For complete details, see: `docs/artist_onboarding.md`

For technical summary, see: `SPRINT4C_COMPLETE_SUMMARY.md`

---

**Version**: 1.0.0  
**Last Updated**: 2024-12-07  
**Status**: Production Ready ✅
