#!/usr/bin/env bash
set -euo pipefail

# Ensure execution from the project root, even if invoked from another directory.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "[1/4] Validando requisitos..."
command -v docker >/dev/null 2>&1 || { echo "Error: docker no esta instalado."; exit 1; }
docker compose version >/dev/null 2>&1 || { echo "Error: docker compose no esta disponible."; exit 1; }

echo "[2/4] Reconstruyendo imagen con cambios nuevos..."
docker compose build --pull

echo "[3/4] Recreando servicio con la imagen actualizada..."
docker compose up -d --force-recreate --remove-orphans

echo "[4/4] Estado actual de servicios..."
docker compose ps

echo "Actualizacion completa."
