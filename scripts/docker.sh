#!/bin/bash
# Docker management script

set -e

COMMAND=${1:-up}

case $COMMAND in
    up)
        echo "🐳 Starting Docker containers..."
        docker-compose up -d
        echo "✅ Containers started!"
        echo "📊 Dashboard: http://localhost:8080"
        echo "🤖 Bot logs: docker-compose logs -f bot"
        ;;
    down)
        echo "🛑 Stopping Docker containers..."
        docker-compose down
        echo "✅ Containers stopped!"
        ;;
    build)
        echo "🔨 Building Docker images..."
        docker-compose build --no-cache
        echo "✅ Build completed!"
        ;;
    logs)
        echo "📜 Showing logs..."
        docker-compose logs -f
        ;;
    status)
        echo "📊 Container status:"
        docker-compose ps
        ;;
    clean)
        echo "🧹 Cleaning up containers and volumes..."
        docker-compose down -v
        docker system prune -f
        echo "✅ Cleanup completed!"
        ;;
    *)
        echo "Usage: $0 {up|down|build|logs|status|clean}"
        exit 1
        ;;
esac