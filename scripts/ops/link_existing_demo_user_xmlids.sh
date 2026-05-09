#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="${ROOT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
export ROOT_DIR

source "$ROOT_DIR/scripts/common/env.sh"
source "$ROOT_DIR/scripts/common/guard_prod.sh"
source "$ROOT_DIR/scripts/_lib/common.sh"

guard_prod_forbid

: "${DB_NAME:?DB_NAME required}"

compose ${COMPOSE_FILES} exec -T odoo sh -lc "odoo shell -d '${DB_NAME}' -c '${ODOO_CONF}'" <<'PY'
import json

module = "smart_construction_demo"
login_to_xmlid = {
    "demo_role_project_read": "user_demo_project_read",
    "demo_role_project_user": "user_demo_project_user",
    "demo_role_project_manager": "user_demo_project_manager",
    "svc_e2e_smoke": "user_demo_e2e_smoke",
    "demo_role_owner": "user_demo_role_owner",
    "demo_role_pm": "user_demo_role_pm",
    "demo_role_finance": "user_demo_role_finance",
    "demo_role_executive": "user_demo_role_executive",
}

Users = env["res.users"].sudo().with_context(active_test=False)
ModelData = env["ir.model.data"].sudo()

linked = []
skipped = []
for login, name in login_to_xmlid.items():
    user = Users.search([("login", "=", login)], limit=1)
    if not user:
        skipped.append({"login": login, "reason": "missing_user"})
        continue

    existing = ModelData.search([("module", "=", module), ("name", "=", name)], limit=1)
    if existing:
        if existing.model == "res.users" and existing.res_id == user.id:
            skipped.append({"login": login, "xmlid": f"{module}.{name}", "reason": "already_linked"})
            continue
        skipped.append(
            {
                "login": login,
                "xmlid": f"{module}.{name}",
                "reason": "xmlid_points_elsewhere",
                "model": existing.model,
                "res_id": existing.res_id,
            }
        )
        continue

    ModelData.create(
        {
            "module": module,
            "name": name,
            "model": "res.users",
            "res_id": user.id,
            "noupdate": True,
        }
    )
    linked.append({"login": login, "id": user.id, "xmlid": f"{module}.{name}"})

env.cr.commit()
print("[link_existing_demo_user_xmlids] PASS")
print(json.dumps({"db": env.cr.dbname, "linked": linked, "skipped": skipped}, ensure_ascii=False, indent=2))
PY
