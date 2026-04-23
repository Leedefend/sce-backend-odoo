#!/usr/bin/env bash
set -euo pipefail

source "$(dirname "$0")/../_lib/common.sh"

ROOT_DIR="${ROOT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"

log "prod-sim deploy: build frontend (containerized)"
docker run --rm \
  -v "${ROOT_DIR}:/workspace" \
  -w /workspace/frontend \
  node:20-bookworm \
  sh -lc "corepack enable && pnpm install --frozen-lockfile && VITE_API_BASE_URL= VITE_ODOO_DB=${DB_NAME} VITE_APP_ENV=prod-sim pnpm build"

log "prod-sim deploy: validate compose manifest"
# shellcheck disable=SC2086
compose ${COMPOSE_FILES} config >/dev/null

log "prod-sim deploy: start compose stack"
# shellcheck disable=SC2086
compose ${COMPOSE_FILES} up -d --build

log "prod-sim deploy: current status"
# shellcheck disable=SC2086
compose ${COMPOSE_FILES} ps

log "prod-sim deploy: ready (nginx :80 -> frontend, /api -> odoo)"
