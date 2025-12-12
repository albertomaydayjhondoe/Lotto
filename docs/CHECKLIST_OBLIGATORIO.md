# ✅ CHECKLIST OBLIGATORIO - STAKAZO

**Versión:** 1.0  
**Fecha:** 2025-12-05  
**Aplicable a:** Todos los PRs y commits

---

## 📋 INSTRUCCIONES DE USO

Este checklist debe ser completado **ANTES** de crear cualquier Pull Request a `integracion/cto-ready` o `MAIN`.

- ✅ = Completado y validado
- ⚠️ = Completado con advertencias
- ❌ = No completado (bloquea merge)
- N/A = No aplica a este cambio

---

## 🔒 SEGURIDAD

### Datos Sensibles
- [ ] ✅ No hay API keys, tokens o credenciales en el código
- [ ] ✅ No hay passwords o secrets en archivos de configuración
- [ ] ✅ Variables sensibles usan `.env` y están en `.gitignore`
- [ ] ✅ No hay información personal identificable (PII) hardcoded

### Validación de Inputs
- [ ] ✅ Todos los endpoints validan inputs con Pydantic/schemas
- [ ] ✅ Inputs de usuario están sanitizados
- [ ] ✅ Queries SQL usan parámetros (no string concatenation)
- [ ] ✅ File uploads tienen validación de tipo y tamaño

### Autenticación y Autorización
- [ ] ✅ Endpoints protegidos requieren autenticación
- [ ] ✅ Permisos de usuario verificados antes de operaciones
- [ ] ✅ Rate limiting implementado donde aplique
- [ ] ✅ CORS configurado apropiadamente

---

## 🧪 TESTING

### Cobertura
- [ ] ✅ Tests unitarios escritos para lógica nueva
- [ ] ✅ Tests de integración para nuevos endpoints
- [ ] ✅ Cobertura mínima de 70% para código nuevo
- [ ] ✅ Tests existentes siguen pasando (`pytest -v`)

### Escenarios de Prueba
- [ ] ✅ Happy path testeado
- [ ] ✅ Edge cases cubiertos
- [ ] ✅ Error handling validado
- [ ] ✅ Inputs inválidos manejados correctamente

### Comandos de Validación
```bash
# Ejecutar tests
pytest -v --cov=app --cov-report=term-missing

# Verificar cobertura
pytest --cov=app --cov-report=html

# Tests específicos de feature
pytest tests/test_<feature>.py -v
```

---

## 📝 CALIDAD DE CÓDIGO

### Estándares Python
- [ ] ✅ Código cumple PEP 8 (`flake8` sin errores)
- [ ] ✅ Type hints en todas las funciones
- [ ] ✅ Docstrings en funciones públicas (Google format)
- [ ] ✅ Imports ordenados (stdlib, third-party, local)
- [ ] ✅ Líneas ≤ 100 caracteres

### Code Review
- [ ] ✅ Código autoexplicativo o comentado donde necesario
- [ ] ✅ Sin código comentado no utilizado
- [ ] ✅ Sin `print()` o debug statements
- [ ] ✅ Sin TODOs sin issue asociado

### Comandos de Validación
```bash
# Linting
flake8 app/ --max-line-length=100

# Type checking
mypy app/ --strict

# Format check
black app/ --check --line-length=100
```

---

## 📚 DOCUMENTACIÓN

### Código
- [ ] ✅ Docstrings actualizados para funciones modificadas
- [ ] ✅ Comentarios explican "por qué", no "qué"
- [ ] ✅ README actualizado si hay cambios de uso
- [ ] ✅ CHANGELOG.md incluye entrada de este cambio

### API
- [ ] ✅ OpenAPI/Swagger actualizado para nuevos endpoints
- [ ] ✅ Ejemplos de request/response documentados
- [ ] ✅ Códigos de error documentados
- [ ] ✅ Rate limits documentados

### Migraciones
- [ ] ✅ Alembic migration creada si hay cambios de DB
- [ ] ✅ Migration tiene rollback funcional
- [ ] ✅ Migration testeada localmente
- [ ] N/A No hay cambios de base de datos

---

## 🚀 PERFORMANCE

### Optimización
- [ ] ✅ No hay N+1 queries
- [ ] ✅ Índices de DB apropiados
- [ ] ✅ Paginación implementada en endpoints de lista
- [ ] ✅ Caching implementado donde aplique

### Recursos
- [ ] ✅ No hay memory leaks evidentes
- [ ] ✅ Archivos grandes procesados en streaming
- [ ] ✅ Timeouts configurados en requests externos
- [ ] ✅ Connection pooling para DB/Redis

### Monitoreo
- [ ] ✅ Logging apropiado (no verbose, no silent)
- [ ] ✅ Métricas expuestas si aplica
- [ ] ✅ Errores capturados y loggeados
- [ ] ✅ No se loggean datos sensibles

---

## 🤖 PROMPT ENGINEERING (si aplica)

### Templates
- [ ] ✅ Prompt usa template versionado de `backend/app/prompts/`
- [ ] ✅ Prompt incluye `prompt_version` en metadata
- [ ] ✅ Examples de few-shot incluidos
- [ ] ✅ Context window dentro de límites del modelo

### Validación
- [ ] ✅ Respuesta del modelo validada con Pydantic
- [ ] ✅ Fallback mechanism implementado
- [ ] ✅ Prompt y response loggeados
- [ ] ✅ Token usage monitoreado

### Compliance
- [ ] ✅ Ver archivo: `backend/app/prompts/PROMPT_REFINEMENT_CHECKLIST.md`
- [ ] ✅ No se envían datos sensibles al modelo
- [ ] ✅ Content filtering implementado
- [ ] N/A No usa AI models en este cambio

---

## 🔄 GIT Y VERSIONADO

### Commits
- [ ] ✅ Commits atómicos y descriptivos
- [ ] ✅ Mensajes siguen Conventional Commits
  - `feat:` nueva funcionalidad
  - `fix:` corrección de bug
  - `chore:` tareas de mantenimiento
  - `docs:` documentación
  - `refactor:` refactorización sin cambio funcional
  - `test:` adición o corrección de tests
- [ ] ✅ Commits referencian issues (`#123`)
- [ ] ✅ Branch name descriptivo (`feat/`, `fix/`, `chore/`)

### Pull Request
- [ ] ✅ Título descriptivo y conciso
- [ ] ✅ Descripción explica QUÉ y POR QUÉ
- [ ] ✅ Screenshots si hay cambios UI
- [ ] ✅ Breaking changes claramente marcados
- [ ] ✅ Reviewers asignados

---

## 🏗️ ARQUITECTURA Y DISEÑO

### Patrones
- [ ] ✅ Sigue arquitectura existente del proyecto
- [ ] ✅ Separación de concerns (API, service, model)
- [ ] ✅ Dependency injection usado apropiadamente
- [ ] ✅ Sin hardcoded values (usar config)

### Escalabilidad
- [ ] ✅ Código es stateless donde posible
- [ ] ✅ No hay race conditions evidentes
- [ ] ✅ Recursos liberados apropiadamente (context managers)
- [ ] ✅ Async/await usado donde aplique

---

## 🔧 DEPENDENCIAS

### Gestión
- [ ] ✅ Dependencias nuevas en `pyproject.toml` o `requirements.txt`
- [ ] ✅ Versiones pinned o con rangos seguros
- [ ] ✅ Dependencias justificadas (no bloat)
- [ ] ✅ Licencias compatibles verificadas

### Actualización
```bash
# Verificar dependencias
pip list --outdated

# Actualizar requirements
pip freeze > requirements.txt

# Verificar seguridad
pip-audit
```

---

## 🚦 CI/CD

### Validación Automática
- [ ] ✅ GitHub Actions workflow pasa completamente
- [ ] ✅ Linting automático sin errores
- [ ] ✅ Tests automáticos pasando
- [ ] ✅ Build exitoso

### Pre-deployment
- [ ] ✅ Variables de entorno documentadas en `.env.example`
- [ ] ✅ Migraciones aplicables sin downtime
- [ ] ✅ Rollback plan documentado si es cambio mayor
- [ ] N/A No requiere deployment especial

---

## 📊 VALIDACIÓN FINAL

### Checklist de Checklist
- [ ] ✅ Ejecutado `python3 scripts/validate_checklist.py`
- [ ] ✅ Archivo `scripts/validate_output.json` generado
- [ ] ✅ Status en validate_output.json es `"ok"` o warnings aceptables
- [ ] ✅ Violations críticas resueltas

### Aprobación Humana
- [ ] ✅ Self-review completado
- [ ] ✅ Code review solicitado
- [ ] ✅ Comentarios de reviewers resueltos
- [ ] ✅ Aprobación de Tech Lead (si es cambio mayor)

---

## 🔥 CHECKLIST PARA HOTFIXES

Si es un hotfix urgente, este es el **checklist mínimo**:

- [ ] ❌ CRÍTICO: No hay secrets expuestos
- [ ] ❌ CRÍTICO: Tests de regresión pasando
- [ ] ❌ CRÍTICO: Rollback plan documentado
- [ ] ✅ Logs y monitoreo activos
- [ ] ✅ Notificación a equipo vía Slack/Telegram

---

## 📞 CONTACTO

**¿Dudas sobre este checklist?**
- Tech Lead: @sistemaproyectomunidal
- Documentación: `docs/LINEA_MAESTRA_DESARROLLO.txt`
- Issues: https://github.com/sistemaproyectomunidal/stakazo/issues

---

## 🔄 HISTORIAL DE VERSIONES

| Versión | Fecha      | Cambios                          |
|---------|------------|----------------------------------|
| 1.0     | 2025-12-05 | Versión inicial del checklist    |

---

**🎯 OBJETIVO:** Mantener calidad, seguridad y consistencia en todo el código de STAKAZO.

**✨ REMEMBER:** Un PR que cumple este checklist es un PR que se mergea rápido y sin sorpresas. 🚀
