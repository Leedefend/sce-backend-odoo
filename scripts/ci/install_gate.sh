#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
source "$ROOT_DIR/scripts/common/guard_prod.sh"
source "$(dirname "$0")/../_lib/common.sh"

guard_prod_forbid

log "install gate (at_install) for MODULE=${MODULE} DB=${DB_CI}"
TEST_TAGS_FINAL="$(normalize_test_tags "${MODULE}" "sc_gate,sc_perm")"

# shellcheck disable=SC2086
compose ${COMPOSE_TEST_FILES} run --rm -T \
  -v "${DOCS_MOUNT_HOST}:${DOCS_MOUNT_CONT}:ro" \
  -v "${CONFIG_MOUNT_HOST}:${CONFIG_MOUNT_CONT}:ro" \
  --entrypoint bash odoo -lc "
    pip3 install -q -r ${CONFIG_MOUNT_CONT}/requirements-test.txt
    exec /usr/bin/odoo \
      --db_host=db --db_port=5432 --db_user=${DB_USER} --db_password=${DB_USER} \
      -d ${DB_CI} \
      --addons-path=/usr/lib/python3/dist-packages/odoo/addons,/mnt/source-addons,${ADDONS_EXTERNAL_MOUNT} \
      -i ${MODULE} \
      --without-demo=all \
      --no-http --workers=0 --max-cron-threads=0 \
      --test-enable \
      --test-tags \"${TEST_TAGS_FINAL}\" \
      --stop-after-init \
      --log-level=test
  "
