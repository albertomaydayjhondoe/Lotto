# Publishing Integrations Module

## 📋 Descripción

Módulo de integración con APIs reales de plataformas sociales (Instagram, TikTok, YouTube) para publicación de videos.

**Estado actual:** STUB implementations - Estructuras completas sin credenciales reales.

## 🏗️ Arquitectura

### Componentes

```
publishing_integrations/
├── base_client.py          # Interfaz base abstracta
├── instagram_client.py     # Instagram Graph API client
├── tiktok_client.py        # TikTok Share API client
├── youtube_client.py       # YouTube Data API v3 client
├── exceptions.py           # Excepciones personalizadas
├── router.py               # Endpoints FastAPI
├── __init__.py             # Exports y factory function
└── README.md               # Esta documentación
```

### Diferencia con Step 2 (Simuladores)

| Aspecto | Step 2 (Simulators) | Step 3 (Integrations) |
|---------|---------------------|----------------------|
| **Propósito** | Testing interno | Producción real |
| **Estructura** | Funciones simples | Clases con OOP |
| **Validación** | Básica | Completa por plataforma |
| **Credenciales** | No necesarias | Preparado para credentials |
| **Red** | Sin llamadas | Hooks para APIs reales |
| **Delays** | Random sleep | Network I/O real |

## 🔌 Clientes Implementados

### 1. Instagram Graph API

**Clase:** `InstagramPublishingClient`

**API:** Instagram Graph API v18.0

**Documentación:** https://developers.facebook.com/docs/instagram-api/

**Flujo de publicación:**
1. Autenticación con OAuth 2.0 (access token + Instagram Business Account ID)
2. Subir video a URL pública (S3, CDN, etc.)
3. Crear media container con `POST /media`
4. Publicar container con `POST /media_publish`

**Límites:**
- Caption: 2,200 caracteres
- Hashtags: 30 máximo
- Duración: 60 minutos máximo
- Tamaño: 100 MB máximo

**Métodos:**
```python
await client.authenticate()
await client.upload_video(file_path, caption="...", cover_url="...")
await client.publish_post(video_id, caption="...", location_id="...")
client.validate_post_params(caption="...")
```

**TODOs para integración real:**
```python
# TODO: insert real upload endpoint
# POST https://graph.facebook.com/v18.0/{ig_user_id}/media

# TODO: exchange short-lived token for long-lived (60 days)
# POST https://graph.facebook.com/v18.0/oauth/access_token

# TODO: add webhook validation for publish completion
# Webhook verification: X-Hub-Signature-256
```

---

### 2. TikTok Share API

**Clase:** `TikTokPublishingClient`

**API:** TikTok Content Posting API v2

**Documentación:** https://developers.tiktok.com/doc/content-posting-api-get-started

**Flujo de publicación:**
1. OAuth 2.0 con scopes: `video.upload`, `video.publish`
2. Inicializar upload: `POST /v2/post/publish/video/init/`
3. Subir video en chunks: `POST /v2/post/publish/video/upload/`
4. Polling status: `GET /v2/post/publish/status/{publish_id}/`

**Límites:**
- Caption: 150 caracteres
- Duración: 3 segundos - 10 minutos
- Tamaño: ~287 MB

**Métodos:**
```python
await client.authenticate()
await client.upload_video(file_path, title="...", privacy_level="PUBLIC_TO_EVERYONE")
await client.publish_post(video_id, title="...", disable_comment=False)
client.validate_post_params(title="...", privacy_level="...")
```

**TODOs para integración real:**
```python
# TODO: implement OAuth 2.0 flow
# Authorization URL: https://www.tiktok.com/v2/auth/authorize/

# TODO: resumable upload for large files
# Chunked upload with byte ranges

# TODO: webhook for publish completion
# Callback URL configuration
```

---

### 3. YouTube Data API

**Clase:** `YouTubePublishingClient`

**API:** YouTube Data API v3

**Documentación:** https://developers.google.com/youtube/v3/

**Flujo de publicación:**
1. OAuth 2.0 con scopes: `youtube.upload`, `youtube`
2. Resumable upload: `POST /upload/youtube/v3/videos?uploadType=resumable`
3. Upload chunks con PUT
4. Video processing (automático)
5. Actualizar metadata: `PUT /youtube/v3/videos`

**Límites:**
- Título: 100 caracteres
- Descripción: 5,000 caracteres
- Tags: 500 máximo, 30 chars cada uno
- Duración: 12 horas máximo
- Tamaño: 256 GB máximo

**Métodos:**
```python
await client.authenticate()
await client.upload_video(
    file_path, 
    title="...", 
    description="...", 
    tags=["tag1", "tag2"],
    category_id="22",
    privacy_status="public"
)
await client.publish_post(video_id)  # Update metadata
client.validate_post_params(title="...", description="...", tags=[...])
```

**TODOs para integración real:**
```python
# TODO: resumable upload implementation
# GET upload_url from Location header

# TODO: OAuth2 credentials
# Client ID + Client Secret from Google Cloud Console

# TODO: playlists support
# Add video to playlist after upload
```

---

## 🔐 Integración de API Keys

### Cómo agregar credenciales reales

Actualmente, los clientes funcionan SIN credenciales (modo STUB). Para activar APIs reales:

#### 1. Instagram

**Credenciales necesarias:**
- `access_token`: Long-lived access token (60 días)
- `instagram_account_id`: Instagram Business Account ID
- `facebook_page_id`: Facebook Page ID conectada

**Dónde obtenerlas:**
1. Crear app en Facebook Developers: https://developers.facebook.com/apps
2. Agregar Instagram Graph API
3. Conectar Instagram Business Account
4. Obtener access token con Graph API Explorer
5. Intercambiar por long-lived token

**Config:**
```python
config = {
    "access_token": "IGQVJ...",
    "instagram_account_id": "17841405793187218",
    "facebook_page_id": "123456789"
}
client = InstagramPublishingClient(config=config)
```

**Pasos para activar:**
1. En `instagram_client.py`, descomentar TODOs
2. Reemplazar URLs simuladas con endpoints reales
3. Agregar lógica de refresh token
4. Configurar webhooks para confirmaciones

---

#### 2. TikTok

**Credenciales necesarias:**
- `client_key`: TikTok App Client Key
- `client_secret`: TikTok App Client Secret
- `access_token`: User access token (OAuth 2.0)
- `refresh_token`: Refresh token

**Dónde obtenerlas:**
1. Crear app en TikTok Developers: https://developers.tiktok.com/
2. Solicitar acceso a Content Posting API
3. Configurar OAuth redirect URL
4. Implementar OAuth flow
5. Obtener access token

**Config:**
```python
config = {
    "client_key": "aw8h5j...",
    "client_secret": "aB3cD...",
    "access_token": "act.example...",
    "refresh_token": "rft.example..."
}
client = TikTokPublishingClient(config=config)
```

**Pasos para activar:**
1. En `tiktok_client.py`, implementar OAuth flow
2. Agregar resumable upload
3. Configurar webhook URL
4. Implementar token refresh logic

---

#### 3. YouTube

**Credenciales necesarias:**
- `client_id`: OAuth 2.0 Client ID
- `client_secret`: OAuth 2.0 Client Secret
- `access_token`: User access token
- `refresh_token`: Refresh token
- `api_key`: API Key (opcional, para operaciones read-only)

**Dónde obtenerlas:**
1. Google Cloud Console: https://console.cloud.google.com/
2. Crear proyecto nuevo
3. Habilitar YouTube Data API v3
4. Crear credenciales OAuth 2.0
5. Configurar pantalla de consentimiento
6. Implementar OAuth flow

**Config:**
```python
config = {
    "client_id": "123456789-abcdef.apps.googleusercontent.com",
    "client_secret": "GOCSPX-...",
    "access_token": "ya29.a0AfH6...",
    "refresh_token": "1//0gZ...",
    "api_key": "AIzaSyB..."  # Optional
}
client = YouTubePublishingClient(config=config)
```

**Pasos para activar:**
1. En `youtube_client.py`, implementar OAuth flow
2. Agregar resumable upload (chunked)
3. Implementar token refresh (cada ~1 hora)
4. Agregar support para playlists

---

## 🧪 Testing

Los clientes están diseñados para testing sin credenciales:

```python
# Modo STUB (sin credenciales)
client = InstagramPublishingClient()
await client.authenticate()  # Simula auth exitosa
result = await client.upload_video("/path/video.mp4")  # Simula upload
```

Para tests con APIs reales:

```python
# Modo REAL (con credenciales)
client = InstagramPublishingClient(config={
    "access_token": os.environ["IG_ACCESS_TOKEN"],
    "instagram_account_id": os.environ["IG_ACCOUNT_ID"]
})
await client.authenticate()  # Llama API real
```

---

## 📡 API Endpoints

### GET /publishing/providers

Lista todos los proveedores disponibles.

**Response:**
```json
["instagram", "tiktok", "youtube"]
```

---

### GET /publishing/providers/{platform}

Obtiene detalles de un proveedor específico.

**Example:** `GET /publishing/providers/instagram`

**Response:**
```json
{
  "platform": "instagram",
  "authenticated": false,
  "features": ["video_upload", "reels", "stories", "carousel"],
  "limits": {
    "max_caption_length": 2200,
    "max_hashtags": 30,
    "max_video_duration_seconds": 3600,
    "max_video_size_mb": 100
  },
  "api_version": "v18.0",
  "documentation": "https://developers.facebook.com/docs/instagram-api/"
}
```

---

### POST /publishing/validate

Valida parámetros de publicación SIN hacer llamadas reales.

**Request:**
```json
{
  "platform": "instagram",
  "params": {
    "caption": "Mi post con #hashtag1 #hashtag2 ... #hashtag31"
  }
}
```

**Response (error):**
```json
{
  "platform": "instagram",
  "valid": false,
  "errors": [
    "Too many hashtags (31). Maximum is 30."
  ]
}
```

**Response (válido):**
```json
{
  "platform": "instagram",
  "valid": true,
  "errors": []
}
```

---

## 🔄 Flujo Completo de Publicación

### Con Simuladores (Step 2)

```
1. Request → publishing_engine/service.py
2. Validar clip + account
3. Crear PublishLog pending
4. Llamar PLATFORM_SIMULATORS["instagram"]
   └─ Simula upload con sleep(0.1-0.3)
   └─ 10% chance de failure
5. Actualizar PublishLog (success/failed)
6. Log eventos a ledger
7. Retornar PublishResult
```

### Con APIs Reales (Step 3 - Futuro)

```
1. Request → publishing_engine/service.py
2. Validar clip + account
3. get_provider_client("instagram", config={...})
4. await client.authenticate()
5. await client.upload_video(file_path, caption="...")
   └─ Llamada REAL a Instagram Graph API
   └─ Upload real con network I/O
6. await client.publish_post(video_id)
   └─ Publicación real
7. Actualizar PublishLog con post_id REAL
8. Log eventos a ledger
9. Retornar PublishResult con URL real
```

---

## 🚀 Próximos Pasos

### Para activar APIs reales:

1. **Obtener credenciales** para cada plataforma
2. **Implementar OAuth flows** en cada cliente
3. **Activar TODOs** en archivos client
4. **Configurar webhooks** para confirmaciones
5. **Agregar retry logic** con backoff exponencial
6. **Rate limiting** y queue management
7. **Media hosting** (S3, CDN) para Instagram
8. **Resumable uploads** para archivos grandes
9. **Token refresh** automático
10. **Error monitoring** y alertas

### Integración con Step 2:

En `publishing_engine/service.py`, cambiar de:
```python
# Step 2 - Simulators
simulator = PLATFORM_SIMULATORS[platform]
result = await simulator(request)
```

A:
```python
# Step 3 - Real APIs
from app.publishing_integrations import get_provider_client

client = get_provider_client(platform, config={
    "access_token": social_account.access_token,
    # ... más credentials
})
await client.authenticate()
upload_result = await client.upload_video(clip.file_path, caption=caption)
publish_result = await client.publish_post(upload_result["video_id"])
```

---

## ⚠️ Limitaciones Actuales

1. **Sin credenciales reales** - Todos los métodos simulan respuestas
2. **Sin llamadas de red** - No hay I/O real a APIs externas
3. **Sin OAuth flows** - Autenticación simulada
4. **Sin webhooks** - No hay confirmaciones de plataforma
5. **Sin retry logic** - Fallos no se reintentan
6. **Sin rate limiting** - No hay manejo de quotas
7. **Sin media hosting** - Asume archivos locales

---

## 📚 Referencias

- **Instagram Graph API:** https://developers.facebook.com/docs/instagram-api/
- **TikTok Developers:** https://developers.tiktok.com/
- **YouTube Data API:** https://developers.google.com/youtube/v3/
- **OAuth 2.0 Spec:** https://oauth.net/2/

---

## 🤝 Contribución

Para agregar una nueva plataforma:

1. Crear `{platform}_client.py` heredando de `BasePublishingClient`
2. Implementar métodos abstractos
3. Agregar validaciones específicas
4. Registrar en `AVAILABLE_PROVIDERS`
5. Agregar tests en `test_publishing_providers.py`
6. Documentar en este README

---

**Última actualización:** Noviembre 2025  
**Versión:** 3.0.0-stub  
**Estado:** Ready for API keys 🔐
