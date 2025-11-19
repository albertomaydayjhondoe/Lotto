#!/bin/bash
set -e

echo "🚀 Configurando entorno de desarrollo Stakazo..."

# Install Python dependencies
echo "📦 Instalando dependencias Python..."
if [ -f requirements.txt ]; then
    pip install -r requirements.txt
fi

if [ -f backend/requirements.txt ]; then
    pip install -r backend/requirements.txt
fi

# Install Node dependencies (only if clients/typescript exists with package.json)
if [ -d clients/typescript ] && [ -f clients/typescript/package.json ]; then
    echo "📦 Instalando dependencias Node.js..."
    cd clients/typescript
    npm install --no-save
    cd ../..
fi

# Build Docker images
echo "🐳 Construyendo imágenes Docker..."
if [ -f docker-compose.yml ]; then
    docker-compose build
fi

echo "✅ Entorno de desarrollo configurado correctamente!"
echo ""
echo "Comandos disponibles:"
echo "  make dev     - Inicia backend y postgres con docker-compose"
echo "  make api     - Arranca solo el backend en modo reload"
echo "  make db      - Arranca solo postgres"
echo "  make migrate - Aplica migrations dentro del contenedor"
echo ""
