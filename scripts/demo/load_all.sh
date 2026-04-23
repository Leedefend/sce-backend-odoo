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

printf '[demo.load.all] db=%s\n' "$DB_NAME"

compose_dev run --rm -T \
  -e DB_NAME \
  --entrypoint /usr/bin/odoo odoo \
  shell --config="$ODOO_CONF" \
  -d "$DB_NAME" \
  --db_host=db --db_port=5432 --db_user="$DB_USER" --db_password="$DB_PASSWORD" \
  --addons-path=/usr/lib/python3/dist-packages/odoo/addons,/mnt/extra-addons,"$ADDONS_EXTERNAL_MOUNT" \
  --no-http --workers=0 --max-cron-threads=0 \
<<'PY'
import os
from odoo.addons.smart_construction_demo.tools.scenario_loader import load_all
db_name = os.environ.get("DB_NAME")
print("[demo.load.all] loading all scenarios", "db:", db_name)
load_all(env, mode="update")
print("[demo.load.all] done")
PY

printf '[demo.load.all] seed showroom\n'
STEPS=demo_showroom,project_stage_sync DB_NAME="$DB_NAME" bash "$ROOT_DIR/scripts/seed/run.sh"
