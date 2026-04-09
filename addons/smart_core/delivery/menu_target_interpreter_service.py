# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path


def _text(value) -> str:
    return str(value or "").strip()


def _to_int(value) -> int | None:
    try:
        parsed = int(value)
    except Exception:
        return None
    return parsed if parsed > 0 else None


TARGET_TYPES = {
    "directory",
    "scene",
    "action",
    "native",
    "url",
    "unavailable",
}

DELIVERY_MODES = {
    "custom_scene",
    "custom_action",
    "native_bridge",
    "external_url",
    "none",
}

SUPPORTED_CUSTOM_ACTION_VIEW_MODES = {
    "tree",
    "list",
    "form",
    "kanban",
}

NATIVE_BRIDGE_ACTION_TYPES = {
    "ir.actions.act_window",
    "ir.actions.server",
    "ir.actions.client",
}

UNAVAILABLE_REASON_CODES = {
    "TARGET_MISSING",
    "ACTION_INVALID",
    "SCENE_UNRESOLVED",
    "DIRECTORY_ONLY",
    "DELIVERY_UNSUPPORTED",
    "PERMISSION_DENIED",
}


class MenuTargetInterpreterService:
    """Interpreter layer: menu_fact -> navigation target (facts remain unchanged)."""

    def __init__(self, env=None):
        self.env = env

    def interpret(self, nav_fact: dict, *, scene_map: dict | None = None, policy: dict | None = None) -> dict:
        resolver = self._build_scene_resolver(scene_map=scene_map, policy=policy)
        flat = nav_fact.get("flat") if isinstance(nav_fact, dict) and isinstance(nav_fact.get("flat"), list) else []
        tree = nav_fact.get("tree") if isinstance(nav_fact, dict) and isinstance(nav_fact.get("tree"), list) else []
        return {
            "flat": [self._explain_node(node, resolver=resolver) for node in flat if isinstance(node, dict)],
            "tree": [self._explain_tree(node, resolver=resolver) for node in tree if isinstance(node, dict)],
        }

    def _build_scene_resolver(self, *, scene_map: dict | None, policy: dict | None) -> dict:
        del policy
        menu_id_to_scene: dict[int, str] = {}
        action_id_to_scene: dict[int, str] = {}

        payload = scene_map if isinstance(scene_map, dict) else {}
        self._merge_explicit_scene_map(payload, menu_id_to_scene, action_id_to_scene)
        self._merge_scene_registry_mapping(menu_id_to_scene, action_id_to_scene)
        return {
            "menu_id": menu_id_to_scene,
            "action_id": action_id_to_scene,
        }

    def _merge_explicit_scene_map(
        self,
        payload: dict,
        menu_id_to_scene: dict[int, str],
        action_id_to_scene: dict[int, str],
    ) -> None:
        menu_map = payload.get("menu_id_to_scene") if isinstance(payload.get("menu_id_to_scene"), dict) else {}
        action_map = payload.get("action_id_to_scene") if isinstance(payload.get("action_id_to_scene"), dict) else {}
        scene_rows = payload.get("entries") if isinstance(payload.get("entries"), list) else []

        for key, value in menu_map.items():
            menu_id = _to_int(key)
            scene_key = _text(value)
            if menu_id and scene_key:
                menu_id_to_scene.setdefault(menu_id, scene_key)

        for key, value in action_map.items():
            action_id = _to_int(key)
            scene_key = _text(value)
            if action_id and scene_key:
                action_id_to_scene.setdefault(action_id, scene_key)

        for row in scene_rows:
            if not isinstance(row, dict):
                continue
            scene_key = _text(row.get("scene_key") or row.get("code"))
            if not scene_key:
                continue
            menu_id = _to_int(row.get("menu_id"))
            action_id = _to_int(row.get("action_id"))
            if menu_id:
                menu_id_to_scene.setdefault(menu_id, scene_key)
            if action_id:
                action_id_to_scene.setdefault(action_id, scene_key)

    def _merge_scene_registry_mapping(
        self,
        menu_id_to_scene: dict[int, str],
        action_id_to_scene: dict[int, str],
    ) -> None:
        for row in self._load_scene_registry_entries():
            scene_key = _text(row.get("code") or row.get("scene_key"))
            if not scene_key:
                continue
            target = row.get("target") if isinstance(row.get("target"), dict) else {}
            menu_id = _to_int(target.get("menu_id"))
            action_id = _to_int(target.get("action_id"))

            menu_xmlid = _text(target.get("menu_xmlid"))
            action_xmlid = _text(target.get("action_xmlid"))
            if not menu_id and menu_xmlid:
                menu_id = self._resolve_xmlid_to_res_id(menu_xmlid, expected_model="ir.ui.menu")
            if not action_id and action_xmlid:
                action_id = self._resolve_xmlid_to_res_id(action_xmlid, expected_model_prefix="ir.actions.")

            if menu_id:
                menu_id_to_scene.setdefault(menu_id, scene_key)
            if action_id:
                action_id_to_scene.setdefault(action_id, scene_key)

    def _load_scene_registry_entries(self) -> list[dict]:
        try:
            from odoo.addons.smart_scene.core.scene_registry_engine import load_scene_registry_content_entries

            rows = load_scene_registry_content_entries(Path(__file__))
            return rows if isinstance(rows, list) else []
        except Exception:
            return []

    def _resolve_xmlid_to_res_id(
        self,
        xmlid: str,
        *,
        expected_model: str | None = None,
        expected_model_prefix: str | None = None,
    ) -> int | None:
        if self.env is None:
            return None
        value = _text(xmlid)
        if not value or "." not in value:
            return None
        module, name = value.split(".", 1)
        if not module or not name:
            return None
        rec = self.env["ir.model.data"].sudo().search(
            [
                ("module", "=", module),
                ("name", "=", name),
            ],
            limit=1,
        )
        if not rec:
            return None
        model_name = _text(rec.model)
        if expected_model and model_name != expected_model:
            return None
        if expected_model_prefix and not model_name.startswith(expected_model_prefix):
            return None
        return _to_int(rec.res_id)

    def _resolve_scene_key(self, *, menu_id, action_id, resolver: dict) -> str:
        menu_map = resolver.get("menu_id") if isinstance(resolver.get("menu_id"), dict) else {}
        action_map = resolver.get("action_id") if isinstance(resolver.get("action_id"), dict) else {}
        resolved = menu_map.get(menu_id)
        if _text(resolved):
            return _text(resolved)
        return _text(action_map.get(action_id))

    def _resolve_custom_action_target(self, *, node: dict, action_id) -> dict:
        action_type = _text(node.get("action_type") or node.get("action_model"))
        if action_type != "ir.actions.act_window":
            return {}
        if not isinstance(action_id, int) or action_id <= 0:
            return {}
        if not bool(node.get("action_exists")):
            return {}
        action_meta = node.get("action_meta") if isinstance(node.get("action_meta"), dict) else {}
        res_model = _text(action_meta.get("res_model"))
        view_mode_raw = _text(action_meta.get("view_mode"))
        if not res_model or not view_mode_raw:
            return {}
        view_modes = [
            token
            for token in (_text(part) for part in view_mode_raw.split(","))
            if token
        ]
        if not view_modes:
            return {}
        if any(token not in SUPPORTED_CUSTOM_ACTION_VIEW_MODES for token in view_modes):
            return {}
        target = {
            "action_id": action_id,
            "res_model": res_model,
            "view_mode": ",".join(view_modes),
        }
        view_id = _to_int(action_meta.get("view_id"))
        if view_id:
            target["view_id"] = view_id
        return target

    def _resolve_native_bridge_target(self, *, node: dict, action_id) -> dict:
        action_type = _text(node.get("action_type") or node.get("action_model"))
        if action_type not in NATIVE_BRIDGE_ACTION_TYPES:
            return {}
        if not isinstance(action_id, int) or action_id <= 0:
            return {}
        if not bool(node.get("action_exists")):
            return {}
        return {
            "action_id": action_id,
            "action_type": action_type,
        }

    def _resolve_url_target(self, *, node: dict, action_id) -> dict:
        action_type = _text(node.get("action_type") or node.get("action_model"))
        if action_type != "ir.actions.act_url":
            return {}
        if not isinstance(action_id, int) or action_id <= 0:
            return {}
        if not bool(node.get("action_exists")):
            return {}
        target = {
            "action_id": action_id,
        }
        url_value = ""
        if self.env is not None:
            rec = self.env["ir.actions.act_url"].sudo().browse([action_id]).exists()
            if rec:
                url_value = _text(rec[0].url)
        if url_value:
            target["url"] = url_value
        return target

    def _resolve_unavailable_reason(self, *, node: dict, has_children: bool, action_raw: str) -> str:
        if has_children and not action_raw:
            return "DIRECTORY_ONLY"
        action_parse_error = _text(node.get("action_parse_error"))
        if action_parse_error:
            return "ACTION_INVALID"
        action_type = _text(node.get("action_type") or node.get("action_model"))
        action_exists = bool(node.get("action_exists"))
        if action_raw and not action_exists:
            return "ACTION_INVALID"
        if action_raw and action_type and action_type not in NATIVE_BRIDGE_ACTION_TYPES and action_type != "ir.actions.act_url":
            return "DELIVERY_UNSUPPORTED"
        if action_raw:
            return "SCENE_UNRESOLVED"
        return "TARGET_MISSING"

    def _is_directory_only(self, *, has_children: bool, target_type: str, action_raw: str) -> bool:
        if not has_children:
            return False
        if target_type in {"scene", "action", "native", "url"}:
            return False
        return not _text(action_raw)

    def _build_route(self, *, target_type: str, target: dict, menu_id) -> str | None:
        suffix = f"?menu_id={menu_id}" if isinstance(menu_id, int) and menu_id > 0 else ""
        if target_type == "scene":
            scene_key = _text(target.get("scene_key"))
            return f"/s/{scene_key}{suffix}" if scene_key else None
        if target_type == "action":
            action_id = _to_int(target.get("action_id"))
            return f"/a/{action_id}{suffix}" if action_id else None
        if target_type == "native":
            action_id = _to_int(target.get("action_id"))
            return f"/native/action/{action_id}{suffix}" if action_id else None
        if target_type == "url":
            return _text(target.get("url")) or None
        return None

    def _build_active_match(self, *, menu_id, target_type: str, target: dict, route: str | None, action_id) -> dict:
        scene_key = _text(target.get("scene_key")) if isinstance(target, dict) else ""
        target_action_id = _to_int(target.get("action_id")) if isinstance(target, dict) else None
        effective_action_id = target_action_id or (action_id if isinstance(action_id, int) else None)
        route_prefix = None
        if target_type == "scene" and scene_key:
            route_prefix = f"/s/{scene_key}"
        elif target_type == "action" and effective_action_id:
            route_prefix = f"/a/{effective_action_id}"
        elif target_type == "native" and effective_action_id:
            route_prefix = f"/native/action/{effective_action_id}"
        elif target_type == "url" and route:
            route_prefix = route
        return {
            "menu_id": menu_id,
            "scene_key": scene_key or None,
            "action_id": effective_action_id,
            "route_prefix": route_prefix,
        }

    def _explain_tree(self, node: dict, *, resolver: dict) -> dict:
        children = node.get("children") if isinstance(node.get("children"), list) else []
        explained = self._explain_node(node, resolver=resolver)
        explained["children"] = [self._explain_tree(child, resolver=resolver) for child in children if isinstance(child, dict)]
        return explained

    def _explain_node(self, node: dict, *, resolver: dict) -> dict:
        menu_id = node.get("menu_id")
        has_children = bool(node.get("has_children")) or bool(node.get("children") or node.get("child_ids"))
        action_raw = str(node.get("action_raw") or "").strip()
        action_type = str(node.get("action_type") or "").strip()
        action_id = node.get("action_id")
        is_clickable = bool(action_raw)

        target_type = "unavailable"
        delivery_mode = "none"
        route = None
        target = {}
        availability_status = "blocked"
        reason_code = "TARGET_MISSING"
        resolved_scene_key = self._resolve_scene_key(menu_id=menu_id, action_id=action_id, resolver=resolver)
        custom_action_target = self._resolve_custom_action_target(node=node, action_id=action_id)
        native_bridge_target = self._resolve_native_bridge_target(node=node, action_id=action_id)
        url_target = self._resolve_url_target(node=node, action_id=action_id)

        if resolved_scene_key:
            target_type = "scene"
            delivery_mode = "custom_scene"
            is_clickable = True
            availability_status = "ok"
            reason_code = ""
            target = {
                "scene_key": resolved_scene_key,
            }
        elif custom_action_target:
            target_type = "action"
            delivery_mode = "custom_action"
            is_clickable = True
            availability_status = "ok"
            reason_code = ""
            target = custom_action_target
        elif url_target:
            target_type = "url"
            delivery_mode = "external_url"
            is_clickable = True
            availability_status = "ok"
            reason_code = ""
            target = url_target
        elif native_bridge_target:
            target_type = "native"
            delivery_mode = "native_bridge"
            is_clickable = True
            availability_status = "ok"
            reason_code = ""
            target = native_bridge_target
        elif has_children and not action_raw:
            target_type = "directory"
            delivery_mode = "none"
            is_clickable = False
            availability_status = "ok"
            reason_code = "DIRECTORY_ONLY"
        else:
            reason_code = self._resolve_unavailable_reason(node=node, has_children=has_children, action_raw=action_raw)

        if reason_code and reason_code not in UNAVAILABLE_REASON_CODES:
            reason_code = "TARGET_MISSING"

        if self._is_directory_only(has_children=has_children, target_type=target_type, action_raw=action_raw):
            target_type = "directory"
            delivery_mode = "none"
            is_clickable = False
            availability_status = "ok"
            reason_code = "DIRECTORY_ONLY"
            target = {}

        route = self._build_route(target_type=target_type, target=target, menu_id=menu_id)
        active_match = self._build_active_match(
            menu_id=menu_id,
            target_type=target_type,
            target=target,
            route=route,
            action_id=action_id,
        )

        if target_type not in TARGET_TYPES:
            target_type = "unavailable"
        if delivery_mode not in DELIVERY_MODES:
            delivery_mode = "none"

        return {
            "menu_id": menu_id,
            "key": str(node.get("key") or f"menu:{menu_id}"),
            "name": str(node.get("name") or ""),
            "is_visible": True,
            "is_clickable": bool(is_clickable),
            "target_type": target_type,
            "delivery_mode": delivery_mode,
            "route": route,
            "target": target,
            "active_match": active_match,
            "availability_status": availability_status,
            "reason_code": reason_code,
            "source": {
                "action_raw": action_raw,
                "action_type": action_type,
                "action_id": action_id,
            },
            "children": [],
        }
