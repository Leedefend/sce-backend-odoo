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
from pathlib import Path

from odoo.exceptions import ValidationError
from odoo.addons.smart_enterprise_base.core_extension import smart_core_extend_system_init
from odoo.tools.safe_eval import safe_eval

OUT_JSON = Path("/mnt/artifacts/backend/company_department_guard.json")
OUT_MD = Path("/mnt/artifacts/backend/company_department_guard.md")

Company = env["res.company"].sudo()
Department = env["hr.department"].sudo()
User = env["res.users"].sudo()

company_action = env.ref("smart_enterprise_base.action_enterprise_company", raise_if_not_found=False)
department_action = env.ref("smart_enterprise_base.action_enterprise_department", raise_if_not_found=False)
user_action = env.ref("smart_enterprise_base.action_enterprise_user", raise_if_not_found=False)
company_tree_view = env.ref("smart_enterprise_base.view_company_tree_enterprise_base", raise_if_not_found=False)
company_form_view = env.ref("smart_enterprise_base.view_company_form_enterprise_base", raise_if_not_found=False)
company_menu = env.ref("smart_enterprise_base.menu_enterprise_company", raise_if_not_found=False)
department_menu = env.ref("smart_enterprise_base.menu_enterprise_department", raise_if_not_found=False)
user_menu = env.ref("smart_enterprise_base.menu_enterprise_user", raise_if_not_found=False)

company = Company.create(
    {
        "name": "Sprint0 启动公司",
        "sc_short_name": "Sprint0",
        "sc_credit_code": "S0-CREDIT-001",
        "sc_contact_phone": "021-00000000",
        "sc_address": "Shanghai",
        "sc_is_active": True,
    }
)
company.write({"sc_short_name": "Sprint0 Updated"})
env.user.write({"company_ids": [(4, company.id)]})

department_entry = company.action_open_enterprise_departments()

root_dept = Department.create(
    {
        "name": "综合管理部",
        "company_id": company.id,
        "sc_manager_user_id": env.user.id,
        "sc_is_active": True,
    }
)
child_dept = Department.create(
    {
        "name": "工程管理部",
        "parent_id": root_dept.id,
        "company_id": company.id,
        "sc_manager_user_id": env.user.id,
        "sc_is_active": True,
    }
)
grandchild_dept = Department.create(
    {
        "name": "施工执行组",
        "parent_id": child_dept.id,
        "company_id": company.id,
        "sc_manager_user_id": env.user.id,
        "sc_is_active": True,
    }
)

user_entry = child_dept.action_open_enterprise_users()
scoped_user = User.with_context(no_reset_password=True).create(
    {
        "name": "Sprint0 启动用户",
        "login": "sprint0_user_guard@example.com",
        "phone": "13800000000",
        "company_id": company.id,
        "company_ids": [(6, 0, [company.id])],
        "sc_department_id": child_dept.id,
        "sc_manager_user_id": env.user.id,
        "active": True,
    }
)

other_company = Company.create({"name": "Sprint0 其他公司"})

manager_user = User.create(
    {
        "name": "Sprint0 部门负责人校验用户",
        "login": "sprint0_manager_guard@example.com",
        "company_id": env.company.id,
        "company_ids": [(6, 0, [env.company.id])],
    }
)

parent_company_error = False
try:
    Department.create(
        {
            "name": "跨公司部门",
            "parent_id": root_dept.id,
            "company_id": other_company.id,
        }
    )
except ValidationError:
    parent_company_error = True

manager_company_error = False
try:
    Department.create(
        {
            "name": "负责人错误部门",
            "company_id": company.id,
            "sc_manager_user_id": manager_user.id,
        }
    )
except ValidationError:
    manager_company_error = True

user_department_error = False
try:
    User.with_context(no_reset_password=True).create(
        {
            "name": "Sprint0 跨公司用户",
            "login": "sprint0_cross_company_user@example.com",
            "company_id": other_company.id,
            "company_ids": [(6, 0, [other_company.id])],
            "sc_department_id": child_dept.id,
        }
    )
except ValidationError:
    user_department_error = True

payload = {}
smart_core_extend_system_init(payload, env, env.user)
mainline = (((payload.get("ext_facts") or {}).get("enterprise_enablement") or {}).get("mainline") or {})
steps = mainline.get("steps") or []
company_action_context = safe_eval(company_action.context or "{}") if company_action else {}

report = {
    "status": "PASS",
    "company_id": int(company.id),
    "company_short_name": str(company.sc_short_name or ""),
    "company_active": bool(company.sc_is_active),
    "department_count": int(Department.search_count([("company_id", "=", company.id)])),
    "extension_modules": str(env["ir.config_parameter"].sudo().get_param("sc.core.extension_modules") or ""),
    "company_action_xmlid": company_action.get_external_id().get(company_action.id, "") if company_action else "",
    "company_action_view_id": int(company_action.view_id.id or 0) if company_action and company_action.view_id else 0,
    "company_action_form_view_ref": str((company_action_context or {}).get("form_view_ref") or "") if company_action else "",
    "department_action_xmlid": department_action.get_external_id().get(department_action.id, "") if department_action else "",
    "user_action_xmlid": user_action.get_external_id().get(user_action.id, "") if user_action else "",
    "company_menu_xmlid": company_menu.get_external_id().get(company_menu.id, "") if company_menu else "",
    "department_menu_xmlid": department_menu.get_external_id().get(department_menu.id, "") if department_menu else "",
    "user_menu_xmlid": user_menu.get_external_id().get(user_menu.id, "") if user_menu else "",
    "department_entry_name": str(department_entry.get("name") or ""),
    "user_entry_name": str(user_entry.get("name") or ""),
    "department_entry_domain": department_entry.get("domain") or [],
    "user_entry_domain": user_entry.get("domain") or [],
    "enablement_phase": str(mainline.get("phase") or ""),
    "enablement_step_count": int(len(steps)),
    "enablement_primary_action_id": int((mainline.get("primary_action") or {}).get("action_id") or 0),
    "parent_company_error": bool(parent_company_error),
    "manager_company_error": bool(manager_company_error),
    "user_department_error": bool(user_department_error),
    "root_department_id": int(root_dept.id),
    "child_department_id": int(child_dept.id),
    "grandchild_department_id": int(grandchild_dept.id),
    "grandchild_parent_id": int(grandchild_dept.parent_id.id or 0),
    "scoped_user_id": int(scoped_user.id),
    "scoped_user_department_id": int(scoped_user.sc_department_id.id or 0),
    "errors": [],
}

if not report["company_id"]:
    report["errors"].append("company should be created")
if report["company_short_name"] != "Sprint0 Updated":
    report["errors"].append("company should be writable")
if report["department_count"] < 3:
    report["errors"].append("department tree should contain at least 3 levels")
if report["company_action_xmlid"] != "smart_enterprise_base.action_enterprise_company":
    report["errors"].append("company action should exist in smart_enterprise_base")
if int(report["company_action_view_id"]) != int(company_tree_view.id or 0):
    report["errors"].append("company action should use enterprise company tree view")
if report["company_action_form_view_ref"] != "smart_enterprise_base.view_company_form_enterprise_base":
    report["errors"].append("company action should point to enterprise company form view")
if report["department_action_xmlid"] != "smart_enterprise_base.action_enterprise_department":
    report["errors"].append("department action should exist in smart_enterprise_base")
if report["user_action_xmlid"] != "smart_enterprise_base.action_enterprise_user":
    report["errors"].append("user action should exist in smart_enterprise_base")
if report["company_menu_xmlid"] != "smart_enterprise_base.menu_enterprise_company":
    report["errors"].append("company menu should exist in smart_enterprise_base")
if report["department_menu_xmlid"] != "smart_enterprise_base.menu_enterprise_department":
    report["errors"].append("department menu should exist in smart_enterprise_base")
if report["user_menu_xmlid"] != "smart_enterprise_base.menu_enterprise_user":
    report["errors"].append("user menu should exist in smart_enterprise_base")
if "smart_enterprise_base" not in [item.strip() for item in str(report["extension_modules"]).split(",") if item.strip()]:
    report["errors"].append("sc.core.extension_modules should include smart_enterprise_base")
if int((department_entry.get("context") or {}).get("default_company_id") or 0) != int(company.id):
    report["errors"].append("company form should point next step to department entry")
if int((user_entry.get("context") or {}).get("default_sc_department_id") or 0) != int(child_dept.id):
    report["errors"].append("department form should point next step to user entry")
if report["enablement_phase"] != "sprint0" or report["enablement_step_count"] < 3:
    report["errors"].append("enablement contract should expose company, department, and user steps")
if report["enablement_primary_action_id"] <= 0:
    report["errors"].append("enablement contract should expose primary frontend action target")
if not root_dept.company_id or not child_dept.company_id or not grandchild_dept.company_id:
    report["errors"].append("departments must all have company_id")
if int(child_dept.parent_id.id or 0) != int(root_dept.id):
    report["errors"].append("child department parent_id mismatch")
if int(grandchild_dept.parent_id.id or 0) != int(child_dept.id):
    report["errors"].append("grandchild department parent_id mismatch")
if not root_dept.sc_manager_user_id or not child_dept.sc_manager_user_id:
    report["errors"].append("department manager should be assignable")
if not report["parent_company_error"]:
    report["errors"].append("cross-company parent department should be blocked")
if not report["manager_company_error"]:
    report["errors"].append("department manager outside company should be blocked")
if int(scoped_user.company_id.id or 0) != int(company.id) or int(scoped_user.sc_department_id.id or 0) != int(child_dept.id):
    report["errors"].append("user should be assignable to company and department")
if not report["user_department_error"]:
    report["errors"].append("user department outside company should be blocked")

if report["errors"]:
    report["status"] = "FAIL"

OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
OUT_MD.parent.mkdir(parents=True, exist_ok=True)
OUT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
OUT_MD.write_text(
    "# Company Department Guard\n\n"
    f"- status: `{report['status']}`\n"
    f"- company_id: `{report['company_id']}`\n"
    f"- department_count: `{report['department_count']}`\n"
    f"- department_entry_name: `{report['department_entry_name']}`\n"
    f"- user_entry_name: `{report['user_entry_name']}`\n"
    f"- enablement_phase: `{report['enablement_phase']}`\n"
    f"- grandchild_parent_id: `{report['grandchild_parent_id']}`\n"
    + ("\n- errors:\n" + "\n".join(f"  - {item}" for item in report["errors"]) if report["errors"] else "\n"),
    encoding="utf-8",
)

if report["errors"]:
    print("[company_department_guard] FAIL")
    for item in report["errors"]:
        print(" - %s" % item)
    raise SystemExit(1)

print("[company_department_guard] PASS")
PY
