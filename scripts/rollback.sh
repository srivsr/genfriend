#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOCKER_DIR="$(dirname "$SCRIPT_DIR")/docker"

echo "=== Gen-Friend Rollback ==="

cd "$DOCKER_DIR"

echo "[1/3] Stopping current deployment..."
docker compose down

echo "[2/3] Rolling back database migration (one step)..."
docker compose run --rm backend alembic downgrade -1

echo "[3/3] Restarting previous version..."
docker compose up -d

echo "Rollback complete. Check logs:"
echo "  docker compose logs -f backend"
