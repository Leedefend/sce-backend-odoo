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
    if not key or not label or not route:
        return None
    meta = {
        "route": route,
        "action_type": "delivery.engine",
        "menu_key": key,
        "product_key": str(menu.get("product_key") or "").strip(),
        "capability_key": str(menu.get("capability_key") or "").strip(),
        "source": "delivery_engine_v1",
    }
    scene_key = str(menu.get("scene_key") or "").strip()
    if scene_key:
        meta["scene_key"] = scene_key
    return {
        "key": key,
        "label": label,
        "title": label,
        "menu_id": synthetic_menu_id(key),
        "children": [],
        "meta": meta,
    }


def build_delivery_menu_group(group_key: str, group_label: str, children: list[dict]) -> Dict[str, Any]:
    return {
        "key": f"group:{group_key}",
        "label": group_label,
        "title": group_label,
        "menu_id": synthetic_menu_id(f"group:{group_key}", base=881_000_000, span=10_000_000),
        "children": children,
        "meta": {"group_key": group_key, "source": "delivery_engine_v1"},
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
