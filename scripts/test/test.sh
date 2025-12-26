#!/usr/bin/env bash
set -euo pipefail
source scripts/common/env.sh
source scripts/common/compose.sh

compose_dev run --rm -T odoo \
  -d "$DB_NAME" \
  -u "$MODULE" \
  --no-http \
  --test-enable \
  --test-tags "$TEST_TAGS_FINAL" \
  --stop-after-init
