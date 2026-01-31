#!/usr/bin/env bash
set -euo pipefail

if [[ "${CI_ENABLE_OPS_BATCH_SMOKE:-0}" != "1" ]]; then
  echo '{"status":"SKIP","reason":"DISABLED_BY_ENV","hint":"set CI_ENABLE_OPS_BATCH_SMOKE=1 to run ops_batch_smoke"}'
  exit 0
fi

python3 scripts/verify/ops_batch_smoke.py
