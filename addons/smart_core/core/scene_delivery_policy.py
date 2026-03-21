# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import os
from typing import Any

from odoo.addons.smart_core.utils.extension_hooks import call_extension_hook_first

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

SURFACE_POLICY_CONSTRUCTION_PM_V1 = "construction_pm_v1"
BUILTIN_SURFACE_NAV_ALLOWLIST = {
    SURFACE_POLICY_CONSTRUCTION_PM_V1: {
        "project.management",
        "projects.dashboard",
        "projects.ledger",
        "projects.intake",
        "my_work.workspace",
    },
}
BUILTIN_SURFACE_DEEP_LINK_ALLOWLIST = {
    SURFACE_POLICY_CONSTRUCTION_PM_V1: (
        "contract.center",
        "cost.budget_alloc",
        "cost.cost_compare",
        "cost.profit_compare",
        "cost.project_boq",
        "cost.project_budget",
        "cost.project_cost_ledger",
        "cost.project_progress",
        "data.dictionary",
        "finance.center",
        "finance.operating_metrics",
        "finance.payment_ledger",
        "finance.payment_requests",
        "finance.settlement_orders",
        "finance.treasury_ledger",
        "config.project_cost_code",
        "risk.monitor",
        "task.center",
    ),
}
SURFACE_POLICY_FILE_DEFAULT = "docs/product/delivery/v1/construction_pm_v1_scene_surface_policy.json"
_SURFACE_POLICY_CACHE: dict[str, Any] = {"path": "", "mtime": -1.0, "payload": {}}


def _builtin_surface_nav_allowlist(env=None) -> dict:
    payload = call_extension_hook_first(env, "smart_core_surface_nav_allowlist", env)
    if isinstance(payload, dict):
        return payload
    return BUILTIN_SURFACE_NAV_ALLOWLIST


def _builtin_surface_deep_link_allowlist(env=None) -> dict:
    payload = call_extension_hook_first(env, "smart_core_surface_deep_link_allowlist", env)
    if isinstance(payload, dict):
        return payload
    return BUILTIN_SURFACE_DEEP_LINK_ALLOWLIST


def _surface_policy_default_name(env=None) -> str:
    payload = call_extension_hook_first(env, "smart_core_surface_policy_default_name", env)
    value = str(payload or "").strip()
    return value or SURFACE_POLICY_CONSTRUCTION_PM_V1


def _surface_policy_default_file(env=None) -> str:
    payload = call_extension_hook_first(env, "smart_core_surface_policy_file_default", env)
    value = str(payload or "").strip()
    return value or SURFACE_POLICY_FILE_DEFAULT


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


def _coerce_surface_input(value: Any) -> str:
    text = str(value or "").strip().lower()
    if text in {"", "false", "none", "null", "0"}:
        return ""
    return text


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


def _resolve_policy_file_path(env=None) -> str | None:
    explicit = str(os.environ.get("SCENE_DELIVERY_POLICY_FILE") or "").strip()
    rel_path = explicit or _surface_policy_default_file(env)
    candidates = [
        rel_path,
        os.path.join("/mnt/e/sc-backend-odoo", rel_path),
        os.path.join("/mnt/extra-addons", rel_path),
        os.path.join("/mnt/addons_external", rel_path),
        os.path.join("/mnt/odoo", rel_path),
        os.path.join("/mnt", rel_path),
    ]
    for item in candidates:
        if item and os.path.isfile(item):
            return item
    return None


def _load_surface_policy_payload_from_file(env=None) -> dict:
    path = _resolve_policy_file_path(env)
    if not path:
        return {}
    try:
        mtime = float(os.path.getmtime(path))
    except Exception:
        mtime = -1.0
    cached_path = str(_SURFACE_POLICY_CACHE.get("path") or "")
    cached_mtime = float(_SURFACE_POLICY_CACHE.get("mtime") or -1.0)
    if cached_path == path and cached_mtime == mtime:
        cached_payload = _SURFACE_POLICY_CACHE.get("payload")
        return cached_payload if isinstance(cached_payload, dict) else {}
    try:
        payload = json.loads(open(path, "r", encoding="utf-8").read() or "{}")
    except Exception:
        return {}
    normalized = payload if isinstance(payload, dict) else {}
    _SURFACE_POLICY_CACHE["path"] = path
    _SURFACE_POLICY_CACHE["mtime"] = mtime
    _SURFACE_POLICY_CACHE["payload"] = normalized
    return normalized


def _load_surface_policy_from_file(env=None) -> dict[str, dict[str, set[str]]]:
    payload = _load_surface_policy_payload_from_file(env)
    surfaces = payload.get("surfaces") if isinstance(payload.get("surfaces"), dict) else {}
    out = {}
    for surface_key, policy in surfaces.items():
        key = _normalize_surface(surface_key)
        if not key or not isinstance(policy, dict):
            continue
        nav_raw = policy.get("nav_allowlist")
        deep_raw = policy.get("deep_link_allowlist")
        nav_allowlist = {str(x or "").strip() for x in (nav_raw if isinstance(nav_raw, list) else []) if str(x or "").strip()}
        deep_link_allowlist = {str(x or "").strip() for x in (deep_raw if isinstance(deep_raw, list) else []) if str(x or "").strip()}
        if nav_allowlist or deep_link_allowlist:
            out[key] = {
                "nav_allowlist": nav_allowlist,
                "deep_link_allowlist": deep_link_allowlist,
            }
    return out


def _resolve_default_surface_from_file(env=None) -> str:
    payload = _load_surface_policy_payload_from_file(env)
    raw = payload.get("default_surface") if isinstance(payload, dict) else ""
    value = _normalize_surface(raw)
    return value if value and value != "default" else ""


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
    builtin_nav_allowlist = _builtin_surface_nav_allowlist(env)
    nav_allowlist = {
        str(item or "").strip()
        for item in (builtin_nav_allowlist.get(key) or set())
        if str(item or "").strip()
    }
    builtin_deep_link_allowlist = _builtin_surface_deep_link_allowlist(env)
    deep_link_allowlist = {
        str(item or "").strip()
        for item in (builtin_deep_link_allowlist.get(key) or ())
        if str(item or "").strip()
    }
    if not nav_allowlist and not deep_link_allowlist:
        return {"name": "", "enabled": False, "source": "none", "nav_allowlist": set(), "deep_link_allowlist": set()}
    return {
        "name": key,
        "enabled": True,
        "source": "builtin",
        "nav_allowlist": nav_allowlist,
        "deep_link_allowlist": deep_link_allowlist,
    }


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
