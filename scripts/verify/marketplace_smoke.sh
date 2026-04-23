#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="${ROOT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
source "$ROOT_DIR/scripts/common/env.sh"
source "$ROOT_DIR/scripts/common/compose.sh"

: "${DB_NAME:?DB_NAME is required}"
CONF="${ODOO_CONF:-/var/lib/odoo/odoo.conf}"

check_module_state() {
  local module="$1"
  compose_dev exec -T odoo python3 - <<PY
import odoo
from odoo import api, SUPERUSER_ID
from odoo.tools import config

db = "${DB_NAME}"
conf = "${CONF}"
config.parse_config(["-c", conf, "-d", db])
registry = odoo.registry(db)
with registry.cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})
    mod = env["ir.module.module"].search([("name","=", "${module}")], limit=1)
    print(mod.state if mod else "missing")
PY
}

ensure_module_installed() {
  local module="$1"
  local state
  state="$(check_module_state "$module" | tail -n 1)"
  if [ "$state" = "installed" ]; then
    return 0
  fi

  echo "[marketplace_smoke] DB ${DB_NAME} missing module ${module} (state=${state})"
  if [ "${E2E_AUTO_INSTALL:-}" = "1" ]; then
    echo "[marketplace_smoke] auto-install enabled, installing ${module}"
    CODEX_NEED_UPGRADE=1 MODULE="${module}" ODOO_ARGS="-i ${module}" make mod.upgrade
    make restart
    return 0
  fi

  echo "[marketplace_smoke] run: CODEX_NEED_UPGRADE=1 MODULE=${module} ODOO_ARGS=\"-i ${module}\" make mod.upgrade"
  return 2
}

ensure_module_installed "smart_core"
ensure_module_installed "smart_construction_core"

python3 "$ROOT_DIR/scripts/verify/marketplace_smoke.py"
