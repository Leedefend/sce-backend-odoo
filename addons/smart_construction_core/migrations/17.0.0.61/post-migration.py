# -*- coding: utf-8 -*-
from __future__ import annotations

import json

from odoo import SUPERUSER_ID, api
from odoo.addons.smart_core.utils.backend_contract_boundaries import MENU_CONFIG_POLICY_MODEL

OLD_CONFIG_LABELS = {"基础设置", "系统设置", "业务配置"}
CONFIG_CENTER_LABEL = "配置中心"
CONFIG_WORKBENCH_LABEL = "配置工作台"
CONFIG_CENTER_XMLID = "smart_construction_core.menu_sc_business_config_center"
CONFIG_WORKBENCH_XMLID = "smart_construction_core.menu_sc_business_config_workbench"


def _replace_path_label(value):
    text = str(value or "")
    if not text:
        return value
    for old_label in OLD_CONFIG_LABELS:
        text = text.replace("/%s/" % old_label, "/%s/" % CONFIG_CENTER_LABEL)
        if text.endswith("/%s" % old_label):
            text = "%s/%s" % (text[: -(len(old_label) + 1)], CONFIG_CENTER_LABEL)
    return text


def _replace_effect_summary(value):
    text = str(value or "")
    if not text:
        return value
    for old_label in OLD_CONFIG_LABELS:
        text = text.replace("智慧施工管理平台/%s" % old_label, "智慧施工管理平台/%s" % CONFIG_CENTER_LABEL)
        text = text.replace("显示为：%s" % old_label, "显示为：%s" % CONFIG_CENTER_LABEL)
    return text


def _normalize_contract_payload(payload, *, config_menu_id, workbench_menu_id):
    if not isinstance(payload, dict):
        return payload, False
    next_payload = dict(payload)
    orchestration = next_payload.get("menu_orchestration")
    if not isinstance(orchestration, dict):
        return payload, False
    next_orchestration = dict(orchestration)
    policies = next_orchestration.get("policies")
    if not isinstance(policies, list):
        return payload, False

    changed = False
    next_policies = []
    for row in policies:
        if not isinstance(row, dict):
            next_policies.append(row)
            continue
        next_row = dict(row)
        menu_id = int(next_row.get("menu_id") or 0)

        if menu_id == config_menu_id:
            if next_row.get("custom_label") != CONFIG_CENTER_LABEL:
                next_row["custom_label"] = CONFIG_CENTER_LABEL
                changed = True
            if next_row.get("menu_label") in OLD_CONFIG_LABELS:
                next_row["menu_label"] = CONFIG_CENTER_LABEL
                changed = True

        if int(next_row.get("target_parent_menu_id") or 0) == config_menu_id:
            if next_row.get("target_parent_label") != "智慧施工管理平台/%s" % CONFIG_CENTER_LABEL:
                next_row["target_parent_label"] = "智慧施工管理平台/%s" % CONFIG_CENTER_LABEL
                changed = True

        if menu_id == workbench_menu_id and next_row.get("custom_label") in {"业务配置工作台", "业务配置", ""}:
            next_row["custom_label"] = CONFIG_WORKBENCH_LABEL
            changed = True

        for key in ("menu_complete_name", "effect_summary"):
            original = next_row.get(key)
            updated = _replace_effect_summary(original) if key == "effect_summary" else _replace_path_label(original)
            if updated != original:
                next_row[key] = updated
                changed = True
        next_policies.append(next_row)

    if not changed:
        return payload, False
    next_orchestration["policies"] = next_policies
    next_payload["menu_orchestration"] = next_orchestration
    return next_payload, True


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    config_menu = env.ref(CONFIG_CENTER_XMLID, raise_if_not_found=False)
    workbench_menu = env.ref(CONFIG_WORKBENCH_XMLID, raise_if_not_found=False)
    if not config_menu:
        print("[17.0.0.61] config center menu not found; skipped")
        return

    Policy = env[MENU_CONFIG_POLICY_MODEL].sudo().with_context(active_test=False)
    policy_updates = 0
    for policy in Policy.search([("menu_id", "=", config_menu.id)]):
        values = {}
        if policy.custom_label != CONFIG_CENTER_LABEL:
            values["custom_label"] = CONFIG_CENTER_LABEL
        if values:
            policy.write(values)
            policy_updates += 1

    contract_updates = 0
    Contract = env["ui.business.config.contract"].sudo().with_context(active_test=False)
    for rec in Contract.search([("name", "=", "menu.config.company.1")], order="id"):
        payload, changed = _normalize_contract_payload(
            rec.contract_json if isinstance(rec.contract_json, dict) else {},
            config_menu_id=config_menu.id,
            workbench_menu_id=workbench_menu.id if workbench_menu else 0,
        )
        if not changed:
            continue
        cr.execute(
            """
            UPDATE ui_business_config_contract
               SET contract_json = %s::jsonb,
                   write_date = NOW()
             WHERE id = %s
            """,
            (json.dumps(payload, ensure_ascii=False), rec.id),
        )
        contract_updates += 1

    stale_contract_updates = 0
    stale_contracts = Contract.search([
        ("action_id", "!=", False),
        ("active", "=", True),
        ("status", "=", "published"),
        ("view_type", "in", ["form", "tree", "list", "search", "pivot", "graph"]),
    ])
    for rec in stale_contracts:
        action_model = str(getattr(rec.action_id, "res_model", "") or "").strip()
        contract_model = str(rec.model or "").strip()
        if not action_model or not contract_model or action_model == contract_model:
            continue
        rec.write({"active": False})
        stale_contract_updates += 1

    print(
        "[17.0.0.61] config center menu baseline normalized: policies=%s contracts=%s stale_contracts_archived=%s"
        % (policy_updates, contract_updates, stale_contract_updates)
    )
