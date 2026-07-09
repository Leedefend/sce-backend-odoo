# -*- coding: utf-8 -*-
"""Sync the product config-center menu baseline by XMLID.

Run with Odoo shell:

    DB_NAME=sc_demo bash scripts/ops/odoo_shell_exec.sh < scripts/ops/config_center_menu_baseline_sync.py
    APPLY=1 DB_NAME=sc_demo bash scripts/ops/odoo_shell_exec.sh < scripts/ops/config_center_menu_baseline_sync.py

This script intentionally uses XMLIDs as the authority. Database numeric IDs
are environment-local implementation details and must never be copied between
local, daily-dev, or production databases.
"""

from __future__ import annotations

import json
import os


APPLY = os.getenv("APPLY") == "1"

BUSINESS_CONFIG_GROUP = "smart_construction_core.group_sc_cap_business_config_admin"
SMART_CORE_BUSINESS_GROUP = "smart_core.group_smart_core_business_config_admin"
SMART_CORE_ADMIN_GROUP = "smart_core.group_smart_core_admin"

BUSINESS_CONFIG_GROUPS = (BUSINESS_CONFIG_GROUP,)
LOWCODE_GROUPS = (BUSINESS_CONFIG_GROUP, SMART_CORE_BUSINESS_GROUP, SMART_CORE_ADMIN_GROUP)

BASELINE = (
    {
        "xmlid": "smart_construction_core.menu_sc_business_config_center",
        "name": "配置中心",
        "parent_xmlid": "smart_construction_core.menu_sc_root",
        "sequence": 85,
        "action_xmlid": None,
        "group_xmlids": BUSINESS_CONFIG_GROUPS,
    },
    {
        "xmlid": "smart_construction_core.menu_sc_business_base_config_group",
        "name": "业务基础数据",
        "parent_xmlid": "smart_construction_core.menu_sc_business_config_center",
        "sequence": 10,
        "action_xmlid": None,
        "group_xmlids": BUSINESS_CONFIG_GROUPS,
    },
    {
        "xmlid": "smart_construction_core.menu_sc_lowcode_system_config_group",
        "name": "低代码系统配置",
        "parent_xmlid": "smart_construction_core.menu_sc_business_config_center",
        "sequence": 20,
        "action_xmlid": None,
        "group_xmlids": LOWCODE_GROUPS,
    },
    {
        "xmlid": "smart_construction_core.menu_sc_business_category",
        "name": "业务分类字典",
        "parent_xmlid": "smart_construction_core.menu_sc_business_base_config_group",
        "sequence": 5,
        "action_xmlid": "smart_construction_core.action_sc_business_category",
        "group_xmlids": BUSINESS_CONFIG_GROUPS,
    },
    {
        "xmlid": "smart_construction_core.menu_sc_approval_scope",
        "name": "审批岗位人员",
        "parent_xmlid": "smart_construction_core.menu_sc_business_base_config_group",
        "sequence": 30,
        "action_xmlid": "smart_construction_core.action_sc_approval_scope",
        "group_xmlids": BUSINESS_CONFIG_GROUPS,
    },
    {
        "xmlid": "smart_construction_core.menu_sc_approval_policy",
        "name": "审批配置",
        "parent_xmlid": "smart_construction_core.menu_sc_business_base_config_group",
        "sequence": 31,
        "action_xmlid": "smart_construction_core.action_sc_approval_policy",
        "group_xmlids": BUSINESS_CONFIG_GROUPS,
    },
    {
        "xmlid": "smart_construction_core.menu_sc_project_stage_requirement_items",
        "name": "阶段要求配置",
        "parent_xmlid": "smart_construction_core.menu_sc_business_base_config_group",
        "sequence": 40,
        "action_xmlid": "smart_construction_core.action_sc_project_stage_requirement_items",
        "group_xmlids": BUSINESS_CONFIG_GROUPS,
    },
    {
        "xmlid": "smart_construction_core.menu_sc_project_cost_code",
        "name": "预算类型",
        "parent_xmlid": "smart_construction_core.menu_sc_business_base_config_group",
        "sequence": 50,
        "action_xmlid": "smart_construction_core.action_project_cost_code",
        "group_xmlids": BUSINESS_CONFIG_GROUPS,
    },
    {
        "xmlid": "smart_construction_core.menu_sc_dictionary",
        "name": "数据字典",
        "parent_xmlid": "smart_construction_core.menu_sc_business_base_config_group",
        "sequence": 70,
        "action_xmlid": "smart_construction_core.action_sc_dictionary_manage",
        "group_xmlids": BUSINESS_CONFIG_GROUPS,
    },
    {
        "xmlid": "smart_construction_core.menu_sc_business_config_workbench",
        "name": "配置工作台",
        "parent_xmlid": "smart_construction_core.menu_sc_lowcode_system_config_group",
        "sequence": 5,
        "action_xmlid": "smart_construction_core.action_sc_business_config_workbench",
        "group_xmlids": LOWCODE_GROUPS,
    },
    {
        "xmlid": "smart_construction_core.menu_ui_menu_config_policy_business_config",
        "name": "菜单配置",
        "parent_xmlid": "smart_construction_core.menu_sc_lowcode_system_config_group",
        "sequence": 6,
        "action_xmlid": "smart_core.action_ui_menu_config_policy",
        "group_xmlids": LOWCODE_GROUPS,
    },
    {
        "xmlid": "smart_construction_core.menu_ui_form_field_policy_business_config",
        "name": "表单字段配置",
        "parent_xmlid": "smart_construction_core.menu_sc_lowcode_system_config_group",
        "sequence": 15,
        "action_xmlid": "smart_construction_core.action_ui_form_field_policy_business_config",
        "group_xmlids": BUSINESS_CONFIG_GROUPS,
    },
    {
        "xmlid": "smart_construction_core.menu_ui_form_custom_field_wizard_business_config",
        "name": "新增表单字段",
        "parent_xmlid": "smart_construction_core.menu_sc_lowcode_system_config_group",
        "sequence": 16,
        "action_xmlid": "smart_construction_core.action_ui_form_custom_field_wizard_business_config",
        "group_xmlids": BUSINESS_CONFIG_GROUPS,
    },
)


def _ref(xmlid):
    record = env.ref(xmlid, raise_if_not_found=False)  # noqa: F821
    return record if record and record.exists() else None


def _record_xmlid(record):
    if not record:
        return None
    xmlids = record.get_external_id()
    return xmlids.get(record.id)


def _action_ref_value(action):
    return "%s,%s" % (action._name, action.id)


def _current_action_value(menu):
    action = menu.action
    if not action:
        return False
    return _action_ref_value(action)


def _group_ids(xmlids, errors):
    groups = []
    for xmlid in xmlids:
        group = _ref(xmlid)
        if not group:
            errors.append({"xmlid": xmlid, "error": "missing_group"})
            continue
        groups.append(group.id)
    return sorted(groups)


def _desired_values(item, errors):
    parent = _ref(item["parent_xmlid"]) if item.get("parent_xmlid") else None
    if item.get("parent_xmlid") and not parent:
        errors.append({"xmlid": item["xmlid"], "error": "missing_parent", "parent_xmlid": item["parent_xmlid"]})
    action = _ref(item["action_xmlid"]) if item.get("action_xmlid") else None
    if item.get("action_xmlid") and not action:
        errors.append({"xmlid": item["xmlid"], "error": "missing_action", "action_xmlid": item["action_xmlid"]})
    group_ids = _group_ids(item.get("group_xmlids") or (), errors)
    return {
        "name": item["name"],
        "parent_id": parent.id if parent else False,
        "sequence": item["sequence"],
        "action": _action_ref_value(action) if action else False,
        "groups_id": group_ids,
        "active": True,
    }


def _diff_menu(menu, desired):
    diff = {}
    checks = {
        "name": menu.name or "",
        "parent_id": menu.parent_id.id if menu.parent_id else False,
        "sequence": menu.sequence,
        "action": _current_action_value(menu),
        "groups_id": sorted(menu.groups_id.ids),
        "active": bool(menu.active),
    }
    for field, current in checks.items():
        expected = desired[field]
        if current != expected:
            diff[field] = {"current": current, "expected": expected}
    return diff


def _write_menu(menu, desired):
    values = {
        "name": desired["name"],
        "parent_id": desired["parent_id"],
        "sequence": desired["sequence"],
        "action": desired["action"] or False,
        "groups_id": [(6, 0, desired["groups_id"])],
        "active": desired["active"],
    }
    menu.sudo().write(values)


def _baseline_state():
    rows = []
    for item in BASELINE:
        menu = _ref(item["xmlid"])
        rows.append(
            {
                "xmlid": item["xmlid"],
                "id": menu.id if menu else None,
                "name": menu.name if menu else None,
                "active": bool(menu.active) if menu else None,
                "parent_xmlid": _record_xmlid(menu.parent_id) if menu and menu.parent_id else None,
                "sequence": menu.sequence if menu else None,
                "action_xmlid": _record_xmlid(menu.action) if menu and menu.action else None,
                "group_xmlids": sorted(
                    xmlid
                    for xmlid in (
                        _record_xmlid(group)
                        for group in (menu.groups_id if menu else env["res.groups"])  # noqa: F821
                    )
                    if xmlid
                ),
            }
        )
    return rows


def main():
    errors = []
    changes = []
    for item in BASELINE:
        menu = _ref(item["xmlid"])
        if not menu:
            errors.append({"xmlid": item["xmlid"], "error": "missing_menu"})
            continue
        desired = _desired_values(item, errors)
        diff = _diff_menu(menu, desired)
        if not diff:
            continue
        changes.append({"xmlid": item["xmlid"], "id": menu.id, "diff": diff})
        if APPLY and not errors:
            _write_menu(menu, desired)

    if APPLY and not errors and changes:
        env.cr.commit()  # noqa: F821

    report = {
        "status": "error" if errors else "ok",
        "apply": APPLY,
        "changes_count": len(changes),
        "changes": changes,
        "errors": errors,
        "baseline_state": _baseline_state(),
    }
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))

    if errors:
        raise SystemExit(1)


main()
