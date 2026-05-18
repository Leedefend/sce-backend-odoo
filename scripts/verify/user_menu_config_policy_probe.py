#!/usr/bin/env python3
"""Verify user-configurable menu policy surface and runtime overlay."""

from __future__ import annotations

import json

from odoo import SUPERUSER_ID, api
from odoo.addons.smart_core.adapters.nav_tree_cleaner import NavTreeCleaner
from odoo.addons.smart_core.adapters.odoo_nav_adapter import OdooNavAdapter
from odoo.addons.smart_core.app_config_engine.services.dispatchers.nav_dispatcher import NavDispatcher
from odoo.addons.smart_core.delivery.delivery_engine import DeliveryEngine
from odoo.addons.smart_core.handlers.system_init import _filter_nav_by_release_gate, _load_platform_release_gate


errors = []


def ref(xmlid):
    rec = env.ref(xmlid, raise_if_not_found=False)  # noqa: F821
    if not rec:
        errors.append({"missing_xmlid": xmlid})
    return rec


Policy = env["ui.menu.config.policy"].sudo()  # noqa: F821
action = ref("smart_core.action_ui_menu_config_policy")
menu = ref("smart_construction_core.menu_ui_menu_config_policy_business_config")
business_config_center = ref("smart_construction_core.menu_sc_business_config_center")
business_config_group = ref("smart_construction_core.group_sc_cap_business_config_admin")
smart_core_admin_group = ref("smart_core.group_smart_core_admin")
smart_core_business_config_group = ref("smart_core.group_smart_core_business_config_admin")

if menu and business_config_center and menu.parent_id != business_config_center:
    errors.append({"menu_parent": menu.parent_id.get_external_id(), "expected": business_config_center.get_external_id()})

if menu and business_config_group and business_config_group not in menu.groups_id:
    errors.append({"menu_missing_group": "smart_construction_core.group_sc_cap_business_config_admin"})

if action and smart_core_business_config_group and smart_core_business_config_group not in action.groups_id:
    errors.append({"action_missing_group": "smart_core.group_smart_core_business_config_admin"})

source = Policy._source_contract()
if "ui.menu.config.policy" not in (source.get("authorities") or []):
    errors.append({"source_authority_missing": source})

target_menu = ref("smart_construction_core.menu_sc_business_config_center")
hidden_menu = ref("smart_construction_core.menu_sc_config_center")

created = Policy.browse()
try:
    if target_menu:
        created |= Policy.create(
            {
                "menu_id": target_menu.id,
                "company_id": env.company.id,  # noqa: F821
                "custom_label": "业务配置中心",
                "sequence_override": 7,
                "visible": True,
            }
        )
    if hidden_menu:
        created |= Policy.create(
            {
                "menu_id": hidden_menu.id,
                "company_id": env.company.id,  # noqa: F821
                "visible": False,
            }
        )
    nav_fact = {
        "flat": [
            {"menu_id": target_menu.id, "name": target_menu.name, "title": target_menu.name, "sequence": 85, "children": []},
            {"menu_id": hidden_menu.id, "name": hidden_menu.name, "title": hidden_menu.name, "sequence": 95, "children": []},
        ],
        "tree": [
            {
                "menu_id": 0,
                "name": "root",
                "title": "root",
                "sequence": 1,
                "children": [
                    {"menu_id": target_menu.id, "name": target_menu.name, "title": target_menu.name, "sequence": 85, "children": []},
                    {"menu_id": hidden_menu.id, "name": hidden_menu.name, "title": hidden_menu.name, "sequence": 95, "children": []},
                ],
            }
        ],
    }
    overlaid, stats = Policy.apply_runtime_overlay(nav_fact, user=env.user)  # noqa: F821
    flat_by_id = {row.get("menu_id"): row for row in overlaid.get("flat", [])}
    if target_menu and flat_by_id.get(target_menu.id, {}).get("name") != "业务配置中心":
        errors.append({"overlay_rename_failed": flat_by_id.get(target_menu.id)})
    if target_menu and flat_by_id.get(target_menu.id, {}).get("sequence") != 7:
        errors.append({"overlay_sequence_failed": flat_by_id.get(target_menu.id)})
    if hidden_menu and hidden_menu.id in flat_by_id:
        errors.append({"overlay_hide_failed": flat_by_id.get(hidden_menu.id)})
    if (stats or {}).get("hidden_count", 0) < 1:
        errors.append({"overlay_hidden_count": stats})
finally:
    if created:
        created.unlink()
    env.cr.rollback()  # noqa: F821

wutao = env["res.users"].sudo().search([("login", "=", "wutao")], limit=1)  # noqa: F821
if not wutao:
    errors.append({"missing_user": "wutao"})
elif menu:
    wutao_env = env(user=wutao.id)  # noqa: F821
    su_env = api.Environment(env.cr, SUPERUSER_ID, dict(wutao_env.context or {}))  # noqa: F821
    nav_data, _nav_versions = NavDispatcher(wutao_env, su_env).build_nav(
        {"subject": "nav", "scene": "web", "root_xmlid": "smart_construction_core.menu_sc_root"}
    )
    native_nav = NavTreeCleaner().clean(nav_data.get("nav") or [])
    OdooNavAdapter().enrich(wutao_env, native_nav)
    delivery_payload = DeliveryEngine(wutao_env).build(
        data={},
        product_key="",
        edition_key="standard",
        base_product_key="",
        native_nav=native_nav,
    )
    release_gate = _load_platform_release_gate(
        wutao_env,
        product_key=str(delivery_payload.get("product_key") or "construction.standard"),
    )
    gated_nav, gate_meta = _filter_nav_by_release_gate(
        delivery_payload.get("nav") if isinstance(delivery_payload.get("nav"), list) else [],
        release_gate,
    )

    def flatten(nodes):
        out = []
        for node in nodes or []:
            if not isinstance(node, dict):
                continue
            out.append(node)
            out.extend(flatten(node.get("children") if isinstance(node.get("children"), list) else []))
        return out

    rows = [
        node
        for node in flatten(gated_nav)
        if node.get("menu_id") == menu.id
        or (isinstance(node.get("meta"), dict) and node["meta"].get("menu_id") == menu.id)
    ]
    if not rows:
        errors.append({"system_init_release_gate_missing_menu": menu.id, "gate_meta": gate_meta})

payload = {
    "status": "FAIL" if errors else "PASS",
    "mode": "user_menu_config_policy_probe",
    "model": "ui.menu.config.policy",
    "action_xmlid": "smart_core.action_ui_menu_config_policy",
    "menu_xmlid": "smart_construction_core.menu_ui_menu_config_policy_business_config",
    "errors": errors,
}
print("USER_MENU_CONFIG_POLICY_PROBE=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
if errors:
    raise SystemExit(1)
