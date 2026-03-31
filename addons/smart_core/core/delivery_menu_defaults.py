# -*- coding: utf-8 -*-
from __future__ import annotations

import zlib
from typing import Any, Dict


def synthetic_menu_id(key: str, base: int = 900_000_000, span: int = 50_000_000) -> int:
    raw = zlib.crc32(str(key or "").encode("utf-8")) & 0xFFFFFFFF
    return int(base + (raw % span))


def build_delivery_menu_child(menu: Dict[str, Any]) -> Dict[str, Any] | None:
    key = str(menu.get("menu_key") or "").strip()
    label = str(menu.get("label") or "").strip()
    route = str(menu.get("route") or "").strip()
    menu_id = menu.get("menu_id")
    action_id = menu.get("action_id")
    model = str(menu.get("model") or "").strip()
    scene_key = str(menu.get("scene_key") or "").strip()
    if not key or not label:
        return None
    if not (route or menu_id or action_id or model or scene_key):
        return None
    meta = {
        "action_type": "delivery.engine",
        "menu_key": key,
        "product_key": str(menu.get("product_key") or "").strip(),
        "capability_key": str(menu.get("capability_key") or "").strip(),
        "source": "delivery_engine_v1",
    }
    if route:
        meta["route"] = route
    if scene_key:
        meta["scene_key"] = scene_key
    if menu_id:
        meta["menu_id"] = menu_id
    action_xmlid = str(menu.get("action_xmlid") or "").strip()
    if action_id:
        meta["action_id"] = action_id
    if action_xmlid:
        meta["action_xmlid"] = action_xmlid
    if model:
        meta["model"] = model
    view_modes = menu.get("view_modes")
    if isinstance(view_modes, list) and view_modes:
        meta["view_modes"] = view_modes
    release_state = str(menu.get("release_state") or "").strip()
    if release_state:
        meta["release_state"] = release_state
    menu_xmlid = str(menu.get("menu_xmlid") or "").strip()
    if menu_xmlid:
        meta["menu_xmlid"] = menu_xmlid
    scene_source = str(menu.get("scene_source") or "").strip()
    if scene_source:
        meta["scene_source"] = scene_source
    return {
        "key": key,
        "label": label,
        "title": label,
        "menu_id": int(menu_id) if isinstance(menu_id, int) and menu_id > 0 else synthetic_menu_id(key),
        "children": [],
        "meta": meta,
    }


def build_delivery_menu_group(group_key: str, group_label: str, children: list[dict]) -> Dict[str, Any]:
    meta = {"group_key": group_key, "source": "delivery_engine_v1"}
    if children and any(((child.get("meta") or {}).get("release_state") == "preview") for child in children if isinstance(child, dict)):
        meta["release_state"] = "preview"
    return {
        "key": f"group:{group_key}",
        "label": group_label,
        "title": group_label,
        "menu_id": synthetic_menu_id(f"group:{group_key}", base=881_000_000, span=10_000_000),
        "children": children,
        "meta": meta,
    }


def build_delivery_menu_root(group_nodes: list[dict], role_code: str) -> Dict[str, Any]:
    return {
        "key": "root:delivery_engine",
        "label": "产品发布面",
        "title": "产品发布面",
        "menu_id": synthetic_menu_id("root:delivery_engine", base=880_000_000, span=10_000_000),
        "children": group_nodes,
        "meta": {"source": "delivery_engine_v1", "role_code": role_code},
    }
