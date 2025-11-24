# ✅ RAILWAY DEPLOYMENT CHECKLIST

**Fecha:** _____________  
**Proyecto:** stakazo-prod  
**Deploy por:** _____________

---

## 🔑 FASE 1: PREPARACIÓN (5 min)

### Cuenta y CLI

- [ ] Cuenta Railway creada (https://railway.app)
- [ ] GitHub conectado a Railway
- [ ] Railway CLI instalado: `npm install -g @railway/cli`
- [ ] Logged in: `railway login`

### Generar Claves

**Ejecutar en terminal:**

```bash
openssl rand -hex 64
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

- [ ] JWT_SECRET generado y guardado
- [ ] CREDENTIALS_ENCRYPTION_KEY generado y guardado

**JWT_SECRET:** `_____________________________________________`

**CREDENTIALS_ENCRYPTION_KEY:** `_____________________________________________`

---

## 🗄️ FASE 2: PROYECTO Y DATABASE (3 min)

### Crear Proyecto

- [ ] Proyecto creado: https://railway.app/new → "Empty Project"
- [ ] Renombrado a: `stakazo-prod`

### PostgreSQL

- [ ] PostgreSQL agregado: "+ New" → "Database" → "Add PostgreSQL"
- [ ] Estado: **Active** (verde)
- [ ] Esperado 30 seg para inicialización

---

## 🖥️ FASE 3: BACKEND (10 min)

### Crear Servicio

- [ ] "+ New" → "GitHub Repo" → `sistemaproyectomunidal/stakazo`
- [ ] Servicio renombrado a: `backend`

### Settings

- [ ] Root Directory: `backend`
- [ ] Watch Paths: `backend/**`
- [ ] Builder: `DOCKERFILE`
- [ ] Dockerfile Path: `Dockerfile.prod`

### Variables (25 variables)

- [ ] DATABASE_URL: Referencia a `Postgres.DATABASE_URL`
- [ ] JWT_SECRET: `[TU CLAVE GENERADA]`
- [ ] ACCESS_TOKEN_EXPIRE_MINUTES: `43200`
- [ ] CREDENTIALS_ENCRYPTION_KEY: `[TU CLAVE GENERADA]`
- [ ] AI_LLM_MODE: `stub`
- [ ] API_BASE_URL: `https://${{RAILWAY_PUBLIC_DOMAIN}}/api`
- [ ] BACKEND_CORS_ORIGINS: `["https://${{RAILWAY_PUBLIC_DOMAIN}}","http://localhost:3000"]`
- [ ] OPENAI_API_KEY: `[vacío o tu key]`
- [ ] AI_OPENAI_MODEL_NAME: `gpt-4`
- [ ] GEMINI_API_KEY: `[vacío o tu key]`
- [ ] AI_GEMINI_MODEL_NAME: `gemini-2.0-flash-exp`
- [ ] AI_WORKER_ENABLED: `true`
- [ ] AI_WORKER_INTERVAL_SECONDS: `30`
- [ ] ORCHESTRATOR_ENABLED: `true`
- [ ] ORCHESTRATOR_INTERVAL_SECONDS: `2`
- [ ] PUBLISHING_STUB_MODE: `true`
- [ ] PUBLISHING_PROVIDER_TIMEOUT_SECONDS: `30`
- [ ] SCHEDULER_TICK_INTERVAL_SECONDS: `60`
- [ ] TELEMETRY_INTERVAL_SECONDS: `3`
- [ ] ALERT_SCAN_INTERVAL_SECONDS: `60`
- [ ] ENVIRONMENT: `production`
- [ ] LOG_LEVEL: `info`
- [ ] TZ: `UTC`

### Deploy

- [ ] Deploy iniciado automáticamente
- [ ] Esperado 3-5 min
- [ ] Status: **Success** (verde)
- [ ] Logs sin errores críticos

### Networking

- [ ] Dominio generado: Settings → Networking → "Generate Domain"
- [ ] URL Backend: `_____________________________________________`

### Migraciones

```bash
railway link
railway run --service backend alembic upgrade head
```

- [ ] Migraciones ejecutadas
- [ ] Output: "Running upgrade ... Initial migration"

---

## 🎨 FASE 4: DASHBOARD (8 min)

### Crear Servicio

- [ ] "+ New" → "GitHub Repo" → `sistemaproyectomunidal/stakazo`
- [ ] Servicio renombrado a: `dashboard`

### Settings

- [ ] Root Directory: `dashboard`
- [ ] Watch Paths: `dashboard/**`
- [ ] Builder: `DOCKERFILE`
- [ ] Dockerfile Path: `Dockerfile`

### Variables (5 variables)

- [ ] NEXT_PUBLIC_API_URL: `https://[BACKEND-URL]/api`
- [ ] NEXT_PUBLIC_WS_URL: `wss://[BACKEND-URL]/api/ws`
- [ ] JWT_SECRET: `[MISMO QUE BACKEND]`
- [ ] NODE_ENV: `production`
- [ ] NEXT_TELEMETRY_DISABLED: `1`

### Deploy

- [ ] Deploy iniciado automáticamente
- [ ] Esperado 4-6 min
- [ ] Status: **Success** (verde)
- [ ] Logs sin errores críticos

### Networking

- [ ] Dominio generado: Settings → Networking → "Generate Domain"
- [ ] URL Dashboard: `_____________________________________________`

---

## 🔧 FASE 5: ACTUALIZAR CORS (2 min)

### Backend CORS

- [ ] Backend → Variables → BACKEND_CORS_ORIGINS
- [ ] Actualizado a: `["https://[DASHBOARD-URL]","http://localhost:3000"]`
- [ ] Servicio reiniciado automáticamente

---

## ✅ FASE 6: VERIFICACIÓN (5 min)

### Health Checks

```bash
curl https://[BACKEND-URL]/health
curl https://[DASHBOARD-URL]/api/health
```

- [ ] Backend health: `{"status":"healthy","database":"connected"}`
- [ ] Dashboard health: `{"status":"ok"}`

### Navegador

- [ ] Abrir: `https://[BACKEND-URL]/docs` → Ver Swagger UI
- [ ] Abrir: `https://[DASHBOARD-URL]` → Ver interfaz dashboard
- [ ] No hay errores CORS en consola (F12)
- [ ] WebSocket conectado (verificar en Network tab)

### Railway Status

- [ ] Postgres: **Active** (verde)
- [ ] Backend: **Active** (verde)
- [ ] Dashboard: **Active** (verde)

---

## 🎯 VERIFICACIÓN FINAL

### URLs de Producción

```
Backend API:  https://[TU-URL-AQUI]
API Docs:     https://[TU-URL-AQUI]/docs
Dashboard:    https://[TU-URL-AQUI]
```

### Funcionalidad

- [ ] Login page carga correctamente
- [ ] API responde a requests
- [ ] Base de datos conectada
- [ ] Sin errores en logs de Railway
- [ ] SSL funciona (candado verde en navegador)

---

## 💰 COSTOS ESTIMADOS

- PostgreSQL: ~$5/mes
- Backend: ~$5/mes
- Dashboard: ~$5/mes
- **Total: ~$15/mes**

---

## 🐛 PROBLEMAS COMUNES

### ❌ Database connection failed
→ Verificar que DATABASE_URL esté referenciando a Postgres

### ❌ CORS error
→ Verificar que BACKEND_CORS_ORIGINS incluya la URL exacta del dashboard

### ❌ JWT verification failed
→ Verificar que JWT_SECRET sea idéntico en backend y dashboard

### ❌ Build failed
→ Revisar logs en Deployments → Click en deployment fallido

---

## 🎉 DEPLOY COMPLETADO

Si todos los checkboxes están marcados: **¡FELICIDADES! Tu aplicación está en producción.**

**Firma:** _____________  
**Fecha:** _____________  
**Tiempo total:** _____________ min

---

**Próximos pasos:**
1. Configurar dominio custom (opcional)
2. Activar AI en modo LIVE
3. Configurar plataformas sociales
4. Configurar monitoring
