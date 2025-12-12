# PASO 6.5: Sistema de Alertas (Alerting System)

## 📋 Resumen Ejecutivo

Sistema completo de alertas en tiempo real que monitorea el estado del sistema y notifica sobre problemas críticos, advertencias y eventos informativos. Incluye backend con motor de detección, base de datos, WebSocket para actualizaciones en tiempo real, frontend con UI reactiva, notificaciones toast y badge en navbar.

**Estado**: ✅ Completado al 100%
- Backend: ✅ 100% (Motor de alertas + WebSocket + Tests)
- Frontend: ✅ 100% (Hooks + Componentes + Página + Toast + Navbar)
- Tests: ✅ 13 tests comprehensivos (supera el mínimo de 10)
- Documentación: ✅ 100%

---

## 🏗️ Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND (Next.js)                        │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │ Alert Center │  │ Toast System │  │ Navbar Badge │         │
│  │   (Page)     │  │  (sonner)    │  │  (🔔 count)  │         │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘         │
│         │                  │                  │                  │
│  ┌──────▼──────────────────▼──────────────────▼───────┐        │
│  │              React Hooks Layer                      │        │
│  │  - useAlerts (React Query)                          │        │
│  │  - useAlertsWebSocket (WebSocket client)            │        │
│  │  - useMarkAlertRead (mutation)                      │        │
│  │  - useAlertStats (polling)                          │        │
│  └──────┬───────────────────────────────────┬──────────┘        │
│         │ REST API                          │ WebSocket         │
└─────────┼───────────────────────────────────┼──────────────────┘
          │                                   │
┌─────────▼───────────────────────────────────▼──────────────────┐
│                      BACKEND (FastAPI)                          │
├─────────────────────────────────────────────────────────────────┤
│  ┌────────────────────────────────────────────────────────┐    │
│  │              Alert Analysis Loop (60s)                  │    │
│  │  - Background asyncio task                             │    │
│  │  - Runs analyze_system_state() every minute            │    │
│  │  - Broadcasts alerts via WebSocket                     │    │
│  └────────────────────┬───────────────────────────────────┘    │
│                       │                                         │
│  ┌────────────────────▼────────────────────────────────────┐   │
│  │              Alert Engine (engine.py)                    │   │
│  │  ┌────────────────────────────────────────────────┐     │   │
│  │  │ analyze_system_state()                         │     │   │
│  │  │  1. _check_queue_saturation()                  │     │   │
│  │  │  2. _check_scheduler_backlog()                 │     │   │
│  │  │  3. _check_orchestrator_activity()             │     │   │
│  │  │  4. _check_publish_failures()                  │     │   │
│  │  │  5. _check_oauth_expiration()                  │     │   │
│  │  │  6. _check_worker_health()                     │     │   │
│  │  │  7. _check_campaign_status()                   │     │   │
│  │  │  8. _check_system_health()                     │     │   │
│  │  └────────────────┬───────────────────────────────┘     │   │
│  │                   │                                      │   │
│  │                   ▼                                      │   │
│  │  ┌────────────────────────────────────────────────┐     │   │
│  │  │ Deduplication (5-minute window)                │     │   │
│  │  │ - check_duplicate_alert()                      │     │   │
│  │  │ - Same type + severity + timestamp            │     │   │
│  │  └────────────────┬───────────────────────────────┘     │   │
│  └───────────────────┼──────────────────────────────────────┘   │
│                      │                                           │
│  ┌───────────────────▼───────────────────────────────────────┐  │
│  │              Service Layer (service.py)                   │  │
│  │  - create_alert() → Database                              │  │
│  │  - mark_alert_read()                                      │  │
│  │  - get_alerts()                                           │  │
│  │  - get_unread_count()                                     │  │
│  └───────────────────┬───────────────────────────────────────┘  │
│                      │                                           │
│  ┌───────────────────▼───────────────────────────────────────┐  │
│  │            REST Router (router.py)                        │  │
│  │  - GET  /alerting/alerts                                  │  │
│  │  - GET  /alerting/alerts/unread                           │  │
│  │  - POST /alerting/alerts/{id}/read                        │  │
│  │  - POST /alerting/run-analysis                            │  │
│  │  - GET  /alerting/stats                                   │  │
│  │  - WebSocket /alerting/ws/alerts                          │  │
│  └───────────────────┬───────────────────────────────────────┘  │
│                      │                                           │
│  ┌───────────────────▼───────────────────────────────────────┐  │
│  │         WebSocket Manager (websocket.py)                  │  │
│  │  - AlertManager.connect()                                 │  │
│  │  - AlertManager.disconnect()                              │  │
│  │  - AlertManager.broadcast_alert()                         │  │
│  └───────────────────┬───────────────────────────────────────┘  │
└────────────────────────┼──────────────────────────────────────┘
                         │
┌────────────────────────▼──────────────────────────────────────┐
│                   DATABASE (SQLite)                            │
├────────────────────────────────────────────────────────────────┤
│  alert_events table:                                           │
│  - id (UUID, PRIMARY KEY)                                      │
│  - alert_type (TEXT, 8 types)                                  │
│  - severity (TEXT, 3 levels)                                   │
│  - message (TEXT)                                              │
│  - metadata (JSON)                                             │
│  - created_at (TIMESTAMP)                                      │
│  - read (INTEGER, 0/1)                                         │
│                                                                │
│  Indices:                                                      │
│  - idx_alert_events_created_at                                 │
│  - idx_alert_events_read                                       │
│  - idx_alert_events_alert_type                                 │
│  - idx_alert_events_severity                                   │
└────────────────────────────────────────────────────────────────┘
```

---

## 🚨 Tipos de Alertas y Umbrales

| Tipo de Alerta | Severidad | Condición | Umbral |
|----------------|-----------|-----------|--------|
| **QUEUE_SATURATION** | CRITICAL | pending > 50 | 50+ clips pendientes |
| | WARNING | pending > 20 | 20-50 clips pendientes |
| **SCHEDULER_BACKLOG** | CRITICAL | scheduled_for < now - 10min | 10+ min de retraso |
| | WARNING | scheduled_for < now | Cualquier retraso |
| **ORCHESTRATOR_INACTIVE** | CRITICAL | no activity > 5min | 5+ min sin eventos |
| | WARNING | no activity > 2min | 2-5 min sin eventos |
| **PUBLISH_FAILURES_SPIKE** | CRITICAL | failures > 10 in 10min | 10+ fallos en 10min |
| | WARNING | failures > 5 in 10min | 5-10 fallos en 10min |
| **OAUTH_EXPIRING_SOON** | CRITICAL | expires_at < now + 5min | Expira en < 5min |
| | WARNING | expires_at < now + 20min | Expira en 5-20min |
| **WORKER_CRASH_DETECTED** | CRITICAL | processing > 5min | Job atascado > 5min |
| **CAMPAIGN_BLOCKED** | WARNING | active + 0 clips | Campaña sin clips |
| **SYSTEM_HEALTH_DEGRADED** | CRITICAL | Multiple subsystems | Problemas múltiples |

### Niveles de Severidad

- **INFO** (🔵): Eventos informativos, no requieren acción inmediata
- **WARNING** (🟡): Situaciones que requieren atención pero no son críticas
- **CRITICAL** (🔴): Problemas que requieren acción inmediata

---

## 📁 Estructura de Archivos

### Backend

```
backend/
├── app/
│   ├── alerting_engine/
│   │   ├── __init__.py         # Exports: router, alert_manager
│   │   ├── models.py           # Pydantic schemas + enums
│   │   ├── engine.py           # Core detection algorithms (522 lines)
│   │   ├── service.py          # CRUD operations (170 lines)
│   │   ├── router.py           # FastAPI endpoints (180 lines)
│   │   └── websocket.py        # AlertManager for broadcasting (88 lines)
│   ├── models/
│   │   └── database.py         # + AlertEventModel
│   └── main.py                 # + alert_analysis_loop() + router
├── alembic/
│   └── versions/
│       └── 009_alert_events.py # Database migration
└── tests/
    └── test_alerting_engine.py # 13 comprehensive tests (370 lines)
```

### Frontend

```
dashboard/
├── app/
│   └── dashboard/
│       ├── layout.tsx          # + Alerts nav link + badge
│       └── alerts/
│           └── page.tsx        # Alert center page
├── components/
│   └── dashboard/
│       ├── alert-card.tsx      # Individual alert card
│       └── alerts-list.tsx     # List with filtering
└── lib/
    └── alerts/
        ├── api.ts              # API client (5 functions)
        └── hooks.ts            # React hooks (5 hooks)
```

---

## 🔌 API Reference

### REST Endpoints

#### 1. GET /alerting/alerts
Obtiene todas las alertas con filtrado opcional.

**Query Parameters:**
- `unread_only` (bool, default: false): Solo alertas no leídas
- `limit` (int, default: 100): Máximo número de alertas

**Response:**
```json
{
  "alerts": [
    {
      "id": "uuid",
      "alert_type": "QUEUE_SATURATION",
      "severity": "CRITICAL",
      "message": "Queue saturation: 55 pending items",
      "metadata": {
        "pending_count": 55
      },
      "created_at": "2024-01-15T10:30:00Z",
      "read": false
    }
  ],
  "total": 42,
  "unread_count": 8
}
```

#### 2. GET /alerting/alerts/unread
Obtiene solo alertas no leídas.

**Query Parameters:**
- `limit` (int, default: 50)

**Response:** Same as GET /alerting/alerts

#### 3. POST /alerting/alerts/{id}/read
Marca una alerta como leída.

**Path Parameters:**
- `id` (string, UUID): ID de la alerta

**Response:**
```json
{
  "success": true,
  "message": "Alert marked as read"
}
```

#### 4. POST /alerting/run-analysis
Ejecuta análisis manual del sistema y broadcast de alertas.

**Response:**
```json
{
  "success": true,
  "alerts_generated": 3,
  "alerts": [
    {
      "id": "uuid",
      "alert_type": "SCHEDULER_BACKLOG",
      "severity": "WARNING",
      "message": "3 jobs overdue",
      "metadata": {
        "overdue_count": 3,
        "most_overdue_minutes": 15
      },
      "created_at": "2024-01-15T10:30:00Z",
      "read": false
    }
  ]
}
```

#### 5. GET /alerting/stats
Obtiene estadísticas del sistema de alertas.

**Response:**
```json
{
  "unread_count": 8,
  "active_connections": 3,
  "has_subscribers": true
}
```

### WebSocket Endpoint

#### WebSocket /alerting/ws/alerts
Stream de alertas en tiempo real.

**Connection:**
```javascript
const ws = new WebSocket('ws://localhost:8000/alerting/ws/alerts');
```

**Message Format (Server → Client):**
```json
{
  "id": "uuid",
  "alert_type": "PUBLISH_FAILURES_SPIKE",
  "severity": "CRITICAL",
  "message": "10 publish failures in the last 10 minutes",
  "metadata": {
    "failure_count": 10,
    "time_window_minutes": 10
  },
  "created_at": "2024-01-15T10:30:00Z",
  "read": false
}
```

**Ping/Pong:**
- Client sends `"ping"` every 30 seconds to keep connection alive
- Server responds with pong (automatically handled)

---

## 💻 Uso del Sistema

### Backend: Análisis Manual

```python
from app.alerting_engine.engine import analyze_system_state
from app.alerting_engine.websocket import alert_manager

# En un endpoint o tarea
async with get_db() as db:
    alerts = await analyze_system_state(db)
    for alert in alerts:
        await alert_manager.broadcast_alert(alert)
```

### Frontend: React Hooks

#### 1. Fetch All Alerts
```typescript
import { useAlerts } from '@/lib/alerts/hooks';

function MyComponent() {
  const { data, isLoading } = useAlerts(false); // all alerts
  // const { data, isLoading } = useAlerts(true); // unread only
  
  return (
    <div>
      {data?.alerts.map(alert => (
        <div key={alert.id}>{alert.message}</div>
      ))}
    </div>
  );
}
```

#### 2. WebSocket Real-Time Updates
```typescript
import { useAlertsWebSocket } from '@/lib/alerts/hooks';
import { toast } from 'sonner';

function MyComponent() {
  const { isConnected, lastAlert } = useAlertsWebSocket((alert) => {
    // Show toast notification
    if (alert.severity === 'CRITICAL') {
      toast.error(alert.message);
    } else if (alert.severity === 'WARNING') {
      toast.warning(alert.message);
    } else {
      toast.info(alert.message);
    }
  });
  
  return (
    <div>
      Status: {isConnected ? 'Connected' : 'Disconnected'}
    </div>
  );
}
```

#### 3. Mark Alert as Read
```typescript
import { useMarkAlertRead } from '@/lib/alerts/hooks';

function AlertCard({ alert }) {
  const markAsRead = useMarkAlertRead();
  
  return (
    <button onClick={() => markAsRead.mutate(alert.id)}>
      Mark as Read
    </button>
  );
}
```

#### 4. Get Unread Count
```typescript
import { useAlertStats } from '@/lib/alerts/hooks';

function Navbar() {
  const { data } = useAlertStats();
  
  return (
    <div>
      Unread: {data?.unread_count || 0}
    </div>
  );
}
```

---

## 🧪 Testing

### Backend Tests (13 tests)

```bash
# Run all alerting tests
cd backend
pytest tests/test_alerting_engine.py -v

# Run specific test
pytest tests/test_alerting_engine.py::test_queue_saturation_critical -v

# Run with coverage
pytest tests/test_alerting_engine.py --cov=app.alerting_engine --cov-report=html
```

**Test Coverage:**
- ✅ Queue saturation (warning + critical)
- ✅ Scheduler backlog detection
- ✅ Orchestrator inactivity monitoring
- ✅ Publish failures spike detection
- ✅ OAuth expiration warnings
- ✅ Worker crash detection
- ✅ Campaign blocked validation
- ✅ Deduplication logic (5-minute window)
- ✅ WebSocket broadcasting
- ✅ Full system analysis
- ✅ Mark as read functionality
- ✅ Unread filtering

### Frontend (Manual Testing)

1. **Start backend:**
   ```bash
   cd backend
   uvicorn app.main:app --reload
   ```

2. **Start frontend:**
   ```bash
   cd dashboard
   npm run dev
   ```

3. **Test scenarios:**
   - Navigate to `/dashboard/alerts`
   - Verify WebSocket connection (should show "Live" badge)
   - Click "Run Analysis" button
   - Check toast notifications appear
   - Verify navbar bell icon shows unread count
   - Mark alerts as read
   - Filter by unread
   - Check color coding (blue/yellow/red)

---

## 🔧 Configuración

### Environment Variables

**Backend (.env):**
```bash
# Database
DATABASE_URL=sqlite+aiosqlite:///./stakazo.db

# Alert Analysis
ALERT_ANALYSIS_INTERVAL=60  # seconds (default: 60)
```

**Frontend (.env.local):**
```bash
# API endpoints
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000

# Optional: Alert polling intervals (ms)
NEXT_PUBLIC_ALERT_STATS_POLL=5000   # 5 seconds
NEXT_PUBLIC_ALERTS_POLL=30000       # 30 seconds
```

### Threshold Tuning

To adjust alert thresholds, edit `backend/app/alerting_engine/engine.py`:

```python
# Queue Saturation
if pending_count > 50:  # Change this
    severity = AlertSeverity.CRITICAL
elif pending_count > 20:  # Or this
    severity = AlertSeverity.WARNING

# Orchestrator Inactive
if time_since_last > 300:  # 5 minutes (in seconds)
    severity = AlertSeverity.CRITICAL
elif time_since_last > 120:  # 2 minutes
    severity = AlertSeverity.WARNING
```

---

## 🚀 Deployment

### Database Migration

```bash
cd backend

# Apply migration
alembic upgrade head

# Verify table creation
sqlite3 stakazo.db "SELECT * FROM alert_events LIMIT 5;"
```

### Background Task

El loop de análisis se ejecuta automáticamente al iniciar la aplicación FastAPI:

```python
# In main.py
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start alert analysis task
    alert_task = asyncio.create_task(alert_analysis_loop())
    
    yield
    
    # Cleanup
    alert_task.cancel()
    try:
        await alert_task
    except asyncio.CancelledError:
        pass
```

**No se requiere configuración adicional** - el sistema comienza a monitorear automáticamente cada 60 segundos.

---

## 🐛 Troubleshooting

### Backend Issues

#### 1. Alerts not being generated
**Síntoma:** No se generan alertas automáticamente

**Diagnóstico:**
```bash
# Check logs
tail -f backend/logs/app.log | grep "Alert analysis"

# Verify background task is running
curl http://localhost:8000/alerting/stats
# Should show active_connections and has_subscribers
```

**Solución:**
- Verificar que el background task esté iniciado en `main.py`
- Comprobar que no haya errores en los logs
- Ejecutar análisis manual: `POST /alerting/run-analysis`

#### 2. WebSocket disconnects frequently
**Síntoma:** Clientes se desconectan constantemente

**Diagnóstico:**
```python
# Check AlertManager connections
from app.alerting_engine.websocket import alert_manager
print(len(alert_manager.active_connections))
```

**Solución:**
- Verificar que el cliente envíe ping cada 30s
- Comprobar firewall/proxy settings
- Aumentar timeout en servidor si es necesario

#### 3. Duplicate alerts
**Síntoma:** Se generan alertas duplicadas

**Diagnóstico:**
```sql
-- Check recent alerts
SELECT alert_type, severity, COUNT(*), MIN(created_at), MAX(created_at)
FROM alert_events
WHERE created_at > datetime('now', '-5 minutes')
GROUP BY alert_type, severity
HAVING COUNT(*) > 1;
```

**Solución:**
- Verificar que `check_duplicate_alert()` esté funcionando
- Ajustar ventana de deduplicación (default: 5 minutos)
- Comprobar índices de base de datos

### Frontend Issues

#### 1. WebSocket not connecting
**Síntoma:** Badge shows "Disconnected"

**Diagnóstico:**
```javascript
// Check browser console
// Should see: "Alert WebSocket connected"
```

**Solución:**
- Verificar `NEXT_PUBLIC_WS_URL` en `.env.local`
- Comprobar CORS settings en backend
- Verificar que el puerto 8000 esté accesible

#### 2. Toast notifications not appearing
**Síntoma:** No se muestran notificaciones

**Solución:**
```typescript
// Verify sonner is installed
import { toast } from 'sonner';

// Add Toaster component to layout
import { Toaster } from 'sonner';

function Layout({ children }) {
  return (
    <>
      {children}
      <Toaster position="top-right" />
    </>
  );
}
```

#### 3. Unread count not updating
**Síntoma:** Badge no refleja cambios

**Diagnóstico:**
```typescript
// Check React Query cache invalidation
import { useQueryClient } from '@tanstack/react-query';

const queryClient = useQueryClient();
queryClient.invalidateQueries({ queryKey: ['alert-stats'] });
```

**Solución:**
- Verificar que `useAlertsWebSocket` esté invalidando queries
- Comprobar polling interval (default: 5s)
- Forzar re-fetch manual si es necesario

---

## 📊 Performance Considerations

### Database

- **Índices**: 4 índices creados para queries eficientes
  - `created_at`: Para filtrado por fecha
  - `read`: Para queries de unread
  - `alert_type`: Para filtrado por tipo
  - `severity`: Para filtrado por severidad

- **Limpieza**: Considerar archivado de alertas antiguas:
  ```sql
  DELETE FROM alert_events 
  WHERE created_at < datetime('now', '-30 days');
  ```

### WebSocket

- **Connections**: AlertManager maneja múltiples conexiones eficientemente
- **Broadcasting**: O(n) donde n = número de clientes conectados
- **Dead Connection Cleanup**: Automático al intentar broadcast

### Frontend

- **React Query**: Cache automático con revalidación
- **Polling**: Configurar intervals según necesidad:
  - Stats: 5s (navbar badge)
  - Alerts: 30s (alert center)
  - WebSocket: Real-time (0 latency)

---

## 🎯 Next Steps

### Posibles Mejoras

1. **Notificaciones por Email**
   - Enviar emails para alertas CRITICAL
   - Configurar destinatarios por tipo de alerta

2. **Alertas Personalizables**
   - Permitir a usuarios crear reglas custom
   - UI para configurar umbrales

3. **Dashboard de Métricas**
   - Gráficos de alertas por tipo/severidad
   - Tendencias temporales
   - MTTR (Mean Time To Resolution)

4. **Integración con Monitoring**
   - Prometheus metrics export
   - Grafana dashboards
   - PagerDuty/Slack integration

5. **Machine Learning**
   - Predicción de alertas
   - Detección de anomalías
   - Auto-tuning de umbrales

---

## 📝 Changelog

### v1.0.0 (2024-01-15)

**Backend:**
- ✅ Alert engine con 8 tipos de detección
- ✅ Base de datos con migration 009_alert_events
- ✅ WebSocket manager para real-time broadcasting
- ✅ REST API con 5 endpoints
- ✅ Background task (análisis cada 60s)
- ✅ Deduplicación (ventana de 5 minutos)
- ✅ 13 tests comprehensivos

**Frontend:**
- ✅ React hooks (useAlerts, useAlertsWebSocket, etc.)
- ✅ Alert center page con tabs y filtros
- ✅ AlertCard y AlertsList components
- ✅ Toast notifications (sonner, 8s auto-close)
- ✅ Navbar badge con unread count
- ✅ Color coding por severidad (azul/amarillo/rojo)

**Documentación:**
- ✅ Arquitectura completa
- ✅ API reference con ejemplos
- ✅ Guía de uso
- ✅ Testing guide
- ✅ Troubleshooting

---

## 👥 Autores

- **Backend**: Alert Engine + WebSocket + Tests
- **Frontend**: React Hooks + Components + UI
- **Documentation**: Architecture + API Reference

---

## 📄 License

MIT License - Ver LICENSE file para detalles

---

## 🙏 Acknowledgments

- FastAPI para backend framework
- Next.js para frontend framework
- shadcn/ui para componentes UI
- sonner para toast notifications
- React Query para data fetching
- SQLAlchemy para ORM

---

**End of Documentation** 🎉
