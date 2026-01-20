#!/usr/bin/env bash
set -euo pipefail

DB_NAME="${DB:-${1:-}}"
PREAMBLE_LINES="${PREAMBLE_LINES:-12}"

echo "STAGE PREFLIGHT"
echo "----- CODEX PREAMBLE (head ${PREAMBLE_LINES}) -----"
head -n "${PREAMBLE_LINES}" docs/ops/codex_preamble_v1.0.txt
echo "----- CODEX RULES: DB POLICY -----"
awk '
  /^## Database Policy/ {p=1}
  p {
    if (seen && /^## /) exit
    print
    seen=1
  }
' docs/ops/codex_rules_v1.0.md
echo "---------------------------------"

if [[ -z "$DB_NAME" ]]; then
  echo "FAIL: DB is required"
  echo "FIX: set DB to allowed value (sc_demo/sc_p2/sc_p3)"
  exit 2
fi

if ! DB="$DB_NAME" bash scripts/ops/check_db_policy.sh; then
  echo "FIX: set DB to allowed value (sc_demo/sc_p2/sc_p3)"
  exit 2
fi

bash scripts/ops/codex_preflight.sh
