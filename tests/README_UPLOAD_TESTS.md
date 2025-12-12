# Tests para el Endpoint /upload

## Archivos de Tests

### 1. `test_upload_integration.py` (Tests de Integración)
Tests que prueban el endpoint real con TestClient.

**4 Tests incluidos:**
- ✅ `test_upload_video_integration` - Upload exitoso completo
- ✅ `test_upload_video_no_file_error` - Error 400 sin archivo
- ✅ `test_upload_video_invalid_type_error` - Error 400 tipo inválido
- ✅ `test_upload_video_with_idempotency` - Verificación de idempotencia

### 2. `test_upload_unit.py` (Tests Unitarios)
Tests con mocks (skeletons para implementar).

## Requisitos

```bash
pip install pytest pytest-asyncio httpx
```

O desde el requirements del backend:
```bash
cd backend
pip install -e .
```

## Ejecutar Tests

### Ejecutar SOLO los tests de integración del endpoint /upload:
```bash
pytest tests/test_upload_integration.py -v
```

### Ejecutar un test específico:
```bash
pytest tests/test_upload_integration.py::test_upload_video_integration -v
```

### Ejecutar con output detallado (prints):
```bash
pytest tests/test_upload_integration.py -v -s
```

### Ejecutar todos los tests del proyecto:
```bash
pytest tests/ -v
```

### Ejecutar solo tests marcados como integration:
```bash
pytest -m integration -v
```

## Estructura del Test de Integración

```python
async def test_upload_video_integration():
    # 1. Crear archivo fake en memoria
    fake_video = BytesIO(b"FAKE VIDEO...")
    
    # 2. Preparar form data
    files = {"file": ("test.mp4", fake_video, "video/mp4")}
    data = {"title": "Test", "description": "Test desc"}
    
    # 3. Hacer request
    async with AsyncClient(app=app) as client:
        response = await client.post("/upload", files=files, data=data)
    
    # 4. Verificar respuesta 201
    assert response.status_code == 201
    
    # 5. Verificar JSON
    json = response.json()
    assert "video_asset_id" in json
    assert "job_id" in json
    assert "message" in json
    
    # 6. Verificar IDs no vacíos
    assert len(json["video_asset_id"]) == 36  # UUID
    assert len(json["job_id"]) == 36
    
    # 7. Verificar archivo creado
    storage_path = Path(f"storage/videos/{json['video_asset_id']}.mp4")
    assert storage_path.exists()
    
    # 8. Cleanup
    storage_path.unlink()
```

## Validaciones Implementadas

### Test 1: Upload Exitoso
- ✅ HTTP 201 Created
- ✅ JSON con `video_asset_id`, `job_id`, `message`
- ✅ IDs son UUIDs válidos (36 caracteres)
- ✅ Message contiene "queued" o "accepted"
- ✅ Archivo creado en `storage/videos/{uuid}.mp4`
- ✅ Tamaño de archivo coincide con bytes subidos
- ✅ Cleanup automático después del test

### Test 2: Error Sin Archivo
- ✅ HTTP 400 Bad Request
- ✅ JSON con campo `detail`
- ✅ Mensaje de error menciona "file"

### Test 3: Error Tipo Inválido
- ✅ HTTP 400 Bad Request
- ✅ JSON con campo `detail`
- ✅ Mensaje de error menciona "video" o "type"

### Test 4: Idempotencia
- ✅ Primer upload retorna 201 con IDs
- ✅ Segundo upload con mismo `idempotency_key` retorna mismos IDs
- ✅ Message indica "idempotency" o "exists"
- ✅ No se crea archivo duplicado

## Dependencias del Test

### NO requiere:
- ❌ Servicios externos
- ❌ E2B
- ❌ Docker corriendo (usa TestClient in-memory)

### SÍ requiere:
- ✅ Base de datos PostgreSQL (docker-compose)
- ✅ Configuración DATABASE_URL correcta
- ✅ Permisos de escritura en `storage/videos/`

## Troubleshooting

### Error: "No module named 'app'"
```bash
# Asegúrate de que backend/ esté en PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)/backend"
pytest tests/test_upload_integration.py -v
```

### Error: "Connection refused" (Database)
```bash
# Inicia los servicios con docker-compose
docker compose up -d postgres

# Verifica que postgres esté corriendo
docker compose ps
```

### Error: "Permission denied" en storage/videos/
```bash
# Crea el directorio con permisos
mkdir -p storage/videos
chmod 755 storage/videos
```

### Los tests pasan pero los archivos no se limpian
Los tests intentan hacer cleanup automático. Si fallan, limpia manualmente:
```bash
rm -f storage/videos/test-*
rm -f storage/videos/*.mp4
```

## Próximos Pasos

1. **Agregar tests de base de datos**: Verificar que VideoAsset y Job se crearon correctamente
2. **Tests de concurrencia**: Múltiples uploads simultáneos
3. **Tests de archivos grandes**: Verificar límite de 500MB
4. **Tests de performance**: Medir tiempo de upload
5. **Tests de seguridad**: Validar que solo se aceptan videos válidos

## Comando Rápido

```bash
# Desde la raíz del proyecto:
pytest tests/test_upload_integration.py -v -s
```

Esto ejecutará los 4 tests de integración con output detallado.
