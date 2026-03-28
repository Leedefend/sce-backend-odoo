# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import os
from typing import Any

from odoo.addons.smart_core.utils.extension_hooks import call_extension_hook_first
from .scene_delivery_policy_builtin_helper import (
    resolve_builtin_surface_deep_link_allowlist as _resolve_builtin_surface_deep_link_allowlist_helper,
    resolve_builtin_surface_nav_allowlist as _resolve_builtin_surface_nav_allowlist_helper,
    resolve_surface_policy_default_name as _resolve_surface_policy_default_name_helper,
)
from .scene_delivery_policy_file_helper import (
    load_surface_policy_payload_from_file as _load_surface_policy_payload_from_file_helper,
    resolve_default_surface_from_file as _resolve_default_surface_from_file_helper,
    resolve_policy_file_path as _resolve_policy_file_path_helper,
    surface_policy_default_file as _surface_policy_default_file_helper,
)
from .scene_delivery_policy_map_helper import (
    load_surface_policy_map_from_payload as _load_surface_policy_map_from_payload_helper,
    resolve_builtin_surface_policy as _resolve_builtin_surface_policy_helper,
)
from .scene_delivery_surface_defaults import (
    coerce_surface_input as _coerce_surface_input,
    is_demo_surface as _is_demo_surface,
    is_internal_surface as _is_internal_surface,
    normalize_surface as _normalize_surface,
    normalize_surfaces as _normalize_surfaces,
    to_bool as _to_bool,
)

REASON_SCENE_INVALID = "SCENE_INVALID"
REASON_SCENE_UNPUBLISHED = "SCENE_UNPUBLISHED"
REASON_SCENE_TARGET_UNRESOLVED = "SCENE_TARGET_UNRESOLVED"
REASON_SCENE_DELIVERY_HIDDEN = "SCENE_DELIVERY_HIDDEN"
REASON_SCENE_DELIVERY_DEEP_LINK_ONLY = "SCENE_DELIVERY_DEEP_LINK_ONLY"
REASON_SCENE_SURFACE_MISMATCH = "SCENE_SURFACE_MISMATCH"
REASON_SCENE_ROLE_PRUNED = "SCENE_ROLE_PRUNED"
REASON_SCENE_CAPABILITY_BLOCKED = "SCENE_CAPABILITY_BLOCKED"
REASON_SCENE_INTERNAL_ONLY = "SCENE_INTERNAL_ONLY"
REASON_SCENE_DEMO_ONLY = "SCENE_DEMO_ONLY"

ALLOWED_REASON_CODES = {
    REASON_SCENE_INVALID,
    REASON_SCENE_UNPUBLISHED,
    REASON_SCENE_TARGET_UNRESOLVED,
    REASON_SCENE_DELIVERY_HIDDEN,
    REASON_SCENE_DELIVERY_DEEP_LINK_ONLY,
    REASON_SCENE_SURFACE_MISMATCH,
    REASON_SCENE_ROLE_PRUNED,
    REASON_SCENE_CAPABILITY_BLOCKED,
    REASON_SCENE_INTERNAL_ONLY,
    REASON_SCENE_DEMO_ONLY,
}

DEFAULT_DELIVERY_MODE = "default"
DELIVERY_MODE_HIDDEN = "hidden"
DELIVERY_MODE_INTERNAL = "internal"
DELIVERY_MODE_DEMO = "demo"
DELIVERY_MODE_DEEP_LINK_ONLY = "deep_link_only"

SURFACE_POLICY_CONSTRUCTION_PM_V1 = "workspace_default_v1"
BUILTIN_SURFACE_NAV_ALLOWLIST = {
    SURFACE_POLICY_CONSTRUCTION_PM_V1: {
        "workspace.home",
        "workspace.list",
        "workspace.management",
    },
}
BUILTIN_SURFACE_DEEP_LINK_ALLOWLIST = {
    SURFACE_POLICY_CONSTRUCTION_PM_V1: (
        "workspace.risk",
        "workspace.finance",
        "workspace.tasks",
        "workspace.cost",
        "workspace.overview",
    ),
}
SURFACE_POLICY_FILE_DEFAULT = "docs/product/delivery/v1/workspace_default_v1_scene_surface_policy.json"
_SURFACE_POLICY_CACHE: dict[str, Any] = {"path": "", "mtime": -1.0, "payload": {}}


def _builtin_surface_nav_allowlist(env=None) -> dict:
    return _resolve_builtin_surface_nav_allowlist_helper(
        env,
        hook=call_extension_hook_first,
        default_map=BUILTIN_SURFACE_NAV_ALLOWLIST,
    )


def _builtin_surface_deep_link_allowlist(env=None) -> dict:
    return _resolve_builtin_surface_deep_link_allowlist_helper(
        env,
        hook=call_extension_hook_first,
        default_map=BUILTIN_SURFACE_DEEP_LINK_ALLOWLIST,
    )


def _surface_policy_default_name(env=None) -> str:
    return _resolve_surface_policy_default_name_helper(
        env,
        hook=call_extension_hook_first,
        default_name=SURFACE_POLICY_CONSTRUCTION_PM_V1,
    )


def _surface_policy_default_file(env=None) -> str:
    return _surface_policy_default_file_helper(
        env,
        hook=call_extension_hook_first,
        default_file=SURFACE_POLICY_FILE_DEFAULT,
    )


def _has_resolvable_target(scene: dict) -> bool:
    target = scene.get("target")
    if not isinstance(target, dict):
        return False
    for key in ("route", "action_id", "action_xmlid", "menu_id", "menu_xmlid", "model"):
        raw = target.get(key)
        if isinstance(raw, str):
            if raw.strip():
                return True
            continue
        if raw not in (None, 0, "", False):
            return True
    return False


def _resolve_policy_file_path(env=None) -> str | None:
    return _resolve_policy_file_path_helper(env, default_file_resolver=_surface_policy_default_file)


def _load_surface_policy_payload_from_file(env=None) -> dict:
    return _load_surface_policy_payload_from_file_helper(
        env,
        cache=_SURFACE_POLICY_CACHE,
        default_file_resolver=_surface_policy_default_file,
    )


def _load_surface_policy_from_file(env=None) -> dict[str, dict[str, set[str]]]:
    payload = _load_surface_policy_payload_from_file(env)
    return _load_surface_policy_map_from_payload_helper(payload, normalize_surface=_normalize_surface)


def _resolve_default_surface_from_file(env=None) -> str:
    return _resolve_default_surface_from_file_helper(
        env,
        payload_loader=_load_surface_policy_payload_from_file,
        normalize_surface=_normalize_surface,
    )


def _select_surface_policy(surface: str, env=None) -> dict:
    key = _normalize_surface(surface)
    file_policy_map = _load_surface_policy_from_file(env)
    file_policy = file_policy_map.get(key) if isinstance(file_policy_map, dict) else None
    if isinstance(file_policy, dict):
        nav_allowlist = set(file_policy.get("nav_allowlist") or set())
        deep_link_allowlist = set(file_policy.get("deep_link_allowlist") or set())
        if nav_allowlist or deep_link_allowlist:
            return {
                "name": key,
                "enabled": True,
                "source": "file",
                "nav_allowlist": nav_allowlist,
                "deep_link_allowlist": deep_link_allowlist,
            }
    return _resolve_builtin_surface_policy_helper(
        key,
        nav_allowlist_map=_builtin_surface_nav_allowlist(env),
        deep_link_allowlist_map=_builtin_surface_deep_link_allowlist(env),
    )


def _classify_scene_surface_delivery(code: str, policy: dict) -> str:
    scene_code = str(code or "").strip()
    if not scene_code:
        return "exclude"
    nav_allowlist = policy.get("nav_allowlist") if isinstance(policy, dict) else set()
    if scene_code in (nav_allowlist or set()):
        return "nav"
    deep_link_allowlist = policy.get("deep_link_allowlist") if isinstance(policy, dict) else set()
    if scene_code in (deep_link_allowlist or set()):
        return "deep_link"
    return "exclude"


def resolve_delivery_policy_runtime(env, params: dict | None) -> dict:
    params = params or {}
    enabled = None
    if isinstance(params, dict) and "scene_delivery_policy_enabled" in params:
        enabled = _to_bool(params.get("scene_delivery_policy_enabled"), False)
    if enabled is None:
        cfg_value = ""
        try:
            cfg_value = env["ir.config_parameter"].sudo().get_param("sc.scene.delivery.policy.enabled") if env is not None else ""
        except Exception:
            cfg_value = ""
        if str(cfg_value or "").strip():
            enabled = _to_bool(cfg_value, False)
    if enabled is None:
        enabled = _to_bool(os.environ.get("SCENE_DELIVERY_POLICY_ENABLED"), False)

    surface = ""
    if isinstance(params, dict):
        surface = _coerce_surface_input(params.get("scene_surface") or params.get("surface"))
    if not surface:
        try:
            surface = _coerce_surface_input(
                env["ir.config_parameter"].sudo().get_param("sc.scene.delivery.surface.default") if env is not None else ""
            )
        except Exception:
            surface = ""
    if not surface:
        surface = _coerce_surface_input(os.environ.get("SCENE_DELIVERY_SURFACE"))
    if not surface:
        file_default = _resolve_default_surface_from_file(env) if bool(enabled) else ""
        surface = file_default or (_surface_policy_default_name(env) if bool(enabled) else "default")

    runtime_env = str(os.environ.get("ENV") or "dev").strip().lower() or "dev"
    return {
        "enabled": bool(enabled),
        "surface": _normalize_surface(surface),
        "runtime_env": runtime_env,
    }


def filter_delivery_scenes(
    scenes: list[dict] | None,
    *,
    surface: str,
    role_surface: dict | None,
    contract_mode: str = "user",
    runtime_env: str = "dev",
    enabled: bool = False,
    env=None,
) -> dict:
    scene_items = [item for item in (scenes or []) if isinstance(item, dict)]
    delivery_scenes = []
    deep_link_scenes = []
    excluded = []
    reason_counts = {}
    normalized_surface = _normalize_surface(surface)
    surface_policy = _select_surface_policy(normalized_surface, env=env)

    def _exclude(scene_code: str, reason_code: str):
        safe_reason = reason_code if reason_code in ALLOWED_REASON_CODES else REASON_SCENE_INVALID
        safe_code = str(scene_code or "").strip()
        reason_counts[safe_reason] = int(reason_counts.get(safe_reason) or 0) + 1
        excluded.append({"code": safe_code, "reason_code": safe_reason})

    def _append_deep_link(scene_item: dict):
        scene_code = str(scene_item.get("code") or scene_item.get("key") or "").strip()
        if not scene_code:
            return
        if any(str(it.get("code") or it.get("key") or "").strip() == scene_code for it in deep_link_scenes):
            return
        deep_link_scenes.append(scene_item)

    def _scene_entry_allowed(scene_item: dict) -> bool:
        visibility_payload = scene_item.get("visibility") if isinstance(scene_item.get("visibility"), dict) else {}
        return _to_bool(visibility_payload.get("entry_allowed"), True) if isinstance(visibility_payload, dict) else True

    def _scene_nav_visible(scene_item: dict) -> bool:
        visibility_payload = scene_item.get("visibility") if isinstance(scene_item.get("visibility"), dict) else {}
        return _to_bool(visibility_payload.get("nav_visible"), True) if isinstance(visibility_payload, dict) else True

    if not enabled:
        return {
            "delivery_scenes": scene_items,
            "deep_link_scenes": [],
            "excluded": [],
            "meta": {
                "enabled": False,
                "surface": normalized_surface,
                "contract_mode": str(contract_mode or "user"),
                "runtime_env": str(runtime_env or "dev"),
                "policy_version": "v1.1",
                "surface_policy_applied": bool(surface_policy.get("enabled")),
                "surface_policy_name": str(surface_policy.get("name") or ""),
                "surface_policy_source": str(surface_policy.get("source") or "none"),
                "delivery_scene_codes_sample": sorted(
                    str((item or {}).get("code") or (item or {}).get("key") or "").strip()
                    for item in scene_items
                    if isinstance(item, dict) and str(item.get("code") or item.get("key") or "").strip()
                )[:20],
                "scene_input_count": len(scene_items),
                "delivery_scene_count": len(scene_items),
                "deep_link_scene_count": 0,
                "excluded_scene_count": 0,
                "excluded_reason_counts": {},
            },
        }

    for scene in scene_items:
        code = str(scene.get("code") or scene.get("key") or "").strip()
        if not code:
            _exclude("", REASON_SCENE_INVALID)
            continue
        if not _has_resolvable_target(scene):
            _exclude(code, REASON_SCENE_TARGET_UNRESOLVED)
            continue
        state = str(scene.get("state") or "").strip().lower()
        if state and state != "published":
            _exclude(code, REASON_SCENE_UNPUBLISHED)
            continue

        # Rule: delivery_mode is the primary strategy gate.
        mode = str(scene.get("delivery_mode") or DEFAULT_DELIVERY_MODE).strip().lower() or DEFAULT_DELIVERY_MODE
        if mode == DELIVERY_MODE_HIDDEN:
            _exclude(code, REASON_SCENE_DELIVERY_HIDDEN)
            continue
        if mode == DELIVERY_MODE_INTERNAL and not _is_internal_surface(normalized_surface):
            _exclude(code, REASON_SCENE_INTERNAL_ONLY)
            continue
        if mode == DELIVERY_MODE_DEMO and not _is_demo_surface(normalized_surface):
            _exclude(code, REASON_SCENE_DEMO_ONLY)
            continue
        if mode == DELIVERY_MODE_DEEP_LINK_ONLY:
            _exclude(code, REASON_SCENE_DELIVERY_DEEP_LINK_ONLY)
            if _scene_entry_allowed(scene):
                _append_deep_link(scene)
            continue

        surfaces = _normalize_surfaces(scene.get("surfaces"))
        if surfaces and normalized_surface not in surfaces:
            _exclude(code, REASON_SCENE_SURFACE_MISMATCH)
            continue
        if bool(surface_policy.get("enabled")):
            route_mode = _classify_scene_surface_delivery(code, surface_policy)
            if route_mode == "exclude":
                _exclude(code, REASON_SCENE_SURFACE_MISMATCH)
                continue
            if route_mode == "deep_link":
                _exclude(code, REASON_SCENE_DELIVERY_DEEP_LINK_ONLY)
                if _scene_entry_allowed(scene):
                    _append_deep_link(scene)
                continue

        access = scene.get("access") if isinstance(scene.get("access"), dict) else {}
        if isinstance(access, dict) and "allowed" in access and not _to_bool(access.get("allowed"), True):
            _exclude(code, REASON_SCENE_ROLE_PRUNED)
            continue

        required_caps = scene.get("required_capabilities")
        if isinstance(required_caps, list) and required_caps and isinstance(role_surface, dict):
            allowed_caps = role_surface.get("capabilities")
            if isinstance(allowed_caps, list):
                allowed_set = {str(item or "").strip() for item in allowed_caps if str(item or "").strip()}
                if not all(str(cap or "").strip() in allowed_set for cap in required_caps):
                    _exclude(code, REASON_SCENE_CAPABILITY_BLOCKED)
                    continue

        # Rule: visibility refines delivery only after delivery_mode passes.
        if not _scene_nav_visible(scene):
            _exclude(code, REASON_SCENE_DELIVERY_DEEP_LINK_ONLY)
            if _scene_entry_allowed(scene):
                _append_deep_link(scene)
            continue

        delivery_scenes.append(scene)

    return {
        "delivery_scenes": delivery_scenes,
        "deep_link_scenes": deep_link_scenes,
        "excluded": excluded,
        "meta": {
            "enabled": True,
            "surface": normalized_surface,
            "contract_mode": str(contract_mode or "user"),
            "runtime_env": str(runtime_env or "dev"),
            "policy_version": "v1.1",
            "surface_policy_applied": bool(surface_policy.get("enabled")),
            "surface_policy_name": str(surface_policy.get("name") or ""),
            "surface_policy_source": str(surface_policy.get("source") or "none"),
            "surface_nav_allowlist_size": len(surface_policy.get("nav_allowlist") or set()),
            "surface_deep_link_allowlist_size": len(surface_policy.get("deep_link_allowlist") or set()),
            "delivery_scene_codes_sample": sorted(
                str((item or {}).get("code") or (item or {}).get("key") or "").strip()
                for item in delivery_scenes
                if isinstance(item, dict) and str(item.get("code") or item.get("key") or "").strip()
            )[:20],
            "deep_link_scene_codes_sample": sorted(
                str((item or {}).get("code") or (item or {}).get("key") or "").strip()
                for item in deep_link_scenes
                if isinstance(item, dict) and str(item.get("code") or item.get("key") or "").strip()
            )[:20],
            "scene_input_count": len(scene_items),
            "delivery_scene_count": len(delivery_scenes),
            "deep_link_scene_count": len(deep_link_scenes),
            "excluded_scene_count": len(excluded),
            "excluded_reason_counts": reason_counts,
        },
    }
