#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="${ROOT_DIR:-$(pwd)}"
cd "$ROOT_DIR"

echo "[verify.contract_drift.guard] checking hard-coded reason_code literals..."

# Guard 1: reason_code must not be assigned a hard-coded uppercase literal in handler code.
# Allowlist:
# - tests
# - canonical reason code modules
# - docs
hardcoded_reason_codes="$(rg -n 'reason_code\s*[:=]\s*"([A-Z0-9_]+)"' addons/*/handlers \
  -g'*.py' \
  -g'!**/tests/**' \
  -g'!**/reason_codes.py' || true)"

if [ -n "$hardcoded_reason_codes" ]; then
  echo "[verify.contract_drift.guard] FAIL: hard-coded reason_code literals found:"
  echo "$hardcoded_reason_codes"
  exit 2
fi

echo "[verify.contract_drift.guard] checking side-effect intents idempotency declarations..."

# Guard 2: key side-effect handlers must declare IDEMPOTENCY_WINDOW_SECONDS.
missing=0
for f in \
  addons/smart_core/handlers/api_data_batch.py \
  addons/smart_core/handlers/api_data_write.py \
  addons/smart_core/handlers/api_data_unlink.py \
  addons/smart_construction_core/handlers/my_work_complete.py
do
  if [ ! -f "$f" ]; then
    echo "[verify.contract_drift.guard] FAIL: missing file $f"
    missing=1
    continue
  fi
  if ! rg -q 'IDEMPOTENCY_WINDOW_SECONDS' "$f"; then
    echo "[verify.contract_drift.guard] FAIL: $f missing IDEMPOTENCY_WINDOW_SECONDS"
    missing=1
  fi
done

# Guard 2b: auto-scan side-effect api.data.* handlers to prevent future drift.
# Any api_data_*.py handler touching api.data.(batch|write|unlink|create|update|delete)
# must declare IDEMPOTENCY_WINDOW_SECONDS.
for f in addons/smart_core/handlers/api_data_*.py; do
  [ -f "$f" ] || continue
  if rg -q 'api\.data\.(batch|write|unlink|create|update|delete)' "$f"; then
    if ! rg -q 'IDEMPOTENCY_WINDOW_SECONDS' "$f"; then
      echo "[verify.contract_drift.guard] FAIL: $f missing IDEMPOTENCY_WINDOW_SECONDS (auto-scan)"
      missing=1
    fi
  fi
done

if [ "$missing" -ne 0 ]; then
  exit 2
fi

echo "[verify.contract_drift.guard] PASS"
