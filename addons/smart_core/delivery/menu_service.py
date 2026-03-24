# -*- coding: utf-8 -*-
from __future__ import annotations

import zlib


def _synthetic_menu_id(key: str, base: int = 900_000_000, span: int = 50_000_000) -> int:
    raw = zlib.crc32(str(key or "").encode("utf-8")) & 0xFFFFFFFF
    return int(base + (raw % span))


class MenuService:
    def build_nav(self, *, policy: dict, role_surface: dict | None = None) -> list[dict]:
        role_code = str((role_surface or {}).get("role_code") or "").strip().lower()
        group_nodes = []
        for idx, group in enumerate(policy.get("menu_groups") or [], start=1):
            if not isinstance(group, dict):
                continue
            children = []
            for menu in group.get("menus") or []:
                if not isinstance(menu, dict):
                    continue
                key = str(menu.get("menu_key") or "").strip()
                label = str(menu.get("label") or "").strip()
                route = str(menu.get("route") or "").strip()
                if not key or not label or not route:
                    continue
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
                children.append(
                    {
                        "key": key,
                        "label": label,
                        "title": label,
                        "menu_id": _synthetic_menu_id(key),
                        "children": [],
                        "meta": meta,
                    }
                )
            if role_code not in {"pm", "owner", "executive"} and str(group.get("group_key") or "") == "released_products":
                children = children[:1]
            group_key = str(group.get("group_key") or f"group:{idx}").strip()
            group_label = str(group.get("group_label") or group_key).strip()
            group_nodes.append(
                {
                    "key": f"group:{group_key}",
                    "label": group_label,
                    "title": group_label,
                    "menu_id": _synthetic_menu_id(f"group:{group_key}", base=881_000_000, span=10_000_000),
                    "children": children,
                    "meta": {"group_key": group_key, "source": "delivery_engine_v1"},
                }
            )
        return [
            {
                "key": "root:delivery_engine",
                "label": "产品发布面",
                "title": "产品发布面",
                "menu_id": _synthetic_menu_id("root:delivery_engine", base=880_000_000, span=10_000_000),
                "children": group_nodes,
                "meta": {"source": "delivery_engine_v1", "role_code": role_code},
            }
        ]

