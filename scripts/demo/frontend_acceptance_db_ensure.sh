#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="${ROOT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
export ROOT_DIR

# Scope validation intentionally runs before loading repository environment
# defaults or invoking any database/module operation.
source "$ROOT_DIR/scripts/common/frontend_acceptance_guard.sh"
guard_frontend_acceptance_scope
acquire_frontend_acceptance_lock lifecycle

source "$ROOT_DIR/scripts/common/env.sh"
source "$ROOT_DIR/scripts/common/guard_prod.sh"
guard_prod_forbid

export DB_NAME SC_ENVIRONMENT SC_ALLOW_DEMO_DATA

make --no-print-directory db.create DB="$DB_NAME"
make --no-print-directory mod.install MODULE=smart_construction_bundle DB_NAME="$DB_NAME"
DB_NAME="$DB_NAME" bash scripts/ops/odoo_shell_exec.sh <<'PY'
param = env['ir.config_parameter'].sudo().get_param('smart_core.release_operator.product_base_keys', '')
bundle = env['ir.module.module'].sudo().search([('name', '=', 'smart_construction_bundle')], limit=1)
if bundle.state != 'installed' or 'construction' not in [v.strip() for v in param.split(',') if v.strip()]:
    raise RuntimeError('acceptance bundle product baseline is not initialized')
print('[frontend.acceptance.ensure] product_base_keys=%s' % param)
PY
make --no-print-directory policy.ensure.role_surface_demo \
  DB_NAME="$DB_NAME" AUTO_FIX_ROLE_SURFACE_DEMO=1 ROLE_SMOKE_PASSWORD=demo

echo "[db.frontend.acceptance.ensure] PASS db=${DB_NAME}"
