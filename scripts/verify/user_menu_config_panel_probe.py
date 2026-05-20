#!/usr/bin/env python3
"""Verify the dedicated menu configuration panel intents."""

from __future__ import annotations

import json

from odoo.addons.smart_core.core.handler_registry import HANDLER_REGISTRY


errors = []


def ref(xmlid):
    rec = env.ref(xmlid, raise_if_not_found=False)  # noqa: F821
    if not rec:
        errors.append({"missing_xmlid": xmlid})
    return rec


panel_user = ref("base.user_admin")
panel_group = ref("smart_core.group_smart_core_business_config_admin")
if panel_user and panel_group and panel_group not in panel_user.sudo().groups_id:
    panel_user.sudo().write({"groups_id": [(4, panel_group.id)]})
panel_env = env(user=panel_user.id) if panel_user else env  # noqa: F821


def _data(result):
    if not isinstance(result, dict):
        return {}
    data = result.get("data")
    return data if isinstance(data, dict) else {}


def _meta(result):
    if not isinstance(result, dict):
        return {}
    meta = result.get("meta")
    return meta if isinstance(meta, dict) else {}


def _panel_call(intent, params):
    handler = HANDLER_REGISTRY.get(intent)
    if not handler:
        errors.append({"missing_handler": intent})
        return {}
    payload = {"intent": intent, "params": params}
    result = handler(panel_env, payload=payload).run(payload=payload)
    if _meta(result).get("intent") != intent:
        errors.append({"intent_meta_mismatch": intent, "meta": _meta(result)})
    return result


Policy = panel_env["ui.menu.config.policy"].sudo().with_context(active_test=False)
Menu = panel_env["ir.ui.menu"].sudo().with_context(active_test=False)
root_menu = ref("smart_construction_core.menu_sc_root")
target_parent = Menu.search([("parent_id", "=", root_menu.id if root_menu else False)], order="sequence, id", limit=1) if root_menu else Menu.browse()
menu = Menu.search([("parent_id", "=", target_parent.id if target_parent else False)], order="sequence, id", limit=1) if target_parent else Menu.browse()
if not menu:
    menu = target_parent
    target_parent = root_menu
business_config_group = ref("smart_core.group_smart_core_business_config_admin")

created = Policy.browse()
try:
    if menu:
        get_result = _panel_call("ui.menu_config.panel.get", {"menu_ids": [menu.id]})
        get_data = _data(get_result)
        menu_rows = get_data.get("menus") if isinstance(get_data.get("menus"), list) else []
        tree_rows = get_data.get("tree") if isinstance(get_data.get("tree"), list) else []
        groups = get_data.get("groups") if isinstance(get_data.get("groups"), list) else []
        source = _meta(get_result).get("source_authority") if isinstance(_meta(get_result).get("source_authority"), dict) else {}

        if menu.id not in {int(row.get("menu_id") or 0) for row in menu_rows if isinstance(row, dict)}:
            errors.append({
                "panel_get_missing_requested_menu": menu.id,
                "menu_count": len(menu_rows),
                "returned": [
                    {
                        "menu_id": row.get("menu_id"),
                        "name": row.get("name"),
                        "xmlid": row.get("xmlid"),
                        "parent_id": row.get("parent_id"),
                    }
                    for row in menu_rows
                    if isinstance(row, dict)
                ],
            })
        if not tree_rows:
            errors.append({"panel_get_empty_tree": {"menu_count": len(menu_rows)}})
        if not groups:
            errors.append({"panel_get_empty_groups": True})
        if source.get("kind") != "ui_menu_config_panel_projection":
            errors.append({"panel_get_source_kind": source})
        if "ui.menu.config.policy" not in (source.get("authorities") or []):
            errors.append({"panel_get_source_authority_missing_policy": source})

        save_result = _panel_call(
            "ui.menu_config.panel.set",
            {
                "rows": [
                    {
                        "menu_id": menu.id,
                        "target_parent_menu_id": target_parent.id if target_parent else 0,
                        "custom_label": "菜单配置面板探针",
                        "sequence_override": 11,
                        "visible": True,
                        "role_group_ids": [business_config_group.id] if business_config_group else [],
                        "note": "runtime panel probe",
                    }
                ]
            },
        )
        save_data = _data(save_result)
        saved = save_data.get("saved") if isinstance(save_data.get("saved"), list) else []
        save_source = _meta(save_result).get("source_authority") if isinstance(_meta(save_result).get("source_authority"), dict) else {}
        if save_data.get("saved_count") != 1 or len(saved) != 1:
            errors.append({"panel_set_saved_count": save_data})
        if save_source.get("kind") != "ui_menu_config_panel_write_proxy" or not save_source.get("write_proxy"):
            errors.append({"panel_set_source_authority": save_source})

        created = Policy.search([
            ("company_id", "=", panel_env.company.id),
            ("menu_id", "=", menu.id),
        ], order="id desc", limit=1)
        if not created:
            errors.append({"panel_set_policy_not_created": menu.id})
        else:
            if created.custom_label != "菜单配置面板探针":
                errors.append({"panel_set_label_mismatch": created.custom_label})
            if int(created.sequence_override or 0) != 11:
                errors.append({"panel_set_sequence_mismatch": int(created.sequence_override or 0)})
            if business_config_group and business_config_group.id not in created.role_group_ids.ids:
                errors.append({"panel_set_role_groups_mismatch": created.role_group_ids.ids})

        reread = _panel_call("ui.menu_config.panel.get", {"menu_ids": [menu.id]})
        reread_policies = _data(reread).get("policies") if isinstance(_data(reread).get("policies"), dict) else {}
        policy_payload = reread_policies.get(str(menu.id)) or reread_policies.get(menu.id)
        if not isinstance(policy_payload, dict):
            errors.append({"panel_get_missing_saved_policy": reread_policies})
        elif policy_payload.get("custom_label") != "菜单配置面板探针":
            errors.append({"panel_get_saved_policy_label": policy_payload})
finally:
    if created:
        created.unlink()
    env.cr.rollback()  # noqa: F821


payload = {
    "status": "FAIL" if errors else "PASS",
    "mode": "user_menu_config_panel_probe",
    "model": "ui.menu.config.policy",
    "get_intent": "ui.menu_config.panel.get",
    "set_intent": "ui.menu_config.panel.set",
    "errors": errors,
}
print("USER_MENU_CONFIG_PANEL_PROBE=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
if errors:
    raise SystemExit(1)
