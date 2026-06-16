# -*- coding: utf-8 -*-
"""Runtime audit for finance/interfund position business menus."""

from __future__ import annotations

import json
import os
from collections import OrderedDict
from pathlib import Path


def artifact_root() -> Path:
    raw = os.getenv("MIGRATION_ARTIFACT_ROOT") or os.getenv("FINANCE_INTERFUND_MENU_ARTIFACT_ROOT")
    candidates = [Path(raw)] if raw else []
    candidates.extend([Path("/mnt/artifacts/backend"), Path(f"/tmp/finance_interfund_position_menu/{env.cr.dbname}")])  # noqa: F821
    for candidate in candidates:
        try:
            candidate.mkdir(parents=True, exist_ok=True)
            probe = candidate / ".write_probe"
            probe.write_text("ok\n", encoding="utf-8")
            probe.unlink()
            return candidate
        except OSError:
            continue
    return Path("/tmp")


MODULE = "smart_construction_core"
PARENT_MENU = f"{MODULE}.menu_sc_finance_interfund_analysis"
EXPECTED_PARENT = f"{MODULE}.menu_sc_finance_center"
EXPECTED_GROUPS = {
    f"{MODULE}.group_sc_cap_finance_read",
    f"{MODULE}.group_sc_cap_finance_user",
    f"{MODULE}.group_sc_cap_finance_manager",
}

EXPECTED_MENUS = OrderedDict(
    [
        (
            f"{MODULE}.menu_sc_finance_project_capital_position",
            {
                "name": "项目资金总览",
                "action": f"{MODULE}.action_sc_finance_project_capital_position",
                "model": "sc.finance.project.capital.position",
            },
        ),
        (
            f"{MODULE}.menu_sc_finance_counterparty_position_summary",
            {
                "name": "往来对象资金总览",
                "action": f"{MODULE}.action_sc_finance_counterparty_position_summary",
                "model": "sc.finance.counterparty.position.summary",
            },
        ),
        (
            f"{MODULE}.menu_sc_finance_project_counterparty_position",
            {
                "name": "项目与对象资金往来",
                "action": f"{MODULE}.action_sc_finance_project_counterparty_position",
                "model": "sc.finance.project.counterparty.position",
            },
        ),
        (
            f"{MODULE}.menu_sc_company_contractor_responsibility_summary",
            {
                "name": "公司-承包人资金责任余额",
                "action": f"{MODULE}.action_sc_company_contractor_responsibility_summary",
                "model": "sc.company.contractor.responsibility.summary",
            },
        ),
        (
            f"{MODULE}.menu_sc_company_contractor_responsibility_fact",
            {
                "name": "公司-承包人资金责任明细",
                "action": f"{MODULE}.action_sc_company_contractor_responsibility_fact",
                "model": "sc.company.contractor.responsibility.fact",
            },
        ),
        (
            f"{MODULE}.menu_sc_finance_business_project_summary",
            {
                "name": "项目收付款汇总",
                "action": f"{MODULE}.action_sc_finance_business_project_summary",
                "model": "sc.finance.business.project.summary",
            },
        ),
        (
            f"{MODULE}.menu_sc_interfund_movement_project_summary",
            {
                "name": "项目借还调拨汇总",
                "action": f"{MODULE}.action_sc_interfund_movement_project_summary",
                "model": "sc.interfund.movement.project.summary",
            },
        ),
        (
            f"{MODULE}.menu_sc_finance_business_fact",
            {
                "name": "项目收付款来源明细",
                "action": f"{MODULE}.action_sc_finance_business_fact",
                "model": "sc.finance.business.fact",
            },
        ),
        (
            f"{MODULE}.menu_sc_interfund_movement_fact",
            {
                "name": "借款还款与调拨明细",
                "action": f"{MODULE}.action_sc_interfund_movement_fact",
                "model": "sc.interfund.movement.fact",
            },
        ),
    ]
)
EXPECTED_PRODUCT_MENU_XMLIDS = (
    f"{MODULE}.menu_sc_finance_project_capital_position",
    f"{MODULE}.menu_sc_finance_counterparty_position_summary",
    f"{MODULE}.menu_sc_finance_project_counterparty_position",
    f"{MODULE}.menu_sc_company_contractor_responsibility_summary",
    f"{MODULE}.menu_sc_company_contractor_responsibility_fact",
)
PRODUCT_KEYS = ("construction.standard", "construction.preview")
VISIBLE_CHECK_USERS = ("wutao", "demo_role_project_read", "sc_fx_pm")


def ref_or_error(xmlid, errors, key):
    try:
        return env.ref(xmlid)  # noqa: F821
    except ValueError:
        errors.append({"key": key, "xmlid": xmlid})
        return None


def action_signature(action):
    if not action:
        return ""
    return f"{action._name},{action.id}"


errors = []
summary = OrderedDict()

parent = ref_or_error(PARENT_MENU, errors, "missing_parent_menu")
expected_parent = ref_or_error(EXPECTED_PARENT, errors, "missing_expected_parent_menu")
if parent:
    parent_groups = set(parent.groups_id.get_external_id().values())
    summary["parent_menu"] = OrderedDict(
        [
            ("xmlid", PARENT_MENU),
            ("name", parent.name),
            ("active", bool(parent.active)),
            ("parent", parent.parent_id.get_external_id().get(parent.parent_id.id, "")),
            ("groups", sorted(parent_groups)),
        ]
    )
    if not parent.active:
        errors.append({"key": "parent_menu_inactive", "menu": PARENT_MENU})
    if expected_parent and parent.parent_id != expected_parent:
        errors.append(
            {
                "key": "parent_menu_wrong_parent",
                "menu": PARENT_MENU,
                "expected": EXPECTED_PARENT,
                "actual": parent.parent_id.get_external_id().get(parent.parent_id.id, ""),
            }
        )
    if not EXPECTED_GROUPS.issubset(parent_groups):
        errors.append(
            {
                "key": "parent_menu_missing_finance_groups",
                "menu": PARENT_MENU,
                "expected_subset": sorted(EXPECTED_GROUPS),
                "actual": sorted(parent_groups),
            }
        )

menu_rows = []
for menu_xmlid, spec in EXPECTED_MENUS.items():
    menu = ref_or_error(menu_xmlid, errors, "missing_business_menu")
    action = ref_or_error(spec["action"], errors, "missing_business_action")
    model_count = env[spec["model"]].sudo().search_count([])  # noqa: F821
    row = OrderedDict(
        [
            ("menu", menu_xmlid),
            ("expected_name", spec["name"]),
            ("action", spec["action"]),
            ("model", spec["model"]),
            ("model_count", int(model_count or 0)),
        ]
    )
    if menu:
        actual_parent = menu.parent_id.get_external_id().get(menu.parent_id.id, "")
        actual_groups = set(menu.groups_id.get_external_id().values())
        row.update(
            [
                ("actual_name", menu.name),
                ("active", bool(menu.active)),
                ("parent", actual_parent),
                ("actual_action", action_signature(menu.action)),
                ("groups", sorted(actual_groups)),
            ]
        )
        if menu.name != spec["name"]:
            errors.append({"key": "business_menu_wrong_name", "menu": menu_xmlid, "expected": spec["name"], "actual": menu.name})
        if not menu.active:
            errors.append({"key": "business_menu_inactive", "menu": menu_xmlid})
        if parent and menu.parent_id != parent:
            errors.append({"key": "business_menu_wrong_parent", "menu": menu_xmlid, "expected": PARENT_MENU, "actual": actual_parent})
        if action and (menu.action._name != action._name or menu.action.id != action.id):
            errors.append(
                {
                    "key": "business_menu_wrong_action",
                    "menu": menu_xmlid,
                    "expected": action_signature(action),
                    "actual": action_signature(menu.action),
                }
            )
        if not EXPECTED_GROUPS.issubset(actual_groups):
            errors.append(
                {
                    "key": "business_menu_missing_finance_groups",
                    "menu": menu_xmlid,
                    "expected_subset": sorted(EXPECTED_GROUPS),
                    "actual": sorted(actual_groups),
                }
            )
    if action and action.res_model != spec["model"]:
        errors.append({"key": "business_action_wrong_model", "action": spec["action"], "expected": spec["model"], "actual": action.res_model})
    if int(model_count or 0) <= 0:
        errors.append({"key": "business_menu_model_empty", "menu": menu_xmlid, "model": spec["model"]})
    menu_rows.append(row)

summary["business_menus"] = menu_rows

product_rows = []
for product_key in PRODUCT_KEYS:
    policy = env["sc.product.policy"].sudo().search([("product_key", "=", product_key)], limit=1)  # noqa: F821
    if not policy:
        errors.append({"key": "missing_product_policy", "product_key": product_key})
        continue
    released = {}
    for group in policy.menu_groups or []:
        if not isinstance(group, dict):
            continue
        group_label = str(group.get("group_label") or group.get("label") or "").strip()
        for menu in group.get("menus") or []:
            if not isinstance(menu, dict):
                continue
            xmlid = str(menu.get("menu_xmlid") or menu.get("page_key") or menu.get("menu_key") or "").strip()
            if xmlid in EXPECTED_PRODUCT_MENU_XMLIDS:
                released[xmlid] = {
                    "group": group_label,
                    "label": str(menu.get("label") or "").strip(),
                    "enabled": bool(menu.get("enabled")),
                    "release_state": str(menu.get("release_state") or "").strip(),
                    "release_domain": str(menu.get("release_domain") or "").strip(),
                }
    missing = [xmlid for xmlid in EXPECTED_PRODUCT_MENU_XMLIDS if xmlid not in released]
    if missing:
        errors.append({"key": "product_policy_missing_finance_interfund_menus", "product_key": product_key, "missing": missing})
    for xmlid, row in released.items():
        if row["group"] != "财务中心":
            errors.append({"key": "product_policy_wrong_group", "product_key": product_key, "menu": xmlid, "actual": row["group"]})
        if not row["enabled"] or row["release_state"] != "released":
            errors.append({"key": "product_policy_menu_not_released", "product_key": product_key, "menu": xmlid, "actual": row})
        if row["release_domain"] != "finance_interfund_analysis":
            errors.append({"key": "product_policy_wrong_release_domain", "product_key": product_key, "menu": xmlid, "actual": row["release_domain"]})
    product_rows.append({"product_key": product_key, "released": released})
summary["product_policy"] = product_rows

visible_by_login = {}
visible_logins_by_menu = {xmlid: [] for xmlid in EXPECTED_PRODUCT_MENU_XMLIDS}
for login in VISIBLE_CHECK_USERS:
    user = env["res.users"].sudo().search([("login", "=", login)], limit=1)  # noqa: F821
    if not user:
        continue
    visible_ids = set(env["ir.ui.menu"].with_user(user)._visible_menu_ids())  # noqa: F821
    visible_by_login[login] = len(visible_ids)
    for xmlid in EXPECTED_PRODUCT_MENU_XMLIDS:
        menu = env.ref(xmlid, raise_if_not_found=False)  # noqa: F821
        if menu and int(menu.id) in visible_ids:
            visible_logins_by_menu.setdefault(xmlid, []).append(login)
for xmlid, logins in visible_logins_by_menu.items():
    if not logins:
        errors.append({"key": "finance_interfund_product_menu_not_visible_to_any_check_user", "menu": xmlid})
summary["visible_check_users"] = visible_by_login
summary["visible_logins_by_product_menu"] = visible_logins_by_menu

access_rows = []
for login in VISIBLE_CHECK_USERS:
    user = env["res.users"].sudo().search([("login", "=", login)], limit=1)  # noqa: F821
    if not user:
        continue
    user_models = []
    for spec in EXPECTED_MENUS.values():
        model = env[spec["model"]].with_user(user)  # noqa: F821
        can_read = bool(model.check_access_rights("read", raise_exception=False))
        can_write = bool(model.check_access_rights("write", raise_exception=False))
        row = {"model": spec["model"], "read": can_read, "write": can_write}
        user_models.append(row)
        if can_read and not can_write:
            errors.append(
                {
                    "key": "finance_interfund_projection_missing_write_acl_for_page_load",
                    "login": login,
                    "model": spec["model"],
                }
            )
    access_rows.append({"login": login, "models": user_models})
summary["projection_access_rights_for_page_load"] = access_rows

result = OrderedDict(
    [
        ("status", "PASS" if not errors else "FAIL"),
        ("database", env.cr.dbname),  # noqa: F821
        ("summary", summary),
        ("errors", errors),
    ]
)

target = artifact_root() / f"finance_interfund_position_menu_runtime_audit_{env.cr.dbname}.json"  # noqa: F821
target.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(result, ensure_ascii=False, indent=2))
if errors:
    raise SystemExit(1)
