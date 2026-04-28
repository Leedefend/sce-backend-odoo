#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="${ROOT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
export ROOT_DIR

# shellcheck source=../common/env.sh
source "$ROOT_DIR/scripts/common/env.sh"
# shellcheck source=../_lib/common.sh
source "$ROOT_DIR/scripts/_lib/common.sh"
# shellcheck source=../common/guard_prod.sh
source "$ROOT_DIR/scripts/common/guard_prod.sh"

: "${DB_NAME:?DB_NAME is required}"
: "${COMPOSE_FILES:=-f docker-compose.yml}"

guard_prod_danger

RUN_ID="${RUN_ID:-prod_history_init_$(date +%Y%m%dT%H%M%S)}"
ARTIFACT_ROOT="${MIGRATION_ARTIFACT_ROOT:-/tmp/history_continuity/${DB_NAME}/${RUN_ID}}"
ALLOWLIST="${MIGRATION_REPLAY_DB_ALLOWLIST:-${DB_NAME}}"
PRODUCTION_MODULES="${HISTORY_PRODUCTION_MODULES:-smart_construction_bootstrap,smart_core,smart_scene,smart_construction_core,smart_construction_custom,smart_construction_portal,smart_construction_scene,smart_license_core,smart_owner_core,smart_owner_bundle,smart_construction_bundle,smart_construction_seed}"
INSTALL_MODULES="${HISTORY_PRODUCTION_INSTALL_MODULES:-1}"

export RUN_ID
export MIGRATION_ARTIFACT_ROOT="$ARTIFACT_ROOT"
export MIGRATION_REPLAY_DB_ALLOWLIST="$ALLOWLIST"
export HISTORY_CONTINUITY_ALLOW_PROD=1
export HISTORY_CONTINUITY_USE_PACKAGED_PAYLOADS="${HISTORY_CONTINUITY_USE_PACKAGED_PAYLOADS:-1}"
export HISTORY_CONTINUITY_INCLUDE_PAYMENT_STATE_RECOVERY="${HISTORY_CONTINUITY_INCLUDE_PAYMENT_STATE_RECOVERY:-1}"

echo "[fresh.production.history.init] db=${DB_NAME} run_id=${RUN_ID} artifact_root=${ARTIFACT_ROOT} packaged_payloads=${HISTORY_CONTINUITY_USE_PACKAGED_PAYLOADS}"
if [[ "$INSTALL_MODULES" == "1" ]]; then
  echo "[fresh.production.history.init] step=start_stack"
  compose ${COMPOSE_FILES} up -d

  echo "[fresh.production.history.init] step=install_modules"
  compose ${COMPOSE_FILES} exec -T odoo odoo \
    -d "$DB_NAME" \
    -c /var/lib/odoo/odoo.conf \
    -i "$PRODUCTION_MODULES" \
    --without-demo=all \
    --stop-after-init

  echo "[fresh.production.history.init] step=apply_extension_modules"
  DB_NAME="$DB_NAME" COMPOSE_FILES="$COMPOSE_FILES" "$ROOT_DIR/scripts/ops/apply_extension_modules.sh"

  echo "[fresh.production.history.init] step=restart_odoo"
  compose ${COMPOSE_FILES} restart odoo
else
  echo "[fresh.production.history.init] skip module install by HISTORY_PRODUCTION_INSTALL_MODULES=0"
fi

echo "[fresh.production.history.init] step=platform_init_preflight"
DB_NAME="$DB_NAME" COMPOSE_FILES="${COMPOSE_FILES}" "$ROOT_DIR/scripts/verify/platform_init_preflight.sh"

echo "[fresh.production.history.init] step=history_replay"
DB_NAME="$DB_NAME" HISTORY_CONTINUITY_MODE=replay bash "$ROOT_DIR/scripts/migration/history_continuity_oneclick.sh"

echo "[fresh.production.history.init] step=business_usable_probe"
DB_NAME="$DB_NAME" "$ROOT_DIR/scripts/ops/odoo_shell_exec.sh" <"$ROOT_DIR/scripts/migration/history_business_usable_probe.py"

echo "[fresh.production.history.init] step=business_smoke"
DB_NAME="$DB_NAME" BASE_URL="${BASE_URL:-http://127.0.0.1:18069}" "$ROOT_DIR/scripts/audit/smoke_business_full.sh"

echo "[fresh.production.history.init] step=role_matrix_smoke"
DB_NAME="$DB_NAME" BASE_URL="${BASE_URL:-http://127.0.0.1:18069}" "$ROOT_DIR/scripts/audit/smoke_role_matrix.sh"

echo "[fresh.production.history.init] step=frontend_smoke"
DB_NAME="$DB_NAME" BASE_URL="${FRONTEND_BASE_URL:-${BASE_URL:-http://127.0.0.1}}" \
  E2E_LOGIN="${E2E_LOGIN:-admin}" E2E_PASSWORD="${E2E_PASSWORD:-admin}" \
  "$ROOT_DIR/scripts/diag/fe_smoke.sh"

echo "[fresh.production.history.init] PASS db=${DB_NAME} run_id=${RUN_ID} artifact_root=${ARTIFACT_ROOT}"
