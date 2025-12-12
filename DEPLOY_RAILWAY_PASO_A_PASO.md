# 🚀 DEPLOY RAILWAY - GUÍA PASO A PASO

**Tiempo estimado:** 20-25 minutos  
**Costo estimado:** $15-20/mes  
**Última actualización:** 2024-11-24

---

## 📋 PRERREQUISITOS (5 minutos)

### ✅ 1. Cuenta de Railway

1. Ve a https://railway.app
2. Click en **"Login"** (arriba derecha)
3. Selecciona **"Login with GitHub"**
4. Autoriza Railway a acceder a tu GitHub
5. ✅ Verás tu dashboard de Railway

### ✅ 2. Instalar Railway CLI (opcional, pero recomendado)

**En tu terminal local:**

```bash
# Instalar Railway CLI
npm install -g @railway/cli

# Verificar instalación
railway --version

# Login
railway login
```

Esto abrirá tu navegador. Autoriza la CLI.

---

## 🔑 PASO 1: GENERAR CLAVES SECRETAS (2 minutos)

**En tu terminal local, ejecuta estos comandos:**

```bash
# Generar JWT_SECRET
echo "=== JWT_SECRET ==="
openssl rand -hex 64
echo ""

# Generar CREDENTIALS_ENCRYPTION_KEY
echo "=== CREDENTIALS_ENCRYPTION_KEY ==="
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
echo ""
```

**⚠️ IMPORTANTE:** Copia y guarda estos valores en un archivo de texto. Los necesitarás en los próximos pasos.

**Ejemplo de salida:**
```
=== JWT_SECRET ===
a1b2c3d4e5f6789....(128 caracteres)

=== CREDENTIALS_ENCRYPTION_KEY ===
abcXYZ123456789_ABCDEFGHIJKLMNOP=
```

---

## 🗄️ PASO 2: CREAR PROYECTO Y POSTGRESQL (5 minutos)

### 2.1. Crear Proyecto

1. Ve a https://railway.app/new
2. Click en **"Empty Project"**
3. En la parte superior, click en el nombre del proyecto (ej: "Project 1")
4. Renómbralo a: **`stakazo-prod`**
5. Presiona Enter

### 2.2. Agregar PostgreSQL

1. Dentro de tu proyecto `stakazo-prod`, click en **"+ New"** (botón morado)
2. Selecciona **"Database"**
3. Selecciona **"Add PostgreSQL"**
4. Railway creará el servicio automáticamente
5. ✅ Verás una tarjeta con el logo de PostgreSQL

**⏳ Espera 30 segundos** mientras PostgreSQL se inicializa.

---

## 🖥️ PASO 3: DESPLEGAR BACKEND (8 minutos)

### 3.1. Crear Servicio Backend

1. En tu proyecto `stakazo-prod`, click en **"+ New"**
2. Selecciona **"GitHub Repo"**
3. Si es la primera vez:
   - Click en **"Configure GitHub App"**
   - Autoriza Railway
   - Selecciona tu repositorio **`stakazo`**
4. Si ya has conectado GitHub antes:
   - Selecciona **`sistemaproyectomunidal/stakazo`** de la lista

### 3.2. Configurar Servicio Backend

Una vez creado el servicio:

1. **Renombrar servicio:**
   - Click en el nombre del servicio (ej: "stakazo")
   - Cámbialo a: **`backend`**
   - Presiona Enter

2. **Configurar Settings:**
   - Click en la tarjeta **`backend`**
   - Ve a la pestaña **"Settings"** (icono de engranaje)
   - Scroll hasta **"Service"**
   - En **"Root Directory"**, escribe: `backend`
   - En **"Watch Paths"**, escribe: `backend/**`
   - Click en el botón **"Update"** (abajo de cada sección)

3. **Configurar Build:**
   - En la misma página de Settings
   - Scroll hasta **"Build"**
   - Verifica que **"Builder"** diga: **`DOCKERFILE`**
   - En **"Dockerfile Path"**, debería aparecer automáticamente: `Dockerfile.prod`
   - Si no aparece, escríbelo manualmente
   - Click **"Update"**

### 3.3. Configurar Variables de Entorno

1. Click en la tarjeta **`backend`**
2. Ve a la pestaña **"Variables"** (icono de llave)
3. Click en **"+ New Variable"**
4. Selecciona **"Add Reference"**
5. En el dropdown, selecciona: **`Postgres` → `DATABASE_URL`**
6. Esto vincula automáticamente la base de datos

Ahora agrega las variables una por una:

**Click en "+ New Variable" y agrega cada una de estas:**

```plaintext
Variable: JWT_SECRET
Value: [PEGA AQUÍ EL JWT_SECRET QUE GENERASTE EN EL PASO 1]

Variable: ACCESS_TOKEN_EXPIRE_MINUTES
Value: 43200

Variable: CREDENTIALS_ENCRYPTION_KEY
Value: [PEGA AQUÍ EL CREDENTIALS_ENCRYPTION_KEY DEL PASO 1]

Variable: AI_LLM_MODE
Value: stub

Variable: API_BASE_URL
Value: https://${{RAILWAY_PUBLIC_DOMAIN}}/api

Variable: BACKEND_CORS_ORIGINS
Value: ["https://${{RAILWAY_PUBLIC_DOMAIN}}","http://localhost:3000"]

Variable: OPENAI_API_KEY
Value: [DEJAR VACÍO o poner tu key si tienes]

Variable: AI_OPENAI_MODEL_NAME
Value: gpt-4

Variable: GEMINI_API_KEY
Value: [DEJAR VACÍO o poner tu key si tienes]

Variable: AI_GEMINI_MODEL_NAME
Value: gemini-2.0-flash-exp

Variable: AI_WORKER_ENABLED
Value: true

Variable: AI_WORKER_INTERVAL_SECONDS
Value: 30

Variable: ORCHESTRATOR_ENABLED
Value: true

Variable: ORCHESTRATOR_INTERVAL_SECONDS
Value: 2

Variable: PUBLISHING_STUB_MODE
Value: true

Variable: PUBLISHING_PROVIDER_TIMEOUT_SECONDS
Value: 30

Variable: SCHEDULER_TICK_INTERVAL_SECONDS
Value: 60

Variable: TELEMETRY_INTERVAL_SECONDS
Value: 3

Variable: ALERT_SCAN_INTERVAL_SECONDS
Value: 60

Variable: ENVIRONMENT
Value: production

Variable: LOG_LEVEL
Value: info

Variable: TZ
Value: UTC
```

**⚠️ IMPORTANTE:** No olvides reemplazar:
- `JWT_SECRET` con tu clave generada
- `CREDENTIALS_ENCRYPTION_KEY` con tu clave generada

### 3.4. Deploy Backend

1. Ve a la pestaña **"Deployments"** (icono de cohete)
2. Railway debería haber iniciado el deploy automáticamente
3. Si no, click en **"Deploy"**
4. **⏳ Espera 3-5 minutos** mientras se construye el container
5. Verás logs en tiempo real
6. ✅ Cuando veas **"Build successful"** y **"Deployment live"**, está listo

### 3.5. Obtener URL del Backend

1. Ve a la pestaña **"Settings"**
2. Scroll hasta **"Networking"**
3. Click en **"Generate Domain"**
4. Railway generará algo como: `backend-prod-production-xyz.up.railway.app`
5. **📝 COPIA ESTA URL** - La necesitarás para el dashboard

**Formato de la URL:**
```
https://backend-prod-production-xyz.up.railway.app
```

### 3.6. Ejecutar Migraciones de Base de Datos

**En tu terminal local:**

```bash
# Asegúrate de estar logueado
railway login

# Link al proyecto
railway link

# Selecciona:
# - Account: [tu cuenta]
# - Project: stakazo-prod
# - Service: backend

# Ejecutar migraciones
railway run --service backend alembic upgrade head
```

**Deberías ver:**
```
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.runtime.migration] Running upgrade -> xxxxx, Initial migration
```

✅ **Migraciones completadas!**

---

## 🎨 PASO 4: DESPLEGAR DASHBOARD (6 minutos)

### 4.1. Crear Servicio Dashboard

1. En tu proyecto `stakazo-prod`, click en **"+ New"**
2. Selecciona **"GitHub Repo"**
3. Selecciona **`sistemaproyectomunidal/stakazo`**

### 4.2. Configurar Servicio Dashboard

1. **Renombrar servicio:**
   - Click en el nombre del servicio
   - Cámbialo a: **`dashboard`**
   - Presiona Enter

2. **Configurar Settings:**
   - Click en la tarjeta **`dashboard`**
   - Ve a la pestaña **"Settings"**
   - En **"Root Directory"**, escribe: `dashboard`
   - En **"Watch Paths"**, escribe: `dashboard/**`
   - Click **"Update"**

3. **Configurar Build:**
   - Scroll hasta **"Build"**
   - Verifica: **"Builder"** = **`DOCKERFILE`**
   - **"Dockerfile Path"** = `Dockerfile` (debe detectarse automáticamente)
   - Click **"Update"**

### 4.3. Configurar Variables de Entorno Dashboard

1. Ve a la pestaña **"Variables"**
2. Agrega estas variables (click "+ New Variable" para cada una):

```plaintext
Variable: NEXT_PUBLIC_API_URL
Value: https://[TU-BACKEND-URL-DEL-PASO-3.5]/api

Variable: NEXT_PUBLIC_WS_URL
Value: wss://[TU-BACKEND-URL-DEL-PASO-3.5]/api/ws

Variable: JWT_SECRET
Value: [EL MISMO JWT_SECRET QUE USASTE EN EL BACKEND]

Variable: NODE_ENV
Value: production

Variable: NEXT_TELEMETRY_DISABLED
Value: 1
```

**⚠️ IMPORTANTE:** 
- Reemplaza `[TU-BACKEND-URL-DEL-PASO-3.5]` con la URL que copiaste antes
- Ejemplo: `https://backend-prod-production-xyz.up.railway.app/api`
- El `JWT_SECRET` **DEBE SER EXACTAMENTE EL MISMO** que el del backend

**Ejemplo completo:**
```
NEXT_PUBLIC_API_URL=https://backend-prod-production-xyz.up.railway.app/api
NEXT_PUBLIC_WS_URL=wss://backend-prod-production-xyz.up.railway.app/api/ws
JWT_SECRET=a1b2c3d4e5f6....(tu clave)
NODE_ENV=production
NEXT_TELEMETRY_DISABLED=1
```

### 4.4. Deploy Dashboard

1. Ve a la pestaña **"Deployments"**
2. Railway iniciará el deploy automáticamente
3. **⏳ Espera 4-6 minutos** (Next.js tarda más en compilar)
4. Verás logs: `Building...` → `Build successful` → `Deployment live`

### 4.5. Obtener URL del Dashboard

1. Ve a **"Settings"**
2. Scroll hasta **"Networking"**
3. Click en **"Generate Domain"**
4. Railway generará: `dashboard-production-xyz.up.railway.app`
5. **📝 COPIA ESTA URL**

---

## 🔧 PASO 5: ACTUALIZAR CORS (3 minutos)

Ahora que tienes ambas URLs, necesitas actualizar el CORS del backend:

1. Ve al servicio **`backend`**
2. Ve a **"Variables"**
3. Busca la variable **`BACKEND_CORS_ORIGINS`**
4. Click en el icono de editar (lápiz)
5. Reemplaza el valor con:

```json
["https://[TU-DASHBOARD-URL]","http://localhost:3000"]
```

**Ejemplo:**
```json
["https://dashboard-production-xyz.up.railway.app","http://localhost:3000"]
```

6. Click **"Update"**
7. El servicio se reiniciará automáticamente (~30 segundos)

---

## ✅ PASO 6: VERIFICACIÓN FINAL (3 minutos)

### 6.1. Verificar Backend

**En tu terminal local:**

```bash
# Health check del backend
curl https://[TU-BACKEND-URL]/health
```

**Deberías ver:**
```json
{
  "status": "healthy",
  "database": "connected",
  "timestamp": "2024-11-24T..."
}
```

✅ Si ves esto, **el backend funciona correctamente!**

### 6.2. Verificar Dashboard

**En tu navegador:**

```bash
# O usa curl
curl https://[TU-DASHBOARD-URL]/api/health
```

**Deberías ver:**
```json
{
  "status": "ok",
  "timestamp": "2024-11-24T..."
}
```

✅ Si ves esto, **el dashboard funciona correctamente!**

### 6.3. Abrir Dashboard en el Navegador

```bash
# Abre el dashboard
open https://[TU-DASHBOARD-URL]
```

O visita la URL en tu navegador.

Deberías ver la página de login o el dashboard de Stakazo.

### 6.4. Probar API Docs

```bash
# Abrir documentación interactiva
open https://[TU-BACKEND-URL]/docs
```

Deberías ver la interfaz de Swagger UI con todos los endpoints.

---

## 📋 CHECKLIST FINAL

Marca cada item cuando lo hayas verificado:

### Backend ✅

- [ ] ✅ Servicio `backend` está en estado **"Active"** (verde)
- [ ] ✅ Deployment más reciente dice **"Success"**
- [ ] ✅ `curl [BACKEND-URL]/health` retorna `{"status":"healthy"}`
- [ ] ✅ `curl [BACKEND-URL]/docs` retorna HTML de Swagger UI
- [ ] ✅ Migraciones ejecutadas: `railway run --service backend alembic current` muestra el head
- [ ] ✅ Logs no muestran errores críticos

### Dashboard ✅

- [ ] ✅ Servicio `dashboard` está en estado **"Active"** (verde)
- [ ] ✅ Deployment más reciente dice **"Success"**
- [ ] ✅ `curl [DASHBOARD-URL]/api/health` retorna `{"status":"ok"}`
- [ ] ✅ Abrir `[DASHBOARD-URL]` en navegador muestra la interfaz
- [ ] ✅ No hay errores de CORS en la consola del navegador
- [ ] ✅ WebSocket se conecta correctamente

### PostgreSQL ✅

- [ ] ✅ Servicio `Postgres` está en estado **"Active"** (verde)
- [ ] ✅ Backend puede conectarse (health check muestra "database":"connected")
- [ ] ✅ Tablas creadas (verificar con migraciones)

### Variables de Entorno ✅

- [ ] ✅ Backend tiene 25+ variables configuradas
- [ ] ✅ Dashboard tiene 5 variables configuradas
- [ ] ✅ `JWT_SECRET` es idéntico en backend y dashboard
- [ ] ✅ `BACKEND_CORS_ORIGINS` incluye la URL del dashboard
- [ ] ✅ `NEXT_PUBLIC_API_URL` apunta al backend correcto
- [ ] ✅ `DATABASE_URL` está referenciando a Postgres correctamente

### Networking ✅

- [ ] ✅ Backend tiene dominio generado: `https://backend-prod-...`
- [ ] ✅ Dashboard tiene dominio generado: `https://dashboard-...`
- [ ] ✅ Ambos dominios son accesibles públicamente
- [ ] ✅ SSL/HTTPS funciona correctamente (candado verde en navegador)

---

## 🎯 URLS FINALES

Una vez completado, guarda estas URLs en un lugar seguro:

```plaintext
=== PRODUCCIÓN RAILWAY ===

Backend API:
https://[TU-BACKEND-URL]

API Docs:
https://[TU-BACKEND-URL]/docs

Dashboard:
https://[TU-DASHBOARD-URL]

PostgreSQL:
(Railway proporciona DATABASE_URL internamente)

=== CREDENCIALES ===

JWT_SECRET: [guardado en password manager]
CREDENTIALS_ENCRYPTION_KEY: [guardado en password manager]

=== COSTOS ===

PostgreSQL: ~$5/mes
Backend: ~$5/mes
Dashboard: ~$5/mes
Total: ~$15/mes
```

---

## 🐛 TROUBLESHOOTING

### Error: "Database connection failed"

```bash
# Verificar que el servicio Postgres esté activo
railway status

# Verificar que DATABASE_URL esté configurada
railway variables --service backend | grep DATABASE_URL

# Re-deployar backend
railway up --service backend
```

### Error: "CORS policy error"

Verifica que `BACKEND_CORS_ORIGINS` incluya la URL exacta del dashboard:

```json
["https://dashboard-production-xyz.up.railway.app","http://localhost:3000"]
```

Sin trailing slash, con `https://`.

### Error: "JWT signature verification failed"

El `JWT_SECRET` debe ser **exactamente el mismo** en backend y dashboard.

Verifica:
```bash
railway variables --service backend | grep JWT_SECRET
railway variables --service dashboard | grep JWT_SECRET
```

Deben ser idénticos.

### Error: "Deployment failed" en el build

1. Ve a **Deployments** → Click en el deployment fallido
2. Revisa los logs
3. Errores comunes:
   - **"Dockerfile not found"**: Verifica Root Directory y Dockerfile Path
   - **"Build timeout"**: Incrementa timeout en Settings → Build
   - **"Out of memory"**: Upgrade a plan superior

### Backend no responde

```bash
# Ver logs en tiempo real
railway logs --service backend --tail

# Reiniciar servicio
railway restart --service backend
```

### Dashboard no carga

```bash
# Ver logs
railway logs --service dashboard --tail

# Verificar que NEXT_PUBLIC_API_URL sea correcta
railway variables --service dashboard | grep NEXT_PUBLIC_API_URL

# Reiniciar
railway restart --service dashboard
```

---

## 🔄 COMANDOS ÚTILES

```bash
# Ver estado de todos los servicios
railway status

# Ver logs en tiempo real
railway logs --service backend --tail
railway logs --service dashboard --tail

# Ver variables
railway variables --service backend
railway variables --service dashboard

# Reiniciar servicio
railway restart --service backend
railway restart --service dashboard

# Re-deployar
railway up --service backend
railway up --service dashboard

# Ejecutar comando en el backend
railway run --service backend [comando]

# Abrir Railway dashboard
railway open

# Desconectar del proyecto
railway unlink
```

---

## 🎉 ¡DEPLOY COMPLETO!

Si todos los checkboxes están marcados, tu aplicación Stakazo está corriendo en producción en Railway.

**URLs de acceso:**
- **Dashboard:** https://[tu-dashboard-url]
- **API Docs:** https://[tu-backend-url]/docs
- **API Health:** https://[tu-backend-url]/health

**Próximos pasos:**
1. Configura dominios custom (opcional)
2. Activa AI en modo LIVE (agrega OPENAI_API_KEY o GEMINI_API_KEY)
3. Configura credenciales de plataformas sociales
4. Configura alertas y monitoring en Railway

---

**¿Necesitas ayuda?**
- Railway Docs: https://docs.railway.app
- Railway Discord: https://discord.gg/railway
- Railway Status: https://status.railway.app

---

**Documentación generada:** 2024-11-24  
**Commit:** 263cc4a  
**Ready:** ✅ GO!
