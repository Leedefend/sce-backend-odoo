# -*- coding: utf-8 -*-
from __future__ import annotations
from odoo.addons.smart_core.core.delivery_menu_defaults import (
    build_delivery_menu_child,
    build_delivery_menu_group,
    build_delivery_menu_root,
)


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
                child = build_delivery_menu_child(menu)
                if child:
                    children.append(child)
            if role_code not in {"pm", "owner", "executive"} and str(group.get("group_key") or "") == "released_products":
                children = children[:1]
            group_key = str(group.get("group_key") or f"group:{idx}").strip()
            group_label = str(group.get("group_label") or group_key).strip()
            group_nodes.append(build_delivery_menu_group(group_key, group_label, children))
        return [build_delivery_menu_root(group_nodes, role_code)]
