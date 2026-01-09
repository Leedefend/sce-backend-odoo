#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="${ROOT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
export ROOT_DIR

# shellcheck source=../common/env.sh
source "$ROOT_DIR/scripts/common/env.sh"
# shellcheck source=../common/compose.sh
source "$ROOT_DIR/scripts/common/compose.sh"

: "${DB_NAME:?DB_NAME is required}"

compose_dev run --rm -T \
  --entrypoint /usr/bin/odoo odoo \
  shell --config="$ODOO_CONF" \
  -d "$DB_NAME" \
  --db_host=db --db_port=5432 --db_user="$DB_USER" --db_password="$DB_PASSWORD" \
  --addons-path=/usr/lib/python3/dist-packages/odoo/addons,/mnt/extra-addons,"$ADDONS_EXTERNAL_MOUNT" \
  --no-http --workers=0 --max-cron-threads=0 \
<<'PY'
from odoo.addons.smart_construction_demo.tools.scenario_loader import SCENARIOS
for k in sorted(SCENARIOS.keys()):
    print(k)
PY
