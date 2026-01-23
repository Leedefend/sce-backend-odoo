#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="${ROOT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
export ROOT_DIR

# shellcheck source=../common/env.sh
source "$ROOT_DIR/scripts/common/env.sh"
# shellcheck source=../common/compose.sh
source "$ROOT_DIR/scripts/common/compose.sh"

DB_NAME="${DB_NAME:-${DB:-}}"
: "${DB_NAME:?DB_NAME is required}"

evidence_dir="$ROOT_DIR/docs/ops/guards"
evidence_path="$evidence_dir/mail_from_guard.csv"
mkdir -p "$evidence_dir"

set -o pipefail
compose_dev exec -T \
  -e PYTHONWARNINGS=ignore \
  odoo odoo shell -d "$DB_NAME" \
  --db_host=db --db_port=5432 --db_user="$DB_USER" --db_password="$DB_PASSWORD" \
  -c "$ODOO_CONF" \
  --logfile=/dev/null --log-level=warn \
  < "$ROOT_DIR/scripts/prod/guard_mail_from.py" | tee "$evidence_path"
rc=${PIPESTATUS[0]}

if [[ "$rc" -eq 0 ]]; then
  echo "RESULT: PASS"
elif [[ "$rc" -eq 2 ]]; then
  echo "RESULT: FAIL (guard mismatch)"
else
  echo "RESULT: ERROR (rc=$rc)"
fi
exit "$rc"
