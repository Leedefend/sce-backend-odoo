# -*- coding: utf-8 -*-
from __future__ import annotations

import zlib


def synthetic_scene_nav_menu_id(key: str, base: int = 700_000_000, span: int = 200_000_000) -> int:
    raw = zlib.crc32(str(key or "").encode("utf-8")) & 0xFFFFFFFF
    return int(base + (raw % span))


def build_scene_nav_leaf(scene: dict) -> dict:
    scene_key = str(scene.get("code") or scene.get("key") or "").strip()
    scene_name = str(scene.get("name") or scene_key).strip() or scene_key
    menu_id = synthetic_scene_nav_menu_id(f"scene:{scene_key}")
    return {
        "key": f"scene:{scene_key}",
        "label": scene_name,
        "title": scene_name,
        "menu_id": menu_id,
        "children": [],
        "scene_key": scene_key,
        "meta": {
            "scene_key": scene_key,
            "action_type": "scene.contract",
            "menu_xmlid": f"scene.contract.{scene_key.replace('.', '_')}",
            "scene_source": "scene_contract",
        },
    }


def build_scene_nav_group_node(group_key: str, group_label: str, children: list[dict]) -> dict:
    return {
        "key": f"group:{group_key}",
        "label": group_label,
        "title": group_label,
        "menu_id": synthetic_scene_nav_menu_id(f"group:{group_key}", base=640_000_000, span=40_000_000),
        "children": children,
        "meta": {
            "scene_source": "scene_contract",
            "group_key": group_key,
        },
    }


def build_scene_nav_root(children: list[dict]) -> dict:
    return {
        "key": "root:scene_contract",
        "label": "场景导航",
        "title": "场景导航",
        "menu_id": synthetic_scene_nav_menu_id("root:scene_contract", base=600_000_000, span=20_000_000),
        "children": children,
        "meta": {
            "scene_source": "scene_contract",
            "menu_xmlid": "scene.contract.root",
        },
    }
