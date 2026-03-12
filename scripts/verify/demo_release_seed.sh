#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="${ROOT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
export ROOT_DIR

# shellcheck source=../common/env.sh
source "$ROOT_DIR/scripts/common/env.sh"
# shellcheck source=../common/guard_prod.sh
source "$ROOT_DIR/scripts/common/guard_prod.sh"
# shellcheck source=../common/compose.sh
source "$ROOT_DIR/scripts/common/compose.sh"

: "${DB_NAME:?DB_NAME is required}"

guard_prod_forbid

printf '[verify.demo.release.seed] db=%s\n' "$DB_NAME"

psql_cmd() {
  compose_dev exec -T db psql -U "$DB_USER" -d "$DB_NAME" -v ON_ERROR_STOP=1 "$@" </dev/null
}

check() {
  local desc="$1"
  local ok_sql="$2"
  local sample_sql="$3"
  if psql_cmd -At -c "$ok_sql" | grep -qx ok; then
    echo "✓ $desc"
    return 0
  fi
  echo "✗ $desc"
  if [ -n "$sample_sql" ]; then
    echo "[sample]"
    psql_cmd -c "$sample_sql" || true
    echo "[/sample]"
  fi
  exit 1
}

check "release seed includes showroom projects" \
  "select case when count(*) >= 10 then 'ok' else 'showroom projects < 10' end from project_project where coalesce(name->>'zh_CN', name->>'en_US', name::text) like '展厅-%';" \
  "select id, coalesce(name->>'zh_CN', name->>'en_US', name::text) as name from project_project where coalesce(name->>'zh_CN', name->>'en_US', name::text) like '展厅-%' order by id;"

check "project 20 cockpit contracts ready" \
  "select case when count(*) >= 2 then 'ok' else 'project20 contracts < 2' end from construction_contract where project_id = 20;" \
  "select id, subject, type, state, amount_total from construction_contract where project_id = 20 order by id;"

check "project 20 cockpit cost ledger ready" \
  "select case when count(*) >= 4 then 'ok' else 'project20 cost_ledger < 4' end from project_cost_ledger where project_id = 20;" \
  "select id, period, amount, note from project_cost_ledger where project_id = 20 order by id;"

check "project 20 cockpit payment requests ready" \
  "select case when count(*) >= 4 then 'ok' else 'project20 payment < 4' end from payment_request where project_id = 20;" \
  "select id, name, type, state, amount from payment_request where project_id = 20 order by id;"

check "release role users complete" \
  "select case when count(*) = 6 then 'ok' else 'release users missing' end from res_users where login in ('demo_pm','demo_finance','demo_cost','demo_audit','demo_readonly','svc_e2e_smoke');" \
  "select id, login, active from res_users where login in ('demo_pm','demo_finance','demo_cost','demo_audit','demo_readonly','svc_e2e_smoke') order by login;"

echo "[OK] verify.demo.release.seed done"

