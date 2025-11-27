# Meta Real-Time Performance Engine (PASO 10.14)

## Objetivo
Motor de detección y respuesta en tiempo real (5-15 min) para cambios críticos de rendimiento en campañas Meta Ads.

## Componentes

### 1. RT-Collector (Detector)
- Consulta incremental cada 5-15 minutos
- Detección de anomalías: drift, spike, sudden-death
- Modo STUB operativo

### 2. Decision Engine
**Reglas:**
- CTR drop ≥25% → reducir budget 20-30%
- CVR drop ≥20% → inspección inmediata
- CPM spike ≥40% → reducir puja
- ROAS drop ≥30% → pausa temporal

**Algoritmos:**
- Short-window drift detection
- Spike detection (z-score)
- Sudden-death protection

### 3. Actions Layer
- `pause_ad`: Pausa inmediata
- `reduce_budget`: Reduce 10-30%
- `increase_budget`: Sube hasta máximo
- `trigger_creative_resync`: Resync con 10.13
- `trigger_full_cycle`: Dispara 10.11
- `trigger_targeting_refresh`: Refresca 10.12

## API Endpoints

- `GET /meta/rt/health` - Health check
- `GET /meta/rt/latest` - Últimas detecciones
- `POST /meta/rt/run` - Ejecutar manualmente
- `POST /meta/rt/actions/apply` - Aplicar acciones
- `GET /meta/rt/logs` - Logs de actividad

## Configuración

```bash
RT_ENGINE_ENABLED=true
RT_ENGINE_INTERVAL_MINUTES=5
RT_ENGINE_MODE=stub
RT_ENGINE_AUTO_APPLY=false
```

## Integración

- **PASO 10.5 (ROAS)**: Consulta métricas ROAS
- **PASO 10.9 (Spikes)**: Complementa spike detection
- **PASO 10.11 (Full Cycle)**: Trigger automático en crisis
- **PASO 10.12 (Targeting)**: Refresh en saturación
- **PASO 10.13 (Creative)**: Resync en fatiga

## Tests
7 tests comprehensivos cubriendo detector, decision engine y actions.

**Versión:** 1.0.0
**Fecha:** 2025-11-27
