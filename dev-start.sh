#!/bin/bash
# Development startup script for Stakazo
# Starts PostgreSQL in Docker and runs backend locally

set -e

echo "🚀 Starting Stakazo Development Environment"
echo "==========================================="

# Check if Docker is available
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not available - starting backend with SQLite fallback"
    echo ""
    cd backend
    source ../venv/bin/activate 2>/dev/null || true
    exec uvicorn main:app --reload --host 0.0.0.0 --port 8000
    exit 0
fi

# Start PostgreSQL in background
echo "📦 Starting PostgreSQL container..."
docker compose up -d postgres

# Wait for PostgreSQL to be ready
echo "⏳ Waiting for PostgreSQL to be ready..."
timeout=30
elapsed=0
while ! docker compose exec -T postgres pg_isready -U postgres &>/dev/null; do
    if [ $elapsed -ge $timeout ]; then
        echo "❌ PostgreSQL failed to start within ${timeout}s"
        exit 1
    fi
    sleep 1
    elapsed=$((elapsed + 1))
done

echo "✅ PostgreSQL is ready"
echo ""

# Run database migrations
echo "🔄 Running database migrations..."
cd backend
source ../venv/bin/activate 2>/dev/null || true
alembic upgrade head

echo ""
echo "✅ Migrations complete"
echo ""
echo "🌐 Starting FastAPI backend..."
echo "   API: http://localhost:8000"
echo "   Docs: http://localhost:8000/docs"
echo "   pgAdmin: http://localhost:5050 (admin@stakazo.local / admin)"
echo ""
echo "Press Ctrl+C to stop"
echo ""

# Start backend
exec uvicorn main:app --reload --host 0.0.0.0 --port 8000
