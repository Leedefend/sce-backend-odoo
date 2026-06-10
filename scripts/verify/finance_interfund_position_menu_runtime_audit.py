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
                "name": "项目资金综合口径",
                "action": f"{MODULE}.action_sc_finance_project_capital_position",
                "model": "sc.finance.project.capital.position",
            },
        ),
        (
            f"{MODULE}.menu_sc_finance_counterparty_position_summary",
            {
                "name": "往来对象资金综合口径",
                "action": f"{MODULE}.action_sc_finance_counterparty_position_summary",
                "model": "sc.finance.counterparty.position.summary",
            },
        ),
        (
            f"{MODULE}.menu_sc_finance_project_counterparty_position",
            {
                "name": "项目往来对象资金口径",
                "action": f"{MODULE}.action_sc_finance_project_counterparty_position",
                "model": "sc.finance.project.counterparty.position",
            },
        ),
        (
            f"{MODULE}.menu_sc_finance_business_project_summary",
            {
                "name": "项目财务业务事实汇总",
                "action": f"{MODULE}.action_sc_finance_business_project_summary",
                "model": "sc.finance.business.project.summary",
            },
        ),
        (
            f"{MODULE}.menu_sc_interfund_movement_project_summary",
            {
                "name": "项目资金往来事实汇总",
                "action": f"{MODULE}.action_sc_interfund_movement_project_summary",
                "model": "sc.interfund.movement.project.summary",
            },
        ),
        (
            f"{MODULE}.menu_sc_finance_business_fact",
            {
                "name": "财务业务事实明细",
                "action": f"{MODULE}.action_sc_finance_business_fact",
                "model": "sc.finance.business.fact",
            },
        ),
        (
            f"{MODULE}.menu_sc_interfund_movement_fact",
            {
                "name": "资金往来事实明细",
                "action": f"{MODULE}.action_sc_interfund_movement_fact",
                "model": "sc.interfund.movement.fact",
            },
        ),
    ]
)


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
