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

guard_prod_forbid

: "${DB_NAME:?DB_NAME is required}"

export ONLINE_VISIBLE_SURFACE_MODE="${ONLINE_VISIBLE_SURFACE_MODE:-incremental}"

# The strict gate shells back into Odoo several times. Use the currently
# resolved compose project explicitly so it does not fall back to _lib defaults.
export LIVE_STRICT_ODOO_SHELL_CMD="${LIVE_STRICT_ODOO_SHELL_CMD:-COMPOSE_PROJECT_NAME=${COMPOSE_PROJECT_NAME} PROJECT=${PROJECT} DB_NAME=${DB_NAME} bash scripts/ops/odoo_shell_exec.sh}"

python3 "$ROOT_DIR/scripts/verify/live_old_system_business_data_strict_parity_gate.py"
