#!/usr/bin/env bash
set -euo pipefail
source scripts/common/compose.sh
compose_dev stop odoo nginx 2>/dev/null || true
bash scripts/test/test.sh
