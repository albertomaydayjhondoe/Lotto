# Meta Ads Budget SPIKE Manager

**Detección automática de picos de rendimiento/gasto + Escalado inteligente de presupuestos**

---

## 📋 Tabla de Contenidos

1. [Introducción](#introducción)
2. [Arquitectura](#arquitectura)
3. [Componentes Principales](#componentes-principales)
4. [Fórmulas Matemáticas](#fórmulas-matemáticas)
5. [Umbrales y Configuración](#umbrales-y-configuración)
6. [API REST Endpoints](#api-rest-endpoints)
7. [Ejemplos de Uso](#ejemplos-de-uso)
8. [Reglas de Negocio](#reglas-de-negocio)
9. [Gestión de Riesgos](#gestión-de-riesgos)
10. [Integración en Producción](#integración-en-producción)

---

## 🎯 Introducción

El **Budget SPIKE Manager** es un sistema inteligente que:

1. **Detecta spikes** en tiempo real usando análisis estadístico avanzado
2. **Clasifica spikes** en tres categorías: Positive, Negative, Risk
3. **Escala presupuestos** automáticamente según reglas matemáticas
4. **Persiste logs** completos en base de datos
5. **Ejecuta scheduler** cada 30 minutos en background

### Casos de Uso

- 📈 **Positive Spike**: CTR/ROAS aumentan → Escalar presupuesto +10% a +50%
- 📉 **Negative Spike**: CTR/ROAS caen → Reducir presupuesto -10% a -40%
- ⚠️ **Risk Spike**: Gasto alto + métricas malas → Pausar inmediatamente

---

## 🏗️ Arquitectura

```
┌─────────────────────────────────────────────────────────────┐
│                    CLIENT (API Requests)                     │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                 FastAPI Router + RBAC                        │
│   POST /detect  │  POST /scale  │  GET /log  │  POST /auto  │