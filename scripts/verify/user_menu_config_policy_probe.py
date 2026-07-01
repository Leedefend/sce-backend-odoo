#!/usr/bin/env python3
"""Verify user-configurable menu policy surface and runtime overlay."""

from __future__ import annotations

import json

from odoo import SUPERUSER_ID, api
from odoo.addons.smart_core.adapters.nav_tree_cleaner import NavTreeCleaner
from odoo.addons.smart_core.adapters.odoo_nav_adapter import OdooNavAdapter
from odoo.addons.smart_core.app_config_engine.services.dispatchers.nav_dispatcher import NavDispatcher
from odoo.addons.smart_core.delivery.delivery_engine import DeliveryEngine
from odoo.addons.smart_core.handlers.api_onchange import ApiOnchangeHandler
from odoo.addons.smart_core.handlers.menu_configuration import _menu_config_contract_json
from odoo.addons.smart_core.handlers.system_init import (
    _apply_user_menu_config_to_delivery_nav,
    _filter_nav_by_release_gate,
    _load_platform_release_gate,
)


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


def publish_temp_menu_contract(policies):
    Contract = env["ui.business.config.contract"].sudo()  # noqa: F821
    company_id = int(env.company.id or 0)  # noqa: F821
    values = {
        "name": "menu.config.company.%s" % company_id,
        "model": "ir.ui.menu",
        "company_id": company_id,
        "active": True,
        "status": "draft",
        "contract_json": _menu_config_contract_json(company_id, policies),
    }
    contract = Contract.search([
        ("active", "=", True),
        ("name", "=", values["name"]),
        ("model", "=", "ir.ui.menu"),
        ("company_id", "in", [False, company_id]),
    ], order="version_no desc, id desc", limit=1)
    if contract:
        contract.write(values)
    else:
        contract = Contract.create(values)
    contract.action_publish()
    return contract


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
destination_menu = ref("smart_construction_core.menu_sc_contract_center")

created = Policy.browse()
created_menus = env["ir.ui.menu"].sudo().browse()  # noqa: F821
try:
    Menu = env["ir.ui.menu"].sudo()  # noqa: F821
    root_menu = ref("smart_construction_core.menu_sc_root")
    probe_destination_menu = Menu.create(
        {
            "name": "__probe_menu_policy_destination__",
            "parent_id": root_menu.id if root_menu else False,
            "sequence": 9901,
        }
    )
    probe_target_menu = Menu.create(
        {
            "name": "__probe_menu_policy_target__",
            "parent_id": root_menu.id if root_menu else False,
            "sequence": 9902,
        }
    )
    probe_hidden_menu = Menu.create(
        {
            "name": "__probe_menu_policy_hidden__",
            "parent_id": root_menu.id if root_menu else False,
            "sequence": 9903,
        }
    )
    created_menus |= probe_destination_menu | probe_target_menu | probe_hidden_menu
    if probe_destination_menu:
        created |= Policy.create(
            {
                "menu_id": probe_destination_menu.id,
                "company_id": env.company.id,  # noqa: F821
                "visible": True,
            }
        )
    if probe_target_menu:
        created |= Policy.create(
            {
                "menu_id": probe_target_menu.id,
                "company_id": env.company.id,  # noqa: F821
                "custom_label": "业务配置中心",
                "sequence_override": 7,
                "target_parent_menu_id": probe_destination_menu.id,
                "visible": True,
            }
        )
        preview = created[:1]._onchange_preview_values()
        current_parent_preview = preview.get("current_parent_menu_id")
        if not (
            isinstance(current_parent_preview, list)
            and len(current_parent_preview) >= 2
            and current_parent_preview[0] == probe_target_menu.parent_id.id
            and current_parent_preview[1]
        ):
            errors.append({"menu_config_current_parent_preview": current_parent_preview})
        if not preview.get("menu_complete_name") or not preview.get("preview_summary"):
            errors.append({"menu_config_preview_missing_details": preview})
        handler_payload = {
            "params": {
                "model": "ui.menu.config.policy",
                "values": {"company_id": env.company.id, "menu_id": probe_target_menu.id, "visible": True},  # noqa: F821
                "changed_fields": ["menu_id"],
                "context": {},
            }
        }
        onchange_result = ApiOnchangeHandler(env, payload=handler_payload).handle()  # noqa: F821
        onchange_patch = (onchange_result.get("data") or {}).get("patch") if isinstance(onchange_result, dict) else {}
        if not onchange_patch.get("original_label") or not onchange_patch.get("preview_summary"):
            errors.append({"menu_config_handler_onchange_missing_details": onchange_patch})
        handler_current_parent = onchange_patch.get("current_parent_menu_id")
        if not (
            isinstance(handler_current_parent, list)
            and len(handler_current_parent) >= 2
            and handler_current_parent[1]
        ):
            errors.append({"menu_config_handler_current_parent_preview": handler_current_parent})
    if probe_hidden_menu:
        created |= Policy.create(
            {
                "menu_id": probe_hidden_menu.id,
                "company_id": env.company.id,  # noqa: F821
                "visible": False,
            }
        )
    nav_fact = {
        "flat": [
            {
                "menu_id": probe_target_menu.id,
                "name": probe_target_menu.name,
                "title": probe_target_menu.name,
                "sequence": 85,
                "children": [],
            },
            {
                "menu_id": probe_hidden_menu.id,
                "name": probe_hidden_menu.name,
                "title": probe_hidden_menu.name,
                "sequence": 95,
                "children": [],
            },
        ],
        "tree": [
            {
                "menu_id": 0,
                "name": "root",
                "title": "root",
                "sequence": 1,
                "children": [
                    {
                        "menu_id": probe_destination_menu.id,
                        "name": probe_destination_menu.name,
                        "title": probe_destination_menu.name,
                        "sequence": 1,
                        "children": [],
                    },
                    {
                        "menu_id": probe_target_menu.id,
                        "name": probe_target_menu.name,
                        "title": probe_target_menu.name,
                        "sequence": 85,
                        "children": [],
                    },
                    {
                        "menu_id": probe_hidden_menu.id,
                        "name": probe_hidden_menu.name,
                        "title": probe_hidden_menu.name,
                        "sequence": 95,
                        "children": [],
                    },
                ],
            }
        ],
    }
    publish_temp_menu_contract(created)
    overlaid, stats = Policy.apply_runtime_overlay(nav_fact, user=env.user)  # noqa: F821
    flat_by_id = {row.get("menu_id"): row for row in overlaid.get("flat", [])}
    if flat_by_id.get(probe_target_menu.id, {}).get("name") != "业务配置中心":
        errors.append({"overlay_rename_failed": flat_by_id.get(probe_target_menu.id)})
    if flat_by_id.get(probe_target_menu.id, {}).get("sequence") != 7:
        errors.append({"overlay_sequence_failed": flat_by_id.get(probe_target_menu.id)})
    if probe_hidden_menu.id in flat_by_id:
        errors.append({"overlay_hide_failed": flat_by_id.get(probe_hidden_menu.id)})
    if (stats or {}).get("hidden_count", 0) < 1:
        errors.append({"overlay_hidden_count": stats})
    if (stats or {}).get("moved_count", 0) < 1:
        errors.append({"overlay_moved_count": stats})
    def flatten_nav(nodes):
        out = []
        for node in nodes or []:
            if not isinstance(node, dict):
                continue
            out.append(node)
            out.extend(flatten_nav(node.get("children") if isinstance(node.get("children"), list) else []))
        return out

    destination_rows = [row for row in flatten_nav(overlaid.get("tree")) if row.get("menu_id") == probe_destination_menu.id]
    destination_children = destination_rows[0].get("children", []) if destination_rows else []
    if probe_target_menu.id not in {row.get("menu_id") for row in destination_children if isinstance(row, dict)}:
        errors.append({"overlay_move_failed": destination_children})
finally:
    if created:
        created.unlink()
    if created_menus:
        created_menus.unlink()
    env.cr.rollback()  # noqa: F821

wutao = env["res.users"].sudo().search([("login", "=", "wutao")], limit=1)  # noqa: F821
if not wutao:
    errors.append({"missing_user": "wutao"})
elif menu:
    runtime_policy = Policy.browse()
    try:
        if destination_menu:
            runtime_policy |= Policy.create(
                {
                    "menu_id": destination_menu.id,
                    "company_id": env.company.id,  # noqa: F821
                    "visible": True,
                }
            )
        runtime_policy |= Policy.create(
            {
                "menu_id": menu.id,
                "company_id": env.company.id,  # noqa: F821
                "custom_label": "菜单显示设置",
                "target_parent_menu_id": destination_menu.id if destination_menu else False,
                "role_group_ids": [(6, 0, [business_config_group.id])] if business_config_group else False,
                "visible": True,
            }
        )
        publish_temp_menu_contract(runtime_policy)
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
        gated_nav, user_menu_config_meta = _apply_user_menu_config_to_delivery_nav(wutao_env, gated_nav)

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
        if rows and rows[0].get("label") != "菜单显示设置":
            errors.append({"system_init_user_menu_config_rename_failed": rows[0]})
        if (user_menu_config_meta or {}).get("renamed_count", 0) < 1:
            errors.append({"system_init_user_menu_config_meta": user_menu_config_meta})
        if (user_menu_config_meta or {}).get("moved_count", 0) < 1:
            errors.append({"system_init_user_menu_config_move_meta": user_menu_config_meta})
        if rows and destination_menu and (rows[0].get("meta") or {}).get("parent_menu_label") != destination_menu.name:
            errors.append({"system_init_user_menu_config_move_failed": rows[0]})
    finally:
        if runtime_policy:
            runtime_policy.unlink()
        env.cr.rollback()  # noqa: F821

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
