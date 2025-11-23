# 🚂 Deploy en Railway - Guía Completa

**Fecha**: 23 de Noviembre de 2025  
**Versión**: 1.0.0  
**Tiempo estimado**: 15-20 minutos

---

## 📋 Índice

1. [Requisitos Previos](#requisitos-previos)
2. [Opción A: Deploy Automático (Recomendado)](#opción-a-deploy-automático)
3. [Opción B: Deploy Manual](#opción-b-deploy-manual)
4. [Configuración Post-Deploy](#configuración-post-deploy)
5. [Verificación](#verificación)
6. [Troubleshooting](#troubleshooting)
7. [Costos Estimados](#costos-estimados)

---

## 🎯 Requisitos Previos

### 1. Cuenta de Railway

- Regístrate en [railway.app](https://railway.app)
- **Plan Hobby** ($5/mes) o superior recomendado
- Verificación de tarjeta de crédito requerida

### 2. Railway CLI

```bash
# Opción 1: npm
npm install -g @railway/cli

# Opción 2: Homebrew (macOS/Linux)
brew install railway

# Opción 3: Script
curl -fsSL https://railway.app/install.sh | sh
```

### 3. Verificar instalación

```bash
railway --version
# Debería mostrar: railway version X.X.X
```

### 4. Login

```bash
railway login
```

Se abrirá un navegador para autenticarte.

---

## 🚀 Opción A: Deploy Automático (Recomendado)

### Paso 1: Ejecutar script de deploy

```bash
cd /workspaces/stakazo
./deploy-railway.sh
```

El script hará **automáticamente**:

✅ Verificar prerequisites  
✅ Generar secrets seguros  
✅ Crear proyecto Railway  
✅ Añadir PostgreSQL  
✅ Deploy backend con migrations  
✅ Deploy dashboard  
✅ Configurar dominios públicos  
✅ Ejecutar health checks  

### Paso 2: Guardar los secrets

El script mostrará al final:

```
🔐 Secrets (save these securely):
  SECRET_KEY=...
  CREDENTIALS_ENCRYPTION_KEY=...
  NEXTAUTH_SECRET=...
```

**IMPORTANTE**: Guarda estos valores en un lugar seguro (1Password, LastPass, etc.)

### Paso 3: Verificar deployment

El script te dará las URLs:

```
📊 Service URLs:
  Backend:   https://stakazo-backend-xxx.up.railway.app
  Dashboard: https://stakazo-dashboard-xxx.up.railway.app
```

Visita las URLs para verificar que funciona.

---

## 🔧 Opción B: Deploy Manual

Si prefieres control total, sigue estos pasos:

### Paso 1: Crear proyecto

```bash
railway init --name stakazo-prod
railway link stakazo-prod
```

### Paso 2: Añadir PostgreSQL

```bash
railway add --service postgres
```

Espera 30 segundos para que inicialice.

### Paso 3: Generar secrets

```bash
# SECRET_KEY
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# CREDENTIALS_ENCRYPTION_KEY
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# NEXTAUTH_SECRET
openssl rand -base64 32
```

Guarda estos valores.

### Paso 4: Deploy Backend

```bash
cd backend

# Crear servicio
railway service create backend

# Configurar variables de entorno
railway variables set \
  SECRET_KEY="<tu-secret-key>" \
  CREDENTIALS_ENCRYPTION_KEY="<tu-encryption-key>" \
  PYTHONUNBUFFERED="1" \
  DEBUG_ENDPOINTS_ENABLED="false" \
  WORKER_ENABLED="true" \
  WORKER_POLL_INTERVAL="2" \
  MAX_JOB_RETRIES="3" \
  AI_LLM_MODE="stub" \
  AI_WORKER_ENABLED="false" \
  VIDEO_STORAGE_DIR="/app/storage/videos" \
  TELEMETRY_INTERVAL_SECONDS="5" \
  --service backend

# Deploy
railway up --service backend --detach

# Ejecutar migraciones
railway run --service backend alembic upgrade head

cd ..
```

### Paso 5: Deploy Dashboard

```bash
cd dashboard

# Crear servicio
railway service create dashboard

# Obtener URL del backend
BACKEND_URL=$(railway domain --service backend)

# Configurar variables de entorno
railway variables set \
  NEXT_PUBLIC_API_BASE_URL="$BACKEND_URL/api" \
  NEXTAUTH_SECRET="<tu-nextauth-secret>" \
  NODE_ENV="production" \
  PORT="3000" \
  NEXT_TELEMETRY_DISABLED="1" \
  --service dashboard

# Deploy
railway up --service dashboard --detach

cd ..
```

### Paso 6: Habilitar dominios públicos

```bash
# Backend
railway domain --service backend

# Dashboard
railway domain --service dashboard
```

### Paso 7: Actualizar CORS

```bash
BACKEND_DOMAIN=$(railway domain --service backend)
DASHBOARD_DOMAIN=$(railway domain --service dashboard)

railway variables set \
  BACKEND_CORS_ORIGINS="[\"$DASHBOARD_DOMAIN\",\"$BACKEND_DOMAIN\"]" \
  --service backend
```

---

## ⚙️ Configuración Post-Deploy

### 1. Configurar Dominio Personalizado (Opcional)

Si tienes un dominio propio:

```bash
railway domain --service backend your-api.com
railway domain --service dashboard your-app.com
```

Luego configurar DNS:

```
Type: CNAME
Name: your-api
Value: stakazo-backend-xxx.up.railway.app
```

### 2. Activar AI en modo LIVE (Opcional)

Si quieres usar OpenAI/Gemini reales:

```bash
railway variables set \
  AI_LLM_MODE="live" \
  OPENAI_API_KEY="sk-..." \
  GEMINI_API_KEY="..." \
  --service backend
```

### 3. Configurar Plataformas Sociales (Opcional)

Para publicar en Instagram/TikTok/YouTube:

```bash
railway variables set \
  INSTAGRAM_APP_ID="..." \
  INSTAGRAM_APP_SECRET="..." \
  TIKTOK_CLIENT_KEY="..." \
  TIKTOK_CLIENT_SECRET="..." \
  YOUTUBE_CLIENT_ID="..." \
  YOUTUBE_CLIENT_SECRET="..." \
  --service backend
```

### 4. Activar AI Global Worker (Opcional)

```bash
railway variables set \
  AI_WORKER_ENABLED="true" \
  AI_WORKER_INTERVAL_SECONDS="60" \
  --service backend
```

---

## ✅ Verificación

### 1. Health Checks

```bash
# Backend
curl https://stakazo-backend-xxx.up.railway.app/health

# Respuesta esperada:
{
  "status": "healthy",
  "service": "Stakazo AI Orchestrator",
  "version": "1.0.0",
  "database": "connected"
}

# Dashboard
curl https://stakazo-dashboard-xxx.up.railway.app/api/health

# Respuesta esperada:
{
  "status": "ok",
  "service": "stakazo-dashboard",
  "timestamp": "2025-11-23T..."
}
```

### 2. Verificar Endpoints Principales

```bash
# API Docs (OpenAPI)
open https://stakazo-backend-xxx.up.railway.app/docs

# Dashboard Overview
open https://stakazo-dashboard-xxx.up.railway.app/dashboard

# Telemetry WebSocket (requiere auth)
# ws://stakazo-backend-xxx.up.railway.app/api/v1/telemetry/ws
```

### 3. Verificar Base de Datos

```bash
# Ver logs del backend
railway logs --service backend

# Debería mostrar:
# "Database connection successful"
# "Uvicorn running on..."
```

### 4. Verificar Workers

```bash
# Ver logs del backend
railway logs --service backend --tail

# Debería mostrar:
# "Publishing worker started"
# "Telemetry broadcast loop started"
# "Alert analysis loop started"
```

### 5. Test Completo con Script

```bash
./scripts/healthcheck-railway.sh
```

---

## 🐛 Troubleshooting

### Problema: "Database connection failed"

**Causa**: PostgreSQL no está conectado al backend

**Solución**:
```bash
# Verificar que existe el servicio postgres
railway service list

# Vincular backend con postgres
railway link --service backend
railway variables set DATABASE_URL="$DATABASE_URL" --service backend
```

### Problema: "Health check failed"

**Causa**: Servicio no inició correctamente

**Solución**:
```bash
# Ver logs
railway logs --service backend --tail

# Revisar errores comunes:
# - Puerto incorrecto (debe usar $PORT)
# - Variables de entorno faltantes
# - Dockerfile path incorrecto
```

### Problema: "CORS error en dashboard"

**Causa**: CORS no configurado correctamente

**Solución**:
```bash
# Actualizar CORS
BACKEND_DOMAIN=$(railway domain --service backend)
DASHBOARD_DOMAIN=$(railway domain --service dashboard)

railway variables set \
  BACKEND_CORS_ORIGINS="[\"$DASHBOARD_DOMAIN\",\"$BACKEND_DOMAIN\",\"http://localhost:3000\"]" \
  --service backend

# Reiniciar backend
railway restart --service backend
```

### Problema: "Next.js build failed"

**Causa**: Falta configuración standalone

**Solución**:
```bash
# Verificar next.config.js tiene:
# output: 'standalone'

# Rebuild
railway up --service dashboard --force
```

### Problema: "Migrations failed"

**Causa**: DATABASE_URL no disponible

**Solución**:
```bash
# Verificar DATABASE_URL
railway variables --service backend | grep DATABASE_URL

# Si no existe, Railway debería inyectarlo automáticamente
# Verificar que postgres service está conectado
railway service list
```

### Problema: "Out of memory"

**Causa**: Worker usando demasiada RAM

**Solución**:
```bash
# Reducir workers de Uvicorn
railway variables set \
  UVICORN_WORKERS="2" \
  --service backend

# O desactivar AI Worker
railway variables set \
  AI_WORKER_ENABLED="false" \
  --service backend
```

---

## 💰 Costos Estimados

### Plan Hobby ($5/mes)

| Servicio | Costo Estimado | Recursos |
|----------|----------------|----------|
| **PostgreSQL** | ~$5/mes | 1GB RAM, 1GB Storage |
| **Backend** | ~$5-10/mes | 512MB RAM, vCPU compartido |
| **Dashboard** | ~$5-10/mes | 512MB RAM, vCPU compartido |
| **Bandwidth** | ~$0-5/mes | 100GB incluidos |
| **Total** | **~$15-30/mes** | Depende de uso |

### Plan Pro ($20/mes)

| Servicio | Costo Estimado | Recursos |
|----------|----------------|----------|
| **PostgreSQL** | ~$10/mes | 2GB RAM, 5GB Storage |
| **Backend** | ~$10-15/mes | 1GB RAM, vCPU dedicado |
| **Dashboard** | ~$10-15/mes | 1GB RAM, vCPU dedicado |
| **Bandwidth** | ~$0-10/mes | 1TB incluidos |
| **Total** | **~$30-50/mes** | Mayor performance |

### Optimización de Costos

1. **Desactivar servicios no usados**:
   ```bash
   railway down --service nginx  # Si no usas nginx
   ```

2. **Usar modo stub para AI** (sin costos de OpenAI):
   ```bash
   AI_LLM_MODE=stub  # No hace llamadas reales
   ```

3. **Escalar según demanda**:
   - Empezar con Plan Hobby
   - Escalar a Pro cuando sea necesario

4. **Monitorear uso**:
   ```bash
   railway metrics --service backend
   ```

---

## 📊 Comandos Útiles

### Ver estado de servicios

```bash
railway status
```

### Ver logs en tiempo real

```bash
# Todos los servicios
railway logs --tail

# Servicio específico
railway logs --service backend --tail
railway logs --service dashboard --tail
```

### Reiniciar servicios

```bash
railway restart --service backend
railway restart --service dashboard
```

### Ver variables de entorno

```bash
railway variables --service backend
railway variables --service dashboard
```

### Escalar servicios

```bash
# Aumentar RAM
railway variables set RAILWAY_RAM="1024" --service backend

# Aumentar replicas (Plan Pro)
railway scale --service backend --replicas 2
```

### Rollback a versión anterior

```bash
railway rollback --service backend
```

### Eliminar proyecto completo

```bash
railway down  # ⚠️ Elimina TODO el proyecto
```

---

## 🔐 Mejores Prácticas de Seguridad

### 1. Rotar Secrets Regularmente

```bash
# Generar nuevo SECRET_KEY
NEW_SECRET=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")

# Actualizar
railway variables set SECRET_KEY="$NEW_SECRET" --service backend
railway restart --service backend
```

### 2. Limitar CORS Estrictamente

```bash
# Solo dominios de producción
railway variables set \
  BACKEND_CORS_ORIGINS="[\"https://yourdomain.com\"]" \
  --service backend
```

### 3. Deshabilitar Debug Endpoints

```bash
railway variables set \
  DEBUG_ENDPOINTS_ENABLED="false" \
  --service backend
```

### 4. Activar Rate Limiting (futuro)

```bash
# En nginx.conf agregar:
# limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
```

---

## 📞 Soporte

### Documentación Railway
- [Guía oficial](https://docs.railway.app)
- [Troubleshooting](https://docs.railway.app/troubleshoot/fixing-common-errors)

### Documentación Stakazo
- **Backend**: `PASO_9_SUMMARY.md`
- **Frontend**: `README_VISUAL_ANALYTICS_FRONTEND.md`
- **IAM**: `README_IAM.md`

### Contacto
- Email: sistemaproyectomunidal@gmail.com
- Issues: [GitHub Issues](https://github.com/sistemaproyectomunidal/stakazo/issues)

---

**Última actualización**: 2025-11-23  
**Versión**: 1.0.0  
**Estado**: ✅ Listo para producción
