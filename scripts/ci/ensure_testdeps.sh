#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/../_lib/common.sh"

log "ensure_testdeps: pip install odoo-test-helper"
# 这里用 test compose 组合，确保跟 CI 跑法一致
# shellcheck disable=SC2086
compose ${COMPOSE_TEST_FILES} run --rm -T --entrypoint bash odoo -lc '
  pip3 install -q odoo-test-helper &&
  python3 -c "import odoo_test_helper; print(\"OK\", odoo_test_helper.__file__)"
'
