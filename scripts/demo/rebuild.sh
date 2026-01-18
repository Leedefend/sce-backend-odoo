#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="${ROOT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
export ROOT_DIR

# shellcheck source=../common/env.sh
source "$ROOT_DIR/scripts/common/env.sh"
# shellcheck source=../common/guard_prod.sh
source "$ROOT_DIR/scripts/common/guard_prod.sh"
# shellcheck source=../common/compose.sh
source "$ROOT_DIR/scripts/common/compose.sh"

: "${DB_NAME:?DB_NAME is required}"

guard_prod_forbid

printf '[demo.rebuild] db=%s\n' "$DB_NAME"

stage=""

log_tail() {
  compose_dev logs --tail="${DEMO_LOG_TAIL:-200}" "${DEMO_LOG_SERVICE:-odoo}" || true
}

run_stage() {
  stage="$1"; shift
  printf '[demo.rebuild] stage=%s\n' "$stage"
  if command -v timeout >/dev/null 2>&1; then
    timeout "${DEMO_TIMEOUT:-600}" "$@"
  else
    "$@"
  fi
}

trap 'status=$?; printf "[demo.rebuild] FAILED stage=%s\n" "$stage"; log_tail; exit $status' ERR

run_stage reset make demo.reset DB_NAME="$DB_NAME"
run_stage install make demo.install DB_NAME="$DB_NAME"
run_stage load_all make demo.load.all DB_NAME="$DB_NAME"
run_stage verify make demo.verify DB_NAME="$DB_NAME"

printf '🎉 demo.rebuild PASSED\n'
