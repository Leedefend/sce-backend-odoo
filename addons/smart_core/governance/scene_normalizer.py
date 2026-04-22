"""Scene normalization engine extracted from system_init orchestration."""
# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Dict, List, Tuple

from odoo.addons.smart_core.utils.reason_codes import (
    REASON_OK,
    REASON_PERMISSION_DENIED,
    failure_meta_for_reason,
)
from odoo.addons.smart_core.governance.scene_drift_engine import append_resolve_error as drift_append_resolve_error


class SceneNormalizer:
    def append_act_url_deprecations(self, nodes, warnings: list):
        _append_act_url_deprecations(nodes, warnings)

    def index_nav_scene_targets(self, nodes):
        return _index_nav_scene_targets(nodes)

    def append_inferred_scene_warnings(self, nodes, scene_keys: set, warnings: list):
        _append_inferred_scene_warnings(nodes, scene_keys, warnings)

    def normalize(
        self,
        env,
        scenes,
        nav_tree,
        capabilities,
        diagnostics,
        *,
        nav_targets=None,
    ):
        self.normalize_structure(scenes, nav_tree, capabilities, diagnostics)
        self.resolve_targets(env, scenes, nav_tree, diagnostics, nav_targets=nav_targets)
        return scenes

    def normalize_structure(self, scenes, nav_tree, capabilities, diagnostics):
        warnings = diagnostics.get("normalize_warnings") if isinstance(diagnostics, dict) else []
        scene_keys = {
            (s.get("code") or s.get("key"))
            for s in scenes or []
            if isinstance(s, dict) and (s.get("code") or s.get("key"))
        }
        _append_inferred_scene_warnings(nav_tree, scene_keys, warnings)
        _normalize_scene_layouts(scenes, warnings)
        _normalize_scene_accesses(scenes, warnings)
        _normalize_scene_tiles(scenes, capabilities, warnings)
        return scenes

    def resolve_targets(self, env, scenes, nav_tree, diagnostics, *, nav_targets=None):
        warnings = diagnostics.get("normalize_warnings") if isinstance(diagnostics, dict) else []
        resolve_errors = diagnostics.get("resolve_errors") if isinstance(diagnostics, dict) else []
        targets = nav_targets if isinstance(nav_targets, dict) else _index_nav_scene_targets(nav_tree)
        _normalize_scene_targets(env, scenes, targets, resolve_errors)
        _sync_nav_scene_keys(nav_tree, scenes, warnings)
        return scenes


def _append_resolve_error(resolve_errors, *, scene_key, kind, code, ref=None, message=None, severity=None, field=None):
    drift_append_resolve_error(
        resolve_errors,
        scene_key=scene_key,
        kind=kind,
        code=code,
        ref=ref,
        message=message,
        severity=severity,
        field=field,
    )


def _normalize_view_mode(raw: str | None) -> str | None:
    if not raw:
        return None
    val = str(raw).strip().lower()
    if val in {"tree", "list", "kanban"}:
        return "list"
    if val in {"form"}:
        return "form"
    return val


def _build_entry_target(*, scene_key: str = "", route: str = "", menu_id=None, action_id=None, model: str = "", record_id=None) -> dict:
    normalized_scene_key = str(scene_key or "").strip()
    normalized_route = str(route or "").strip()
    if not normalized_scene_key and normalized_route.startswith("/s/"):
        normalized_scene_key = normalized_route.replace("/s/", "", 1).strip("/")
    if not normalized_scene_key:
        return {}
    target = {
        "type": "scene",
        "scene_key": normalized_scene_key,
    }
    if normalized_route:
        target["route"] = normalized_route
    compatibility = {}
    if isinstance(menu_id, int) and menu_id > 0:
        compatibility["menu_id"] = menu_id
    if isinstance(action_id, int) and action_id > 0:
        compatibility["action_id"] = action_id
    normalized_model = str(model or "").strip()
    if normalized_model:
        compatibility["model"] = normalized_model
    if isinstance(record_id, int) and record_id > 0:
        compatibility["record_id"] = record_id
    if normalized_model and isinstance(record_id, int) and record_id > 0:
        record_entry = {
            "model": normalized_model,
            "record_id": record_id,
        }
        if isinstance(action_id, int) and action_id > 0:
            record_entry["action_id"] = action_id
        if isinstance(menu_id, int) and menu_id > 0:
            record_entry["menu_id"] = menu_id
        target["record_entry"] = record_entry
    if compatibility:
        target["compatibility_refs"] = compatibility
    return target


def _append_inferred_scene_warnings(nodes, scene_keys: set, warnings: list):
    if warnings is None:
        return

    def walk(items):
        for node in items or []:
            meta = node.get("meta") or {}
            if meta.get("scene_key_inferred_from") == "action_xmlid":
                scene_key = node.get("scene_key") or meta.get("scene_key")
                if scene_key and scene_key not in scene_keys:
                    warnings.append({
                        "code": "SCENEKEY_INFERRED_NOT_FOUND",
                        "severity": "warn",
                        "scene_key": scene_key,
                        "message": "scene_key inferred from action_xmlid but not found in registry",
                        "field": "scene_key",
                        "reason": "inferred_scene_missing",
                        "menu_xmlid": node.get("xmlid") or meta.get("menu_xmlid"),
                        "action_xmlid": meta.get("action_xmlid"),
                    })
            if node.get("children"):
                walk(node.get("children"))

    walk(nodes)


def _resolve_action_id(env, xmlid: str | None) -> int | None:
    if not xmlid:
        return None
    try:
        rec = env.ref(xmlid, raise_if_not_found=False)
        if rec and rec.id:
            return int(rec.id)
    except Exception:
        return None
    return None


def _resolve_xmlid(env, xmlid: str | None) -> int | None:
    return _resolve_action_id(env, xmlid)


def _index_nav_scene_targets(nodes):
    targets = {}

    def walk(items):
        for node in items or []:
            meta = node.get("meta") or {}
            scene_key = node.get("scene_key") or meta.get("scene_key")
            if scene_key:
                targets[scene_key] = {
                    "menu_id": node.get("menu_id") or node.get("id"),
                    "action_id": meta.get("action_id"),
                    "model": meta.get("model"),
                    "view_mode": meta.get("view_mode") or meta.get("view_type"),
                }
            if node.get("children"):
                walk(node["children"])

    walk(nodes)
    return targets


def _append_act_url_deprecations(nodes, warnings):
    if warnings is None:
        return

    def walk(items):
        for node in items or []:
            meta = node.get("meta") or {}
            action_type = str(meta.get("action_type") or "").strip().lower()
            scene_key = node.get("scene_key") or meta.get("scene_key")
            if action_type == "ir.actions.act_url" and scene_key:
                warnings.append({
                    "code": "ACT_URL_LEGACY",
                    "severity": "info",
                    "scene_key": scene_key,
                    "message": "act_url menu resolved via scene_key (legacy action type)",
                    "field": "action_type",
                    "reason": "legacy_act_url",
                    "menu_xmlid": node.get("xmlid") or meta.get("menu_xmlid"),
                })
            if action_type == "ir.actions.act_url" and not scene_key:
                warnings.append({
                    "code": "ACT_URL_MISSING_SCENE",
                    "severity": "warn",
                    "scene_key": "",
                    "message": "act_url menu missing scene_key mapping",
                    "field": "scene_key",
                    "reason": "legacy_act_url_missing_scene",
                    "menu_xmlid": node.get("xmlid") or meta.get("menu_xmlid"),
                })
            if node.get("children"):
                walk(node.get("children"))

    walk(nodes)


def _normalize_scene_targets(env, scenes, nav_targets, resolve_errors):
    for scene in scenes:
        scene_key = scene.get("code") or scene.get("key")
        if not scene_key:
            continue
        target = scene.get("target") or {}
        route = target.get("route")
        route_is_missing_fallback = isinstance(route, str) and "TARGET_MISSING" in route
        action_xmlid = target.get("action_xmlid") or target.get("actionXmlid")
        menu_xmlid = target.get("menu_xmlid") or target.get("menuXmlid")
        if action_xmlid:
            action_id = _resolve_xmlid(env, action_xmlid)
            if action_id:
                current_action_id = int(target.get("action_id") or 0)
                if current_action_id and current_action_id != action_id:
                    _append_resolve_error(
                        resolve_errors,
                        scene_key=scene_key,
                        kind="target",
                        code="TARGET_ID_XMLID_MISMATCH",
                        ref=action_xmlid,
                        field="action_id",
                        message="action_id mismatches action_xmlid; xmlid resolution applied",
                        severity="warn",
                    )
                target["action_id"] = action_id
            else:
                _append_resolve_error(
                    resolve_errors,
                    scene_key=scene_key,
                    kind="target",
                    code="XMLID_NOT_FOUND",
                    ref=action_xmlid,
                    field="action_xmlid",
                    message="action_xmlid not found",
                )
        if menu_xmlid:
            menu_id = _resolve_xmlid(env, menu_xmlid)
            if menu_id:
                current_menu_id = int(target.get("menu_id") or 0)
                if current_menu_id and current_menu_id != menu_id:
                    _append_resolve_error(
                        resolve_errors,
                        scene_key=scene_key,
                        kind="target",
                        code="TARGET_ID_XMLID_MISMATCH",
                        ref=menu_xmlid,
                        field="menu_id",
                        message="menu_id mismatches menu_xmlid; xmlid resolution applied",
                        severity="warn",
                    )
                target["menu_id"] = menu_id
            else:
                _append_resolve_error(
                    resolve_errors,
                    scene_key=scene_key,
                    kind="target",
                    code="XMLID_NOT_FOUND",
                    ref=menu_xmlid,
                    field="menu_xmlid",
                    message="menu_xmlid not found",
                )
        if "action_xmlid" in target:
            target.pop("action_xmlid", None)
        if "actionXmlid" in target:
            target.pop("actionXmlid", None)
        if "menu_xmlid" in target:
            target.pop("menu_xmlid", None)
        if "menuXmlid" in target:
            target.pop("menuXmlid", None)
        if target.get("action_id") or target.get("model") or (target.get("route") and not route_is_missing_fallback):
            scene["target"] = target
        else:
            nav = nav_targets.get(scene_key) or {}
            resolved = {}
            if nav.get("action_id"):
                resolved["action_id"] = nav.get("action_id")
            elif nav.get("model"):
                resolved["model"] = nav.get("model")
                if nav.get("view_mode"):
                    resolved["view_mode"] = nav.get("view_mode")
            if nav.get("menu_id"):
                resolved["menu_id"] = nav.get("menu_id")
            if resolved:
                scene["target"] = resolved
            else:
                semantic_fallback = f"/s/{scene_key}"
                scene["target"] = {"route": semantic_fallback}
                _append_resolve_error(
                    resolve_errors,
                    scene_key=scene_key,
                    kind="target",
                    code="MISSING_TARGET",
                    ref=semantic_fallback,
                    field="target",
                    message="target missing; semantic fallback route applied",
                )
        final_target = scene.get("target") if isinstance(scene.get("target"), dict) else {}
        entry_target = _build_entry_target(
            scene_key=scene_key,
            route=str(final_target.get("route") or "").strip(),
            menu_id=final_target.get("menu_id") if isinstance(final_target.get("menu_id"), int) else None,
            action_id=final_target.get("action_id") if isinstance(final_target.get("action_id"), int) else None,
            model=str(final_target.get("model") or "").strip(),
            record_id=final_target.get("record_id") if isinstance(final_target.get("record_id"), int) else None,
        )
        if entry_target:
            final_target["entry_target"] = entry_target
            scene["target"] = final_target
    return scenes


def _normalize_scene_layouts(scenes, warnings):
    for scene in scenes:
        scene_key = scene.get("code") or scene.get("key") or ""
        layout = scene.get("layout")
        if not isinstance(layout, dict):
            warnings.append({
                "code": "LAYOUT_MISSING_OR_INVALID",
                "severity": "non_critical",
                "scene_key": scene_key,
                "message": "layout missing or invalid; no defaults applied",
                "field": "layout",
                "reason": "missing_or_invalid",
            })
            continue
    return scenes


def _to_string_list(value) -> List[str]:
    if not isinstance(value, list):
        return []
    out = []
    for item in value:
        text = str(item or "").strip()
        if text:
            out.append(text)
    return sorted(set(out))


def _to_bool(value, default: bool) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        text = value.strip().lower()
        if text in {"1", "true", "yes", "y", "on"}:
            return True
        if text in {"0", "false", "no", "n", "off"}:
            return False
        return default
    return bool(value)


def _normalize_tile_status(value) -> str:
    status = str(value or "").strip().lower()
    if status in {"ga", "beta", "alpha"}:
        return status
    return ""


def _normalize_tile_state(value) -> str:
    state = str(value or "").strip().upper()
    if state in {"READY", "LOCKED", "PREVIEW"}:
        return state
    return ""


def _normalize_capability_state(value) -> str:
    state = str(value or "").strip().lower()
    if state in {"allow", "readonly", "deny", "pending", "coming_soon"}:
        return state
    return ""


def _derive_tile_state(status: str, allowed) -> str:
    if isinstance(allowed, bool):
        return "READY" if allowed else "LOCKED"
    return "READY" if status == "ga" else "PREVIEW"


def _derive_capability_state(*, status: str, allowed) -> str:
    if isinstance(allowed, bool) and not allowed:
        return "deny"
    normalized = _normalize_tile_status(status)
    if normalized == "alpha":
        return "coming_soon"
    if normalized == "beta":
        return "pending"
    return "allow"


def _normalize_scene_tiles(scenes, capabilities, warnings):
    cap_map: Dict[str, dict] = {}
    for capability in capabilities or []:
        if not isinstance(capability, dict):
            continue
        cap_key = str(capability.get("key") or "").strip()
        if not cap_key:
            continue
        cap_map[cap_key] = {
            "status": _normalize_tile_status(capability.get("status")),
            "state": _normalize_tile_state(capability.get("state")),
            "capability_state": _normalize_capability_state(capability.get("capability_state")),
            "capability_state_reason": str(capability.get("capability_state_reason") or "").strip(),
            "reason_code": str(capability.get("reason_code") or "").strip(),
            "reason": str(capability.get("reason") or "").strip(),
        }

    for scene in scenes or []:
        if not isinstance(scene, dict):
            continue
        scene_key = scene.get("code") or scene.get("key") or ""
        tiles = scene.get("tiles")
        if not isinstance(tiles, list):
            continue
        for tile in tiles:
            if not isinstance(tile, dict):
                continue
            key = str(tile.get("key") or "").strip()
            cap_meta = cap_map.get(key) if key else None
            status = _normalize_tile_status(tile.get("status"))
            state = _normalize_tile_state(tile.get("state"))
            capability_state = _normalize_capability_state(tile.get("capability_state"))
            if not status and cap_meta:
                status = cap_meta.get("status") or ""
            if not state and cap_meta:
                state = cap_meta.get("state") or ""
            if not capability_state and cap_meta:
                capability_state = cap_meta.get("capability_state") or ""
            if not state:
                state = _derive_tile_state(status or "ga", tile.get("allowed"))
            if not status:
                status = "ga" if state == "READY" else "alpha"
            if not capability_state:
                capability_state = _derive_capability_state(status=status, allowed=tile.get("allowed"))
            tile["status"] = status
            tile["state"] = state
            tile["capability_state"] = capability_state
            if cap_meta:
                if not tile.get("capability_state_reason") and cap_meta.get("capability_state_reason"):
                    tile["capability_state_reason"] = cap_meta.get("capability_state_reason")
                if not tile.get("reason_code") and cap_meta.get("reason_code"):
                    tile["reason_code"] = cap_meta.get("reason_code")
                if not tile.get("reason") and cap_meta.get("reason"):
                    tile["reason"] = cap_meta.get("reason")
            if not key:
                warnings.append({
                    "code": "TILE_KEY_MISSING",
                    "severity": "non_critical",
                    "scene_key": scene_key,
                    "message": "tile key missing; state/status defaults applied",
                    "field": "tiles.key",
                    "reason": "missing_key",
                })
    return scenes


def _normalize_scene_accesses(scenes, warnings):
    for scene in scenes:
        if not isinstance(scene, dict):
            continue
        scene_key = scene.get("code") or scene.get("key") or ""
        raw_access = scene.get("access")
        if raw_access is None:
            access = {}
        elif isinstance(raw_access, dict):
            access = dict(raw_access)
        else:
            warnings.append({
                "code": "ACCESS_INVALID",
                "severity": "non_critical",
                "scene_key": scene_key,
                "message": "access should be object; fallback access defaults applied",
                "field": "access",
                "reason": "invalid_type",
            })
            access = {}

        tile_caps = []
        for tile in scene.get("tiles") or []:
            if not isinstance(tile, dict):
                continue
            tile_caps.extend(_to_string_list(tile.get("required_capabilities")))

        caps = sorted(set(
            _to_string_list(scene.get("required_capabilities"))
            + _to_string_list(access.get("required_capabilities"))
            + tile_caps
        ))

        visible = _to_bool(access.get("visible"), True)
        if "allowed" in access:
            allowed = _to_bool(access.get("allowed"), visible)
        else:
            allowed = visible
        has_access_clause = bool(caps)
        reason_code = str(access.get("reason_code") or "").strip().upper()
        if not reason_code:
            reason_code = REASON_OK if allowed else REASON_PERMISSION_DENIED
        suggested_action = str(access.get("suggested_action") or "").strip()
        if not suggested_action and reason_code != REASON_OK:
            suggested_action = str(failure_meta_for_reason(reason_code).get("suggested_action") or "")

        scene["access"] = {
            "visible": visible,
            "allowed": allowed,
            "reason_code": reason_code,
            "suggested_action": suggested_action,
            "required_capabilities": caps,
            "required_capabilities_count": len(caps),
            "has_access_clause": has_access_clause,
        }

    return scenes


def _build_scene_target_maps(scenes):
    menu_id_map: Dict[int, str] = {}
    action_id_map: Dict[int, str] = {}
    model_view_map: Dict[Tuple[str, str | None], str] = {}
    for scene in scenes or []:
        if not isinstance(scene, dict):
            continue
        scene_key = str(scene.get("code") or scene.get("key") or "").strip()
        if not scene_key:
            continue
        target = scene.get("target")
        if not isinstance(target, dict):
            continue
        menu_id = target.get("menu_id")
        action_id = target.get("action_id")
        model = str(target.get("model") or "").strip()
        view_mode = _normalize_view_mode(target.get("view_mode") or target.get("view_type"))

        if isinstance(menu_id, int) and menu_id > 0:
            menu_id_map.setdefault(menu_id, scene_key)
        if isinstance(action_id, int) and action_id > 0:
            action_id_map.setdefault(action_id, scene_key)
        if model:
            model_view_map.setdefault((model, view_mode), scene_key)
    return menu_id_map, action_id_map, model_view_map


def _sync_nav_scene_keys(nav_tree, scenes, warnings):
    scene_keys = {
        str(scene.get("code") or scene.get("key") or "").strip()
        for scene in scenes or []
        if isinstance(scene, dict)
    }
    scene_keys = {key for key in scene_keys if key}
    if not scene_keys:
        return

    menu_id_map, action_id_map, model_view_map = _build_scene_target_maps(scenes)

    def walk(nodes):
        for node in nodes or []:
            if not isinstance(node, dict):
                continue
            meta = node.get("meta") if isinstance(node.get("meta"), dict) else {}
            node_scene_key = str(node.get("scene_key") or "").strip()
            meta_scene_key = str(meta.get("scene_key") or "").strip()
            scene_key = node_scene_key or meta_scene_key
            if scene_key and scene_key not in scene_keys:
                warnings.append({
                    "code": "NAV_SCENEKEY_INVALID",
                    "severity": "warn",
                    "scene_key": scene_key,
                    "message": "nav scene_key not found in scenes payload; fallback to menu/action routing",
                    "field": "nav.scene_key",
                    "reason": "scene_not_in_registry",
                    "menu_xmlid": node.get("xmlid") or meta.get("menu_xmlid"),
                })
                node.pop("scene_key", None)
                meta.pop("scene_key", None)
                scene_key = ""

            if not scene_key:
                menu_id = node.get("menu_id") or node.get("id")
                action_id = meta.get("action_id")
                if isinstance(action_id, str) and action_id.isdigit():
                    action_id = int(action_id)
                if isinstance(menu_id, str) and menu_id.isdigit():
                    menu_id = int(menu_id)
                model = str(meta.get("model") or "").strip()
                view_mode = _normalize_view_mode(meta.get("view_mode") or meta.get("view_type"))
                if not view_mode:
                    view_modes = meta.get("view_modes")
                    if isinstance(view_modes, list) and view_modes:
                        view_mode = _normalize_view_mode(view_modes[0])

                if isinstance(menu_id, int) and menu_id in menu_id_map:
                    scene_key = menu_id_map[menu_id]
                elif isinstance(action_id, int) and action_id in action_id_map:
                    scene_key = action_id_map[action_id]
                elif model and (model, view_mode) in model_view_map:
                    scene_key = model_view_map[(model, view_mode)]
                elif model and (model, None) in model_view_map:
                    scene_key = model_view_map[(model, None)]

            if scene_key and scene_key in scene_keys:
                node["scene_key"] = scene_key
                meta["scene_key"] = scene_key
                node["meta"] = meta

            if node.get("children"):
                walk(node.get("children"))

    walk(nav_tree)
