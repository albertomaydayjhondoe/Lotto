# 🔐 POLÍTICA DE AISLAMIENTO DE IDENTIDAD, IPs Y VPNs PARA STAKAZO

**DOCUMENTO CRÍTICO DE SEGURIDAD OPERACIONAL**

Este documento define cómo el sistema debe gestionar VPNs, proxies, dispositivos virtuales y aislamiento de comportamiento para evitar:

- ❌ Shadowban
- ❌ Detención de patrones robotizados
- ❌ Enlazado entre cuentas
- ❌ Riesgo de baneos masivos
- ❌ Relación entre mis cuentas oficiales y las satélite
- ❌ Relación entre actividad humana y automática

---

## 🔥 1. PRINCIPIO MAESTRO

> **"Ningún módulo que interactúe con redes sociales o APIs no oficiales puede usar la misma IP, fingerprint o dispositivo que otro módulo."**

Esto aplica a:
- ✅ Cuentas satélite
- ✅ Ingeniería de intercambios (TelegramBot Exchange Engine)
- ✅ Vision Engine (si hace scrapes permitidos)
- ✅ Cualquier crawler o capturador de métricas no oficial
- ✅ Mis cuentas oficiales (Stakazo cuentas reales)

---

## 🟣 2. CUENTAS SATÉLITE — REGLAS ESTRICTAS

### 🔐 2.1. Aislamiento obligatorio por cuenta

**Cada cuenta satélite debe tener:**

1. ✅ **1 VPN o Proxy residencial único**
2. ✅ **1 perfil GoLogin o ADB con fingerprint exclusivo**
3. ✅ **1 historial aislado**
4. ✅ **1 dispositivo virtual simulado**

### 📌 2.2. PROHIBIDO:

- ❌ Usar la IP del servidor
- ❌ Compartir IP entre cuentas
- ❌ Reutilizar el mismo fingerprint
- ❌ Hacer peticiones desde el backend sin proxy

### 📌 2.3. Qué debe implementar el sistema

El módulo `account_manager.py` debe controlar:

```python
account.ip_proxy = assign_unique_proxy()
account.device_fingerprint = assign_unique_fingerprint()
account.profile = gologin.create_profile(proxy=account.ip_proxy)
```

### 📡 2.4. Publicaciones → deben seguir este flujo:

```
SatelliteEngine → AccountManager → GoLoginProfile → Proxy → Plataforma
```

**NUNCA:**
```
SatelliteEngine → Backend IP → Plataforma  ❌
```

---

## 🔵 3. TELEGRAMBOT (INTERCAMBIOS) — REGLAS ESPECIALES

**CRÍTICO:** Este bot NO es un bot normal de control interno.

Este bot forma parte del **ecosistema de intercambios humanos**, por tanto:

### 🔐 3.1. NUNCA puede usar:

- ❌ La IP del backend
- ❌ La IP de las cuentas satélite
- ❌ Ningún fingerprint del sistema central
- ❌ La IP del Orchestrator
- ❌ La IP de mis cuentas principales (Stakazo)

### ⚙️ 3.2. El TelegramBot necesita SU PROPIA VPN

**Debe tener:**

1. ✅ **1 VPN exclusiva** (diferente de todo)
2. ✅ **1 entorno aislado** (Docker / micro-VM)
3. ✅ **1 fingerprint neutro** (no Android spoof ni iOS spoof, sino **generic PC**)

**Para que:**
- Parezca un humano real usando Telegram
- No se relacione con la actividad automática de cuentas satélite
- No se relacione con mi actividad personal

### 📡 3.3. Interacciones del TelegramBot

El motor de intercambios (Exchange Engine) deberá usar:

```python
telegram_bot_proxy = proxy_pool.get("telegram_bot")
bot_env = isolated_device(profile="GENERIC_PC", proxy=telegram_bot_proxy)
```

### 🧠 3.4. Por qué es necesario

**Si el Bot usa la misma IP que las cuentas satélite:**

- ❌ Instagram/TikTok podrían detectar vínculos
- ❌ Las interacciones humanas parecerían automatizadas
- ❌ Riesgo de bloquear cuentas satélite
- ❌ Relación entre mi cuenta oficial y el bot
- ❌ Shadowban por interacción artificial
- ❌ Bloqueo masivo en cadena

---

## 🟠 4. APIS NO OFICIALES (scrapers, collectors, listeners)

El sistema debe asignar **otro grupo separado** de VPNs/proxies exclusivamente para:

- Scraping de métricas externas
- Obtención de tendencias (si no vía API oficial)
- Monitoreo de hashtags
- Cualquier request no oficial hacia TikTok/IG/YouTube

### 🔐 4.1. No pueden usar:

- ❌ IP del backend
- ❌ IP del TelegramBot
- ❌ IP de las cuentas satélite
- ❌ IP de mis cuentas oficiales

### ⚙️ 4.2. Cómo debe gestionarlo el ProxyRouter:

```python
if module == "satellite_account":
    use_proxy(account.proxy)
elif module == "telegram_exchange":
    use_proxy(telegram_proxy)
elif module == "scraper":
    use_proxy(scraper_proxy_pool.rotate())
elif module == "official_api":
    use_backend_ip()   # permitido solo en APIs oficiales
```

---

## 🧱 5. INTEGRACIÓN CON GOLOGIN / ADB

### 🟢 5.1. Para cuentas satélite:

**Obligatorio.**

- GoLogin o ADB crea un "device environment"
- Proxy asignado por cuenta
- Fingerprint único
- Navegador aislado
- Cookies individuales
- Preferencias individuales

### 🔵 5.2. Para TelegramBot:

**Opcional pero recomendado.**

Si se usa GoLogin:
- Perfil **GENERIC_PC**
- Proxy único
- Fingerprint neutral
- User-agent estable

---

## 🚫 6. PREVENCIÓN DE CORRELACIÓN ENTRE HUMANO Y ROBOTS

El sistema DEBE aplicar:

### ❌ 6.1. Nunca mezclar IPs

| Componente | Puede usar backend IP | Debe usar proxy | Debe usar VPN exclusiva |
|------------|----------------------|-----------------|------------------------|
| Orchestrator | ✔️ | ❌ | ❌ |
| Ads Engine | ✔️ (Meta Ads API) | ❌ | ❌ |
| Mi cuenta oficial | ❌ | ❌ | ✔️ (si se gestiona desde sistema) |
| Cuentas satélite | ❌ | ✔️ | ✔️ |
| TelegramBot exchange | ❌ | ✔️ | ✔️ |
| Scrapers | ❌ | ✔️ | según pool |

### ❌ 6.2. Nunca mezclar fingerprints

**Cada perfil es un dispositivo distinto.**

### ❌ 6.3. Nunca mezclar patrones de interacción

- El bot no puede comportarse como los satélites
- Los satélites no pueden comportarse como el bot

---

## 🧠 7. INSTRUCCIONES FINALES PARA EL SISTEMA

### A PARTIR DE AHORA:

#### 1. Cada cuenta satélite DEBE utilizar:
   - ✅ Un proxy único
   - ✅ Un fingerprint único
   - ✅ Un perfil GoLogin o ADB aislado
   - ❌ Nunca debe usar la IP del servidor

#### 2. El TelegramBot (Exchange Bot) DEBE utilizar:
   - ✅ Una VPN exclusiva
   - ✅ Un fingerprint neutral
   - ✅ Un entorno aislado (VM/Docker)
   - ❌ Nunca debe compartir IP con satélites o backend

#### 3. Las APIs no oficiales DEBEN:
   - ✅ Usar un pool separado de proxies dedicados
   - ✅ Rotar IPs
   - ❌ No compartir IP con satélites ni bot

#### 4. El Orchestrator:
   - ✅ Debe enrutar cada módulo al proxy correspondiente
   - ❌ Nunca mezclar IPs entre componentes
   - ✅ Debe garantizar aislamiento total de identidad, tráfico y fingerprints

#### 5. Objetivo:
   - ✅ Evitar shadowban
   - ✅ Evitar correlaciones automáticas entre entidades
   - ✅ Maximizar seguridad operacional
   - ✅ Mantener comportamiento humano consistente y no relacionable

---

## 📊 MATRIZ DE AISLAMIENTO

```
┌─────────────────────┬──────────────┬────────────────┬──────────────────┐
│ Componente          │ IP Source    │ Fingerprint    │ Isolation Level  │
├─────────────────────┼──────────────┼────────────────┼──────────────────┤
│ Official Account    │ Personal VPN │ Unique         │ MAXIMUM          │
│ Satellite #1        │ Proxy #1     │ Unique #1      │ MAXIMUM          │
│ Satellite #2        │ Proxy #2     │ Unique #2      │ MAXIMUM          │
│ Satellite #N        │ Proxy #N     │ Unique #N      │ MAXIMUM          │
│ TelegramBot         │ VPN Exclusive│ Generic PC     │ MAXIMUM          │
│ Scraper Pool        │ Rotating     │ Generic Mobile │ HIGH             │
│ Orchestrator        │ Backend IP   │ N/A            │ NONE (internal)  │
│ Meta Ads API        │ Backend IP   │ N/A            │ NONE (official)  │
└─────────────────────┴──────────────┴────────────────┴──────────────────┘
```

---

## ⚠️ CONSECUENCIAS DE NO SEGUIR ESTA POLÍTICA

1. **Shadowban masivo** de todas las cuentas satélite
2. **Detección de automatización** por patrones de IP
3. **Bloqueo en cadena** de cuentas relacionadas
4. **Pérdida de inversión** en proxies/cuentas
5. **Compromiso de la cuenta oficial** (Stakazo)
6. **Detención del Exchange Engine** por comportamiento sospechoso

---

## 📌 VERSIÓN Y VIGENCIA

- **Versión:** 1.0
- **Fecha:** Diciembre 2025
- **Estado:** OBLIGATORIO - CRÍTICO
- **Implementación:** INMEDIATA
- **Revisión:** Cada 30 días o tras incidente

---

**🚨 ESTE DOCUMENTO ES PRIORITARIO Y DEBE SER IMPLEMENTADO ANTES DE CUALQUIER PUBLICACIÓN SATÉLITE O ACTIVACIÓN DEL EXCHANGE ENGINE 🚨**
