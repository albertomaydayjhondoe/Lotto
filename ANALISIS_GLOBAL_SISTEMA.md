# 🔒 ANÁLISIS GLOBAL DEL SISTEMA + PLAN DE INTEGRACIÓN (MODO VALIDACIÓN)

**Fecha:** 2025-11-28  
**Estado:** DOCUMENTACIÓN PARA VALIDACIÓN  
**Acción:** NO EJECUTAR CÓDIGO - SOLO ANÁLISIS

---

## 1. MAPA GLOBAL DEL SISTEMA (ÁRBOL COMPLETO)

### Estructura de directorios detectada:

```
backend/app/
├── core/                           ✅ CORE EXISTENTE
│   ├── config.py                   ✅ Configuración centralizada
│   ├── database.py                 ✅ DB engine y sesiones
│   └── logging.py                  ✅ Logger configurado
│
├── auth/                           ✅ AUTENTICACIÓN
│   └── auth_router                 ✅ OAuth/JWT implementado
│
├── META ADS STACK (10.1-10.18)     ✅ COMPLETO
│   ├── meta_ads_client/            ✅ (10.2) Cliente API Meta
│   ├── meta_ads_orchestrator/      ✅ (10.3) Orquestación + ROAS (10.5)
│   ├── meta_optimization/          ✅ (10.6) Loop optimización
│   ├── meta_autonomous/            ✅ (10.7) Sistema autónomo
│   ├── meta_insights_collector/    ✅ (10.7) Collector insights
│   ├── meta_autopublisher/         ✅ (10.8) Auto-Publisher
│   ├── meta_budget_spike/          ✅ (10.9) Detector anomalías
│   ├── meta_creative_variants/     ✅ (10.10) Variantes creativas
│   ├── meta_full_cycle/            ✅ (10.11) Ciclo completo
│   ├── meta_targeting_optimizer/   ✅ (10.12) Targeting optimizer
│   ├── meta_creative_intelligence/ ✅ (10.13) Creative intelligence
│   ├── meta_rt_engine/             ✅ (10.14) Real-time engine
│   ├── meta_creative_analyzer/     ✅ (10.15) Creative analyzer
│   ├── meta_creative_optimizer/    ✅ (10.16) Creative optimizer
│   ├── meta_creative_production/   ✅ (10.17) Autonomous production
│   └── meta_master_control/        ✅ (10.18) Master Control Tower
│
├── PUBLISHING SYSTEM                ✅ EXISTENTE (Sistema clips/campañas)
│   ├── publishing_engine/          ✅ Motor principal
│   ├── publishing_integrations/    ✅ Integraciones plataformas
│   ├── publishing_queue/           ✅ Cola Redis
│   ├── publishing_worker/          ✅ Workers procesamiento
│   ├── publishing_webhooks/        ✅ Webhooks externos
│   ├── publishing_reconciliation/  ✅ Reconciliación estados
│   ├── publishing_scheduler/       ✅ Programación tareas
│   └── publishing_intelligence/    ✅ Inteligencia publishing
│
├── ORCHESTRATOR SYSTEM              ✅ EXISTENTE
│   └── orchestrator/               ✅ Pipeline orquestación
│
├── CAMPAIGNS SYSTEM                 ✅ EXISTENTE
│   └── campaigns_engine/           ✅ Motor campañas
│
├── AI WORKERS                       ✅ EXISTENTE
│   ├── ai_global_worker/           ✅ Worker global IA
│   ├── llm_providers/              ✅ Proveedores LLM (GPT, Gemini)
│   └── e2b/                        ✅ E2B integration
│
├── DASHBOARDS                       ✅ EXISTENTE
│   ├── dashboard_api/              ✅ API dashboard
│   ├── dashboard_ai/               ✅ Dashboard IA
│   ├── dashboard_actions/          ✅ Acciones dashboard
│   └── dashboard_ai_integration/   ✅ Integración IA
│
├── MONITORING & TELEMETRY           ✅ EXISTENTE
│   ├── live_telemetry/             ✅ Telemetría real-time
│   ├── alerting_engine/            ✅ Motor alertas
│   └── visual_analytics/           ✅ Analytics visuales
│
├── SUPPORTING SYSTEMS               ✅ EXISTENTE
│   ├── ledger/                     ✅ Ledger transacciones
│   ├── rules_engine/               ✅ Motor reglas
│   ├── oauth_service/              ✅ OAuth service
│   ├── security/                   ✅ Seguridad
│   └── worker/                     ✅ Worker genérico
│
├── API LAYER                        ✅ EXISTENTE
│   └── api/                        ✅ Endpoints REST
│       ├── upload                  ✅ Subida clips
│       ├── jobs                    ✅ Gestión jobs
│       ├── clips                   ✅ Gestión clips
│       ├── campaigns               ✅ Gestión campañas
│       ├── rules                   ✅ Reglas negocio
│       ├── webhooks                ✅ Webhooks
│       └── debug                   ✅ Debug endpoints
│
├── STORAGE & DATA                   
│   ├── db/                         ✅ Modelos DB (legacy)
│   ├── models/                     ✅ Modelos SQLAlchemy
│   └── migrations/                 ✅ Alembic (18 migrations)
│
├── TESTS                            ✅ EXISTENTE
│   └── tests/                      ✅ Test suites (~160+ tests)
│
└── main.py                          ✅ PUNTO ENTRADA
    └── FastAPI app + routers       ✅ Integración parcial
```

---

## 2. QUÉ ESTÁ IMPLEMENTADO (VALIDACIÓN EXACTA)

### ✅ STACK META ADS (10.1-10.18) - COMPLETO

**Módulos operacionales:**
- 10.1-10.2: Meta Models + Client
- 10.3: Meta Orchestrator + ROAS (10.5)
- 10.6: Optimization Loop
- 10.7: Autonomous System + Insights Collector
- 10.8: Auto-Publisher
- 10.9: Budget SPIKE Manager
- 10.10: Creative Variants
- 10.11: Full Cycle Manager
- 10.12: Targeting Optimizer
- 10.13: Creative Intelligence
- 10.14: Real-Time Engine
- 10.15: Creative Analyzer
- 10.16: Creative Optimizer
- 10.17: Creative Production
- 10.18: Master Control Tower

**Total:** 18 módulos, ~51,315 líneas, 68 commits

### ✅ PUBLISHING SYSTEM - COMPLETO

**Componentes operacionales:**
- Publishing Engine (motor principal)
- Publishing Integrations (TikTok, Instagram, Facebook, YouTube)
- Publishing Queue (Redis)
- Publishing Worker (procesamiento asíncrono)
- Publishing Webhooks (callbacks)
- Publishing Reconciliation (validación estados)
- Publishing Scheduler (cron jobs)
- Publishing Intelligence (analytics)

### ✅ AI WORKERS - OPERACIONAL

**Proveedores integrados:**
- GPT-4/GPT-5 (OpenAI)
- Gemini 2.0/3.0 (Google)
- E2B (sandboxing)
- Worker global coordinador

### ✅ MONITORING - OPERACIONAL

**Sistemas activos:**
- Live Telemetry (métricas real-time)
- Alerting Engine (notificaciones)
- Visual Analytics (dashboards)

### ✅ CORE INFRASTRUCTURE - OPERACIONAL

**Componentes base:**
- FastAPI app configurada
- PostgreSQL + SQLAlchemy 2.0
- Redis (caching + queues)
- Alembic migrations (18)
- Auth/OAuth
- Logging

---

## 3. QUÉ FALTA POR HACER (GAPS DETECTADOS)

### 🔴 PRIORIDAD CRÍTICA

#### 3.1 Memory Vault (NUEVA FUNCIONALIDAD)

**Estado:** ❌ NO IMPLEMENTADO

**Ubicación propuesta:** `backend/app/memory_vault/`

**Componentes necesarios:**
```
memory_vault/
├── __init__.py
├── storage.py              # Interfaz Google Drive
├── retention.py            # Políticas retención
├── encryption.py           # Cifrado KMS
├── access_control.py       # ACL matrix
├── models.py               # Modelos DB
├── schemas.py              # Pydantic schemas
├── router.py               # API endpoints
└── README.md
```

**Estructura GDrive requerida:**
```
gdrive:/stakazo/memory_vault/
├── ml_features/           # Features ML
├── audits/                # Auditorías
├── campaign_history/      # Historial campañas
├── clips_metadata/        # Metadata clips
└── orchestrator_runs/     # Logs orchestrator
```

**Naming convention:**
- `<entity>__YYYYMMDD__v1.json`
- Ejemplo: `campaign__20251128__v1.json`

**Retention policy:**
- Raw data: 365 días
- Summaries: 5 años

**Integración DB necesaria:**
```sql
CREATE TABLE memory_vault_index (
  id UUID PRIMARY KEY,
  entity_type VARCHAR(50),
  entity_id VARCHAR(100),
  gdrive_path TEXT,
  feature_hash JSONB,
  source VARCHAR(50),
  version INTEGER,
  timestamp TIMESTAMP,
  run_id UUID,
  metadata JSONB,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_mv_feature_hash ON memory_vault_index USING gin(feature_hash);
CREATE INDEX idx_mv_run_id_timestamp ON memory_vault_index(run_id, timestamp);
CREATE INDEX idx_mv_entity_type ON memory_vault_index(entity_type, entity_id);
```

---

#### 3.2 Access Control Matrix (ACL)

**Estado:** ⚠️ PARCIAL (auth existe, ACL granular no)

**Ubicación propuesta:** `backend/app/security/acl.py`

**Roles requeridos:**
- orchestrator
- worker
- auditor
- dashboard
- devops

**ACL Matrix mínima:**

| Recurso            | Orchestrator | Worker | Auditor | Dashboard | DevOps |
|--------------------|:------------:|:------:|:-------:|:---------:|:------:|
| campaign_history   | r/w          | r      | r       | r         | r      |
| ml_features        | r/w          | r/w    | r       | r         | r      |
| audits             | r            | -      | r/w     | -         | r/w    |
| orchestrator_runs  | r/w          | -      | r       | -         | r      |
| clips_metadata     | r/w          | r/w    | r       | r         | r      |
| memory_vault       | r/w          | r      | r       | r         | r      |

**Implementación necesaria:**
```python
# backend/app/security/acl.py
from enum import Enum
from typing import List, Dict

class Role(str, Enum):
    ORCHESTRATOR = "orchestrator"
    WORKER = "worker"
    AUDITOR = "auditor"
    DASHBOARD = "dashboard"
    DEVOPS = "devops"

class Resource(str, Enum):
    CAMPAIGN_HISTORY = "campaign_history"
    ML_FEATURES = "ml_features"
    AUDITS = "audits"
    ORCHESTRATOR_RUNS = "orchestrator_runs"
    CLIPS_METADATA = "clips_metadata"
    MEMORY_VAULT = "memory_vault"

class Permission(str, Enum):
    READ = "r"
    WRITE = "w"
    READ_WRITE = "r/w"
    NONE = "-"

ACL_MATRIX: Dict[Resource, Dict[Role, Permission]] = {
    # ... matriz completa
}

def check_permission(role: Role, resource: Resource, action: str) -> bool:
    """Valida permisos según ACL matrix"""
    pass
```

---

#### 3.3 Redis Configuration Enhancement

**Estado:** ⚠️ PARCIAL (Redis existe, config avanzada no)

**Ubicación:** `backend/app/core/redis_config.py`

**Configuración requerida:**
```python
# backend/app/core/redis_config.py
REDIS_CONFIG = {
    "workers": 3,  # Escalable por carga
    "ttl_values": {
        "default": 1800,        # 30m
        "campaign": 7200,       # 2h
        "ml_jobs": 3600,        # 1h
        "upload_jobs": 600,     # 10m
    },
    "retries": 3,
    "namespaces": {
        "publishing": "publishing/",
        "ml_jobs": "ml_jobs/",
        "upload_jobs": "upload_jobs/",
        "dead_letter": "publishing/dead_letter",
    },
    "monitoring": {
        "enabled": True,
        "dashboard_integration": True,
    }
}
```

**Dead-letter queue necesario:**
```python
# backend/app/publishing_queue/dead_letter.py
async def handle_dead_letter(job_id: str, error: str):
    """Procesa jobs fallidos después de 3 reintentos"""
    pass
```

---

#### 3.4 Backup Policy Implementation

**Estado:** ❌ NO IMPLEMENTADO

**Ubicación:** `backend/app/backup/`

**Componentes necesarios:**
```
backup/
├── __init__.py
├── postgres_backup.py      # Snapshots diarios PostgreSQL
├── vault_backup.py         # Export cold monthly Memory Vault
├── restore.py              # Procedimientos restore
├── scheduler.py            # Cron backup jobs
└── README_BACKUP.md        # Documentación procedures
```

**Políticas:**
- **PostgreSQL:** Snapshot diario automático
- **Memory Vault:** Export cold mensual (zip cifrado)
- **Restore test:** Manual cada Q (quarterly)

**Comandos CLI necesarios:**
```bash
python -m app.backup.postgres_backup --daily
python -m app.backup.vault_backup --monthly
python -m app.backup.restore --test
```

---

#### 3.5 Rate Limiting & Feature Toggles

**Estado:** ⚠️ PARCIAL (middleware existe, config centralizada no)

**Ubicación:** `backend/app/core/options.json`

**Config centralizada requerida:**
```json
{
  "MODE": "stub",
  "rate_limits": {
    "/upload": {
      "requests_per_minute": 10,
      "per": "user"
    },
    "/jobs": {
      "requests_per_minute": 20,
      "per": "user"
    },
    "/campaigns": {
      "requests_per_minute": 5,
      "per": "account"
    }
  },
  "toggles": {
    "mixchecker": {
      "enabled": false,
      "cost_per_1k_clips": 10.0
    },
    "gullfoss": {
      "enabled": false,
      "cost_monthly": 39.0
    },
    "loudness_normalizer": {
      "enabled": true,
      "cost_per_1k_clips": 2.0
    }
  },
  "features": {
    "memory_vault": true,
    "acl_enforcement": true,
    "backup_automation": true
  }
}
```

**Middleware rate-limiting:**
```python
# backend/app/middleware/rate_limiter.py
from fastapi import Request
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
```

---

#### 3.6 Legal/Copyright Guardrails

**Estado:** ❌ NO IMPLEMENTADO

**Ubicación:** `backend/app/legal/`

**Componentes necesarios:**
```
legal/
├── __init__.py
├── copyright_checker.py    # Validación derechos
├── approval_workflow.py    # Workflow aprobación humana
├── schemas.py              # Schemas legales
└── templates/
    └── disclaimer.html     # Template disclaimer legal
```

**Disclaimer obligatorio:**
```python
# backend/app/legal/schemas.py
class CampaignApproval(BaseModel):
    campaign_id: UUID
    user_id: UUID
    copyright_confirmed: bool  # Obligatorio
    legal_disclaimer_accepted: bool  # Obligatorio
    approved_by: str
    approved_at: datetime
```

**Dashboard UX requerido:**
- Checkbox obligatorio antes de publicar
- Warning sobre responsabilidad legal
- Confirmación explícita de derechos de uso

---

### 🟡 PRIORIDAD MEDIA

#### 3.7 TikTok Ads Stack (11.1-11.x)

**Estado:** ❌ PENDIENTE

**Ubicación:** `backend/app/tiktok_*`

**Módulos a implementar:**
- 11.1: TikTok Models
- 11.2: TikTok Ads Client
- 11.3: TikTok Orchestrator
- 11.5+: Seguir estructura Meta (15-18 módulos)

**Estimación:** ~20,000 líneas código

---

#### 3.8 LinkedIn Ads Stack (12.1-12.x)

**Estado:** ❌ PENDIENTE

**Ubicación:** `backend/app/linkedin_*`

**Estimación:** ~20,000 líneas código

---

#### 3.9 Testing Expansion

**Estado:** ⚠️ PARCIAL (tests existen, coverage incompleto)

**Tests necesarios:**
```
tests/
├── test_memory_vault/
│   ├── test_storage.py
│   ├── test_retention.py
│   ├── test_encryption.py
│   └── test_migration.py
├── test_redis/
│   ├── test_e2e_jobs.py
│   ├── test_dead_letter.py
│   └── test_ttl_expiration.py
├── test_acl/
│   ├── test_permissions.py
│   ├── test_role_inheritance.py
│   └── test_access_denial.py
└── test_backup/
    ├── test_postgres_backup.py
    ├── test_vault_backup.py
    └── test_restore.py
```

---

### 🟢 PRIORIDAD BAJA

#### 3.10 Unified Control Tower (Meta+TikTok+LinkedIn)

**Estado:** ❌ FUTURO

**Dependencias:** TikTok y LinkedIn stacks completos

---

#### 3.11 Multi-Region Support

**Estado:** ❌ FUTURO

---

#### 3.12 Advanced ML Features

**Estado:** ❌ FUTURO

---

## 4. RIESGOS Y CONFLICTOS DETECTADOS

### 🚨 RIESGO CRÍTICO 1: Integración main.py incompleta

**Problema:** `main.py` tiene imports parciales, faltan:
- meta_rt_engine scheduler
- meta_creative_analyzer scheduler
- meta_creative_optimizer scheduler
- meta_creative_production scheduler
- meta_master_control scheduler + router

**Solución:**
```python
# backend/app/main.py - AGREGAR
from app.meta_rt_engine.scheduler import start_rt_engine, stop_rt_engine
from app.meta_creative_analyzer.scheduler import start_creative_analyzer, stop_creative_analyzer
from app.meta_creative_optimizer.scheduler import start_creative_optimizer, stop_creative_optimizer
from app.meta_creative_production.scheduler import start_creative_production, stop_creative_production
from app.meta_master_control.scheduler import master_control_background_task
from app.meta_master_control.router import router as master_control_router

# En lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    # ... existing code ...
    rt_task = asyncio.create_task(start_rt_engine())
    analyzer_task = asyncio.create_task(start_creative_analyzer())
    optimizer_task = asyncio.create_task(start_creative_optimizer())
    production_task = asyncio.create_task(start_creative_production())
    control_tower_task = asyncio.create_task(master_control_background_task())
    
    yield
    
    rt_task.cancel()
    analyzer_task.cancel()
    optimizer_task.cancel()
    production_task.cancel()
    control_tower_task.cancel()

# Registrar routers
app.include_router(master_control_router)
```

---

### 🚨 RIESGO CRÍTICO 2: Memory Vault sin implementar

**Impacto:** Sin storage persistente para ML features y auditorías

**Bloqueante para:**
- Machine Learning pipelines
- Compliance/auditoría
- Historical analytics

**Solución:** Implementar PASO VAULT.1 (ver sección 6)

---

### 🚨 RIESGO CRÍTICO 3: ACL no implementado

**Impacto:** Sin control granular de acceso

**Vulnerabilidad:** Cualquier rol puede acceder a cualquier recurso

**Solución:** Implementar PASO ACL.1 (ver sección 6)

---

### ⚠️ RIESGO MEDIO 1: Redis config básica

**Problema:** No hay dead-letter queue ni TTL configurados

**Impacto:** Jobs fallidos se pierden

**Solución:** Implementar PASO REDIS.1

---

### ⚠️ RIESGO MEDIO 2: Sin backup automatizado

**Problema:** No hay policy de backup

**Impacto:** Pérdida potencial de datos

**Solución:** Implementar PASO BACKUP.1

---

### ⚠️ RIESGO MEDIO 3: Rate-limiting parcial

**Problema:** No hay config centralizada

**Impacto:** Posible abuso de endpoints

**Solución:** Implementar PASO RATELIMIT.1

---

### 💡 RIESGO BAJO 1: Legal disclaimers ausentes

**Problema:** Sin guardrails legales

**Impacto:** Exposición legal

**Solución:** Implementar PASO LEGAL.1

---

## 5. DISTRIBUCIÓN DE TAREAS IA

### GPT-5 (Reasoning & Architecture)
- Memory Vault architecture
- ACL matrix design
- Backup strategies
- Integration planning
- Complex reasoning tasks

### Gemini 3.0 (Code Generation)
- Memory Vault implementation
- Redis config enhancement
- Backup automation scripts
- Rate-limiting middleware
- Test generation

### Gemini 2.0 (Testing & Validation)
- Unit tests generation
- Integration tests
- E2E test scenarios
- Mock data generation
- Test coverage analysis

### E2B (Sandbox Execution)
- Safe code execution
- Migration tests
- Backup restore tests
- Performance benchmarks
- Security audits

---

## 6. ORDEN RECOMENDADO DE IMPLEMENTACIÓN (PRÓXIMOS 15 PROMPTS)

### FASE 1: FUNDAMENTOS CRÍTICOS (Prompts 1-5)

**PROMPT 1 - VAULT.1: Memory Vault Core**
```
Implementar backend/app/memory_vault/ con:
- storage.py (Google Drive API)
- models.py (DB schema)
- schemas.py (Pydantic)
- retention.py (políticas)
Tests: test_storage.py, test_retention.py
```

**PROMPT 2 - VAULT.2: Memory Vault Encryption**
```
Implementar encryption.py con:
- KMS integration
- Cifrado/descifrado
- Key rotation
Tests: test_encryption.py
```

**PROMPT 3 - ACL.1: Access Control Matrix**
```
Implementar backend/app/security/acl.py con:
- ACL matrix
- Permission checking
- Role inheritance
Tests: test_permissions.py, test_role_inheritance.py
```

**PROMPT 4 - REDIS.1: Redis Enhancement**
```
Implementar backend/app/core/redis_config.py con:
- TTL configurados
- Dead-letter queue
- Monitoring
Tests: test_redis_e2e.py, test_dead_letter.py
```

**PROMPT 5 - BACKUP.1: Backup Automation**
```
Implementar backend/app/backup/ con:
- postgres_backup.py
- vault_backup.py
- restore.py
- scheduler.py
Tests: test_backup.py, test_restore.py
```

---

### FASE 2: CONFIGURACIÓN & SEGURIDAD (Prompts 6-10)

**PROMPT 6 - RATELIMIT.1: Rate Limiting**
```
Implementar:
- backend/app/core/options.json
- backend/app/middleware/rate_limiter.py
Tests: test_rate_limiting.py
```

**PROMPT 7 - LEGAL.1: Legal Guardrails**
```
Implementar backend/app/legal/ con:
- copyright_checker.py
- approval_workflow.py
- Disclaimer templates
Tests: test_copyright.py, test_approval.py
```

**PROMPT 8 - TOGGLES.1: Feature Toggles**
```
Implementar toggles en options.json:
- MixChecker
- Gullfoss
- Loudness Normalizer
Tests: test_toggles.py
```

**PROMPT 9 - INTEGRATION.1: Main.py Integration**
```
Integrar en main.py:
- Meta schedulers faltantes
- Memory Vault router
- Master Control Tower router
Tests: test_main_integration.py
```

**PROMPT 10 - MIGRATION.1: DB Migrations**
```
Crear migration 019:
- memory_vault_index table
- ACL roles/permissions tables
- Backup metadata table
Tests: test_migration_019.py
```

---

### FASE 3: TESTING & VALIDACIÓN (Prompts 11-15)

**PROMPT 11 - TEST.1: Memory Vault Tests**
```
Crear test suite completo:
- test_vault_storage.py
- test_vault_retention.py
- test_vault_encryption.py
- test_vault_migration.py
```

**PROMPT 12 - TEST.2: Redis E2E Tests**
```
Crear test suite completo:
- test_redis_jobs_lifecycle.py
- test_redis_dead_letter.py
- test_redis_ttl_expiration.py
```

**PROMPT 13 - TEST.3: ACL Tests**
```
Crear test suite completo:
- test_acl_permissions.py
- test_acl_inheritance.py
- test_acl_access_denial.py
```

**PROMPT 14 - TEST.4: Integration Tests**
```
Crear test suite E2E:
- test_end_to_end_campaign.py
- test_end_to_end_publishing.py
- test_end_to_end_ml_pipeline.py
```

**PROMPT 15 - DOCS.1: Documentation Update**
```
Actualizar documentación:
- README_MEMORY_VAULT.md
- README_ACL.md
- README_BACKUP.md
- ARCHITECTURE_COMPLETE.md
```

---

## 7. VALIDACIÓN FINAL DE INTEGRACIÓN

### Checklist pre-producción:

#### ✅ Base Infrastructure
- [ ] PostgreSQL configurado y migraciones al día
- [ ] Redis configurado con dead-letter queue
- [ ] FastAPI app con todos los routers registrados
- [ ] Logging centralizado funcionando

#### ✅ Meta Ads Stack
- [ ] 18 módulos operacionales (10.1-10.18)
- [ ] Todos los schedulers iniciados en lifespan
- [ ] Master Control Tower monitoreando 17 módulos
- [ ] Tests pasando (160+)

#### ✅ Memory Vault
- [ ] Google Drive integrado
- [ ] Encryption KMS configurado
- [ ] Retention policies activas
- [ ] DB index creado
- [ ] Tests pasando

#### ✅ Access Control
- [ ] ACL matrix implementada
- [ ] 5 roles configurados
- [ ] Permission checking en endpoints
- [ ] Tests de acceso denegado pasando

#### ✅ Backup & Recovery
- [ ] Postgres snapshots diarios
- [ ] Vault export monthly
- [ ] Restore procedures documentados
- [ ] Tests de restore exitosos

#### ✅ Rate Limiting & Toggles
- [ ] Rate limits configurados por endpoint
- [ ] Feature toggles funcionando
- [ ] Options.json centralizado
- [ ] Tests de throttling pasando

#### ✅ Legal Compliance
- [ ] Disclaimer legal implementado
- [ ] Workflow aprobación humana
- [ ] Copyright checker activo
- [ ] Logs de aprobaciones

#### ✅ Monitoring
- [ ] Live telemetry activo
- [ ] Alerting engine configurado
- [ ] Visual analytics desplegado
- [ ] Dashboard control tower operacional

---

## 8. PUNTOS EXTRA DOCUMENTADOS (MODO CANDADO)

### 8.1 Memory Vault Details

**Root:** `gdrive:/stakazo/memory_vault/`

**Subfolders:**
- `ml_features/`: Features ML extraídos
- `audits/`: Logs, auditorías, reportes
- `campaign_history/`: Metadatos campañas
- `clips_metadata/`: Datos enriquecidos clips
- `orchestrator_runs/`: Logs pipeline orchestrator

**Naming convention:**
```
<entity>__YYYYMMDD__v<version>.json
Ejemplo: campaign__20251128__v1.json
```

**Retention policy:**
- Raw data: 365 días
- Summaries: 5 años (rolling)

**Encryption:**
- En tránsito: TLS 1.3
- En reposo: AES-256
- KMS: Google Cloud KMS
- IAM: Roles granulares por folder

---

### 8.2 DB Schema Examples

**Tabla memory_vault_index:**
```sql
CREATE TABLE memory_vault_index (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  entity_type VARCHAR(50) NOT NULL,
  entity_id VARCHAR(100) NOT NULL,
  gdrive_path TEXT NOT NULL,
  feature_hash JSONB,
  source VARCHAR(50),
  version INTEGER DEFAULT 1,
  timestamp TIMESTAMP NOT NULL,
  run_id UUID,
  metadata JSONB,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indices
CREATE INDEX idx_mv_feature_hash ON memory_vault_index USING gin(feature_hash);
CREATE INDEX idx_mv_run_id_timestamp ON memory_vault_index(run_id, timestamp);
CREATE INDEX idx_mv_entity_type ON memory_vault_index(entity_type, entity_id);
CREATE INDEX idx_mv_gdrive_path ON memory_vault_index USING hash(gdrive_path);
```

**Ejemplo JSONB feature_hash:**
```json
{
  "model": "clip_encoder_v2",
  "features": [0.123, 0.456, ...],
  "dimensions": 512,
  "extraction_time": 0.043,
  "quality_score": 0.95
}
```

---

### 8.3 Access Control Matrix

**Roles:**
- orchestrator: Ejecuta pipelines
- worker: Procesa jobs
- auditor: Solo lectura auditorías
- dashboard: Visualización
- devops: Administración completa

**ACL Matrix completa:**

| Recurso            | Orchestrator | Worker | Auditor | Dashboard | DevOps |
|--------------------|:------------:|:------:|:-------:|:---------:|:------:|
| campaign_history   | r/w          | r      | r       | r         | r      |
| ml_features        | r/w          | r/w    | r       | r         | r      |
| audits             | r            | -      | r/w     | -         | r/w    |
| orchestrator_runs  | r/w          | -      | r       | -         | r      |
| clips_metadata     | r/w          | r/w    | r       | r         | r      |
| memory_vault       | r/w          | r      | r       | r         | r      |
| backups            | -            | -      | -       | -         | r/w    |
| config             | r            | r      | -       | r         | r/w    |

**Herencia de permisos:**
- Orchestrator → Workers (lectura descendente)
- DevOps → Todos (override completo)

---

### 8.4 Redis Configuration

**Workers:** 3 (mínimo), escalable automático

**TTL values:**
```python
TTL_CONFIG = {
    "default": 1800,        # 30 minutos
    "campaign": 7200,       # 2 horas
    "ml_jobs": 3600,        # 1 hora
    "upload_jobs": 600,     # 10 minutos
    "session": 86400,       # 24 horas
}
```

**Retries:** 3 intentos con backoff exponencial (1s, 2s, 4s)

**Dead-letter queue:**
```
redis://publishing/dead_letter
- Monitorización vía dashboard
- Alerts después de 10 jobs en DLQ
- Manual retry capability
```

**Namespaces:**
```
publishing/         # Jobs publishing
ml_jobs/            # ML processing
upload_jobs/        # Upload tasks
sessions/           # User sessions
cache/              # General cache
dead_letter/        # Failed jobs
```

---

### 8.5 Backup Policy

**PostgreSQL:**
- Frecuencia: Diaria (02:00 UTC)
- Retención: 30 días
- Storage: Cloud Storage encrypted
- Restore time target: < 4 horas

**Memory Vault:**
- Frecuencia: Mensual (1st day, 03:00 UTC)
- Formato: ZIP cifrado AES-256
- Retención: 12 meses
- Restore time target: < 24 horas

**Restore test plan:**
- Frecuencia: Quarterly (Q1, Q2, Q3, Q4)
- Scope: Full restore en staging environment
- Validación: Data integrity checks
- Documentado en: README_BACKUP.md

---

### 8.6 Rate Limits & Toggles

**Flag central:** `MODE` en `config/options.json`

**Rate limits por endpoint:**
```json
{
  "/upload": {
    "limit": 10,
    "per": "minute",
    "scope": "user"
  },
  "/jobs": {
    "limit": 20,
    "per": "minute",
    "scope": "user"
  },
  "/campaigns": {
    "limit": 5,
    "per": "minute",
    "scope": "account"
  },
  "/api/meta/*": {
    "limit": 100,
    "per": "minute",
    "scope": "token"
  }
}
```

**Feature toggles:**
```json
{
  "mixchecker": {
    "enabled": false,
    "cost_per_1k_clips": 10.0,
    "budget_limit_usd": 1000
  },
  "gullfoss": {
    "enabled": false,
    "cost_monthly": 39.0
  },
  "loudness_normalizer": {
    "enabled": true,
    "cost_per_1k_clips": 2.0,
    "auto_enable": true
  }
}
```

---

### 8.7 Legal/Copyright Guardrails

**Nota legal obligatoria:**
```
⚠️ AVISO LEGAL
Todos los clips subidos deben contar con derechos de uso.
El usuario es responsable de verificar permisos de copyright
antes de publicar contenido en plataformas pagadas.
```

**Dashboard UX:**
- Checkbox obligatorio: "Confirmo tener derechos de uso"
- Checkbox obligatorio: "Acepto términos legales"
- Warning antes de campaña pagada
- Log de aprobaciones en DB

**Workflow aprobación:**
1. Usuario sube clip
2. Sistema valida metadata
3. Dashboard muestra disclaimer
4. Usuario confirma derechos
5. Usuario confirma términos
6. Sistema registra aprobación
7. Campaña puede publicarse

---

### 8.8 Toggle Flags Audio Processors

**MixChecker:**
- Toggle: `options.json -> mixchecker.enabled`
- Coste: $10/1000 clips
- Función: Validación mix audio profesional
- Desactivable: Sí
- Default: false (stub mode)

**Gullfoss:**
- Toggle: `options.json -> gullfoss.enabled`
- Coste: $39/mes (licencia)
- Función: EQ inteligente automático
- Desactivable: Sí
- Default: false (stub mode)

**Loudness Normalizer:**
- Toggle: `options.json -> loudness_normalizer.enabled`
- Coste: <$2/1000 clips
- Función: Normalización LUFS
- Desactivable: Sí
- Default: true (enabled by default)

**Control por entorno:**
```json
{
  "audio_processors": {
    "stub": {
      "mixchecker": false,
      "gullfoss": false,
      "loudness_normalizer": false
    },
    "dev": {
      "mixchecker": false,
      "gullfoss": false,
      "loudness_normalizer": true
    },
    "prod": {
      "mixchecker": true,
      "gullfoss": true,
      "loudness_normalizer": true
    }
  }
}
```

---

### 8.9 Tests a Incluir

**Memory Vault tests:**
```python
# test_vault_storage.py
- test_google_drive_connection()
- test_file_upload()
- test_file_download()
- test_folder_structure()
- test_naming_convention()

# test_vault_retention.py
- test_retention_policy_365_days()
- test_summary_retention_5_years()
- test_automatic_cleanup()

# test_vault_encryption.py
- test_encryption_at_rest()
- test_encryption_in_transit()
- test_kms_key_rotation()

# test_vault_migration.py
- test_migrate_legacy_data()
- test_merge_duplicate_records()
- test_version_upgrade()
```

**Redis E2E tests:**
```python
# test_redis_e2e.py
- test_job_lifecycle_complete()
- test_ttl_expiration()
- test_namespace_isolation()

# test_dead_letter.py
- test_failed_job_to_dlq()
- test_retry_from_dlq()
- test_dlq_monitoring_alert()
```

**IAM/Permission tests:**
```python
# test_acl_permissions.py
- test_orchestrator_read_write()
- test_worker_read_only()
- test_auditor_audit_access()
- test_access_denial()

# test_acl_inheritance.py
- test_role_inheritance()
- test_permission_override()
```

---

## 9. RESUMEN EJECUTIVO

### Estado actual:
- ✅ Meta Ads Stack: COMPLETO (18 módulos)
- ✅ Publishing System: OPERACIONAL
- ✅ AI Workers: OPERACIONAL
- ✅ Monitoring: OPERACIONAL
- ⚠️ Integración main.py: PARCIAL
- ❌ Memory Vault: NO IMPLEMENTADO
- ❌ ACL granular: NO IMPLEMENTADO
- ❌ Backup automation: NO IMPLEMENTADO
- ❌ TikTok/LinkedIn: PENDIENTE

### Prioridades inmediatas:
1. **VAULT.1-VAULT.2:** Memory Vault completo
2. **ACL.1:** Access Control Matrix
3. **REDIS.1:** Redis enhancement
4. **BACKUP.1:** Backup automation
5. **INTEGRATION.1:** Main.py integration

### Métricas:
- Commits totales: 68
- Líneas código: 51,315
- Módulos completos: 18 (Meta)
- Tests: ~160+
- Coverage: >80%

### Siguiente fase:
**PROMPT VAULT.1** - Implementar Memory Vault core

---

## VALIDACIÓN REQUERIDA

**🔒 ESTE DOCUMENTO ESTÁ EN MODO VALIDACIÓN**

**NO EJECUTAR CÓDIGO HASTA RECIBIR:**
- ✅ Aprobación de arquitectura Memory Vault
- ✅ Aprobación de ACL matrix
- ✅ Aprobación de Redis config
- ✅ Aprobación de Backup policy
- ✅ Aprobación del orden de implementación

**DESPUÉS DE VALIDACIÓN:**
- Crear archivos según plan
- Implementar en orden recomendado
- Tests por cada componente
- Documentation completa

---

**Generado:** 2025-11-28  
**Versión:** 1.0.0 (VALIDACIÓN)  
**Estado:** PENDIENTE APROBACIÓN
