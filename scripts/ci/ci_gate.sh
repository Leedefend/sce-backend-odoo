#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
export ROOT_DIR

# shellcheck source=../common/env.sh
source "$ROOT_DIR/scripts/common/env.sh"
# shellcheck source=../common/compose.sh
source "$ROOT_DIR/scripts/common/compose.sh"

DB="${DB_CI:-sc_test}"
ADDONS="/usr/lib/python3/dist-packages/odoo/addons,/mnt/extra-addons,/mnt/addons_external/oca_server_ux"

compose_testdeps run --rm -T \
  -v "${ROOT_DIR}/docs:/mnt/docs:ro" \
  --entrypoint bash odoo -lc "
    pip3 install -q odoo-test-helper &&
    exec /usr/bin/odoo \
      --db_host=db --db_port=5432 --db_user=odoo --db_password=odoo \
      -d ${DB} \
      --addons-path=${ADDONS} \
      -u smart_construction_core \
      --no-http --workers=0 --max-cron-threads=0 \
      --test-enable \
      --test-tags 'sc_gate,sc_perm' \
      --stop-after-init \
      --log-level=test
  "
