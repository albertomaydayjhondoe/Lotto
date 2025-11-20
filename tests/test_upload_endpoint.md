# Test del Endpoint POST /upload - Implementación REAL

## Resumen de Implementación

Se ha implementado la lógica REAL del endpoint `/upload` con todos los requisitos especificados.

### Cambios Realizados

#### 1. **backend/app/core/config.py**
```python
VIDEO_STORAGE_DIR: str = "storage/videos"  # Nueva configuración
```

#### 2. **backend/app/api/upload.py** (183 líneas)
Implementación completa con:

- ✅ **Aceptar multipart/form-data** con campos: file, title, description, release_date, idempotency_key
- ✅ **VIDEO_STORAGE_DIR configurado** en settings (default: "storage/videos")
- ✅ **Generación UUID + extensión original** del archivo
- ✅ **Guardado en chunks** (8MB) para eficiencia de memoria
- ✅ **Captura de file_size** durante la escritura
- ✅ **Inserción en video_assets** con todos los campos
- ✅ **Creación de Job** con job_type='cut_analysis', status='PENDING', params={"reason": "initial_cut_from_upload"}
- ✅ **Respuesta VideoUploadResponse** con video_asset_id, job_id, message
- ✅ **Manejo de errores** con HTTPException 400 y 500, rollback en caso de error
- ✅ **Código asíncrono** usando async/await, aiofiles
- ✅ **Reutilización de modelos existentes** VideoAsset, Job, JobStatus
- ✅ **Match exacto con OpenAPI spec** incluyendo todos los campos opcionales
- ✅ **Idempotencia** mediante idempotency_key para prevenir uploads duplicados
- ✅ **Validación de release_date** con formato ISO

## Flujo de Procesamiento

```
1. Validación de archivo (presencia + content_type video/*)
   ├─ Error 400 si falta file
   └─ Error 400 si no es video/*

2. Verificación de idempotencia (si se proporciona idempotency_key)
   └─ Retorna asset + job existente si ya fue procesado

3. Generación de UUID + extracción de extensión
   └─ Ejemplo: f1a2b3c4-5678-90ab-cdef-1234567890ab.mp4

4. Creación de directorio storage/videos/ (si no existe)

5. Validación de release_date (si se proporciona)
   └─ Error 400 si formato inválido

6. Guardado de archivo en chunks de 8MB
   ├─ Ruta DB: "storage/videos/{uuid}.mp4"
   ├─ Ruta filesystem: /workspaces/stakazo/storage/videos/{uuid}.mp4
   └─ Captura de file_size acumulativo

7. Creación de VideoAsset en DB
   ├─ id: UUID generado
   ├─ title, description, release_date (opcionales)
   ├─ file_path: ruta relativa
   ├─ file_size: bytes totales
   ├─ duration_ms: NULL (calculado después)
   └─ idempotency_key (opcional)

8. Creación de Job en DB
   ├─ job_type: "cut_analysis"
   ├─ status: JobStatus.PENDING
   ├─ video_asset_id: FK al VideoAsset
   ├─ clip_id: NULL
   └─ params: {"reason": "initial_cut_from_upload"}

9. Commit de transacción
   └─ En caso de error: rollback + cleanup de archivo

10. Respuesta 201 Created
    {
      "video_asset_id": "uuid",
      "job_id": "uuid",
      "message": "Upload accepted, analysis job queued"
    }
```

## Casos de Error Manejados

### 400 Bad Request
- No se proporciona archivo
- Archivo no es de tipo video/*
- release_date en formato inválido

### 500 Internal Server Error
- Error al escribir archivo en disco
- Error al insertar en base de datos
- Cualquier excepción durante el procesamiento
- **Incluye rollback automático** de transacción DB
- **Cleanup del archivo** si se creó parcialmente

## Pruebas a Ejecutar

### 1. Upload Básico
```bash
curl -X POST http://localhost:8000/upload \
  -F "file=@video.mp4" \
  -F "title=Mi Video de Prueba" \
  -F "description=Descripción del video" \
  -H "Authorization: Bearer fake-token-for-testing"
```

**Resultado esperado:**
- Status: 201
- JSON con video_asset_id, job_id, message
- Archivo guardado en `storage/videos/{uuid}.mp4`
- Registro en tabla `video_assets`
- Registro en tabla `jobs` con job_type='cut_analysis'

### 2. Upload con Todos los Campos
```bash
curl -X POST http://localhost:8000/upload \
  -F "file=@video.mp4" \
  -F "title=Video Completo" \
  -F "description=Con todos los campos" \
  -F "release_date=2024-01-15" \
  -F "idempotency_key=test-key-123" \
  -H "Authorization: Bearer fake-token-for-testing"
```

**Resultado esperado:**
- Status: 201
- VideoAsset con release_date y idempotency_key

### 3. Idempotencia (Segundo Upload con Mismo Key)
```bash
# Repetir comando anterior
curl -X POST http://localhost:8000/upload \
  -F "file=@video.mp4" \
  -F "title=Video Duplicado" \
  -F "description=No debería subir" \
  -F "release_date=2024-01-15" \
  -F "idempotency_key=test-key-123" \
  -H "Authorization: Bearer fake-token-for-testing"
```

**Resultado esperado:**
- Status: 201 (mismo que original)
- message: "Upload already exists (idempotency)"
- Mismo video_asset_id y job_id del primer upload
- NO se crea archivo duplicado

### 4. Error 400 - Sin Archivo
```bash
curl -X POST http://localhost:8000/upload \
  -F "title=Solo Titulo" \
  -H "Authorization: Bearer fake-token-for-testing"
```

**Resultado esperado:**
- Status: 400
- detail: "No file provided"

### 5. Error 400 - Tipo Inválido
```bash
curl -X POST http://localhost:8000/upload \
  -F "file=@documento.pdf" \
  -F "title=PDF Invalido" \
  -H "Authorization: Bearer fake-token-for-testing"
```

**Resultado esperado:**
- Status: 400
- detail: "Invalid file type. Expected video/*, got application/pdf"

### 6. Error 400 - Fecha Inválida
```bash
curl -X POST http://localhost:8000/upload \
  -F "file=@video.mp4" \
  -F "title=Fecha Mala" \
  -F "release_date=invalid-date" \
  -H "Authorization: Bearer fake-token-for-testing"
```

**Resultado esperado:**
- Status: 400
- detail: "Invalid release_date format..."

### 7. Verificar Archivo Guardado
```bash
# Después de un upload exitoso
ls -lh storage/videos/
cat storage/videos/{uuid}.mp4 | head -c 100
```

### 8. Verificar Base de Datos
```sql
-- VideoAsset creado
SELECT id, title, file_path, file_size, duration_ms, idempotency_key 
FROM video_assets 
ORDER BY created_at DESC 
LIMIT 1;

-- Job creado
SELECT id, job_type, status, params, video_asset_id 
FROM jobs 
WHERE job_type = 'cut_analysis' 
ORDER BY created_at DESC 
LIMIT 1;
```

**Resultado esperado:**
- VideoAsset con file_path='storage/videos/{uuid}.mp4', file_size > 0
- Job con job_type='cut_analysis', status='PENDING', params='{"reason": "initial_cut_from_upload"}'

## Conformidad con OpenAPI

✅ **Endpoint**: POST /upload  
✅ **Request Body**: multipart/form-data  
✅ **Campos**: file (required), title, description, release_date, idempotency_key (optional)  
✅ **Response 201**: VideoUploadResponse schema  
✅ **Response 400**: Error schema  
✅ **Security**: bearerAuth (configurado en FastAPI)  

## Mejoras de la Implementación vs Versión Anterior

| Característica | Versión Anterior | Versión REAL |
|----------------|-----------------|--------------|
| Storage | `/tmp/uploads` | `storage/videos/` configurable |
| Filename | `{uuid}.mp4` fijo | `{uuid}{ext}` preserva extensión |
| File Write | `await file.read()` completo | Chunks de 8MB (memory-safe) |
| File Size | `len(content)` | Acumulado durante escritura |
| Job Type | "analyze_video" | "cut_analysis" |
| Job Status | PENDING | PENDING (correcto) |
| Job Params | {"auto_generated": True} | {"reason": "initial_cut_from_upload"} |
| Idempotencia | Implementada | Mejorada con búsqueda de job |
| Release Date | Form field | Validado y parseado |
| Error Handling | Básico | Rollback + file cleanup |
| Documentación | Comentarios básicos | Docstring completa |

## Notas de Producción

1. **Logging**: Actualmente usa `print()` - reemplazar con `logging` module
2. **File Size Limit**: Configurado en `MAX_UPLOAD_SIZE=500MB` 
3. **Chunk Size**: 8MB es óptimo para balance memoria/performance
4. **Duration**: Se calcula en job posterior (no en upload)
5. **Storage**: Usar volumen persistente en producción (no filesystem local)
6. **Security**: Implementar validación de tokens JWT
7. **Rate Limiting**: Agregar throttling para prevenir abuse
8. **Virus Scanning**: Considerar escaneo de archivos subidos
9. **Cleanup**: Implementar job para limpiar archivos huérfanos
10. **Monitoring**: Agregar métricas de upload (tiempo, tamaño, errores)

## Estado del Código

- ✅ Implementado completamente
- ✅ Sigue arquitectura existente
- ✅ Usa modelos y schemas existentes
- ✅ Match exacto con OpenAPI spec
- ✅ Código asíncrono y eficiente
- ✅ Manejo robusto de errores
- ⚠️ Requiere testing con servicios running (docker-compose)
