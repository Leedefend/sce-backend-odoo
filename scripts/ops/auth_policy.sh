#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   scripts/ops/auth_policy.sh apply   -p <compose_project> -d <db>
#   scripts/ops/auth_policy.sh rollback -p <compose_project> -d <db>
#   scripts/ops/auth_policy.sh verify  -p <compose_project> -d <db>
#
# Example:
#   scripts/ops/auth_policy.sh apply   -p sc-backend-odoo-prod -d sc_prod

ACTION="${1:-}"
shift || true

PROJECT="sc-backend-odoo-prod"
DB="sc_prod"

while [[ $# -gt 0 ]]; do
  case "$1" in
    -p|--project) PROJECT="$2"; shift 2;;
    -d|--db) DB="$2"; shift 2;;
    *) echo "Unknown arg: $1" >&2; exit 2;;
  esac
done

psql_exec() {
  local sql="$1"
  docker compose -p "$PROJECT" exec -T db psql -U odoo -d "$DB" -v ON_ERROR_STOP=1 -q -c "$sql"
}

apply_policy() {
  # Align with dev: open signup + reset enabled + signup mode=open
  psql_exec "
INSERT INTO ir_config_parameter(key,value) VALUES
  ('auth_signup.allow_uninvited','True'),
  ('auth_signup.reset_password','True'),
  ('sc.signup.mode','open')
ON CONFLICT (key) DO UPDATE SET value=EXCLUDED.value;
"
}

rollback_policy() {
  # Roll back to prod: invite-only + disallow open signup (delete allow_uninvited = False)
  psql_exec "
DELETE FROM ir_config_parameter WHERE key='auth_signup.allow_uninvited';
INSERT INTO ir_config_parameter(key,value) VALUES
  ('auth_signup.reset_password','True'),
  ('sc.signup.mode','invite')
ON CONFLICT (key) DO UPDATE SET value=EXCLUDED.value;
"
}

verify_policy() {
  psql_exec "
SELECT key, value
FROM ir_config_parameter
WHERE key IN (
  'auth_signup.allow_uninvited',
  'auth_signup.reset_password',
  'sc.signup.mode'
)
ORDER BY key;
"
  # Additional: verify routes are reachable (inside odoo container)
  docker compose -p "$PROJECT" exec -T odoo sh -lc "
set -e
for u in /web/signup /web/reset_password '/web/login?signup=1' '/web/login?reset_password=1'; do
  echo \"==> \$u\"
  curl -I -s http://127.0.0.1:8069\$u | head -n 3
  echo
done
"
}

case "$ACTION" in
  apply) apply_policy;;
  rollback) rollback_policy;;
  verify) verify_policy;;
  *)
    echo "Usage: $0 {apply|rollback|verify} -p <compose_project> -d <db>" >&2
    exit 2
    ;;
esac
