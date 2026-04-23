#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
source "$ROOT_DIR/scripts/common/guard_prod.sh"

DB_NAME=${DB_NAME:-sc_demo}
POLICY_MODULE=${POLICY_MODULE:-smart_construction_custom}

guard_prod_danger

make mod.upgrade MODULE="$POLICY_MODULE" DB_NAME="$DB_NAME"

DB_NAME="$DB_NAME" docker compose exec -T odoo odoo shell -d "$DB_NAME" -c /var/lib/odoo/odoo.conf <<'PY'
res = env["sc.security.policy"].apply_role_matrix()
env.cr.commit()
print("apply_role_matrix:", res)
PY
