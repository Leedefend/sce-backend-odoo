#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="${ROOT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
export ROOT_DIR
source "$ROOT_DIR/scripts/common/env.sh"

fingerprint() {
  DB_NAME=sc_demo bash scripts/ops/odoo_shell_exec.sh \
    < scripts/verify/frontend_productization_history_fingerprint.py \
    | grep '^FRONTEND_HISTORY_FINGERPRINT=' | tail -1
}

before="$(fingerprint)"
for denied_db in sc_demo postgres arbitrary_database ""; do
  set +e
  make --no-print-directory demo.frontend.fixture DB_NAME="$denied_db" >/tmp/frontend-fixture-deny.log 2>&1
  status=$?
  set -e
  if [[ $status -eq 0 ]]; then
    cat /tmp/frontend-fixture-deny.log >&2
    echo "[verify.frontend.fixture.guard] FAIL accepted DB_NAME=${denied_db:-<empty>}" >&2
    exit 2
  fi
  if ! grep -q '^\[DENY\] frontend acceptance fixture requires DB_NAME=sc_frontend_acceptance' /tmp/frontend-fixture-deny.log; then
    cat /tmp/frontend-fixture-deny.log >&2
    echo "[verify.frontend.fixture.guard] FAIL database guard did not fail first" >&2
    exit 2
  fi
  echo "[verify.frontend.fixture.guard] denied DB_NAME=${denied_db:-<empty>} exit=${status}"
done
after="$(fingerprint)"
if [[ "$before" != "$after" ]]; then
  echo "[verify.frontend.fixture.guard] FAIL sc_demo fingerprint changed" >&2
  echo "before: $before" >&2
  echo "after:  $after" >&2
  exit 2
fi
echo "[verify.frontend.fixture.guard] PASS sc_demo fingerprint unchanged"
echo "$after"
