#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/../_lib/common.sh"

log "ensure_testdeps: pip install -r ${CONFIG_MOUNT_CONT}/requirements-test.txt"
# 这里用 test compose 组合，确保跟 CI 跑法一致
# shellcheck disable=SC2086
compose ${COMPOSE_TEST_FILES} run --rm -T \
  -v "${CONFIG_MOUNT_HOST}:${CONFIG_MOUNT_CONT}:ro" \
  --entrypoint bash odoo -lc '
  pip3 install -q -r '"${CONFIG_MOUNT_CONT}"'/requirements-test.txt &&
  python3 -c "import odoo_test_helper; print(\"OK\", odoo_test_helper.__file__)"
'
