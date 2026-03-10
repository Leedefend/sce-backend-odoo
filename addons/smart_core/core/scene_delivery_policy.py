# -*- coding: utf-8 -*-
from __future__ import annotations

import os
from typing import Any

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


def _to_bool(value: Any, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        text = value.strip().lower()
        if text in {"1", "true", "yes", "on"}:
            return True
        if text in {"0", "false", "no", "off"}:
            return False
    return default


def _normalize_surface(value: Any) -> str:
    text = str(value or "").strip().lower()
    return text or "default"


def _is_internal_surface(surface: str) -> bool:
    value = _normalize_surface(surface)
    return value in {"internal", "internal_ops", "ops_internal", "debug"}


def _is_demo_surface(surface: str) -> bool:
    value = _normalize_surface(surface)
    return value in {"demo", "showcase"}


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


def _normalize_surfaces(raw: Any) -> list[str]:
    if not isinstance(raw, list):
        return []
    out = []
    seen = set()
    for item in raw:
        key = _normalize_surface(item)
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(key)
    return out


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
        surface = str(params.get("scene_surface") or params.get("surface") or "").strip()
    if not surface:
        try:
            surface = str(
                env["ir.config_parameter"].sudo().get_param("sc.scene.delivery.surface.default") if env is not None else ""
            ).strip()
        except Exception:
            surface = ""
    if not surface:
        surface = str(os.environ.get("SCENE_DELIVERY_SURFACE") or "").strip()
    if not surface:
        surface = "default"

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
) -> dict:
    scene_items = [item for item in (scenes or []) if isinstance(item, dict)]
    delivery_scenes = []
    deep_link_scenes = []
    excluded = []
    reason_counts = {}
    normalized_surface = _normalize_surface(surface)

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
            "scene_input_count": len(scene_items),
            "delivery_scene_count": len(delivery_scenes),
            "deep_link_scene_count": len(deep_link_scenes),
            "excluded_scene_count": len(excluded),
            "excluded_reason_counts": reason_counts,
        },
    }
