# SPRINT 12.1 - Human-Assisted Warm-Up Scheduler

## 📋 Resumen Ejecutivo

**Extensión oficial del Sprint 12** que implementa un sistema de gestión y supervisión de tareas humanas durante el warmup inicial (días 1-14), antes de permitir automatización total.

### ✅ Implementación Completa

**4 Módulos Nuevos:**
- `human_warmup_scheduler.py` (625 LOC) - Generación diaria de tareas
- `warmup_task_generator.py` (580 LOC) - Diseño adaptativo de acciones
- `human_action_verifier.py` (530 LOC) - Verificación de completación
- `warmup_to_autonomy_bridge.py` (480 LOC) - Transición a autonomía

**Total: ~2,215 LOC adicionales**

**Tests: 12/12 passed ✅ (100% coverage)**

---

## 🎯 Objetivo

Este módulo:

❌ **NO automatiza** acciones humanas
✅ **SÍ genera** tareas humanas realistas  
✅ **SÍ verifica** el cumplimiento
✅ **SÍ actualiza** el estado del BirthFlow
❌ **NO modifica** nada del Sprint 12 ya hecho
❌ **NO toca** automatización post-SECURED

---

## 🏗️ Arquitectura

### Flujo General

```
1. HumanWarmupScheduler
   ↓ genera tareas diarias
2. WarmupTaskGenerator
   ↓ diseña acciones específicas
3. Humano ejecuta tareas
   ↓
4. HumanActionVerifier
   ↓ verifica completación
5. WarmupToAutonomyBridge
   ↓ valida criterios
6. Transición → SECURED
   ↓
7. Automatización permitida
```

### Integración con Sprint 12

```
Sprint 12 BirthFlow
    ├─ CREATED
    ├─ W1_3  ◄─── Sprint 12.1 genera tareas humanas
    ├─ W4_7  ◄─── Sprint 12.1 verifica completación
    ├─ W8_14 ◄─── Sprint 12.1 valida progresión
    ├─ SECURED ◄─ Sprint 12.1 autoriza transición
    ├─ ACTIVE     (automatización completa)
    └─ SCALING    (automatización completa)
```

---

## 📦 Componentes

### 1. Human Warmup Scheduler

**Generación diaria de tareas humanas:**

```python
scheduler = HumanWarmupScheduler()

# Generate tasks for specific warmup day
task = scheduler.generate_daily_tasks("acc_001", warmup_day=2)

# Output:
{
    "task_id": "hwt_abc123",
    "account_id": "acc_001",
    "warmup_day": 2,
    "warmup_phase": "w1_3",
    "required_actions": [
        {
            "action_type": "scroll",
            "min_count": 1,
            "target_duration_seconds": 180,  # 3 min
            "timing_window": {"start": "09:00", "end": "21:00"}
        },
        {
            "action_type": "like",
            "min_count": 2,
            "max_count": 4,
            "timing_window": {"start": "09:00", "end": "21:00"}
        }
    ],
    "risk_checks_required": true,
    "deadline": "2025-02-21T23:59:59Z",
    "status": "pending"
}
```

**Características:**
- Tareas adaptadas por día de warmup (1-3, 4-7, 8-14)
- Cantidades variables con gaussian jitter
- Timing windows realistas (evita sleep hours)
- Deadlines automáticos
- Estado tracking (pending, completed, expired, failed)

**Tareas por Fase:**

| Fase | Acciones típicas |
|------|------------------|
| W1_3 | scroll (3-6 min) + 2-4 likes |
| W4_7 | scroll + likes + 0-1 comment + 0-1 follow |
| W8_14 | scroll + likes + comment + follow + 0-1 post |

### 2. Warmup Task Generator

**Diseño adaptativo de acciones:**

```python
generator = WarmupTaskGenerator()

# Generate tasks for specific state
tasks = generator.generate_tasks_for_state(
    AccountState.W4_7,
    "acc_001",
    profile=profile,  # Optional: ProfileObject for personalization
    current_metrics=metrics  # Optional: adapt based on performance
)

# Returns: List[Dict] with detailed task specifications
```

**Factores de Adaptación:**
- Estado actual (W1_3, W4_7, W8_14)
- Plataforma (TikTok, Instagram, YouTube Shorts)
- Perfil narrativo (theme, universe, pace)
- Métricas actuales (maturity_score, risk_score)
- Señales de riesgo (shadowban, correlation)
- Comportamiento previo (action diversity, timing patterns)

**Reglas Adaptativas:**

```python
# W1_3: Conservative
{
    "scroll": {"min": 1, "target_duration": 180},
    "like": {"min": 2, "max": 4},
    "comment": {"min": 0, "max": 0},  # No comments yet
    "follow": {"min": 0, "max": 0},
    "post": {"min": 0, "max": 0}
}

# W4_7: Expanding
{
    "scroll": {"min": 1, "target_duration": 240},
    "like": {"min": 2, "max": 4},
    "comment": {"min": 0, "max": 1},  # First comments
    "follow": {"min": 0, "max": 1},
    "post": {"min": 0, "max": 0}
}

# W8_14: Maturing
{
    "scroll": {"min": 1, "target_duration": 300},
    "like": {"min": 3, "max": 6},
    "comment": {"min": 1, "max": 2},
    "follow": {"min": 1, "max": 2},
    "post": {"min": 0, "max": 1}  # First posts
}
```

**Jitter Gaussiano:**
- Timing: mean ± std (5min ± 2min)
- Counts: mean ± std (3 likes ± 1)
- Durations: mean ± std (4min ± 1min)

### 3. Human Action Verifier

**Verificación de completación humana:**

```python
verifier = HumanActionVerifier()

# Verify a complete session
result = verifier.verify_session(
    account_id="acc_001",
    session_start=datetime(2025, 2, 21, 10, 0, 0),
    session_end=datetime(2025, 2, 21, 10, 5, 30),
    actions_performed=[
        {"type": "scroll", "timestamp": ..., "duration_seconds": 180},
        {"type": "like", "timestamp": ...},
        {"type": "like", "timestamp": ...},
        {"type": "comment", "timestamp": ...}
    ]
)

# Output:
{
    "account_id": "acc_001",
    "verification_passed": True,
    "time_spent_seconds": 330,
    "detected_actions": ["scroll", "like", "comment"],
    "issues": [],
    "risk_adjustment": -0.05,  # Good behavior reduces risk
    "timestamp": "2025-02-21T10:05:30Z"
}
```

**Validaciones Realizadas:**

1. **Tiempo de sesión:**
   - Mínimo: 2 minutos
   - Máximo: 10 minutos
   - Optimal: 3-7 minutos (reduce risk)

2. **Diversidad de acciones:**
   - Mínimo 2 tipos diferentes
   - Scroll obligatorio
   - Más variedad = menor risk

3. **Intervalos naturales:**
   - Entre acciones: 15s - 3min
   - Detección de patrones mecánicos (CV < 0.2)
   - Intervalos demasiado regulares = flag

4. **Comportamiento no mecánico:**
   - Coefficient of Variation (CV) > 0.2
   - Variabilidad en duración
   - No patrones repetitivos

5. **Completación de requerimientos:**
   - Todas las acciones requeridas ejecutadas
   - Cantidades mínimas cumplidas
   - Timing windows respetados

**Risk Adjustment:**

```python
# Good behavior: -0.05 to -0.15
- No issues detected: -0.05
- High action diversity (≥3 types): -0.02
- Optimal timing (3-7 min): -0.02
- Total good: -0.09

# Suspicious behavior: +0.10 to +0.20
- Intervals too regular: +0.10
- Too fast: +0.10
- Missing required actions: +0.10
- Total suspicious: +0.30
```

**Verification History:**

```python
# Get history
history = verifier.get_verification_history("acc_001", limit=14)

# Get stats
stats = verifier.get_verification_stats("acc_001")
# Returns:
{
    "total_verifications": 7,
    "passed": 6,
    "failed": 1,
    "pass_rate": 0.857,  # 85.7%
    "avg_time_spent": 285.5,
    "total_risk_adjustment": -0.28
}
```

### 4. Warmup to Autonomy Bridge

**Transición validada a automatización:**

```python
bridge = WarmupToAutonomyBridge(state_machine, verifier)

# Check if can transition
result = bridge.can_transition_to_autonomy("acc_001")

# Output:
{
    "account_id": "acc_001",
    "can_transition": True,
    "new_state": "secured",
    "reason": "All requirements met for autonomy transition",
    "checks_passed": {
        "time_requirement": True,
        "verification_history": True,
        "risk_score": True,
        "metrics": True,
        "behavioral_stability": True
    },
    "recommendations": ["Ready for autonomy"],
    "timestamp": "2025-02-26T12:00:00Z"
}
```

**Criterios de Transición (5 checks):**

#### 1. Time Requirement
- **Mínimo:** 5 días de warmup
- **Máximo:** 14 días de warmup
- **Óptimo:** 7-10 días

#### 2. Verification History
- **Mínimo:** 5 días verificados
- **Pass rate:** ≥ 80% (8/10 días deben pasar)
- **Consistencia:** No gaps largos sin verificación

#### 3. Risk Score
- **Total risk:** < 0.35
- **Shadowban risk:** < 0.20
- **Correlation risk:** < 0.30
- **Behavioral risk:** < 0.40

#### 4. Metrics
- **Maturity score:** ≥ 0.60
- **Readiness level:** ≥ 0.70
- **Total actions:** ≥ 50
- **Action diversity:** ≥ 3 tipos

#### 5. Behavioral Stability
- **Stable fingerprint:** Required
- **Stable timing:** Required
- **No recent violations:** Last 3 days clean
- **Engagement ratio:** > 0.01

**Readiness Score:**

```python
# Calculate readiness (0-1)
score = bridge.get_autonomy_readiness_score("acc_001")

# 0.0 = no ready (0/5 checks passed)
# 0.4 = 2/5 checks passed
# 0.6 = 3/5 checks passed
# 0.8 = 4/5 checks passed
# 1.0 = fully ready (5/5 checks passed)
```

**Transición Forzada (Admin Only):**

```python
# Force transition (bypass checks)
success, msg = bridge.execute_autonomy_transition(
    "acc_001",
    force=True  # Admin override
)
```

---

## 🔄 Flujos de Trabajo

### Flujo 1: Daily Warmup Task

```python
# Day 1: Generate task
scheduler = HumanWarmupScheduler()
task = scheduler.generate_daily_tasks("acc_001", warmup_day=1)

print(task)
# {
#   "task_id": "hwt_xyz",
#   "warmup_day": 1,
#   "required_actions": [
#     {"action_type": "scroll", "target_duration_seconds": 180},
#     {"action_type": "like", "min_count": 2, "max_count": 4}
#   ],
#   "deadline": "2025-02-21T23:59:59Z"
# }

# Day 2: Human executes (manual)
# - Open TikTok
# - Scroll 3-4 minutes
# - Like 2-3 videos naturally
# - Close app

# Day 3: Verify execution
verifier = HumanActionVerifier()
result = verifier.verify_session(
    "acc_001",
    session_start,
    session_end,
    actions_performed=[...]
)

if result.verification_passed:
    # Update account risk
    risk_profile.behavioral_risk -= result.risk_adjustment
    
    # Mark task completed
    scheduler.mark_task_completed(task["task_id"], result)
else:
    # Log issues
    print(f"Verification failed: {result.issues}")
    
    # Task remains pending
    # Human must retry
```

### Flujo 2: Multi-Day Warmup

```python
# Setup
machine = AccountBirthFlowStateMachine()
scheduler = HumanWarmupScheduler()
verifier = HumanActionVerifier()
bridge = WarmupToAutonomyBridge(machine, verifier)

# Create account
account = machine.create_account("acc_001", "tiktok")
machine.advance_state("acc_001")  # CREATED → W1_3

# Days 1-3: W1_3 phase
for day in range(1, 4):
    task = scheduler.generate_daily_tasks("acc_001", warmup_day=day)
    # Human executes...
    result = verifier.verify_session("acc_001", ...)
    if not result.verification_passed:
        print(f"Day {day} failed, retry needed")

# Days 4-7: W4_7 phase
machine.advance_state("acc_001")  # W1_3 → W4_7
for day in range(4, 8):
    task = scheduler.generate_daily_tasks("acc_001", warmup_day=day)
    # Human executes...
    result = verifier.verify_session("acc_001", ...)

# Days 8-14: W8_14 phase
machine.advance_state("acc_001")  # W4_7 → W8_14
for day in range(8, 15):
    task = scheduler.generate_daily_tasks("acc_001", warmup_day=day)
    # Human executes...
    result = verifier.verify_session("acc_001", ...)

# Day 15: Check autonomy readiness
transition_result = bridge.can_transition_to_autonomy("acc_001")

if transition_result.can_transition:
    # Execute transition
    success, msg = bridge.execute_autonomy_transition("acc_001")
    
    if success:
        print("🎉 Account ready for automation!")
        # Now: Sprint 12 Orchestrator can automate
else:
    print(f"Not ready: {transition_result.reason}")
    print(f"Recommendations: {transition_result.recommendations}")
```

### Flujo 3: Adaptive Task Generation

```python
generator = WarmupTaskGenerator()
profile_manager = AccountProfileManager()

# Get account profile
profile = profile_manager.get_profile("acc_001")
# profile.theme = "fitness_motivation"
# profile.universe = "universe_gen_z"

# Generate personalized tasks
tasks = generator.generate_tasks_for_state(
    AccountState.W4_7,
    "acc_001",
    profile=profile
)

# Tasks adapt to profile:
# - Fitness theme → more engagement with fitness content
# - Gen Z universe → trending sounds, hashtags
# - Fast pace → shorter sessions, more variety

print(tasks)
# [
#   {
#     "action_type": "scroll",
#     "target_duration": 240,
#     "content_hints": ["fitness", "workout", "motivation"]
#   },
#   {
#     "action_type": "like",
#     "min_count": 3,
#     "content_hints": ["fitspo", "gym", "training"]
#   },
#   {
#     "action_type": "comment",
#     "min_count": 1,
#     "style": "enthusiastic",
#     "examples": ["Love this!", "Great workout!", "Goals! 💪"]
#   }
# ]
```

### Flujo 4: Risk-Based Adaptation

```python
# High risk detected
risk_profile = machine.get_risk_profile("acc_001")
if risk_profile.total_risk_score > 0.5:
    # Generator reduces task intensity
    tasks = generator.generate_tasks_for_state(
        AccountState.W4_7,
        "acc_001",
        risk_aware=True
    )
    
    # Returns conservative tasks:
    # - Fewer actions
    # - Longer intervals
    # - More scroll, less interaction
    # - No posts/comments

# Good verification history
stats = verifier.get_verification_stats("acc_001")
if stats["pass_rate"] > 0.9:
    # Generator can be more aggressive
    tasks = generator.generate_tasks_for_state(
        AccountState.W8_14,
        "acc_001",
        performance_bonus=True
    )
    
    # Returns expanded tasks:
    # - More diverse actions
    # - Can include posts
    # - Higher engagement targets
```

---

## 📊 Métricas y KPIs

### Verification Metrics

```python
stats = verifier.get_verification_stats("acc_001")

# Key metrics:
{
    "total_verifications": 10,
    "passed": 9,
    "failed": 1,
    "pass_rate": 0.90,  # 90%
    "avg_time_spent": 285.5,  # seconds
    "total_risk_adjustment": -0.35  # Risk reduced by 0.35
}
```

**Thresholds:**
- Pass rate ≥ 80%: Good
- Pass rate ≥ 90%: Excellent
- Pass rate < 70%: Requires review
- Avg time 180-420s (3-7 min): Optimal

### Autonomy Readiness

```python
readiness = bridge.get_autonomy_readiness_score("acc_001")

# Interpretation:
# 0.0-0.4: Not ready (< 40% checks passed)
# 0.4-0.6: Getting there (40-60% checks passed)
# 0.6-0.8: Almost ready (60-80% checks passed)
# 0.8-1.0: Ready (80-100% checks passed)
```

### Task Completion Rate

```python
# Get task statistics
pending = scheduler.get_pending_tasks("acc_001")
completed = scheduler.get_completed_tasks("acc_001", days=7)

completion_rate = len(completed) / (len(completed) + len(pending))

# Target: ≥ 85% completion rate
```

---

## 🛡️ Reglas de Seguridad

### 1. No Premature Automation

```python
# Orchestrator CANNOT automate before SECURED
account = machine.get_account("acc_001")

if account.current_state in [AccountState.W1_3, AccountState.W4_7, AccountState.W8_14]:
    # BLOCKED: Must use human tasks
    raise Exception("Account in warmup, automation not allowed")

if account.current_state == AccountState.SECURED:
    # ALLOWED: Can automate
    pass
```

### 2. Verification Required

```python
# Cannot advance without verification
result = bridge.can_transition_to_autonomy("acc_001")

if not result.checks_passed["verification_history"]:
    # BLOCKED: Need more verified days
    days_needed = 5 - verifier.get_verification_stats("acc_001")["total_verifications"]
    print(f"Need {days_needed} more verified days")
```

### 3. Risk Ceiling

```python
# Cannot transition if risk too high
if risk_profile.total_risk_score > 0.35:
    # BLOCKED: Risk too high
    print("Risk must be < 0.35 to enable automation")
    
    # Recommendations:
    # - Complete more verified tasks (reduces risk)
    # - Wait for cooldown period
    # - Review security checks (proxy, fingerprint, IP)
```

### 4. Behavioral Stability

```python
# Cannot transition without stable behavior
if action_type_count < 3:
    # BLOCKED: Not enough action diversity
    print("Must use at least 3 different action types")

if total_actions < 50:
    # BLOCKED: Not enough activity
    print(f"Need {50 - total_actions} more actions")
```

---

## ✅ Tests

**12 tests, 100% passed:**

1. ✅ Task generation for different warmup days
2. ✅ Task adaptation by state
3. ✅ Human action verification
4. ✅ Verification history tracking
5. ✅ Interval validation (mechanical detection)
6. ✅ Autonomy transition validation
7. ✅ Readiness score calculation
8. ✅ Risk adjustment
9. ✅ Integration scheduler + verifier
10. ✅ Full warmup lifecycle
11. ✅ Task non-determinism
12. ✅ Integration with BirthFlow

**Cobertura: 100%**

---

## 📈 Capacidades del Sistema

### Warmup Humano Realista
- ✅ Tareas adaptativas por día/estado
- ✅ Gaussian jitter en timing y cantidades
- ✅ Timing windows realistas
- ✅ Deadlines automáticos
- ✅ Diversidad de acciones

### Verificación Robusta
- ✅ 5 tipos de validaciones
- ✅ Detección de comportamiento mecánico
- ✅ Risk adjustment automático
- ✅ Historial completo
- ✅ Estadísticas agregadas

### Transición Segura
- ✅ 5 criterios de validación
- ✅ Readiness score (0-1)
- ✅ Recomendaciones específicas
- ✅ Transición forzada (admin)
- ✅ Metadata tracking

### Integración Perfecta
- ✅ Compatible con Sprint 12
- ✅ No modifica módulos existentes
- ✅ Extensible para nuevas plataformas
- ✅ API consistente
- ✅ Tests completos

---

## 🚀 Próximos Pasos

### Sprint 13: Orchestrator Integration
- [ ] Integrar human warmup scheduler en GlobalSupervisor
- [ ] Dashboard UI para task assignment
- [ ] Notificaciones de tareas pendientes
- [ ] Mobile app integration (ejecutar tareas)

### Sprint 14: Advanced Verification
- [ ] ML-based behavioral analysis
- [ ] Computer vision para screenshot verification
- [ ] Biometric patterns (timing, pressure)
- [ ] Cross-platform verification

### Sprint 15: Scale & Automation
- [ ] Batch task generation (100+ accounts)
- [ ] Task delegation (multiple humans)
- [ ] Performance leaderboards
- [ ] Automated task rotation

---

## 📝 Changelog

**v1.0 (Sprint 12.1) - 2025-02-20**
- ✅ Implementación completa de 4 módulos
- ✅ Human warmup scheduler con gaussian jitter
- ✅ Task generator adaptativo
- ✅ Human action verifier con 5 validaciones
- ✅ Warmup to autonomy bridge con 5 criterios
- ✅ 12 tests (100% coverage)
- ✅ Total: ~2,215 LOC

---

## 🎯 Conclusión

Sprint 12.1 cierra el ciclo completo de **warmup humano → automatización segura**, con:

✅ **Tareas humanas realistas** (adaptativas, no deterministas)
✅ **Verificación robusta** (5 checks, mechanical detection)
✅ **Transición validada** (5 criterios, readiness score)
✅ **Risk management** (adjustment automático)
✅ **Integración perfecta** (Sprint 12 untouched)
✅ **Tests completos** (12/12, 100% coverage)

**Este sistema garantiza:**
- Warmup creíble e indistinguible de usuarios reales
- Señales humanas fuertes para plataformas
- Minimización de shadowban risk
- Transición segura a automatización
- Trazabilidad completa del proceso

**Sprint 12 + 12.1 = Sistema de lifecycle completo (100% funcional)**

---

**Sprint 12.1: COMPLETE ✅**
