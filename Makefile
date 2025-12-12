.PHONY: help dev api db migrate migrate-create init-db stop logs clean test build ps shell-backend shell-db

help: ## Muestra esta ayuda
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-18s\033[0m %s\n", $$1, $$2}'

dev: ## Inicia el backend y postgres con docker-compose
	@echo "🚀 Iniciando backend y postgres..."
	docker-compose up -d
	@echo "✅ Servicios iniciados. Backend: http://localhost:8000"
	@echo "📚 API Docs: http://localhost:8000/docs"

api: ## Arranca solo el backend en modo reload (local)
	@echo "🚀 Iniciando backend en modo desarrollo..."
	@if ! docker ps | grep -q stakazo_postgres; then \
		echo "⚠️  PostgreSQL no está corriendo. Iniciando..."; \
		docker-compose up -d postgres; \
		echo "⏳ Esperando a que PostgreSQL esté listo..."; \
		sleep 3; \
	fi
	cd backend && DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/stakazo_db uvicorn main:app --host 0.0.0.0 --port 8000 --reload

db: ## Arranca solo postgres
	@echo "🐘 Iniciando PostgreSQL..."
	docker-compose up -d postgres
	@echo "✅ PostgreSQL iniciado en puerto 5432"

migrate: ## Aplica migrations dentro del contenedor
	@echo "🔄 Aplicando migraciones..."
	docker-compose exec backend alembic upgrade head
	@echo "✅ Migraciones aplicadas correctamente"

migrate-create: ## Crea una nueva migration (uso: make migrate-create MSG="descripción")
	@if [ -z "$(MSG)" ]; then \
		echo "❌ Error: Debes proporcionar un mensaje"; \
		echo "   Uso: make migrate-create MSG='descripcion de la migracion'"; \
		exit 1; \
	fi
	@echo "📝 Creando migración: $(MSG)"
	cd backend && alembic revision --autogenerate -m "$(MSG)"

init-db: ## Inicializa la base de datos con schema y datos de ejemplo
	@echo "🔧 Inicializando base de datos..."
	@if ! docker ps | grep -q stakazo_postgres; then \
		echo "⚠️  PostgreSQL no está corriendo. Iniciando..."; \
		docker-compose up -d postgres; \
		echo "⏳ Esperando a que PostgreSQL esté listo..."; \
		sleep 5; \
	fi
	cd backend && DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/stakazo_db python -m app.db.init_db

stop: ## Detiene todos los servicios
	@echo "🛑 Deteniendo servicios..."
	docker-compose down
	@echo "✅ Servicios detenidos"

logs: ## Muestra logs de los servicios
	docker-compose logs -f

clean: ## Limpia contenedores, volúmenes y cache
	@echo "🧹 Limpiando entorno..."
	docker-compose down -v
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "✅ Entorno limpiado"

test: ## Ejecuta los tests
	@echo "🧪 Ejecutando tests..."
	cd backend && pytest -v

build: ## Reconstruye las imágenes Docker
	@echo "🔨 Reconstruyendo imágenes Docker..."
	docker-compose build --no-cache
	@echo "✅ Imágenes reconstruidas"

ps: ## Muestra el estado de los servicios
	docker-compose ps

shell-backend: ## Accede a la shell del contenedor backend
	docker-compose exec backend bash

shell-db: ## Accede a la shell de PostgreSQL
	docker-compose exec postgres psql -U postgres -d stakazo_db

