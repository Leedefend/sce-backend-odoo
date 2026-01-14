#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="${ROOT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
export ROOT_DIR

# shellcheck source=../common/env.sh
source "$ROOT_DIR/scripts/common/env.sh"
source "$(dirname "$0")/../_lib/common.sh"
log "dev test (upgrade + tests) DB=${DB_NAME} tags=${TEST_TAGS}"
TEST_TAGS_FINAL="$(normalize_test_tags "${MODULE}" "${TEST_TAGS}")"

RUN_RM="${RUN_RM:---rm}"
RUN_NAME=()
if [[ "${KEEP_TEST_CONTAINER:-0}" == "1" ]]; then
  RUN_RM=""
  RUN_NAME=(--name "sc-test-odoo-${DB_NAME}")
fi

# shellcheck disable=SC2086
compose ${COMPOSE_FILES} run ${RUN_RM} -T "${RUN_NAME[@]}" \
  -v "${DOCS_MOUNT_HOST}:${DOCS_MOUNT_CONT}:ro" \
  --entrypoint bash odoo -lc "
    pip3 install -q odoo-test-helper >/dev/null 2>&1 || true
    exec /usr/bin/odoo \
      --db_host=db --db_port=5432 --db_user=${DB_USER} --db_password=${DB_PASSWORD} \
      -d ${DB_NAME} \
      --addons-path=/usr/lib/python3/dist-packages/odoo/addons,/mnt/extra-addons,${ADDONS_EXTERNAL_MOUNT} \
      -i ${MODULE} \
      --without-demo=all \
      --no-http --workers=0 --max-cron-threads=0 \
      --test-enable \
      --test-tags \"${TEST_TAGS_FINAL}\" \
      --stop-after-init \
      --log-level=test
  "
