# SATELLITE ENGINE 2.0 - GUÍA COMPLETA

Guía detallada para usar el Satellite Engine y gestionar cuentas satélite virales.

---

## 📚 TABLA DE CONTENIDOS

1. [Introducción](#introducción)
2. [Instalación](#instalación)
3. [Quick Start](#quick-start)
4. [Configuración de Cuentas](#configuración-de-cuentas)
5. [Gestión de Nichos](#gestión-de-nichos)
6. [Routing de Contenido](#routing-de-contenido)
7. [Warm-up de Cuentas](#warm-up-de-cuentas)
8. [Publicación Multi-Cuenta](#publicación-multi-cuenta)
9. [ML Learning](#ml-learning)
10. [A/B Testing de Sonidos](#ab-testing-de-sonidos)
11. [Monitoring y Métricas](#monitoring-y-métricas)
12. [Best Practices](#best-practices)
13. [Troubleshooting](#troubleshooting)

---

## 📖 INTRODUCCIÓN

El **Satellite Engine 2.0** es un sistema completo para gestionar cuentas satélite virales en TikTok, Instagram y YouTube. Diseñado para:

- 🎯 Gestionar 100+ cuentas simultáneamente
- 🎭 Asignar 1 nicho único por cuenta
- 🤖 Simular comportamiento humano (anti-detección)
- 🎨 Routing inteligente de contenido (Vision + ML)
- 🔒 Identidad aislada (VPN+Proxy+Fingerprint)
- 📈 Optimización ML continua
- 🎵 Pruebas A/B de música

---

## 🔧 INSTALACIÓN

### Requisitos

```bash
Python 3.12+
FastAPI
NumPy
```

### Setup

```bash
# Instalar dependencias
cd /workspaces/stakazo/backend
pip install -r requirements.txt

# Verificar instalación
python -c "from app.satellite_engine import *; print('✓ Satellite Engine instalado')"
```

---

## ⚡ QUICK START

### Ejemplo Básico: 1 Cuenta

```python
from app.satellite_engine import (
    SatelliteBehaviorEngine,
    SatelliteNicheEngine,
    SatelliteContentRouter,
    SatelliteWarmupEngine,
    SatellitePublishingEngine,
    Niche,
    ContentType,
    Platform
)
from datetime import datetime

# 1. Crear engines
behavior = SatelliteBehaviorEngine()
niche = SatelliteNicheEngine()
router = SatelliteContentRouter()
warmup = SatelliteWarmupEngine()
publishing = SatellitePublishingEngine()

# 2. Configurar cuenta
account_id = "tiktok_shameless_001"

# Asignar nicho
niche.assign_niche_to_account(account_id, Niche.SHAMELESS_EDITS)

# Crear schedule de comportamiento
schedule = behavior.create_schedule(account_id, "tiktok", timezone_offset=-5)

# Crear plan de warm-up
warmup_plan = warmup.create_warmup_plan(account_id, "tiktok")

# Crear identidad aislada
identity = publishing.create_identity(account_id)

print(f"✅ Cuenta {account_id} configurada!")
print(f"   Nicho: Shameless Edits")
print(f"   Posts/día objetivo: {schedule.daily_posts_target}")
print(f"   Warm-up días: 5")
print(f"   Identity hash: {identity.get_fingerprint_hash()}")

# 3. Analizar y routear contenido
candidate = router.analyze_content(
    content_id="shameless_scene_001",
    content_type=ContentType.VIDEO_CLIP,
    source_path="/clips/shameless_dark_scene.mp4",
    duration_seconds=15.0,
    music_track_id="stakas_barrio_oro",
    lyric_keywords=["barrio", "oro"]
)

profile = niche.get_account_profile(account_id)

decision = router.route_content_to_account(
    account_id=account_id,
    niche_name=profile.name,
    niche_palette=profile.visual_library.color_palette,
    content_candidates=[candidate],
    preferred_platform="tiktok"
)

print(f"✅ Content routed: {decision.content_candidate.content_id}")
print(f"   Virality score: {decision.virality_score.overall_score:.2f}")
print(f"   Priority: {decision.priority}/10")

# 4. Programar publicación
next_time = warmup.get_next_post_time(account_id)

task = publishing.queue_publish(
    account_id=account_id,
    platform=Platform.TIKTOK,
    content_id=decision.content_candidate.content_id,
    content_path=decision.content_candidate.source_path,
    caption="Barrio con oro 🏆✨ #Shameless #Edits",
    hashtags=profile.style_book.hashtag_templates[:5],
    scheduled_time=next_time,
    music_track_id="stakas_barrio_oro"
)

print(f"✅ Publicación programada para: {next_time}")

# 5. Publicar (cuando llegue el momento)
result = publishing.publish(task)

if result.success:
    print(f"✅ Publicado exitosamente!")
    print(f"   URL: {result.platform_url}")
    
    # Registrar en warm-up
    warmup.register_post(account_id, datetime.now())
    
    # Registrar en behavior engine
    behavior.register_post(account_id)
else:
    print(f"❌ Error: {result.error}")
```

---

## 🎯 CONFIGURACIÓN DE CUENTAS

### Setup de 1 Cuenta

```python
def setup_satellite_account(
    account_id: str,
    niche: Niche,
    platform: str,
    timezone_offset: int = -5
):
    """Setup completo de cuenta satélite."""
    
    # Engines
    behavior = SatelliteBehaviorEngine()
    niche_engine = SatelliteNicheEngine()
    warmup = SatelliteWarmupEngine()
    publishing = SatellitePublishingEngine()
    
    # 1. Assign niche
    niche_engine.assign_niche_to_account(account_id, niche)
    
    # 2. Create behavior schedule
    schedule = behavior.create_schedule(account_id, platform, timezone_offset)
    
    # 3. Create warmup plan
    plan = warmup.create_warmup_plan(account_id, platform)
    
    # 4. Create identity
    identity = publishing.create_identity(account_id)
    
    return {
        "account_id": account_id,
        "niche": niche.value,
        "schedule": schedule,
        "warmup_plan": plan,
        "identity": identity
    }

# Uso
account = setup_satellite_account(
    "tiktok_shameless_001",
    Niche.SHAMELESS_EDITS,
    "tiktok"
)
```

### Setup Batch de 100 Cuentas

```python
def setup_satellite_fleet(count: int = 100):
    """Setup de flota completa de cuentas satélite."""
    
    # Distribución de nichos
    niche_distribution = {
        Niche.SHAMELESS_EDITS: 20,
        Niche.STRANGER_THINGS: 15,
        Niche.GTA_CINEMATIC: 20,
        Niche.EA_SPORTS_FIFA: 15,
        Niche.ANIME_EDITS: 15,
        Niche.CORRIDOS_AESTHETIC: 10,
        Niche.LIFESTYLE_NEON: 5
    }
    
    accounts = []
    account_counter = 0
    
    for niche, count in niche_distribution.items():
        for i in range(count):
            account_counter += 1
            account_id = f"tiktok_{niche.value}_{account_counter:03d}"
            
            account = setup_satellite_account(
                account_id=account_id,
                niche=niche,
                platform="tiktok"
            )
            
            accounts.append(account)
    
    return accounts

# Setup
fleet = setup_satellite_fleet(100)
print(f"✅ {len(fleet)} cuentas configuradas!")
```

---

## 🎨 GESTIÓN DE NICHOS

### Nichos Disponibles

```python
from app.satellite_engine import Niche

# 7 nichos predefinidos
nichos = [
    Niche.SHAMELESS_EDITS,       # Urban gritty
    Niche.STRANGER_THINGS,       # Retro horror
    Niche.GTA_CINEMATIC,         # Gaming cinematic
    Niche.EA_SPORTS_FIFA,        # Sports hype
    Niche.ANIME_EDITS,           # Anime aesthetic
    Niche.CORRIDOS_AESTHETIC,    # Regional mexicano
    Niche.LIFESTYLE_NEON         # Neon cyberpunk
]
```

### Explorar Nicho

```python
niche_engine = SatelliteNicheEngine()

# Get profile
profile = niche_engine.get_niche_profile(Niche.SHAMELESS_EDITS)

print(f"Nicho: {profile.name}")
print(f"Descripción: {profile.description}")
print(f"Plataformas: {profile.platforms_priority}")
print(f"Color palette: {profile.visual_library.color_palette}")
print(f"Hashtags: {profile.style_book.hashtag_templates}")

# Get random visual prompt
prompt = profile.get_visual_prompt_random()
print(f"Visual prompt: {prompt}")

# Get random hashtags
hashtags = profile.get_hashtags_random(count=5)
print(f"Hashtags: {hashtags}")
```

### Personalizar Style Book

```python
# Agregar prompts visuales
profile.style_book.add_visual_prompt(
    "Dark urban scene with dramatic gold lighting"
)

# Configurar estilo de edición
profile.style_book.set_editing_style({
    "transitions": "hard_cuts",
    "color_grading": "dark_contrast",
    "effects": ["slow_motion", "zoom_in"],
    "text_style": "bold_white_outline"
})

# Agregar regla de music mapping
profile.style_book.add_music_mapping_rule({
    "lyric_keyword": "barrio con oro",
    "scene_to_use": "shameless_gold_scene",
    "timing": "on_beat",
    "duration": 2.5
})
```

---

## 🎬 ROUTING DE CONTENIDO

### Analizar Contenido

```python
router = SatelliteContentRouter()

# Analizar video
candidate = router.analyze_content(
    content_id="content_001",
    content_type=ContentType.VIDEO_CLIP,
    source_path="/clips/shameless_scene.mp4",
    duration_seconds=15.0,
    music_track_id="stakas_track_001",
    lyric_keywords=["barrio", "oro", "poder"]
)

print(f"Visual tags: {candidate.visual_tags}")
print(f"Dominant colors: {candidate.dominant_colors}")
print(f"Scene: {candidate.scene_description}")
print(f"Motion intensity: {candidate.motion_intensity}")
```

### Routing Inteligente

```python
# Pool de candidatos
candidates = [
    router.analyze_content(f"content_{i}", ContentType.VIDEO_CLIP, f"/clips/video_{i}.mp4", 15.0)
    for i in range(10)
]

# Route a cuenta específica
profile = niche_engine.get_account_profile("tiktok_shameless_001")

decision = router.route_content_to_account(
    account_id="tiktok_shameless_001",
    niche_name=profile.name,
    niche_palette=profile.visual_library.color_palette,
    content_candidates=candidates,
    preferred_platform="tiktok"
)

print(f"Best content: {decision.content_candidate.content_id}")
print(f"Virality score: {decision.virality_score.overall_score:.2f}")
print(f"Virality level: {decision.virality_score.level.value}")
print(f"Niche match: {decision.niche_match_score:.2f}")
print(f"Priority: {decision.priority}/10")
print(f"Reasoning: {decision.reasoning}")
```

### Batch Routing

```python
# Route para múltiples cuentas
accounts = [
    {
        "account_id": "tiktok_shameless_001",
        "niche_name": "Shameless Edits",
        "niche_palette": ["#1a1a2e", "#e94560"],
        "platform": "tiktok"
    },
    {
        "account_id": "tiktok_gta_001",
        "niche_name": "GTA Cinematic",
        "niche_palette": ["#ff6b00", "#ffd700"],
        "platform": "tiktok"
    }
]

decisions = router.batch_route_content(accounts, candidates)

for decision in decisions:
    print(f"{decision.account_id}: {decision.content_candidate.content_id} (score={decision.virality_score.overall_score:.2f})")
```

---

## 🌱 WARM-UP DE CUENTAS

### Crear Plan de Warm-up

```python
warmup_engine = SatelliteWarmupEngine()

plan = warmup_engine.create_warmup_plan(
    account_id="new_account_001",
    platform="tiktok"
)

print(f"Account: {plan.account_id}")
print(f"Current day: {plan.current_day}")
print(f"Current phase: {plan.current_phase.value}")
print(f"Daily schedules: {len(plan.daily_schedules)}")

# Ver schedule de cada día
for schedule in plan.daily_schedules:
    print(f"  Day {schedule.day}: {schedule.target_posts} posts")
```

### Ejecutar Warm-up

```python
account_id = "new_account_001"

# Loop de warm-up
while warmup_engine.is_in_warmup(account_id):
    # Get next post time
    next_time = warmup_engine.get_next_post_time(account_id)
    
    if next_time is None:
        print("Día completo, avanzar al siguiente")
        plan = warmup_engine.get_plan(account_id)
        plan.advance_day()
        continue
    
    print(f"Next post at: {next_time}")
    
    # Esperar hasta next_time...
    # Publicar contenido...
    
    # Registrar post
    warmup_engine.register_post(account_id, next_time)
    
    # Check progress
    progress = warmup_engine.get_warmup_progress(account_id)
    print(f"  Day {progress['current_day']}: {progress['posts_today']}/{progress['target_today']}")

print("✅ Warm-up completado!")
```

---

## 📤 PUBLICACIÓN MULTI-CUENTA

### Crear Identidad

```python
publishing_engine = SatellitePublishingEngine()

identity = publishing_engine.create_identity("account_001")

print(f"VPN: {identity.vpn_server}")
print(f"Proxy: {identity.proxy_ip}:{identity.proxy_port}")
print(f"User-Agent: {identity.user_agent}")
print(f"Screen: {identity.screen_resolution}")
print(f"Timezone: {identity.timezone}")
print(f"Fingerprint: {identity.get_fingerprint_hash()}")
```

### Queue y Publicar

```python
# Queue task
task = publishing_engine.queue_publish(
    account_id="account_001",
    platform=Platform.TIKTOK,
    content_id="content_001",
    content_path="/videos/edit_001.mp4",
    caption="Caption con emojis 🔥✨",
    hashtags=["#Viral", "#Edits", "#Music"],
    scheduled_time=datetime.now() + timedelta(hours=1),
    music_track_id="stakas_track_001"
)

print(f"Task queued: {task.task_id}")
print(f"Scheduled for: {task.scheduled_time}")

# Cuando llega el momento...
result = publishing_engine.publish(task)

if result.success:
    print(f"✅ Published!")
    print(f"   Post ID: {result.platform_post_id}")
    print(f"   URL: {result.platform_url}")
    print(f"   Time taken: {result.time_taken_seconds:.1f}s")
else:
    print(f"❌ Failed: {result.error}")
    
    # Retry si es posible
    if task.can_retry():
        print(f"Retrying... (attempt {task.retry_count + 1}/{task.max_retries})")
        result = publishing_engine.publish(task)
```

### Publicación Batch

```python
# Queue múltiples tasks
tasks = []
for account in satellite_accounts:
    task = publishing_engine.queue_publish(
        account_id=account["id"],
        platform=Platform.TIKTOK,
        content_id=account["content"],
        content_path=account["path"],
        caption=account["caption"],
        hashtags=account["hashtags"],
        scheduled_time=account["scheduled_time"]
    )
    tasks.append(task)

# Publicar en paralelo (respetando anti-correlation)
for task in tasks:
    # Wait for safe time (anti-correlation)
    # ...
    
    result = publishing_engine.publish(task)
    print(f"{task.account_id}: {'✅' if result.success else '❌'}")
```

---

## 🧠 ML LEARNING

### Iniciar Ciclo de Aprendizaje

```python
ml_engine = SatelliteMLLearning()

# Start 48h learning cycle
cycle = ml_engine.start_learning_cycle()

print(f"Cycle ID: {cycle.cycle_id}")
print(f"Start: {cycle.start_time}")
print(f"End: {cycle.end_time}")
print(f"Phase: {cycle.phase.value}")
```

### Registrar Performance

```python
from app.satellite_engine import PerformanceMetrics

# Crear métricas de post
metrics = PerformanceMetrics(
    post_id="post_12345",
    account_id="tiktok_shameless_001",
    platform="tiktok",
    published_at=datetime.now(),
    views=50000,
    likes=2500,
    comments=150,
    shares=500,
    saves=800,
    retention_rate=0.85,
    ctr=0.045,
    completion_rate=0.90,
    viral_velocity=2083.33,  # views/hour first 24h
    hour_published=18,
    day_of_week=3  # Thursday
)

# Calcular virality score
virality = metrics.calculate_virality_score()
print(f"Virality score: {virality:.2f}")

# Registrar en ML engine
ml_engine.record_performance(metrics)
```

### Analizar Ciclo

```python
# Después de 48h...
cycle = ml_engine.current_cycle

if len(cycle.metrics_collected) >= 20:  # Suficientes datos
    analyzed_cycle = ml_engine.analyze_cycle(cycle)
    
    print(f"✅ Cycle analyzed")
    print(f"Optimal timings detected: {len(analyzed_cycle.optimal_timings)}")
    print(f"Micro-moments detected: {len(analyzed_cycle.micro_moments)}")
    
    # Ver optimal timings
    for timing in analyzed_cycle.optimal_timings[:5]:
        print(f"  {timing}")
    
    # Ver recommendations
    print("Recommendations:")
    for key, value in analyzed_cycle.recommendations.items():
        print(f"  {key}: {value}")
```

### Aplicar Optimizaciones

```python
# Get recommendations para cuenta
recommendations = ml_engine.get_recommendations("tiktok_shameless_001")

# Aplicar automáticamente
from app.satellite_engine.ml_learning import BehaviorOptimizer

optimizer = BehaviorOptimizer()
optimizations = optimizer.apply_optimizations(
    "tiktok_shameless_001",
    recommendations
)

print(f"Applied {len(optimizations['changes'])} optimizations")
for change in optimizations['changes']:
    print(f"  {change['type']}: {change['reason']}")
```

---

## 🎵 A/B TESTING DE SONIDOS

### Crear Test

```python
sound_engine = SoundTestingEngine()

# Pool de cuentas para test
test_accounts = [f"tiktok_test_{i:03d}" for i in range(1, 11)]

# Create A/B test
test = sound_engine.create_ab_test(
    sound_a_id="stakas_barrio_oro",
    sound_a_name="Barrio con Oro",
    sound_b_id="stakas_noche_plata",
    sound_b_name="Noche de Plata",
    accounts_pool=test_accounts
)

print(f"Test ID: {test.test_id}")
print(f"Sound A accounts: {test.sound_a_accounts}")
print(f"Sound B accounts: {test.sound_b_accounts}")
print(f"Duration: {test.config.test_duration_hours} hours")

# Start test
sound_engine.start_test(test.test_id)
```

### Registrar Performance Durante Test

```python
# Durante el test (cada vez que se publica un post)
sound_engine.record_post_performance(
    test_id=test.test_id,
    sound_id="stakas_barrio_oro",
    post_id="post_001",
    views=15000,
    likes=750,
    comments=50,
    shares=200,
    saves=300,
    ctr=0.05,
    retention=0.85,
    completion_rate=0.92
)

# Monitorear progreso
progress = sound_engine.get_test_progress(test.test_id)

print(f"Progress: {progress['progress_percentage']:.1f}%")
print(f"Hours remaining: {progress['hours_remaining']:.1f}h")
print(f"\nSound A:")
print(f"  Posts: {progress['sound_a']['posts']}")
print(f"  Views: {progress['sound_a']['views']}")
print(f"  Virality: {progress['sound_a']['virality_score']:.2f}")
print(f"\nSound B:")
print(f"  Posts: {progress['sound_b']['posts']}")
print(f"  Views: {progress['sound_b']['views']}")
print(f"  Virality: {progress['sound_b']['virality_score']:.2f}")
```

### Completar Test y Ver Resultados

```python
# Después de 72h...
result = sound_engine.complete_test(test.test_id)

print(f"Winner: {result.winner.value}")
if result.winner_sound_name:
    print(f"Winning sound: {result.winner_sound_name}")
print(f"Sound A score: {result.sound_a_score:.2f}")
print(f"Sound B score: {result.sound_b_score:.2f}")
print(f"Difference: {result.difference_percentage:.1f}%")
print(f"Significant: {result.is_significant}")
print(f"Confidence: {result.confidence:.0%}")
print(f"\nRecommendation: {result.recommendation}")
```

---

## 📊 MONITORING Y MÉTRICAS

### Stats Globales

```python
# Get all stats
behavior_stats = behavior_engine.get_stats()
niche_stats = niche_engine.get_stats()
router_stats = router.get_stats()
warmup_stats = warmup_engine.get_stats()
publishing_stats = publishing_engine.get_stats()
ml_stats = ml_engine.get_stats()
sound_stats = sound_engine.get_stats()

# Display
print("📊 SATELLITE ENGINE STATS")
print(f"\nBehavior:")
print(f"  Total schedules: {behavior_stats['total_schedules']}")
print(f"  Platforms: {behavior_stats['platforms']}")

print(f"\nNiche:")
print(f"  Total niches: {niche_stats['total_niches']}")
print(f"  Assigned accounts: {niche_stats['assigned_accounts']}")
print(f"  Distribution: {niche_stats['niche_distribution']}")

print(f"\nPublishing:")
print(f"  Total identities: {publishing_stats['total_identities']}")
print(f"  Queued tasks: {publishing_stats['queued_tasks']}")
print(f"  Completed: {publishing_stats['completed_tasks']}")
print(f"  Success rate: {publishing_stats['success_rate']:.1f}%")

print(f"\nML Learning:")
print(f"  Total cycles: {ml_stats['total_cycles']}")
print(f"  Completed: {ml_stats['completed_cycles']}")
print(f"  Metrics recorded: {ml_stats['total_metrics_recorded']}")
print(f"  Micro-moments: {ml_stats['micro_moments_detected']}")
```

### Stats Por Cuenta

```python
account_id = "tiktok_shameless_001"

# Behavior
schedule = behavior_engine.get_schedule(account_id)
if schedule:
    print(f"Schedule: {schedule.daily_posts_target} posts/day")
    print(f"Last post: {schedule.last_post_at}")

# Niche
profile = niche_engine.get_account_profile(account_id)
if profile:
    print(f"Niche: {profile.name}")

# Warmup
if warmup_engine.is_in_warmup(account_id):
    progress = warmup_engine.get_warmup_progress(account_id)
    print(f"Warm-up: Day {progress['current_day']}, {progress['posts_today']}/{progress['target_today']}")
else:
    print("Warm-up: Completed")

# Publishing
identity = publishing_engine.get_identity(account_id)
if identity:
    print(f"Identity: {identity.get_fingerprint_hash()}")
```

---

## ✨ BEST PRACTICES

### 1. Anti-Detección

```python
# ✅ GOOD: Usar jitter y randomización
schedule = behavior_engine.create_schedule(
    account_id,
    platform,
    timezone_offset
)

# ✅ GOOD: Verificar anti-correlation
next_time = behavior_engine.get_next_post_time(account_id)

# ❌ BAD: Posts a horario fijo
# fixed_time = datetime.now().replace(hour=14, minute=0)  # NO!
```

### 2. Identidad Única

```python
# ✅ GOOD: Crear identidad única por cuenta
identity = publishing_engine.create_identity(account_id)

# ✅ GOOD: Verificar fingerprint único
hash1 = identity1.get_fingerprint_hash()
hash2 = identity2.get_fingerprint_hash()
assert hash1 != hash2  # Siempre diferente

# ❌ BAD: Reusar identidad entre cuentas
# identity_shared = ...  # NO!
```

### 3. Warm-up Progresivo

```python
# ✅ GOOD: Seguir plan de warm-up
if warmup_engine.is_in_warmup(account_id):
    next_time = warmup_engine.get_next_post_time(account_id)
else:
    # Full speed
    next_time = behavior_engine.get_next_post_time(account_id)

# ❌ BAD: Publicar full speed desde día 1
# Esto triggerea detección de plataforma!
```

### 4. Content Routing

```python
# ✅ GOOD: Usar routing inteligente
decision = router.route_content_to_account(...)
best_content = decision.content_candidate

# ✅ GOOD: Respetar niche matching
if decision.niche_match_score < 0.5:
    print("Warning: Poor niche match")

# ❌ BAD: Asignar contenido random sin routing
# random_content = random.choice(candidates)  # NO!
```

### 5. ML Learning

```python
# ✅ GOOD: Registrar todas las métricas
ml_engine.record_performance(metrics)

# ✅ GOOD: Analizar después de suficientes datos
if len(cycle.metrics_collected) >= 20:
    analyzed = ml_engine.analyze_cycle(cycle)

# ✅ GOOD: Aplicar recomendaciones
recommendations = ml_engine.get_recommendations(account_id)
optimizer.apply_optimizations(account_id, recommendations)
```

---

## 🔧 TROUBLESHOOTING

### Problema: Correlation Events

```python
# Síntoma: Validator detecta correlación
# Solución: Ajustar threshold o espaciamiento

validator = behavior_engine.anti_correlation_validator

# Check stats
stats = validator.get_stats()
if stats['correlation_events'] > 0:
    print("⚠️ Correlation detected! Adjusting schedules...")
    
    # Increase threshold
    validator.correlation_threshold = 10  # 10 min instead of 5
```

### Problema: Low Virality Scores

```python
# Síntoma: Scores bajos consistentemente
# Solución: Revisar routing y timing

# 1. Check niche matching
decision = router.route_content_to_account(...)
if decision.niche_match_score < 0.7:
    print("⚠️ Poor niche match")
    # Usar contenido más alineado al nicho

# 2. Check optimal timing
optimal = ml_engine.get_optimal_timing_for_account(
    account_id,
    day_of_week=datetime.now().weekday()
)
if optimal:
    print(f"Post at {optimal.hour}:00 for best results")
```

### Problema: Warm-up Stuck

```python
# Síntoma: Cuenta stuck en warm-up
# Solución: Forzar advance o reset

plan = warmup_engine.get_plan(account_id)

# Check si debería estar completo
if plan.current_day > 5 and not plan.warmup_completed:
    print("⚠️ Forcing warmup completion")
    plan.warmup_completed = True
    plan.completed_at = datetime.now()
```

### Problema: Publishing Failures

```python
# Síntoma: Muchos publishes fallan
# Solución: Check identity, retry logic

result = publishing_engine.publish(task)

if not result.success:
    print(f"❌ Failed: {result.error}")
    
    # Check identity
    identity = publishing_engine.get_identity(task.account_id)
    if not identity:
        print("Creating new identity...")
        identity = publishing_engine.create_identity(task.account_id)
    
    # Retry
    if task.can_retry():
        print(f"Retrying ({task.retry_count + 1}/{task.max_retries})")
        result = publishing_engine.publish(task)
```

---

## 📞 SUPPORT

Para soporte adicional:
- Documentación completa: `/SPRINT_8_SUMMARY.md`
- Tests de referencia: `/backend/tests/test_satellite_engine.py`
- Código fuente: `/backend/app/satellite_engine/`

---

**Version:** 2.0.0  
**Última actualización:** Diciembre 9, 2025  
**Estado:** Production Ready ✅
