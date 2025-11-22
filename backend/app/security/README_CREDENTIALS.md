# Secure Credentials System

**PASO 5.1: Sistema de Credenciales Seguras para Social Accounts**

Este módulo proporciona almacenamiento seguro de credenciales de plataformas sociales (Instagram, TikTok, YouTube, etc.) utilizando cifrado simétrico Fernet.

## 📋 Tabla de Contenidos

- [Arquitectura](#arquitectura)
- [Configuración](#configuración)
- [Uso](#uso)
- [Seguridad](#seguridad)
- [Migración de Base de Datos](#migración-de-base-de-datos)
- [Testing](#testing)

---

## 🏗️ Arquitectura

### Componentes

1. **`app/security/credentials.py`** - Funciones de bajo nivel para cifrado/descifrado
2. **`app/services/social_accounts.py`** - Capa de servicio de alto nivel para manejo de credenciales
3. **`app/models/database.py`** - Modelo `SocialAccountModel` extendido con campos de cifrado
4. **`alembic/versions/007_credentials_encryption.py`** - Migración para añadir columnas

### Flujo de Datos

```
┌─────────────────┐
│   Raw Dict      │  {"access_token": "abc", "refresh_token": "xyz"}
│  (Plaintext)    │
└────────┬────────┘
         │
         │ encrypt_credentials()
         ▼
┌─────────────────┐
│ Encrypted Bytes │  b'gAAAAABh...' (Fernet token)
└────────┬────────┘
         │
         │ Store in DB
         ▼
┌─────────────────────────────────────────┐
│ social_accounts.encrypted_credentials   │
│ social_accounts.credentials_version     │  "fernet-v1"
│ social_accounts.credentials_updated_at  │  2025-11-22 10:30:00
└────────┬────────────────────────────────┘
         │
         │ Retrieve from DB
         ▼
┌─────────────────┐
│ Encrypted Bytes │  b'gAAAAABh...'
└────────┬────────┘
         │
         │ decrypt_credentials()
         ▼
┌─────────────────┐
│   Raw Dict      │  {"access_token": "abc", "refresh_token": "xyz"}
│  (Plaintext)    │
└─────────────────┘
```

---

## ⚙️ Configuración

### 1. Generar Clave de Cifrado

La clave de cifrado debe ser una clave Fernet válida de 32 bytes (codificada en base64).

**Generar nueva clave:**

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

**Salida ejemplo:**
```
k8YzJ3vR9mP4xW2bN6cQ1fH5gT7dL0aE8sV3nM9oU4i=
```

### 2. Configurar Variable de Entorno

**Archivo `.env`:**

```env
CREDENTIALS_ENCRYPTION_KEY=k8YzJ3vR9mP4xW2bN6cQ1fH5gT7dL0aE8sV3nM9oU4i=
```

**O exportar directamente:**

```bash
export CREDENTIALS_ENCRYPTION_KEY="k8YzJ3vR9mP4xW2bN6cQ1fH5gT7dL0aE8sV3nM9oU4i="
```

### 3. Verificar Configuración

```python
from app.core.config import settings

print(settings.CREDENTIALS_ENCRYPTION_KEY)  # Should not be None
```

⚠️ **IMPORTANTE:** Si `CREDENTIALS_ENCRYPTION_KEY` no está configurada, las funciones de cifrado lanzarán `ValueError` con mensaje claro.

---

## 🚀 Uso

### API de Alto Nivel (Recomendado)

#### Almacenar Credenciales

```python
from app.services.social_accounts import set_account_credentials
from uuid import UUID

# Credenciales de plataforma
instagram_creds = {
    "access_token": "IGQVJXa1b2c3d4...",
    "refresh_token": "IGQVJYx9y8z7...",
    "expires_at": 1735689600,
    "scope": ["user_profile", "user_media"],
    "user_id": "17841405309213234"
}

# Almacenar cifradas
account = await set_account_credentials(
    db=db,
    account_id=UUID("123e4567-e89b-12d3-a456-426614174000"),
    creds=instagram_creds
)

print(account.credentials_version)      # "fernet-v1"
print(account.credentials_updated_at)   # datetime object
print(type(account.encrypted_credentials))  # <class 'bytes'>
```

#### Recuperar Credenciales

```python
from app.services.social_accounts import get_account_credentials

# Obtener credenciales descifradas
creds = await get_account_credentials(
    db=db,
    account_id=account.id
)

if creds:
    print(creds["access_token"])  # "IGQVJXa1b2c3d4..."
    # Usar credenciales para llamar a API de Instagram
else:
    print("No credentials stored for this account")
```

### API de Bajo Nivel (Avanzado)

#### Cifrado Directo

```python
from app.security.credentials import encrypt_credentials, decrypt_credentials

# Cifrar
raw_creds = {"access_token": "secret123", "refresh_token": "refresh456"}
encrypted_token = encrypt_credentials(raw_creds)  # bytes

# Descifrar
decrypted_creds = decrypt_credentials(encrypted_token)  # dict
assert decrypted_creds == raw_creds
```

---

## 🔒 Seguridad

### Características de Seguridad

1. **Cifrado Simétrico Fernet (AES-128-CBC + HMAC)**
   - Autenticación de mensajes (detección de manipulación)
   - Timestamp incluido (prevención de replay attacks)
   - Padding automático

2. **Versionado de Formato**
   - Campo `credentials_version` permite rotación futura
   - Actualmente: `"fernet-v1"`
   - Permite migrar a algoritmos más fuertes sin romper datos existentes

3. **Timestamp de Actualización**
   - Campo `credentials_updated_at` para auditoría
   - Permite detectar credenciales antiguas que necesitan renovación

4. **Manejo Seguro de Errores**
   - Las funciones de bajo nivel (`encrypt_credentials`, `decrypt_credentials`) lanzan excepciones explícitas
   - La capa de servicio (`get_account_credentials`) maneja errores gracefully y retorna `None`
   - Los errores de descifrado se loggean pero no rompen la aplicación

### Buenas Prácticas

✅ **DO:**
- Generar claves con `Fernet.generate_key()`
- Almacenar clave en variable de entorno (nunca en código)
- Rotar claves periódicamente (implementar en versión futura)
- Usar capa de servicio de alto nivel para operaciones DB

❌ **DON'T:**
- Hardcodear claves en código fuente
- Compartir claves en repositorios Git
- Reutilizar claves entre entornos (dev/staging/prod)
- Ignorar errores de descifrado sin logging

### Rotación de Claves (Futuro)

Para rotación de claves en el futuro:

1. Añadir nueva clave en `CREDENTIALS_ENCRYPTION_KEY_V2`
2. Descifrar con clave antigua (basándose en `credentials_version`)
3. Re-cifrar con clave nueva
4. Actualizar `credentials_version` a `"fernet-v2"`
5. Una vez migradas todas las credenciales, remover clave antigua

---

## 🗄️ Migración de Base de Datos

### Aplicar Migración

```bash
cd backend
alembic upgrade head
```

### Campos Añadidos a `social_accounts`

| Campo                     | Tipo         | Nullable | Descripción                                    |
|---------------------------|--------------|----------|------------------------------------------------|
| `encrypted_credentials`   | LargeBinary  | Yes      | Credenciales cifradas con Fernet              |
| `credentials_version`     | String(50)   | Yes      | Versión del algoritmo (ej: "fernet-v1")       |
| `credentials_updated_at`  | DateTime     | Yes      | Timestamp de última actualización             |

### Rollback (si es necesario)

```bash
alembic downgrade -1
```

⚠️ **ADVERTENCIA:** El rollback **eliminará permanentemente** todas las credenciales cifradas.

---

## 🧪 Testing

### Ejecutar Tests de Credenciales

```bash
# Solo tests de credenciales
pytest backend/tests/test_credentials_security.py -v

# Con cobertura
pytest backend/tests/test_credentials_security.py --cov=app.security --cov=app.services.social_accounts
```

### Tests Incluidos

1. ✅ **test_encrypt_decrypt_roundtrip_ok** - Roundtrip básico
2. ✅ **test_decrypt_invalid_token_raises** - Manejo de tokens inválidos
3. ✅ **test_set_and_get_account_credentials_roundtrip** - Integración DB completa
4. ✅ **test_get_account_credentials_returns_none_if_empty** - Cuentas sin credenciales
5. ✅ **test_encrypt_raises_if_no_key_configured** - Validación de configuración
6. ✅ **test_decrypt_with_wrong_key_returns_none** - Manejo de claves incorrectas
7. ✅ **test_set_credentials_account_not_found_raises** - Validación de cuenta
8. ✅ **test_update_existing_credentials** - Actualización de credenciales
9. ✅ **test_empty_credentials_dict** - Edge case: dict vacío
10. ✅ **test_unicode_characters_in_credentials** - Soporte Unicode/emojis

### Configuración de Test

Los tests configuran automáticamente una clave de cifrado temporal:

```python
@pytest_asyncio.fixture
def test_encryption_key():
    """Generate a valid Fernet key for testing."""
    return Fernet.generate_key().decode('utf-8')

@pytest_asyncio.fixture
def configure_test_key(test_encryption_key, monkeypatch):
    """Configure test encryption key in settings."""
    monkeypatch.setattr(settings, 'CREDENTIALS_ENCRYPTION_KEY', test_encryption_key)
    return test_encryption_key
```

---

## 📊 Ejemplo Completo: Integración con Instagram

```python
from app.models.database import SocialAccountModel
from app.services.social_accounts import set_account_credentials, get_account_credentials
from uuid import uuid4
from datetime import datetime

async def setup_instagram_account(db):
    """Create Instagram account and store credentials."""
    
    # 1. Crear cuenta de Instagram
    account = SocialAccountModel(
        id=uuid4(),
        platform="instagram",
        handle="@stakazo.oficial",
        external_id="17841405309213234",
        is_main_account=1,
        is_active=1,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(account)
    await db.commit()
    await db.refresh(account)
    
    # 2. Almacenar credenciales cifradas
    instagram_creds = {
        "access_token": "IGQVJXa1b2c3d4e5f6g7h8i9j0...",
        "refresh_token": "IGQVJYx9y8z7w6v5u4t3s2r1...",
        "token_type": "bearer",
        "expires_at": 1735689600,  # Unix timestamp
        "scope": ["user_profile", "user_media"],
        "user_id": "17841405309213234"
    }
    
    await set_account_credentials(
        db=db,
        account_id=account.id,
        creds=instagram_creds
    )
    
    print(f"✅ Instagram account created: {account.handle}")
    print(f"✅ Credentials encrypted and stored")
    
    return account


async def publish_to_instagram(db, account_id, clip):
    """Publish clip to Instagram using stored credentials."""
    
    # 1. Obtener credenciales
    creds = await get_account_credentials(db=db, account_id=account_id)
    
    if not creds:
        raise ValueError("No credentials found for account")
    
    # 2. Usar credenciales para llamar a API de Instagram
    access_token = creds["access_token"]
    user_id = creds["user_id"]
    
    # 3. Publicar (implementación futura)
    # instagram_api.create_media_container(user_id, clip.file_path, access_token)
    # instagram_api.publish_media(container_id, access_token)
    
    print(f"📸 Publishing to Instagram with token: {access_token[:10]}...")
```

---

## 🔗 Referencias

- **Cryptography Library:** https://cryptography.io/
- **Fernet Spec:** https://github.com/fernet/spec/
- **SQLAlchemy LargeBinary:** https://docs.sqlalchemy.org/en/20/core/type_basics.html#sqlalchemy.types.LargeBinary

---

## 📝 Notas Adicionales

### Compatibilidad de Base de Datos

- ✅ **SQLite:** Usa tipo `BLOB` para `LargeBinary`
- ✅ **PostgreSQL:** Usa tipo `BYTEA` para `LargeBinary`
- ✅ Migración compatible con ambos

### Límites de Tamaño

- **Fernet:** Sin límite práctico (soporta GB de datos)
- **LargeBinary:** Depende de DB (SQLite: 1GB, PostgreSQL: 1GB default)
- **Credenciales típicas:** < 1 KB (muy por debajo del límite)

### Rendimiento

- **Cifrado:** ~1ms para credenciales típicas
- **Descifrado:** ~1ms para credenciales típicas
- **Impacto DB:** Mínimo (columna binaria estándar)

---

**Documentación generada para PASO 5.1 - Sistema de Credenciales Seguras**  
*Última actualización: 2025-11-22*
