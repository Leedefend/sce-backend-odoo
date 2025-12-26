#!/usr/bin/env bash
set -euo pipefail
source scripts/common/env.sh
source scripts/common/compose.sh

DB_CI="$DB_CI" MODULE="$MODULE" TEST_TAGS_FINAL="$TEST_TAGS_FINAL" \
compose_ci up --abort-on-container-exit --exit-code-from odoo
