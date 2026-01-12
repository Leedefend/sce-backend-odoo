#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/../common/env.sh"
source "$(dirname "$0")/../common/compose.sh"

echo "[diag.project] COMPOSE_PROJECT_NAME=${COMPOSE_PROJECT_NAME}"
echo "[diag.project] docker compose ps:"
compose_dev ps

echo "[diag.project] containers (name -> compose project label):"
docker ps --format '{{.Names}} {{.Label "com.docker.compose.project"}}' \
  | awk -v p="${COMPOSE_PROJECT_NAME}" '$2==p {print}'
