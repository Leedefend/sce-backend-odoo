#!/usr/bin/env bash
set -euo pipefail

source "$(dirname "$0")/../_lib/common.sh"

ROOT_DIR="${ROOT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
PROD_SIM_MODULES="${PROD_SIM_MODULES:-smart_construction_bootstrap,smart_core,smart_scene,smart_construction_core,smart_construction_custom,smart_construction_portal,smart_construction_scene,smart_license_core,smart_owner_core,smart_owner_bundle,smart_construction_bundle,smart_construction_seed,smart_construction_demo}"

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

log "prod-sim deploy: install production module set"
# shellcheck disable=SC2086
compose ${COMPOSE_FILES} exec -T odoo odoo \
  -d "${DB_NAME}" \
  -c /var/lib/odoo/odoo.conf \
  -i "${PROD_SIM_MODULES}" \
  --without-demo=all \
  --stop-after-init

log "prod-sim deploy: apply extension module registry"
DB_NAME="${DB_NAME}" COMPOSE_FILES="${COMPOSE_FILES}" scripts/ops/apply_extension_modules.sh

log "prod-sim deploy: restart odoo after module install"
# shellcheck disable=SC2086
compose ${COMPOSE_FILES} restart odoo

log "prod-sim deploy: platform initialization preflight"
DB_NAME="${DB_NAME}" COMPOSE_FILES="${COMPOSE_FILES}" scripts/verify/platform_init_preflight.sh

log "prod-sim deploy: ready (nginx :80 -> frontend, /api -> odoo)"
