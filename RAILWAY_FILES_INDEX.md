# 📂 Railway Deployment - Índice de Archivos

**Commit:** aa7ee5c  
**Status:** ✅ Ready to Deploy  
**Fecha:** 2024-11-23

---

## 🗂️ Archivos de Configuración Railway

### Variables de Entorno

| Archivo | Ubicación | Descripción |
|---------|-----------|-------------|
| Backend .env | `backend/.env.production` | Variables para el servicio backend |
| Dashboard .env | `dashboard/.env.production` | Variables para el servicio dashboard |

**Nota:** Estos archivos son **templates**. Copia su contenido a Railway UI → Variables.

---

### Configuración de Servicios

| Archivo | Ubicación | Descripción |
|---------|-----------|-------------|
| Backend Config | `backend/railway.json` | Configuración del servicio backend |
| Dashboard Config | `dashboard/railway.json` | Configuración del servicio dashboard |
| Nginx Config | `infra/railway.json` | Configuración del reverse proxy (opcional) |

**Nota:** Railway lee automáticamente estos archivos si conectas el repo.

---

### Dockerfiles

| Archivo | Ubicación | Descripción |
|---------|-----------|-------------|
| Backend Docker | `backend/Dockerfile.prod` | Container de producción para backend |
| Dashboard Docker | `dashboard/Dockerfile` | Container de producción para dashboard |
| Nginx Docker | `infra/Dockerfile.nginx` | Container del reverse proxy (opcional) |

**Nota:** Railway detecta automáticamente estos Dockerfiles.

---

## 📖 Documentación

### Guías de Deployment

| Documento | Descripción | Cuándo Usar |
|-----------|-------------|-------------|
| [RAILWAY_QUICKSTART.md](./RAILWAY_QUICKSTART.md) | ⚡ **Inicio más rápido** - Deploy en 3 pasos | Primera vez deployando |
| [RAILWAY_SECRETS_GENERATION.md](./RAILWAY_SECRETS_GENERATION.md) | 🔑 Generación de claves seguras | Antes de configurar variables |
| [DEPLOY_RAILWAY.md](./DEPLOY_RAILWAY.md) | 📚 Guía completa + troubleshooting | Referencia detallada |
| [PASO_9.1_RAILWAY_SUMMARY.md](./PASO_9.1_RAILWAY_SUMMARY.md) | 📊 Resumen ejecutivo del proyecto | Context para el equipo |

---

### Scripts Automatizados

| Script | Ubicación | Descripción |
|--------|-----------|-------------|
| Deploy Script | `deploy-railway.sh` | ⚙️ Deploy automatizado (CLI) |
| Health Check | `scripts/healthcheck-railway.sh` | ✅ Verificación post-deploy |

**Nota:** Los scripts son opcionales. Puedes deployar manualmente vía Railway UI.

---

## 🚀 Flujo de Trabajo Recomendado

### Para Primera Vez

```
1. Leer:    RAILWAY_QUICKSTART.md
2. Generar: RAILWAY_SECRETS_GENERATION.md
3. Deploy:  Seguir pasos en QUICKSTART
4. Verificar: scripts/healthcheck-railway.sh
```

### Para CI/CD Automatizado

```
1. Configurar: railway.json en cada servicio
2. Conectar: GitHub repo → Railway
3. Auto-deploy: En cada push a main
```

### Para Troubleshooting

```
1. Consultar: DEPLOY_RAILWAY.md (sección Troubleshooting)
2. Verificar: scripts/healthcheck-railway.sh
3. Logs: railway logs --tail
```

---

## 📋 Checklist Pre-Deploy

- [ ] **Claves generadas**
  ```bash
  openssl rand -hex 64  # JWT_SECRET
  python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"  # FERNET_KEY
  ```

- [ ] **Railway CLI instalado**
  ```bash
  npm install -g @railway/cli
  ```

- [ ] **Logged in a Railway**
  ```bash
  railway login
  ```

- [ ] **PostgreSQL creado** en Railway

- [ ] **Variables de entorno** copiadas de `backend/.env.production`

- [ ] **Variables de entorno** copiadas de `dashboard/.env.production`

- [ ] **Dominios** reemplazados (TU-DOMINIO → dominios reales)

- [ ] **JWT_SECRET** es el mismo en backend y dashboard

---

## 🔄 Actualizar Deployment

### Actualizar Código

```bash
git pull origin MAIN
# Railway auto-deploya si está conectado al repo
```

### Actualizar Variables

1. Railway UI → Service → Variables
2. Editar variable
3. Service se reinicia automáticamente

### Rollback

```bash
railway rollback --service backend
railway rollback --service dashboard
```

---

## 🔒 Archivos Sensibles (No en Git)

Estos archivos **NO** están en el repositorio por seguridad:

- `backend/.env` (desarrollo local)
- `dashboard/.env.local` (desarrollo local)
- Cualquier archivo con `API_KEY` reales
- Archivos con `JWT_SECRET` reales

Los archivos `.env.production` son **templates** sin valores reales.

---

## 🌐 URLs de Producción (Ejemplo)

Después del deploy, tus URLs serán similares a:

```
Backend API:    https://stakazo-backend-prod.up.railway.app
Dashboard:      https://stakazo-dashboard-prod.up.railway.app
API Docs:       https://stakazo-backend-prod.up.railway.app/docs
Health Check:   https://stakazo-backend-prod.up.railway.app/health
```

Railway genera estas URLs automáticamente. Puedes configurar dominios custom después.

---

## 💡 Tips

1. **Usa el Quickstart primero** - Es la forma más rápida de deployar
2. **Guarda las claves en un password manager** - Las necesitarás
3. **Configura CORS después del deploy** - Usa los dominios reales de Railway
4. **Monitorea el costo** - Railway muestra uso en tiempo real
5. **Habilita notificaciones** - Railway te avisa de errores

---

## 📞 Soporte

- **Railway Docs:** https://docs.railway.app
- **Railway Discord:** https://discord.gg/railway
- **Documentación Stakazo:** Ver archivos en este directorio

---

## ✅ Estado del Proyecto

**Infraestructura Railway:** ✅ Completa  
**Documentación:** ✅ Completa  
**Scripts:** ✅ Listos  
**Templates:** ✅ Actualizados  
**Ready to Deploy:** ✅ **YES**

---

**Última actualización:** 2024-11-23  
**Commit:** aa7ee5c  
**Branch:** MAIN
