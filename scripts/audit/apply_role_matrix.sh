#!/usr/bin/env bash
set -euo pipefail

DB_NAME=${DB_NAME:-sc_demo}
POLICY_MODULE=${POLICY_MODULE:-smart_construction_custom}

make mod.upgrade MODULE="$POLICY_MODULE" DB_NAME="$DB_NAME"

DB_NAME="$DB_NAME" docker compose exec -T odoo odoo shell -d "$DB_NAME" -c /var/lib/odoo/odoo.conf <<'PY'
res = env["sc.security.policy"].apply_role_matrix()
print("apply_role_matrix:", res)
PY
