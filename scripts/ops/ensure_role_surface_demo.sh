#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="${ROOT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
export ROOT_DIR

source "$ROOT_DIR/scripts/common/env.sh"
source "$ROOT_DIR/scripts/common/guard_prod.sh"
source "$ROOT_DIR/scripts/_lib/common.sh"

guard_prod_forbid

: "${DB_NAME:?DB_NAME required}"
ROLE_SMOKE_PASSWORD="${ROLE_SMOKE_PASSWORD:-demo}"

compose ${COMPOSE_FILES} exec -T odoo sh -lc "ROLE_SMOKE_PASSWORD='${ROLE_SMOKE_PASSWORD}' odoo shell -d '${DB_NAME}' -c '${ODOO_CONF}'" <<'PY'
import json
import os

pwd = os.getenv("ROLE_SMOKE_PASSWORD", "demo")
required_logins = [
    "demo_role_owner",
    "demo_role_pm",
    "demo_role_finance",
    "demo_role_executive",
]

users = env["res.users"].sudo().search([("login", "in", required_logins)])
by_login = {u.login: u for u in users}
missing = [login for login in required_logins if login not in by_login]
if missing:
    print("[policy.ensure.role_surface_demo] FAIL missing users:", ",".join(missing))
    raise SystemExit(2)

updated = []
for login in required_logins:
    user = by_login[login]
    vals = {}
    if not user.active:
        vals["active"] = True
    vals["password"] = pwd
    user.write(vals)
    updated.append({"login": login, "active": bool(user.active)})

print("[policy.ensure.role_surface_demo] PASS set role demo passwords")
print(json.dumps({"db": env.cr.dbname, "updated": updated}, ensure_ascii=False, indent=2))
PY
