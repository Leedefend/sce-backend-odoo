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

required_modules = [
    "smart_core",
    "smart_construction_core",
    "smart_construction_custom",
    "smart_construction_seed",
    "smart_construction_demo",
]
required_logins = [
    "demo_role_owner",
    "demo_role_pm",
    "demo_role_finance",
    "demo_role_executive",
]

mod_rows = env["ir.module.module"].sudo().search([("name", "in", required_modules)])
states = {m.name: m.state for m in mod_rows}
missing_modules = [name for name in required_modules if states.get(name) != "installed"]

users = env["res.users"].sudo().search([("login", "in", required_logins)])
by_login = {u.login: u for u in users}
missing_users = [login for login in required_logins if login not in by_login]
inactive_users = [u.login for u in users if not u.active]
role_smoke_password = os.getenv("ROLE_SMOKE_PASSWORD", "demo")
invalid_credentials = []
for login in required_logins:
    if login not in by_login:
        continue
    try:
        uid = env["res.users"].sudo().authenticate(env.cr.dbname, login, role_smoke_password, {})
    except Exception:
        uid = False
    if not uid:
        invalid_credentials.append(login)

sale_tax = env.ref("smart_construction_seed.tax_sale_9", raise_if_not_found=False)
purchase_tax = env.ref("smart_construction_seed.tax_purchase_13", raise_if_not_found=False)
has_app_menu_config = "app.menu.config" in env.registry

summary = {
    "db": env.cr.dbname,
    "module_states": states,
    "missing_modules": missing_modules,
    "missing_users": missing_users,
    "inactive_users": inactive_users,
    "invalid_credentials": invalid_credentials,
    "role_smoke_password": role_smoke_password,
    "has_app_menu_config": has_app_menu_config,
    "has_seed_tax_sale_9": bool(sale_tax),
    "has_seed_tax_purchase_13": bool(purchase_tax),
}

issues = []
if missing_modules:
    issues.append(
        "modules not installed: "
        + ",".join(missing_modules)
        + " | hint: make policy.ensure.role_surface_demo DB_NAME=%s AUTO_FIX_ROLE_SURFACE_DEMO=1"
        % env.cr.dbname
    )
if not has_app_menu_config:
    issues.append("model app.menu.config missing in registry | hint: make restart")
if not sale_tax or not purchase_tax:
    issues.append(
        "seed tax xmlids missing (smart_construction_seed.tax_sale_9/tax_purchase_13)"
        + " | hint: make policy.ensure.role_surface_demo DB_NAME=%s AUTO_FIX_ROLE_SURFACE_DEMO=1"
        % env.cr.dbname
    )
if missing_users:
    issues.append(
        "demo role users missing: "
        + ",".join(missing_users)
        + " | hint: make policy.ensure.role_surface_demo DB_NAME=%s AUTO_FIX_ROLE_SURFACE_DEMO=1"
        % env.cr.dbname
    )
if inactive_users:
    issues.append(
        "demo role users inactive: "
        + ",".join(inactive_users)
        + " | hint: make policy.ensure.role_surface_demo DB_NAME=%s AUTO_FIX_ROLE_SURFACE_DEMO=1"
        % env.cr.dbname
    )
if invalid_credentials:
    issues.append(
        "demo role users auth failed with ROLE_SMOKE_PASSWORD: "
        + ",".join(invalid_credentials)
        + " | hint: make policy.ensure.role_surface_demo DB_NAME=%s AUTO_FIX_ROLE_SURFACE_DEMO=1 ROLE_SMOKE_PASSWORD=<pwd>"
        % env.cr.dbname
    )

if issues:
    print("[role_surface_preflight] FAIL")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    for issue in issues:
        print("[role_surface_preflight] ISSUE:", issue)
    raise SystemExit(2)

print("[role_surface_preflight] PASS")
print(json.dumps(summary, ensure_ascii=False, indent=2))
PY
