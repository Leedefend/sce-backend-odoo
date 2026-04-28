# -*- coding: utf-8 -*-
from __future__ import annotations
from odoo.addons.smart_core.core.delivery_menu_defaults import (
    build_delivery_menu_child,
    build_delivery_menu_group,
    build_delivery_menu_root,
)
from odoo.addons.smart_core.delivery.menu_delivery_convergence_service import MenuDeliveryConvergenceService


class MenuService:
    NATIVE_PREVIEW_GROUP_KEY = "native_preview"
    NATIVE_PREVIEW_GROUP_LABEL = "系统菜单"

    def _is_admin_role(self, role_code: str) -> bool:
        normalized = str(role_code or "").strip().lower()
        return normalized in {"admin", "platform_admin", "system_admin", "administrator"}

    def _is_business_config_role(self, role_code: str) -> bool:
        normalized = str(role_code or "").strip().lower()
        return normalized in {"executive", "business_config_admin", "business_admin", "implementation_admin"}

    def _converged_menu(self, *, menu: dict, group_label: str, role_code: str):
        row = dict(menu or {})
        label = str(row.get("label") or "").strip()
        if not label:
            return None
        service = MenuDeliveryConvergenceService()
        category = service._classify_leaf(
            label,
            [group_label, label],
            is_admin=self._is_admin_role(role_code),
            is_business_config_admin=self._is_business_config_role(role_code),
        )
        if category.startswith("hidden_"):
            return None
        renamed = service.RENAME_LABELS.get(label)
        if renamed:
            row["label"] = renamed
        row["delivery_bucket"] = category
        return row

    def _iter_leaf_nodes(self, nodes, ancestors=None):
        parent_chain = list(ancestors or [])
        for node in nodes or []:
            if not isinstance(node, dict):
                continue
            children = node.get("children") if isinstance(node.get("children"), list) else []
            if children:
                yield from self._iter_leaf_nodes(children, parent_chain + [node])
                continue
            yield parent_chain, node

    def _resolve_preview_group_anchor(self, ancestors: list[dict]) -> tuple[str, str]:
        for ancestor in reversed(ancestors or []):
            if not isinstance(ancestor, dict):
                continue
            key = str(ancestor.get("key") or "").strip()
            if key.startswith("root:"):
                continue
            label = str(ancestor.get("label") or ancestor.get("title") or ancestor.get("name") or "").strip()
            menu_id = ancestor.get("menu_id")
            if (isinstance(menu_id, int) and menu_id > 0) and label:
                return f"menu_{menu_id}", label
        for ancestor in reversed(ancestors or []):
            if not isinstance(ancestor, dict):
                continue
            label = str(ancestor.get("label") or ancestor.get("title") or ancestor.get("name") or "").strip()
            if label:
                key = str(ancestor.get("key") or "").strip().replace(":", "_") or "ungrouped"
                return key, label
        return "ungrouped", "原生菜单"

    def _menu_dedupe_key(self, row: dict) -> str:
        menu_id = row.get("menu_id")
        if isinstance(menu_id, int) and menu_id > 0:
            return f"menu_id:{menu_id}"
        scene_key = str(row.get("scene_key") or "").strip()
        if scene_key:
            return f"scene:{scene_key}"
        route = str(row.get("route") or "").strip()
        if route:
            return f"route:{route}"
        menu_xmlid = str(row.get("menu_xmlid") or "").strip()
        if menu_xmlid:
            return f"xmlid:{menu_xmlid}"
        return f"label:{str(row.get('label') or '').strip()}"

    def _flatten_policy_menus(self, policy: dict) -> list[dict]:
        out = []
        index = 0
        for group in policy.get("menu_groups") or []:
            if not isinstance(group, dict):
                continue
            for menu in group.get("menus") or []:
                if not isinstance(menu, dict):
                    continue
                index += 1
                scene_key = str(menu.get("scene_key") or "").strip()
                menu_id = menu.get("menu_id")
                raw_anchor = scene_key or (str(menu_id) if isinstance(menu_id, int) and menu_id > 0 else str(menu.get("menu_key") or "").strip() or str(index))
                sanitized_anchor = raw_anchor.replace(":", "_").replace("/", "_").replace(".", "_")
                route = str(menu.get("route") or "").strip()
                action_id = menu.get("action_id")
                model = str(menu.get("model") or "").strip()
                if not action_id and not model and route != "/my-work":
                    continue
                out.append(
                    {
                        "menu_key": f"system.policy.{sanitized_anchor}",
                        "label": str(menu.get("label") or "").strip(),
                        "menu_id": menu_id,
                        "route": route,
                        "scene_key": scene_key,
                        "product_key": str(menu.get("product_key") or "").strip(),
                        "capability_key": str(menu.get("capability_key") or "").strip(),
                        "menu_xmlid": str(menu.get("menu_xmlid") or "").strip(),
                        "action_id": action_id,
                        "action_xmlid": str(menu.get("action_xmlid") or "").strip(),
                        "model": model,
                        "view_modes": menu.get("view_modes") if isinstance(menu.get("view_modes"), list) else [],
                        "scene_source": "delivery_policy",
                    }
                )
        return [row for row in out if row.get("menu_key") and row.get("label")]

    def _native_preview_menus(self, *, native_nav: list[dict], policy: dict) -> list[dict]:
        preview_menus_by_group = {}
        group_order = []
        emitted_menu_ids = set()
        scene_route_map = {}
        for scene in policy.get("scenes") or []:
            if not isinstance(scene, dict):
                continue
            scene_key = str(scene.get("scene_key") or "").strip()
            route = str(scene.get("route") or "").strip()
            if scene_key and route:
                scene_route_map[scene_key] = route
        for ancestors, leaf in self._iter_leaf_nodes(native_nav):
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
            anchor_key, anchor_label = self._resolve_preview_group_anchor(ancestors)
            group_key = f"system.{anchor_key}"
            if group_key not in preview_menus_by_group:
                preview_menus_by_group[group_key] = {
                    "group_key": group_key,
                    "group_label": anchor_label,
                    "menus": [],
                }
                group_order.append(group_key)
            preview_menus_by_group[group_key]["menus"].append(
                {
                    "menu_key": f"system.menu_{normalized_menu_id}",
                    "label": label,
                    "menu_id": normalized_menu_id,
                    "route": str(meta.get("route") or leaf.get("route") or scene_route_map.get(scene_key) or ""),
                    "scene_key": scene_key,
                    "product_key": "",
                    "capability_key": "",
                    "menu_xmlid": str((meta.get("menu_xmlid")) or ""),
                    "scene_source": str((meta.get("scene_source")) or "native_nav"),
                    "action_id": meta.get("action_id") or leaf.get("action_id"),
                    "action_xmlid": str(meta.get("action_xmlid") or leaf.get("action_xmlid") or ""),
                    "model": str(meta.get("model") or leaf.get("model") or ""),
                    "view_modes": (
                        meta.get("view_modes")
                        if isinstance(meta.get("view_modes"), list)
                        else (leaf.get("view_modes") if isinstance(leaf.get("view_modes"), list) else [])
                    ),
                }
            )
        return [preview_menus_by_group[group_key] for group_key in group_order]

    def build_nav(self, *, policy: dict, role_surface: dict | None = None, native_nav: list[dict] | None = None) -> list[dict]:
        role_code = str((role_surface or {}).get("role_code") or "").strip().lower()
        grouped_native = self._native_preview_menus(native_nav=native_nav or [], policy=policy)
        groups_by_key = {}
        group_order = []
        scene_group_map = {}
        dedupe_ids = set()
        dedupe_scenes = set()
        dedupe_routes = set()
        dedupe_xmlids = set()

        for group in grouped_native:
            if not isinstance(group, dict):
                continue
            group_key = str(group.get("group_key") or "").strip() or "system.ungrouped"
            group_label = str(group.get("group_label") or "").strip() or "系统菜单"
            groups_by_key[group_key] = {
                "group_key": group_key,
                "group_label": group_label,
                "menus": [],
            }
            group_order.append(group_key)
            for menu in group.get("menus") or []:
                if not isinstance(menu, dict):
                    continue
                converged_menu = self._converged_menu(menu=menu, group_label=group_label, role_code=role_code)
                if not converged_menu:
                    continue
                menu_id = menu.get("menu_id")
                scene_key = str(menu.get("scene_key") or "").strip()
                route = str(menu.get("route") or "").strip()
                menu_xmlid = str(menu.get("menu_xmlid") or "").strip()
                if isinstance(menu_id, int) and menu_id > 0:
                    dedupe_ids.add(menu_id)
                if scene_key:
                    dedupe_scenes.add(scene_key)
                if route:
                    dedupe_routes.add(route)
                if menu_xmlid:
                    dedupe_xmlids.add(menu_xmlid)
                groups_by_key[group_key]["menus"].append(converged_menu)
                if scene_key and scene_key not in scene_group_map:
                    scene_group_map[scene_key] = group_key

        if not group_order:
            fallback_key = "system.ungrouped"
            groups_by_key[fallback_key] = {
                "group_key": fallback_key,
                "group_label": "系统菜单",
                "menus": [],
            }
            group_order.append(fallback_key)

        for menu in self._flatten_policy_menus(policy):
            converged_menu = self._converged_menu(menu=menu, group_label=str(groups_by_key.get(group_order[0], {}).get("group_label") or "系统菜单"), role_code=role_code)
            if not converged_menu:
                continue
            menu_id = menu.get("menu_id")
            scene_key = str(menu.get("scene_key") or "").strip()
            route = str(menu.get("route") or "").strip()
            menu_xmlid = str(menu.get("menu_xmlid") or "").strip()
            if (isinstance(menu_id, int) and menu_id > 0 and menu_id in dedupe_ids) or (scene_key and scene_key in dedupe_scenes) or (route and route in dedupe_routes) or (menu_xmlid and menu_xmlid in dedupe_xmlids):
                continue
            if isinstance(menu_id, int) and menu_id > 0:
                dedupe_ids.add(menu_id)
            if scene_key:
                dedupe_scenes.add(scene_key)
            if route:
                dedupe_routes.add(route)
            if menu_xmlid:
                dedupe_xmlids.add(menu_xmlid)
            target_group_key = scene_group_map.get(scene_key) or group_order[0]
            groups_by_key[target_group_key]["menus"].append(converged_menu)

        group_nodes = []
        for group_key in group_order:
            row = groups_by_key.get(group_key) or {}
            children = [
                build_delivery_menu_child(menu)
                for menu in (row.get("menus") if isinstance(row.get("menus"), list) else [])
            ]
            children = [child for child in children if child]
            if not children:
                continue
            group_nodes.append(
                build_delivery_menu_group(
                    str(row.get("group_key") or group_key),
                    str(row.get("group_label") or "系统菜单"),
                    children,
                )
            )

        root = build_delivery_menu_root(group_nodes, role_code)
        root["key"] = "root:system_menu"
        root["label"] = "系统菜单"
        root["title"] = "系统菜单"
        root["meta"] = {
            "source": "delivery_engine_v1",
            "role_code": role_code,
            "strategy": "unified_system_menu",
        }
        return [root]

    def _count_leaf_nodes(self, nodes: list[dict] | None) -> int:
        count = 0
        for node in nodes or []:
            if not isinstance(node, dict):
                continue
            children = node.get("children") if isinstance(node.get("children"), list) else []
            if children:
                count += self._count_leaf_nodes(children)
            else:
                count += 1
        return count

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
            "stable_group_count": len(groups),
            "native_preview_group_count": 0,
            "stable_leaf_count": sum(self._count_leaf_nodes(group.get("children") or []) for group in groups),
            "native_preview_leaf_count": 0,
            "native_preview_group_key": "",
            "group_keys": [
                str(((group.get("meta") or {}).get("group_key")) or "").strip()
                for group in groups
                if isinstance(group, dict)
            ],
        }
