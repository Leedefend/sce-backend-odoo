#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="${ROOT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
export ROOT_DIR

# shellcheck source=../common/env.sh
source "$ROOT_DIR/scripts/common/env.sh"
# shellcheck source=../common/guard_prod.sh
source "$ROOT_DIR/scripts/common/guard_prod.sh"

: "${DB_NAME:?DB_NAME is required}"

APPLY="${USER_MODULE_HISTORY_BASELINE_APPLY:-0}"
ASSET_ROOT="${MIGRATION_ASSET_ROOT:-migration_assets}"
ASSET_LOCK="${MIGRATION_ASSET_LOCK:-docs/migration_alignment/migration_asset_package_lock_v1.json}"
ARTIFACT_ROOT="${MIGRATION_ARTIFACT_ROOT:-/tmp/user_module_history_business_baseline/${DB_NAME}}"

export MIGRATION_ASSET_ROOT="$ASSET_ROOT"
export MIGRATION_ASSET_LOCK="$ASSET_LOCK"
export MIGRATION_ARTIFACT_ROOT="$ARTIFACT_ROOT"
export MIGRATION_REPLAY_DB_ALLOWLIST="${MIGRATION_REPLAY_DB_ALLOWLIST:-$DB_NAME}"
export HISTORY_CONTINUITY_USE_PACKAGED_PAYLOADS="${HISTORY_CONTINUITY_USE_PACKAGED_PAYLOADS:-1}"

if [[ "${USER_MODULE_HISTORY_BASELINE_ALLOW_PROD:-0}" == "1" ]]; then
  guard_prod_danger
else
  guard_prod_forbid
fi

run_make() {
  make -C "$ROOT_DIR" --no-print-directory "$@"
}

echo "[user_module.history_business_baseline] db=${DB_NAME} apply=${APPLY} asset_root=${ASSET_ROOT} artifact_root=${ARTIFACT_ROOT}"

run_make verify.user_module.product_boundary
run_make migration.assets.fetch
run_make migration.assets.verify_all
run_make migration.assets.delivery_audit

HISTORY_CONTINUITY_MODE=rehearse run_make history.continuity.rehearse

if [[ "$APPLY" != "1" ]]; then
  echo "[user_module.history_business_baseline] rehearsal PASS; set USER_MODULE_HISTORY_BASELINE_APPLY=1 to replay into DB"
  exit 0
fi

HISTORY_CONTINUITY_MODE=replay run_make history.continuity.replay
run_make history.business.usable.init
run_make verify.user_module.data_baseline.runtime_audit

echo "[user_module.history_business_baseline] PASS db=${DB_NAME} artifact_root=${ARTIFACT_ROOT}"
