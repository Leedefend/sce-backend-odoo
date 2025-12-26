#!/usr/bin/env bash
set -euo pipefail

DB=sc_test
ADDONS="/usr/lib/python3/dist-packages/odoo/addons,/mnt/extra-addons,/mnt/addons_external/oca_server_ux"

docker compose -p sc -f docker-compose.yml -f docker-compose.testdeps.yml run --rm -T \
  -v "$(pwd)/docs:/mnt/docs:ro" \
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
