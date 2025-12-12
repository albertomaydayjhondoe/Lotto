#!/bin/bash
# Stop all development services

echo "🛑 Stopping Stakazo Development Environment"

# Stop Docker services if available
if command -v docker &> /dev/null; then
    echo "📦 Stopping Docker containers..."
    docker compose down
    echo "✅ Docker services stopped"
else
    echo "ℹ️  Docker not available, nothing to stop"
fi

echo ""
echo "✅ Development environment stopped"
