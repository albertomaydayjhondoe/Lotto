#!/bin/bash
# Quick Start Script para Stakazo

echo "🚀 Iniciando Stakazo - Orquestador AI API"
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker no está corriendo. Por favor inicia Docker Desktop."
    exit 1
fi

echo "✅ Docker está corriendo"
echo ""

# Start services
echo "📦 Iniciando servicios..."
docker-compose up -d

# Wait for services to be ready
echo "⏳ Esperando a que los servicios estén listos..."
sleep 5

# Check if services are running
if docker-compose ps | grep -q "Up"; then
    echo "✅ Servicios iniciados correctamente"
    echo ""
    echo "📚 Documentación disponible en:"
    echo "   - Swagger UI: http://localhost:8000/docs"
    echo "   - ReDoc:      http://localhost:8000/redoc"
    echo "   - Health:     http://localhost:8000/health"
    echo ""
    echo "🔧 Comandos útiles:"
    echo "   - make logs       Ver logs"
    echo "   - make stop       Detener servicios"
    echo "   - make init-db    Reinicializar BD"
    echo "   - make help       Ver todos los comandos"
    echo ""
    echo "✨ Sistema listo para desarrollo!"
else
    echo "❌ Error al iniciar servicios"
    docker-compose ps
    exit 1
fi
