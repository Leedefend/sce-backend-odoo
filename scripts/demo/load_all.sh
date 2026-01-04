#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="${ROOT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
export ROOT_DIR

# shellcheck source=../common/env.sh
source "$ROOT_DIR/scripts/common/env.sh"
# shellcheck source=../common/compose.sh
source "$ROOT_DIR/scripts/common/compose.sh"

: "${DB_NAME:?DB_NAME is required}"

printf '[demo.load.all] db=%s\n' "$DB_NAME"

compose_dev run --rm -T \
  -e DB_NAME \
  --entrypoint /usr/bin/odoo odoo \
  shell --config=/etc/odoo/odoo.conf \
  -d "$DB_NAME" \
  --db_host=db --db_port=5432 --db_user="$DB_USER" --db_password="$DB_PASSWORD" \
  --addons-path=/usr/lib/python3/dist-packages/odoo/addons,/mnt/extra-addons,"$ADDONS_EXTERNAL_MOUNT" \
  --logfile=/dev/stdout \
  --no-http --workers=0 --max-cron-threads=0 \
<<'PY'
import os
from odoo.addons.smart_construction_demo.tools.scenario_loader import load_all
db_name = os.environ.get("DB_NAME")
print("[demo.load.all] loading all scenarios", "db:", db_name)
load_all(env, mode="update")
print("[demo.load.all] done")
PY
