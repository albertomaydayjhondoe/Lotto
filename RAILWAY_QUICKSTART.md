# 🚀 Railway Quick Start - Stakazo

**Commit:** 4338a1c  
**Status:** ✅ Ready to Deploy

---

## ⚡ Deploy en 3 Pasos

### 1️⃣ Generar Claves

```bash
# JWT Secret (para autenticación)
JWT_SECRET=$(openssl rand -hex 64)
echo "JWT_SECRET=$JWT_SECRET"

# Fernet Key (para encriptación de credenciales)
FERNET_KEY=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
echo "CREDENTIALS_ENCRYPTION_KEY=$FERNET_KEY"
```

**⚠️ GUARDA ESTOS VALORES** - Los necesitarás para Railway.

---

### 2️⃣ Crear Proyecto en Railway

1. Ve a https://railway.app/new
2. Selecciona "Empty Project"
3. Nombra tu proyecto: `stakazo-prod`

---

### 3️⃣ Agregar Servicios

#### A) PostgreSQL Database

1. Click en "New" → "Database" → "Add PostgreSQL"
2. Railway generará automáticamente `DATABASE_URL`
3. ✅ Listo!

#### B) Backend Service

1. Click en "New" → "GitHub Repo" → Selecciona `stakazo`
2. En **Settings**:
   - Root Directory: `backend`
   - Watch Paths: `backend/**`
3. En **Variables** pega esto (reemplazando TUS claves):

```env
JWT_SECRET=tu_jwt_secret_generado_paso_1
ACCESS_TOKEN_EXPIRE_MINUTES=43200
CREDENTIALS_ENCRYPTION_KEY=tu_fernet_key_generado_paso_1
AI_LLM_MODE=stub
DATABASE_URL=${{Postgres.DATABASE_URL}}
BACKEND_CORS_ORIGINS=["https://${{RAILWAY_PUBLIC_DOMAIN}}","http://localhost:3000"]
OPENAI_API_KEY=
AI_OPENAI_MODEL_NAME=gpt-4
GEMINI_API_KEY=
AI_GEMINI_MODEL_NAME=gemini-2.0-flash-exp
AI_WORKER_ENABLED=true
AI_WORKER_INTERVAL_SECONDS=30
ORCHESTRATOR_ENABLED=true
ORCHESTRATOR_INTERVAL_SECONDS=2
PUBLISHING_STUB_MODE=true
PUBLISHING_PROVIDER_TIMEOUT_SECONDS=30
SCHEDULER_TICK_INTERVAL_SECONDS=60
TELEMETRY_INTERVAL_SECONDS=3
ALERT_SCAN_INTERVAL_SECONDS=60
ENVIRONMENT=production
LOG_LEVEL=info
TZ=UTC
```

4. En **Deploy**:
   - Railway detectará automáticamente `backend/Dockerfile.prod`
   - Click "Deploy"

5. **Espera** a que termine el deploy (~3-5 min)

6. **Ejecutar Migraciones:**
   - Ve a **Settings** → **Deploy**
   - En "Service Variables", anota el dominio (ej: `backend-prod-xyz.up.railway.app`)
   - Abre terminal local:
   ```bash
   railway login
   railway link  # Selecciona tu proyecto
   railway run --service backend alembic upgrade head
   ```

7. ✅ **Verificar:** 
   ```bash
   curl https://tu-backend.up.railway.app/health
   ```
   Deberías ver: `{"status":"healthy","database":"connected"}`

#### C) Dashboard Service

1. Click en "New" → "GitHub Repo" → Selecciona `stakazo`
2. En **Settings**:
   - Root Directory: `dashboard`
   - Watch Paths: `dashboard/**`
3. En **Variables** pega esto (usando tu JWT_SECRET y el dominio del backend):

```env
NEXT_PUBLIC_API_URL=https://tu-backend.up.railway.app/api
NEXT_PUBLIC_WS_URL=wss://tu-backend.up.railway.app/api/ws
JWT_SECRET=tu_jwt_secret_del_paso_1
NODE_ENV=production
NEXT_TELEMETRY_DISABLED=1
```

4. En **Deploy**:
   - Railway detectará `dashboard/Dockerfile`
   - Click "Deploy"

5. ✅ **Verificar:**
   ```bash
   curl https://tu-dashboard.up.railway.app/api/health
   ```

---

## ✅ Post-Deploy

### Configurar CORS Correctamente

Después de que ambos servicios estén desplegados:

1. Ve al servicio **Backend** → **Variables**
2. Actualiza `BACKEND_CORS_ORIGINS`:
   ```env
   BACKEND_CORS_ORIGINS=["https://tu-dashboard.up.railway.app"]
   ```
3. Redeploy backend

### Verificar Conectividad

```bash
# Backend health
curl https://tu-backend.up.railway.app/health

# Dashboard health
curl https://tu-dashboard.up.railway.app/api/health

# API docs
open https://tu-backend.up.railway.app/docs
```

### Abrir Dashboard

```bash
open https://tu-dashboard.up.railway.app
```

---

## 💰 Costos Estimados

| Servicio | Hobby Plan | Pro Plan |
|----------|------------|----------|
| PostgreSQL | $5/mes | $10/mes |
| Backend | $5/mes | $10/mes |
| Dashboard | $5/mes | $10/mes |
| **Total** | **$15/mes** | **$30/mes** |

Railway incluye 100GB bandwidth gratis.

---

## 🐛 Troubleshooting

### Error: "Database connection failed"

```bash
# Verifica que PostgreSQL esté running
railway status

# Verifica DATABASE_URL en backend
railway variables --service backend | grep DATABASE_URL
```

### Error: "CORS error"

Asegúrate de que `BACKEND_CORS_ORIGINS` incluya el dominio exacto del dashboard (con `https://`).

### Error: "JWT signature verification failed"

El `JWT_SECRET` debe ser **exactamente el mismo** en backend y dashboard.

---

## 📚 Documentación Completa

- **Guía Detallada:** [DEPLOY_RAILWAY.md](./DEPLOY_RAILWAY.md)
- **Generación de Claves:** [RAILWAY_SECRETS_GENERATION.md](./RAILWAY_SECRETS_GENERATION.md)
- **Resumen PASO 9.1:** [PASO_9.1_RAILWAY_SUMMARY.md](./PASO_9.1_RAILWAY_SUMMARY.md)

---

## 🎉 ¡Listo!

Tu aplicación estará corriendo en:
- **Backend API:** `https://tu-backend.up.railway.app`
- **Dashboard:** `https://tu-dashboard.up.railway.app`
- **API Docs:** `https://tu-backend.up.railway.app/docs`

**Tiempo total:** ~15-20 minutos  
**Costo:** ~$15/mes

---

**⚡ Happy deploying!** 🚀
