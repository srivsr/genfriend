#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
DOCKER_DIR="$PROJECT_DIR/docker"

echo "=== Gen-Friend Production Deployment ==="

# Check required env vars
if [ ! -f "$DOCKER_DIR/.env" ]; then
    echo "ERROR: $DOCKER_DIR/.env not found."
    echo "Copy .env.production.example to docker/.env and fill in values."
    exit 1
fi

# Source env to validate required vars
set -a
source "$DOCKER_DIR/.env"
set +a

for var in DB_USER DB_PASSWORD JWT_SECRET ADMIN_SECRET_KEY CLERK_SECRET_KEY; do
    if [ -z "${!var:-}" ]; then
        echo "ERROR: $var is not set in .env"
        exit 1
    fi
done

echo "[1/5] Pulling latest images..."
cd "$DOCKER_DIR"
docker compose pull db redis 2>/dev/null || true

echo "[2/5] Building application images..."
docker compose build --no-cache backend frontend

echo "[3/5] Running database migrations..."
docker compose run --rm backend alembic upgrade head

echo "[4/5] Starting services..."
docker compose up -d

echo "[5/5] Waiting for health checks..."
sleep 10

HEALTH=$(curl -sf http://localhost:8002/health/ready 2>/dev/null || echo '{"status":"failed"}')
echo "Backend health: $HEALTH"

if echo "$HEALTH" | grep -q '"ready"'; then
    echo ""
    echo "=== Deployment successful! ==="
    echo "Frontend: https://genfriend.app"
    echo "API:      https://api.genfriend.app"
    echo "Health:   https://api.genfriend.app/health/ready"
else
    echo ""
    echo "WARNING: Backend health check failed. Check logs:"
    echo "  docker compose -f $DOCKER_DIR/docker-compose.yml logs backend"
fi
