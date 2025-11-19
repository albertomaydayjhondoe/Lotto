# Stakazo - Orquestador AI API

API para el Orquestador del Sistema Maestro de IA. Maneja uploads de videos, jobs de procesamiento, clips, campañas y la integración con plataformas sociales.

## 🚀 Inicio Rápido

### 1. Clonar e Iniciar Servicios

```bash
# Iniciar PostgreSQL y Backend
make dev

# O iniciar solo la base de datos
make db
```

### 2. Inicializar Base de Datos

```bash
# Crear schema y datos de ejemplo
make init-db
```

### 3. Explorar la API

- **API Docs (Swagger)**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## 📚 Comandos Disponibles

```bash
make help           # Muestra todos los comandos disponibles
make dev            # Inicia backend y postgres
make api            # Inicia solo el backend en modo reload (local)
make db             # Inicia solo PostgreSQL
make init-db        # Inicializa BD con schema y datos
make migrate        # Aplica migraciones
make migrate-create # Crea nueva migración
make stop           # Detiene todos los servicios
make logs           # Muestra logs
make clean          # Limpia contenedores y cache
make test           # Ejecuta tests
make build          # Reconstruye imágenes Docker
```

## 📁 Estructura del Proyecto

```
stakazo/
├── .devcontainer/          # Configuración Dev Container
│   ├── devcontainer.json   # Python 3.11 + Node 20 + Docker in Docker
│   ├── Dockerfile
│   └── post-create.sh      # Auto-setup en Codespaces
├── backend/                # FastAPI Backend
│   ├── app/
│   │   ├── api/           # Endpoints
│   │   │   ├── upload.py        # POST /upload
│   │   │   ├── jobs.py          # Jobs endpoints
│   │   │   ├── clips.py         # Clips endpoints
│   │   │   ├── campaigns.py     # Campaigns
│   │   │   ├── rules.py         # Platform rules
│   │   │   ├── confirm_publish.py
│   │   │   └── webhooks.py      # Instagram webhooks
│   │   ├── models/
│   │   │   ├── schemas.py       # Pydantic models
│   │   │   └── database.py      # SQLAlchemy models
│   │   ├── core/
│   │   │   ├── config.py        # Settings
│   │   │   └── database.py      # DB connection
│   │   ├── db/
│   │   │   └── init_db.py       # DB initialization
│   │   └── main.py              # FastAPI app
│   ├── alembic/                 # Database migrations
│   ├── main.py                  # Entry point
│   ├── Dockerfile
│   └── requirements.txt
├── clients/                # Generated API clients
│   ├── python/            # Python client
│   └── typescript-axios/  # TypeScript client
├── openapi/               # OpenAPI specification
│   └── orquestador_openapi.yaml
├── docker-compose.yml
├── Makefile
└── README.md
```

## 🔌 API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/upload` | Upload video file |
| POST | `/jobs` | Create processing job |
| GET | `/jobs` | List all jobs |
| GET | `/jobs/{id}` | Get job details |
| GET | `/clips` | List clips |
| POST | `/clips/{id}/variants` | Generate clip variants |
| POST | `/confirm_publish` | Confirm publishing |
| POST | `/webhook/instagram` | Instagram webhook |
| POST | `/campaigns` | Create campaign |
| GET | `/campaigns` | List campaigns |
| GET | `/rules` | Get platform rules |
| POST | `/rules` | Propose rule changes |

## 🗄️ Database Schema

### Tablas Principales

- **video_assets**: Videos subidos
- **clips**: Clips extraídos de videos
- **clip_variants**: Variantes optimizadas por plataforma
- **jobs**: Tareas de procesamiento
- **campaigns**: Campañas publicitarias
- **platform_rules**: Reglas específicas por plataforma
- **publications**: Registro de publicaciones

### Relaciones

- `VideoAsset` → muchos `Clips`
- `Clip` → muchas `ClipVariants`
- `Clip` → muchos `Jobs`
- `Clip` → muchas `Campaigns`
- `Clip` → muchas `Publications`

## 🔧 Configuración

### Variables de Entorno

Crear archivo `.env` en `backend/`:

```bash
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/stakazo_db
SECRET_KEY=your-secret-key-change-in-production
UPLOAD_DIR=/tmp/uploads
MAX_UPLOAD_SIZE=524288000
```

### Database Connection

```python
# Local (host)
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/stakazo_db

# Docker (container to container)
DATABASE_URL=postgresql+asyncpg://postgres:postgres@postgres:5432/stakazo_db
```

## 🧪 Testing

```bash
# Ejecutar todos los tests
make test

# Ejecutar tests específicos
cd backend && pytest tests/test_jobs.py -v
```

## 🐳 Docker

### Servicios

- **postgres**: PostgreSQL 15 (puerto 5432)
- **backend**: FastAPI con hot-reload (puerto 8000)

### Volúmenes

- `postgres_data`: Datos de PostgreSQL
- `uploads_data`: Archivos subidos

## 🔄 Migrations con Alembic

```bash
# Crear nueva migración (auto-detecta cambios)
make migrate-create MSG="add user table"

# Aplicar migraciones
make migrate

# Ver historial
cd backend && alembic history

# Rollback
cd backend && alembic downgrade -1
```

## 🧑‍💻 Desarrollo

### Dev Container (Codespaces)

El proyecto está configurado con Dev Container que incluye:

- Python 3.11
- Node 20
- Docker in Docker
- Extensiones VS Code: Python, FastAPI, Docker, YAML
- Auto-instalación de dependencias al crear el Codespace

### Desarrollo Local

```bash
# 1. Instalar dependencias
pip install -r requirements.txt
pip install -r backend/requirements.txt

# 2. Iniciar PostgreSQL
make db

# 3. Inicializar BD
make init-db

# 4. Iniciar backend en modo dev
make api
```

## 📦 Clientes Generados

### Python Client

```python
from orquestador_api_client import Client
from orquestador_api_client.api.default import post_jobs
from orquestador_api_client.models import JobCreate

client = Client(base_url="http://localhost:8000")

job = post_jobs.sync(
    client=client,
    json_body=JobCreate(
        job_type="process",
        clip_id="uuid-here"
    )
)
```

### TypeScript Client

```typescript
import { DefaultService } from './clients/typescript-axios';

const campaign = await DefaultService.postCampaigns({
  name: "Holiday Campaign",
  clip_id: "uuid-here",
  budget_cents: 100000
});
```

## 🚢 Deployment

### Railway / Render

1. Conectar repositorio
2. Configurar variables de entorno
3. Agregar PostgreSQL addon
4. Deploy automático en cada push a `main`

### Environment Variables para Producción

```bash
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/db
SECRET_KEY=<generate-secure-key>
UPLOAD_DIR=/app/uploads
MAX_UPLOAD_SIZE=524288000
BACKEND_CORS_ORIGINS=["https://yourdomain.com"]
```

## 📝 Licencia

Proyecto privado - Sistema Proyecto Mundial

---

**Desarrollado con** ❤️ **usando FastAPI + PostgreSQL + Docker**

