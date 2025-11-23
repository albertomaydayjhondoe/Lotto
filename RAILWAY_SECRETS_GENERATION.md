# 🔑 Generación de Claves Seguras para Railway

Este archivo contiene los comandos para generar las claves criptográficas necesarias para el despliegue en Railway.

## 📋 Claves Requeridas

### 1. JWT_SECRET (para autenticación)

**Comando:**
```bash
openssl rand -hex 64
```

**Descripción:** Genera una clave hexadecimal de 128 caracteres para firmar tokens JWT.

**Ejemplo de salida:**
```
a1b2c3d4e5f6...
```

**Dónde usar:**
- Backend: `JWT_SECRET`
- Dashboard: `JWT_SECRET` (debe ser el mismo)

---

### 2. CREDENTIALS_ENCRYPTION_KEY (para encriptar credenciales)

**Comando:**
```bash
python3 - <<EOF
from cryptography.fernet import Fernet
print(Fernet.generate_key().decode())
EOF
```

**Descripción:** Genera una clave Fernet válida para encriptar credenciales de plataformas sociales.

**Ejemplo de salida:**
```
abcdefghijklmnopqrstuvwxyz0123456789ABCD=
```

**Dónde usar:**
- Backend: `CREDENTIALS_ENCRYPTION_KEY`

---

## 🚀 Pasos para Railway

### Paso 1: Generar Claves

Ejecuta los comandos de arriba y guarda los valores generados en un lugar seguro (ej: 1Password, LastPass, archivo local cifrado).

```bash
# Generar JWT_SECRET
JWT_SECRET=$(openssl rand -hex 64)
echo "JWT_SECRET=$JWT_SECRET"

# Generar CREDENTIALS_ENCRYPTION_KEY
CRED_KEY=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
echo "CREDENTIALS_ENCRYPTION_KEY=$CRED_KEY"
```

### Paso 2: Configurar Variables en Railway

1. Ve a tu proyecto en Railway: https://railway.app/dashboard
2. Selecciona el servicio **Backend**
3. Ve a la pestaña **Variables**
4. Copia las variables de `backend/.env.production` y reemplaza:
   - `REEMPLAZA_CON_UNA_CLAVE_SEGURA` → Tu JWT_SECRET generado
   - `REEMPLAZA_CON_FERNET_KEY` → Tu CREDENTIALS_ENCRYPTION_KEY generado
   - `TU-DOMINIO` → El dominio que Railway te asignó (ej: `stakazo-backend.up.railway.app`)

5. Selecciona el servicio **Dashboard**
6. Ve a la pestaña **Variables**
7. Copia las variables de `dashboard/.env.production` y reemplaza:
   - `REEMPLAZA_CON_MISMO_QUE_BACKEND` → El mismo JWT_SECRET del backend
   - `TU-DOMINIO` → El dominio del backend (sin `/api`)

---

## 📝 Template Backend (Railway Variables)

```env
JWT_SECRET=TU_JWT_SECRET_GENERADO_AQUI
ACCESS_TOKEN_EXPIRE_MINUTES=43200
CREDENTIALS_ENCRYPTION_KEY=TU_FERNET_KEY_GENERADA_AQUI
AI_LLM_MODE=stub
DATABASE_URL=${{postgresql.DATABASE_URL}}
API_BASE_URL=https://stakazo-backend.up.railway.app/api
BACKEND_CORS_ORIGINS=["https://stakazo-dashboard.up.railway.app","http://localhost:3000"]
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

---

## 📝 Template Dashboard (Railway Variables)

```env
NEXT_PUBLIC_API_URL=https://stakazo-backend.up.railway.app/api
NEXT_PUBLIC_WS_URL=wss://stakazo-backend.up.railway.app/api/ws
JWT_SECRET=TU_JWT_SECRET_GENERADO_AQUI
NODE_ENV=production
NEXT_TELEMETRY_DISABLED=1
```

---

## ✅ Verificación

Después de configurar las variables:

1. **Deploy Backend:**
   ```bash
   railway up --service backend
   ```

2. **Ejecutar Migraciones:**
   ```bash
   railway run --service backend alembic upgrade head
   ```

3. **Deploy Dashboard:**
   ```bash
   railway up --service dashboard
   ```

4. **Verificar Health:**
   ```bash
   curl https://stakazo-backend.up.railway.app/health
   curl https://stakazo-dashboard.up.railway.app/api/health
   ```

---

## 🔒 Seguridad

**IMPORTANTE:**
- ✅ **NUNCA** subas las claves al repositorio Git
- ✅ Guarda las claves en un gestor de contraseñas
- ✅ Rota las claves cada 90 días
- ✅ Usa diferentes claves para desarrollo, staging y producción
- ✅ El JWT_SECRET debe ser el mismo en backend y dashboard

---

## 🛠️ Troubleshooting

### Error: "Invalid Fernet key"
```bash
# Regenerar clave Fernet
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### Error: "JWT signature verification failed"
```bash
# Asegúrate de que JWT_SECRET sea exactamente el mismo en backend y dashboard
```

### Error: "Database connection failed"
```bash
# Railway inyecta automáticamente DATABASE_URL
# Verifica que el servicio PostgreSQL esté running:
railway status
```

---

## 📚 Referencias

- **Railway Docs**: https://docs.railway.app/
- **Fernet (cryptography)**: https://cryptography.io/en/latest/fernet/
- **OpenSSL**: https://www.openssl.org/docs/
- **JWT**: https://jwt.io/

---

**Generado:** 2024-11-23  
**PASO:** 9.1 Railway Deployment Preparation
