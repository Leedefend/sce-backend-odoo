# -*- coding: utf-8 -*-
from __future__ import annotations
from odoo.addons.smart_core.core.delivery_menu_defaults import (
    build_delivery_menu_child,
    build_delivery_menu_group,
    build_delivery_menu_root,
)


class MenuService:
    NATIVE_PREVIEW_GROUP_KEY = "native_preview"
    NATIVE_PREVIEW_GROUP_LABEL = "原生菜单（预发布）"

    def _iter_leaf_nodes(self, nodes):
        for node in nodes or []:
            if not isinstance(node, dict):
                continue
            children = node.get("children") if isinstance(node.get("children"), list) else []
            if children:
                yield from self._iter_leaf_nodes(children)
                continue
            yield node

    def _native_preview_menus(self, *, native_nav: list[dict], policy: dict) -> list[dict]:
        preview_menus = []
        emitted_menu_ids = set()
        scene_route_map = {}
        for scene in policy.get("scenes") or []:
            if not isinstance(scene, dict):
                continue
            scene_key = str(scene.get("scene_key") or "").strip()
            route = str(scene.get("route") or "").strip()
            if scene_key and route:
                scene_route_map[scene_key] = route
        for leaf in self._iter_leaf_nodes(native_nav):
            meta = leaf.get("meta") if isinstance(leaf.get("meta"), dict) else {}
            menu_id = leaf.get("menu_id") or meta.get("menu_id")
            scene_key = str(leaf.get("scene_key") or ((leaf.get("meta") or {}).get("scene_key")) or "").strip()
            label = str(leaf.get("label") or leaf.get("title") or scene_key).strip()
            if not label or not menu_id:
                continue
            try:
                normalized_menu_id = int(menu_id)
            except Exception:
                continue
            if normalized_menu_id <= 0 or normalized_menu_id in emitted_menu_ids:
                continue
            emitted_menu_ids.add(normalized_menu_id)
            preview_menus.append(
                {
                    "menu_key": f"release.native_preview.menu_{normalized_menu_id}",
                    "label": label,
                    "menu_id": normalized_menu_id,
                    "route": str(meta.get("route") or leaf.get("route") or scene_route_map.get(scene_key) or ""),
                    "scene_key": scene_key,
                    "product_key": "native_preview",
                    "capability_key": "",
                    "release_state": "preview",
                    "menu_xmlid": str((meta.get("menu_xmlid")) or ""),
                    "scene_source": str((meta.get("scene_source")) or "native_nav"),
                    "action_id": meta.get("action_id"),
                    "action_xmlid": str(meta.get("action_xmlid") or ""),
                    "model": str(meta.get("model") or ""),
                    "view_modes": meta.get("view_modes") if isinstance(meta.get("view_modes"), list) else [],
                }
            )
        return preview_menus

    def build_nav(self, *, policy: dict, role_surface: dict | None = None, native_nav: list[dict] | None = None) -> list[dict]:
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
        native_preview_children = [
            build_delivery_menu_child(menu)
            for menu in self._native_preview_menus(native_nav=native_nav or [], policy=policy)
        ]
        native_preview_children = [child for child in native_preview_children if child]
        if native_preview_children:
            group_nodes.append(
                build_delivery_menu_group(
                    self.NATIVE_PREVIEW_GROUP_KEY,
                    self.NATIVE_PREVIEW_GROUP_LABEL,
                    native_preview_children,
                )
            )
        return [build_delivery_menu_root(group_nodes, role_code)]

    def describe_nav(self, nav: list[dict] | None) -> dict:
        root = (nav or [None])[0] if isinstance(nav, list) and nav else {}
        groups = root.get("children") if isinstance(root, dict) and isinstance(root.get("children"), list) else []
        stable_groups = []
        native_preview_groups = []
        for group in groups:
            if not isinstance(group, dict):
                continue
            group_key = str(((group.get("meta") or {}).get("group_key")) or "").strip()
            if group_key == self.NATIVE_PREVIEW_GROUP_KEY:
                native_preview_groups.append(group)
            else:
                stable_groups.append(group)
        return {
            "group_count": len(groups),
            "stable_group_count": len(stable_groups),
            "native_preview_group_count": len(native_preview_groups),
            "stable_leaf_count": sum(len(group.get("children") or []) for group in stable_groups),
            "native_preview_leaf_count": sum(len(group.get("children") or []) for group in native_preview_groups),
            "native_preview_group_key": self.NATIVE_PREVIEW_GROUP_KEY,
            "group_keys": [
                str(((group.get("meta") or {}).get("group_key")) or "").strip()
                for group in groups
                if isinstance(group, dict)
            ],
        }
