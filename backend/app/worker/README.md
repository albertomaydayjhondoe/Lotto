# Job Runner System

Sistema completo de procesamiento autónomo de jobs del orquestador.

## 🏗️ Arquitectura

```
backend/app/worker/
├── __init__.py          # Exports principales
├── worker.py            # Loop principal del worker
├── queue.py             # Cola persistente con locking
├── dispatcher.py        # Tabla de dispatch job_type → handler
└── handlers/
    ├── __init__.py
    └── cut_analysis.py  # Handler para análisis de cortes
```

## 🔄 Estados de Jobs

```
PENDING    → Job creado, esperando procesamiento
PROCESSING → Job en ejecución
RETRY      → Job falló, será reintentado
COMPLETED  → Job completado exitosamente
FAILED     → Job falló permanentemente
```

## 🎯 Componentes

### 1. Cola Persistente (`queue.py`)

**Función principal:** `async def dequeue_job(db: AsyncSession)`

Características:
- Usa `SELECT FOR UPDATE SKIP LOCKED` para PostgreSQL
- Fallback para SQLite (sin locking concurrente)
- Selecciona jobs PENDING ordenados por created_at
- Marca inmediatamente como PROCESSING
- Commit automático para bloquear el job
- Soporta múltiples workers concurrentes

**SQL (PostgreSQL):**
```sql
SELECT * FROM jobs 
WHERE status = 'pending'
ORDER BY created_at
FOR UPDATE SKIP LOCKED
LIMIT 1
```

### 2. Dispatcher (`dispatcher.py`)

**DISPATCH_TABLE:**
```python
{
    "cut_analysis": run_cut_analysis,
    # Añadir más handlers aquí
}
```

**Función:** `async def dispatch_job(job: Job, db: AsyncSession)`

- Valida que el job_type exista en DISPATCH_TABLE
- Ejecuta el handler correspondiente
- Lanza KeyError si job_type desconocido

### 3. Worker Loop (`worker.py`)

**Función principal:** `async def worker_loop(db: AsyncSession)`

**Flujo:**
```python
while True:
    job = await dequeue_job(db)
    if not job:
        await asyncio.sleep(WORKER_POLL_INTERVAL)
        continue
    
    try:
        handler = DISPATCH_TABLE[job.job_type]
        result = await handler(job, db)
        job.status = COMPLETED
        job.result = result
    except Exception as e:
        job.status = FAILED
        job.error = str(e)
    
    await db.commit()
```

**Función auxiliar:** `async def process_single_job(db: AsyncSession)`

- Procesa UN solo job del queue
- Usado por endpoint `/jobs/process` (dev)
- Retorna dict con summary del procesamiento

### 4. Handler: Cut Analysis (`handlers/cut_analysis.py`)

**Función:** `async def run_cut_analysis(job: Job, db: AsyncSession)`

**Proceso:**
1. Lee el video_asset_id del job
2. Obtiene VideoAsset de la DB
3. Simula análisis con `asyncio.sleep(0.5)`
4. Genera N clips basados en duración (1 clip cada 20s)
5. Calcula visual_score para cada clip
6. Crea registros Clip en la DB
7. Retorna dict:
   ```json
   {
     "clips_created": 3,
     "duration": 60000,
     "variants": [
       {
         "clip_id": "uuid",
         "start_ms": 0,
         "end_ms": 20000,
         "visual_score": 0.85
       }
     ]
   }
   ```

## 🔌 API Endpoints

### POST /jobs/process (DEV ONLY)

Procesa el siguiente job PENDING de la cola.

**Request:**
```bash
POST /jobs/process
```

**Response:**
```json
{
  "processed": true,
  "job_id": "uuid",
  "job_type": "cut_analysis",
  "status": "completed",
  "result": {
    "clips_created": 3,
    "duration": 60000,
    "variants": [...]
  },
  "processing_time_ms": 544,
  "error": null
}
```

**Si no hay jobs:**
```json
{
  "processed": false,
  "message": "No pending jobs in queue"
}
```

## ⚙️ Configuración

En `backend/app/core/config.py`:

```python
WORKER_POLL_INTERVAL: int = 2      # Segundos entre checks
MAX_JOB_RETRIES: int = 3           # Reintentos máximos
WORKER_ENABLED: bool = False       # Activar worker background
```

## 🧪 Tests

**Archivo:** `tests/test_job_runner.py`

**Tests implementados:**
1. ✅ **test_process_job_from_queue** - Procesa job desde cola completo
2. ✅ **test_no_reprocess_completed_jobs** - No reprocesa jobs completados
3. ✅ **test_unknown_job_type_fails** - Job type inválido marca FAILED
4. ✅ **test_concurrent_queue_processing** - 3 jobs procesados sin conflictos
5. ✅ **test_queue_empty_returns_false** - Queue vacío retorna processed=false

**Ejecutar tests:**
```bash
cd backend
PYTHONPATH=/workspaces/stakazo/backend:$PYTHONPATH pytest tests/test_job_runner.py -v -s
```

**Resultado:**
```
5 passed, 60 warnings in 3.06s
```

## 🚀 Uso

### Modo Manual (Dev)

```python
from app.worker import process_single_job
from app.core.database import get_db

async for db in get_db():
    result = await process_single_job(db)
    print(result)
    break
```

### Modo Background Worker

```python
from app.worker import worker_loop
from app.core.database import get_db
import asyncio

async def start_worker():
    async for db in get_db():
        await worker_loop(db)

asyncio.run(start_worker())
```

### Via API (Testing)

```bash
curl -X POST http://localhost:8000/jobs/process
```

## 📊 Flujo Completo

```
1. Cliente crea job:
   POST /upload → crea VideoAsset + Job(status=PENDING)

2. Worker dequeue:
   SELECT ... FOR UPDATE SKIP LOCKED
   → Marca PROCESSING

3. Dispatcher:
   DISPATCH_TABLE[job_type] → handler

4. Handler ejecuta:
   run_cut_analysis(job, db)
   → Genera clips

5. Worker actualiza:
   job.status = COMPLETED
   job.result = {...}
   → COMMIT

6. Cliente consulta:
   GET /jobs/{id} → status=COMPLETED
```

## 🔒 Concurrencia

**Múltiples workers:**
- ✅ Row-level locking con FOR UPDATE SKIP LOCKED
- ✅ Cada worker procesa jobs diferentes
- ✅ Sin deadlocks
- ✅ Sin duplicación de procesamiento

**SQLite Limitation:**
- ⚠️ No soporta FOR UPDATE SKIP LOCKED
- ⚠️ Fallback a SELECT simple
- ⚠️ No recomendado para múltiples workers en producción
- ✅ PostgreSQL recomendado para producción

## 🎨 Extensibilidad

### Añadir nuevo handler:

1. Crear handler en `handlers/`:

```python
# handlers/my_handler.py
async def run_my_handler(job: Job, db: AsyncSession) -> Dict[str, Any]:
    # Tu lógica aquí
    return {"result": "success"}
```

2. Registrar en dispatcher:

```python
# dispatcher.py
from app.worker.handlers.my_handler import run_my_handler

DISPATCH_TABLE = {
    "cut_analysis": run_cut_analysis,
    "my_handler": run_my_handler,  # ← Añadir aquí
}
```

3. Crear jobs con el nuevo tipo:

```python
job = Job(
    job_type="my_handler",
    status=JobStatus.PENDING,
    params={...}
)
```

## 📈 Monitoreo

**Queries útiles:**

```sql
-- Jobs por estado
SELECT status, COUNT(*) FROM jobs GROUP BY status;

-- Jobs fallidos recientes
SELECT * FROM jobs WHERE status = 'failed' ORDER BY updated_at DESC LIMIT 10;

-- Tiempo promedio de procesamiento
SELECT AVG(EXTRACT(EPOCH FROM (updated_at - created_at))) 
FROM jobs 
WHERE status = 'completed';
```

## 🐛 Debugging

**Activar logs:**
```python
import logging
logging.basicConfig(level=logging.INFO)
```

**Logs importantes:**
- `Processing job {id} (type: {type})`
- `Job {id} completed successfully in {ms}ms`
- `Job {id} failed: {error}`

## ✅ Checklist de Producción

- [ ] WORKER_ENABLED = True en producción
- [ ] Usar PostgreSQL (no SQLite)
- [ ] Configurar MAX_JOB_RETRIES adecuadamente
- [ ] Monitorear queue depth
- [ ] Logs centralizados
- [ ] Alertas para jobs FAILED
- [ ] Métricas de throughput
- [ ] Health checks del worker
