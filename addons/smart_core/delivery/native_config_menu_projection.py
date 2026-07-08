# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any

from odoo.addons.smart_core.core.source_authority import build_source_authority_contract
from odoo.addons.smart_core.utils.backend_contract_boundaries import MENU_CONFIG_POLICY_MODEL
from odoo.addons.smart_core.utils.extension_hooks import call_extension_hook_first

CONFIG_APP_ID = "config"
CONFIG_GROUP_KEY = "platform.config"
CONFIG_GROUP_LABEL = "配置中心"

SOURCE_KIND = "native_business_config_menu_projection"
SOURCE_AUTHORITIES = ("ir.ui.menu", "ir.actions", "res.groups", MENU_CONFIG_POLICY_MODEL)
NO_BUSINESS_FACT_AUTHORITY = True
NATIVE_CONFIG_DELIVERY_EXCLUDED_MENU_XMLIDS_PARAM = "smart_core.native_config_delivery_excluded_menu_xmlids"


def source_authority_contract() -> dict[str, Any]:
    return build_source_authority_contract(
        kind=SOURCE_KIND,
        authorities=SOURCE_AUTHORITIES,
        no_business_fact_authority=NO_BUSINESS_FACT_AUTHORITY,
        projection_only=True,
        runtime_carrier="delivery_engine_v1.nav/app_shell.config",
    )


def _text(value: Any) -> str:
    return str(value or "").strip()


def _visible_menu_ids(env) -> set[int]:
    try:
        return set(env["ir.ui.menu"]._visible_menu_ids(debug=False))
    except Exception:
        try:
            return set(env["ir.ui.menu"]._visible_menu_ids())
        except Exception:
            return set()


def _xmlid(record: Any) -> str:
    try:
        return _text(record.get_external_id().get(record.id))
    except Exception:
        return ""


def _csv_values(value: Any) -> set[str]:
    if isinstance(value, (list, tuple, set)):
        return {_text(item) for item in value if _text(item)}
    return {_text(item) for item in _text(value).replace("\n", ",").split(",") if _text(item)}


def native_config_delivery_excluded_menu_xmlids(env) -> set[str]:
    xmlids: set[str] = set()
    hook_xmlids = call_extension_hook_first(env, "smart_core_native_config_delivery_excluded_menu_xmlids", env)
    xmlids.update(_csv_values(hook_xmlids))
    try:
        raw = env["ir.config_parameter"].sudo().get_param(NATIVE_CONFIG_DELIVERY_EXCLUDED_MENU_XMLIDS_PARAM, "")
    except Exception:
        raw = ""
    xmlids.update(_csv_values(raw))
    return xmlids


def native_config_root(env):
    hook_xmlid = call_extension_hook_first(env, "smart_core_native_config_root_menu_xmlid", env)
    xmlid = _text(hook_xmlid)
    if not xmlid:
        try:
            xmlid = _text(env["ir.config_parameter"].sudo().get_param("smart_core.native_config_root_menu_xmlid", ""))
        except Exception:
            xmlid = ""
    if not xmlid:
        return None
    try:
        return env.ref(xmlid, raise_if_not_found=False)
    except Exception:
        return None


def native_config_available(env) -> bool:
    root = native_config_root(env)
    return bool(root and int(root.id or 0) in _visible_menu_ids(env))


def _action_payload(menu: Any) -> dict[str, Any]:
    action = getattr(menu, "action", None)
    action_id = int(getattr(action, "id", 0) or 0) if action else 0
    menu_id = int(getattr(menu, "id", 0) or 0)
    route = f"/a/{action_id}?menu_id={menu_id}" if action_id and menu_id else (f"/m/{menu_id}" if menu_id else "")
    payload = {
        "subject": "action" if action_id else "menu",
        "menu_id": menu_id,
        "route": route,
        "menu_xmlid": _xmlid(menu),
    }
    if action_id:
        view_mode = _text(getattr(action, "view_mode", ""))
        payload.update(
            {
                "id": action_id,
                "action_id": action_id,
                "model": _text(getattr(action, "res_model", "")),
                "view_type": view_mode.split(",", 1)[0] or "tree",
                "view_modes": [_text(item) for item in view_mode.split(",") if _text(item)],
                "action_xmlid": _xmlid(action),
            }
        )
    return payload


def _build_config_node(menu: Any, visible_ids: set[int]) -> dict[str, Any] | None:
    menu_id = int(getattr(menu, "id", 0) or 0)
    if menu_id not in visible_ids:
        return None
    children = []
    for child in menu.child_id.sorted(lambda row: (row.sequence or 10, row.name or "")):
        node = _build_config_node(child, visible_ids)
        if node:
            children.append(node)
    target = _action_payload(menu)
    if not children and not target.get("action_id"):
        return None
    meta = {
        "app": CONFIG_APP_ID,
        "feature": _xmlid(menu) or f"menu_{menu_id}",
        "kind": "config",
        "delivery_bucket": "delivery_business_config",
        "menu_id": menu_id,
        "menu_xmlid": _xmlid(menu),
        "open": target,
        "entry_target": target,
        "route": target.get("route"),
        "source": SOURCE_KIND,
        "source_authority": source_authority_contract(),
    }
    if target.get("action_id"):
        meta.update(
            {
                "action_id": target.get("action_id"),
                "action_xmlid": target.get("action_xmlid"),
                "model": target.get("model"),
                "view_modes": target.get("view_modes") or ([target.get("view_type")] if target.get("view_type") else []),
            }
        )
    node = {
        "key": f"menu:{menu_id}",
        "id": menu_id,
        "menu_id": menu_id,
        "label": _text(menu.name),
        "children": children,
        "sequence": int(menu.sequence or 10),
        "meta": meta,
    }
    if target.get("route"):
        node["route"] = target.get("route")
    if target.get("action_id"):
        node["action_id"] = target.get("action_id")
    return node


def native_config_app_children(env) -> list[dict[str, Any]]:
    root = native_config_root(env)
    if not root:
        return []
    visible_ids = _visible_menu_ids(env)
    rows = []
    for child in root.child_id.sorted(lambda row: (row.sequence or 10, row.name or "")):
        node = _build_config_node(child, visible_ids)
        if node:
            rows.append(node)
    return rows


def _node_to_delivery_menu(
    node: dict[str, Any],
    excluded_xmlids: set[str] | None = None,
    *,
    path_labels: list[str] | None = None,
) -> dict[str, Any] | None:
    if not isinstance(node, dict):
        return None
    meta = node.get("meta") if isinstance(node.get("meta"), dict) else {}
    menu_id = int(node.get("menu_id") or meta.get("menu_id") or 0)
    label = _text(node.get("label"))
    if not menu_id or not label:
        return None
    menu_xmlid = _text(meta.get("menu_xmlid"))
    if menu_xmlid and menu_xmlid in (excluded_xmlids or set()):
        return None
    route = _text(node.get("route") or meta.get("route"))
    action_id = meta.get("action_id") or node.get("action_id")
    model = _text(meta.get("model"))
    if not action_id and not model:
        return None
    visible_path_parts = [_text(item) for item in (path_labels or []) if _text(item)]
    visible_path_parts.append(label)
    return {
        "menu_key": f"system.menu_{menu_id}",
        "label": label,
        "menu_id": menu_id,
        "route": route,
        "scene_key": "",
        "product_key": "",
        "capability_key": "",
        "menu_xmlid": menu_xmlid,
        "scene_source": SOURCE_KIND,
        "action_id": action_id,
        "action_xmlid": _text(meta.get("action_xmlid")),
        "model": model,
        "entry_target": meta.get("entry_target") if isinstance(meta.get("entry_target"), dict) else {},
        "view_modes": meta.get("view_modes") if isinstance(meta.get("view_modes"), list) else [],
        "delivery_bucket": "delivery_business_config",
        "visible_menu_path": " / ".join(visible_path_parts),
        "source_authority": source_authority_contract(),
    }


def native_config_delivery_groups(env) -> list[dict[str, Any]]:
    menus = []
    excluded_xmlids = native_config_delivery_excluded_menu_xmlids(env)
    root = native_config_root(env)
    root_label = _text(getattr(root, "name", "")) or CONFIG_GROUP_LABEL

    def visit(node: dict[str, Any], ancestors: list[str]) -> None:
        if not isinstance(node, dict):
            return
        menu = _node_to_delivery_menu(node, excluded_xmlids, path_labels=ancestors)
        if menu:
            menus.append(menu)
        for child in node.get("children") or []:
            visit(child, [*ancestors, _text(node.get("label"))])

    for node in native_config_app_children(env):
        visit(node, ["智慧施工管理平台", root_label])
    if not menus:
        return []
    return [
        {
            "group_key": CONFIG_GROUP_KEY,
            "group_label": CONFIG_GROUP_LABEL,
            "menus": menus,
        }
    ]
