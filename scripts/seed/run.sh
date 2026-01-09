#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="${ROOT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
export ROOT_DIR

# shellcheck source=../common/env.sh
source "$ROOT_DIR/scripts/common/env.sh"
# shellcheck source=../common/compose.sh
source "$ROOT_DIR/scripts/common/compose.sh"

: "${DB_NAME:?DB_NAME is required}"
: "${STEPS:?STEPS is required. e.g. STEPS=project_owner_demo_pm}"

ODOO_ADDONS_PATH="${ODOO_ADDONS_PATH:-/usr/lib/python3/dist-packages/odoo/addons,/mnt/extra-addons,/mnt/addons_external/oca_server_ux}"

printf '[seed.run] db=%s steps=%s\n' "$DB_NAME" "$STEPS"

compose_dev exec -T -e STEPS="$STEPS" odoo odoo shell --config="$ODOO_CONF" -d "$DB_NAME" \
  --db_host=db --db_port=5432 --db_user="$DB_USER" --db_password="$DB_PASSWORD" \
  --addons-path="$ODOO_ADDONS_PATH" \
<<'PY'
from odoo.addons.smart_construction_seed.seed import run_steps
import os

steps = os.environ["STEPS"]
result = run_steps(env, steps)
print(result)
env.cr.commit()
PY
