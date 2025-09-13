#!/bin/bash

VERSION=${1:-latest}

echo "🚀 Deploying GladOS version: $VERSION"
echo "📅 Deploy time: $(date)"

# Экспортируем версию для docker-compose
export RELEASE_VERSION=$VERSION

echo "🛑 Stopping existing services..."
docker-compose down

echo "🐳 Building images with version $VERSION..."
docker-compose build --build-arg RELEASE_VERSION=$VERSION

echo "🏷️ Tagging images..."
docker tag glados-backend:$VERSION glados-backend:latest
docker tag glados-frontend:$VERSION glados-frontend:latest

echo "🔄 Starting services..."
docker-compose up -d

echo "⏳ Waiting for services to start..."
sleep 10

echo "📊 Service status:"
docker-compose ps

echo "📝 Backend logs:"
docker logs glados-backend-1 --tail 10

echo "📝 Frontend logs:"
docker logs glados-frontend-1 --tail 10

echo "✅ Deployment completed!"
echo "🔗 Version deployed: $VERSION"

# Показываем информацию о запущенных контейнерах
echo ""
echo "📋 Container information:"
docker ps --format "table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}" --filter "name=glados"

# Показываем версии из переменных окружения
echo ""
echo "🏷️ Version information:"
docker exec glados-backend-1 env | grep VERSION || echo "Backend version info not available"