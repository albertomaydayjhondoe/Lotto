# 📝 MIS URLS DE RAILWAY - Completar Durante Deploy

**Proyecto:** stakazo-prod  
**Fecha deploy:** _______________  
**Deploy por:** _______________

---

## 🔑 CLAVES GENERADAS

**⚠️ COPIAR ESTAS CLAVES ANTES DE CONTINUAR:**

### JWT_SECRET (generado con: `openssl rand -hex 64`)

```
_____________________________________________________________________________

_____________________________________________________________________________
```

### CREDENTIALS_ENCRYPTION_KEY (generado con python + Fernet)

```
_____________________________________________________________________________
```

---

## 🗄️ POSTGRESQL

**Estado en Railway:** ☐ Active (verde)

**DATABASE_URL:** (Railway lo inyecta automáticamente, no necesitas escribirlo)

---

## 🖥️ BACKEND

### URLs

**Dominio Railway generado:**
```
https://_______________________________________________.up.railway.app
```

**Health Check:**
```
https://_______________________________________________.up.railway.app/health
```

**API Docs (Swagger):**
```
https://_______________________________________________.up.railway.app/docs
```

### Verificación

**Comando ejecutado:**
```bash
curl https://_______________________________________________.up.railway.app/health
```

**Respuesta esperada:** ☐ `{"status":"healthy","database":"connected"}`

**Migraciones ejecutadas:** ☐ Sí

**Comando usado:**
```bash
railway run --service backend alembic upgrade head
```

### Variables Configuradas (25 total)

- ☐ DATABASE_URL (referencia a Postgres)
- ☐ JWT_SECRET
- ☐ ACCESS_TOKEN_EXPIRE_MINUTES (43200)
- ☐ CREDENTIALS_ENCRYPTION_KEY
- ☐ AI_LLM_MODE (stub)
- ☐ API_BASE_URL
- ☐ BACKEND_CORS_ORIGINS
- ☐ OPENAI_API_KEY
- ☐ AI_OPENAI_MODEL_NAME (gpt-4)
- ☐ GEMINI_API_KEY
- ☐ AI_GEMINI_MODEL_NAME (gemini-2.0-flash-exp)
- ☐ AI_WORKER_ENABLED (true)
- ☐ AI_WORKER_INTERVAL_SECONDS (30)
- ☐ ORCHESTRATOR_ENABLED (true)
- ☐ ORCHESTRATOR_INTERVAL_SECONDS (2)
- ☐ PUBLISHING_STUB_MODE (true)
- ☐ PUBLISHING_PROVIDER_TIMEOUT_SECONDS (30)
- ☐ SCHEDULER_TICK_INTERVAL_SECONDS (60)
- ☐ TELEMETRY_INTERVAL_SECONDS (3)
- ☐ ALERT_SCAN_INTERVAL_SECONDS (60)
- ☐ ENVIRONMENT (production)
- ☐ LOG_LEVEL (info)
- ☐ TZ (UTC)

**Settings Configurados:**
- ☐ Root Directory: `backend`
- ☐ Watch Paths: `backend/**`
- ☐ Dockerfile Path: `Dockerfile.prod`

---

## 🎨 DASHBOARD

### URLs

**Dominio Railway generado:**
```
https://_______________________________________________.up.railway.app
```

**Health Check:**
```
https://_______________________________________________.up.railway.app/api/health
```

### Verificación

**Comando ejecutado:**
```bash
curl https://_______________________________________________.up.railway.app/api/health
```

**Respuesta esperada:** ☐ `{"status":"ok"}`

**Interfaz web carga:** ☐ Sí

**URL para abrir en navegador:**
```
https://_______________________________________________.up.railway.app
```

### Variables Configuradas (5 total)

- ☐ NEXT_PUBLIC_API_URL
  ```
  https://_______________________________________________.up.railway.app/api
  ```

- ☐ NEXT_PUBLIC_WS_URL
  ```
  wss://_______________________________________________.up.railway.app/api/ws
  ```

- ☐ JWT_SECRET (mismo que backend)
- ☐ NODE_ENV (production)
- ☐ NEXT_TELEMETRY_DISABLED (1)

**Settings Configurados:**
- ☐ Root Directory: `dashboard`
- ☐ Watch Paths: `dashboard/**`
- ☐ Dockerfile Path: `Dockerfile`

---

## 🔧 CORS ACTUALIZADO

**Variable actualizada en Backend:**
```json
["https://___[DASHBOARD-URL]___","http://localhost:3000"]
```

**Servicio reiniciado:** ☐ Sí (automático)

---

## ✅ VERIFICACIÓN FINAL

### Health Checks

- ☐ Backend health: OK
- ☐ Dashboard health: OK
- ☐ Database connected: OK

### Funcionalidad

- ☐ API Docs carga correctamente
- ☐ Dashboard carga correctamente
- ☐ No hay errores CORS en consola
- ☐ WebSocket conecta correctamente
- ☐ SSL funciona (candado verde)

### Railway Status

- ☐ Postgres: Active (verde)
- ☐ Backend: Active (verde)
- ☐ Dashboard: Active (verde)

---

## 💰 COSTOS ESTIMADOS

**Plan actual:** ☐ Hobby  ☐ Pro

**Estimación mensual:**
- PostgreSQL: $___
- Backend: $___
- Dashboard: $___
- **Total:** $___/mes

---

## 📊 COMANDOS ÚTILES

```bash
# Ver status
railway status

# Ver logs backend
railway logs --service backend --tail

# Ver logs dashboard
railway logs --service dashboard --tail

# Reiniciar backend
railway restart --service backend

# Reiniciar dashboard
railway restart --service dashboard

# Ver variables backend
railway variables --service backend

# Ver variables dashboard
railway variables --service dashboard

# Ejecutar comando en backend
railway run --service backend [comando]

# Abrir Railway dashboard
railway open
```

---

## 🎯 ACCESOS RÁPIDOS

**Copiar estos enlaces para acceso rápido:**

```markdown
### Stakazo Production (Railway)

- **Dashboard:** https://___[COMPLETA]___
- **API Docs:** https://___[COMPLETA]___/docs
- **Health Check:** https://___[COMPLETA]___/health
- **Railway Project:** https://railway.app/project/[PROJECT-ID]
```

---

## 🔐 SEGURIDAD

**Claves guardadas en:** _______________________________________________

**Acceso a claves:** _______________________________________________

**Última rotación de claves:** _______________________________________________

**Próxima rotación:** _______________________________________________ (90 días)

---

## 📝 NOTAS

```
_______________________________________________________________________________

_______________________________________________________________________________

_______________________________________________________________________________

_______________________________________________________________________________

_______________________________________________________________________________
```

---

## ✍️ CONFIRMACIÓN

**Deploy completado por:** _______________________________________________

**Fecha:** _______________________________________________

**Hora:** _______________________________________________

**Tiempo total:** _______________ minutos

**Firma:** _______________________________________________

---

**✅ Deploy completado exitosamente**

Guardar este archivo en un lugar seguro para referencia futura.
