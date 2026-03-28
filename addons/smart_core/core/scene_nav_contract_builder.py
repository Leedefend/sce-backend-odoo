# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path
from typing import Dict, List

from odoo.addons.smart_scene.core.nav_policy_registry import resolve_nav_group_policy
from .scene_nav_grouping_helper import build_scene_nav_grouped_nodes
from .scene_nav_node_defaults import (
    build_scene_nav_group_node,
    build_scene_nav_leaf,
    build_scene_nav_root,
)

NAV_POLICY_KEY = "scene_nav_v1"

EXCLUDED_REASON_NO_CODE = "no_code"
EXCLUDED_REASON_IMPORTED_PKG = "imported_pkg_variant"
EXCLUDED_REASON_SMOKE_CODE = "smoke_code"
EXCLUDED_REASON_INTERNAL_TAG = "internal_or_smoke_tag"
EXCLUDED_REASON_NO_TARGET = "missing_target"
EXCLUDED_REASON_DEFAULT_PLACEHOLDER = "default_placeholder"
EXCLUDED_REASON_SHOWCASE = "showcase_or_demo"
EXCLUDED_REASON_PORTAL_LEGACY = "portal_legacy"
EXCLUDED_REASON_NOT_SPA_READY = "portal_only_not_spa_ready"
EXCLUDED_REASON_DEMO_TARGET = "demo_target"
EXCLUDED_REASON_NO_NAV_TARGET = "target_fields_empty"
EXCLUDED_REASON_ACCESS_DENIED = "access_denied"
EXCLUDED_REASON_DEPRECATED_ALIAS = "deprecated_alias"

NAV_HIDDEN_SCENE_CODES = set()


def _hidden_scene_codes() -> set[str]:
    return set(NAV_HIDDEN_SCENE_CODES)


def _demo_target_markers() -> tuple[str, ...]:
    return ("demo",)


def _to_bool(value, default=False) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        text = value.strip().lower()
        if text in {"1", "true", "yes", "on"}:
            return True
        if text in {"0", "false", "no", "off"}:
            return False
    return default


def _delivery_gate_reason(scene: dict, code: str, target: dict) -> str | None:
    if code == "default":
        return EXCLUDED_REASON_DEFAULT_PLACEHOLDER
    lowered = code.lower()
    if "showcase" in lowered or ".demo" in lowered or lowered.endswith(".demo"):
        return EXCLUDED_REASON_SHOWCASE
    portal_only = _to_bool(scene.get("portal_only"), False)
    spa_ready = _to_bool(scene.get("spa_ready"), True)
    if portal_only and not spa_ready:
        return EXCLUDED_REASON_NOT_SPA_READY
    route = str(target.get("route") or "").strip().lower()
    if route.startswith("/portal/") or route.startswith("/workbench"):
        return EXCLUDED_REASON_PORTAL_LEGACY
    target_text = " ".join(
        [
            str(target.get("action_xmlid") or ""),
            str(target.get("menu_xmlid") or ""),
            str(target.get("route") or ""),
        ]
    ).lower()
    if any(marker in target_text for marker in _demo_target_markers()):
        return EXCLUDED_REASON_DEMO_TARGET
    return None


def _scene_allowed(scene: dict) -> bool:
    access = scene.get("access")
    if isinstance(access, dict):
        allowed = access.get("allowed")
        if isinstance(allowed, bool):
            return allowed
    return True


def _scene_valid(scene: dict) -> tuple[bool, str | None]:
    code = str(scene.get("code") or scene.get("key") or "").strip()
    if not code:
        return False, EXCLUDED_REASON_NO_CODE
    if code in _hidden_scene_codes():
        return False, EXCLUDED_REASON_DEPRECATED_ALIAS
    if "__pkg" in code:
        return False, EXCLUDED_REASON_IMPORTED_PKG
    if code.startswith("scene_smoke_"):
        return False, EXCLUDED_REASON_SMOKE_CODE
    tags = scene.get("tags")
    if isinstance(tags, list):
        tags_norm = {str(t or "").strip().lower() for t in tags}
        if "internal" in tags_norm or "smoke" in tags_norm:
            return False, EXCLUDED_REASON_INTERNAL_TAG
    target = scene.get("target")
    if not isinstance(target, dict):
        return False, EXCLUDED_REASON_NO_TARGET
    gate_reason = _delivery_gate_reason(scene, code, target)
    if gate_reason:
        return False, gate_reason
    has_target = any(
        bool(target.get(k))
        for k in ("route", "action_id", "action_xmlid", "menu_id", "menu_xmlid", "model")
    )
    if not has_target:
        return False, EXCLUDED_REASON_NO_NAV_TARGET
    if not _scene_allowed(scene):
        return False, EXCLUDED_REASON_ACCESS_DENIED
    return True, None


def _scene_structurally_valid(scene: dict) -> tuple[bool, str | None]:
    code = str(scene.get("code") or scene.get("key") or "").strip()
    if not code:
        return False, EXCLUDED_REASON_NO_CODE
    if code in _hidden_scene_codes():
        return False, EXCLUDED_REASON_DEPRECATED_ALIAS
    target = scene.get("target")
    if not isinstance(target, dict):
        return False, EXCLUDED_REASON_NO_TARGET
    has_target = any(
        bool(target.get(k))
        for k in ("route", "action_id", "action_xmlid", "menu_id", "menu_xmlid", "model")
    )
    if not has_target:
        return False, EXCLUDED_REASON_NO_NAV_TARGET
    return True, None


def build_scene_delivery_report(scenes: list[dict] | None, *, policy_applied: bool = False) -> dict:
    input_items = [item for item in (scenes or []) if isinstance(item, dict)]
    ready_codes: List[str] = []
    excluded: List[dict] = []
    reason_counts: Dict[str, int] = {}

    for item in input_items:
        code = str(item.get("code") or item.get("key") or "").strip()
        valid, reason = _scene_structurally_valid(item) if policy_applied else _scene_valid(item)
        if code and valid:
            ready_codes.append(code)
            continue
        safe_reason = str(reason or "unknown").strip() or "unknown"
        safe_code = code
        reason_counts[safe_reason] = int(reason_counts.get(safe_reason, 0)) + 1
        excluded.append({"code": safe_code, "reason": safe_reason})

    return {
        "scene_input_count": len(input_items),
        "scene_count": len(ready_codes),
        "excluded_scene_count": len(excluded),
        "excluded_reason_counts": reason_counts,
        "excluded_scenes": excluded,
        "delivery_ready_scene_codes": sorted(set(ready_codes)),
    }


def _resolve_nav_policy() -> dict:
    return resolve_nav_group_policy(NAV_POLICY_KEY, base_dir=Path(__file__).resolve())


def build_scene_nav_contract(data: dict) -> dict:
    nav_policy = _resolve_nav_policy()
    policy_labels = nav_policy.get("group_labels") if isinstance(nav_policy.get("group_labels"), dict) else {}
    policy_order = nav_policy.get("group_order") if isinstance(nav_policy.get("group_order"), dict) else {}
    policy_aliases = nav_policy.get("group_aliases") if isinstance(nav_policy.get("group_aliases"), dict) else {}
    policy_validation = nav_policy.get("validation") if isinstance(nav_policy.get("validation"), dict) else {}

    scenes = data.get("scenes") if isinstance(data.get("scenes"), list) else []
    role_surface = data.get("role_surface") if isinstance(data.get("role_surface"), dict) else {}
    role_candidates = [
        str(x or "").strip()
        for x in (role_surface.get("scene_candidates") or [])
        if str(x or "").strip()
    ]
    policy_applied = bool(data.get("delivery_policy_applied"))
    delivery_report = build_scene_delivery_report(scenes, policy_applied=policy_applied)
    ready_codes = set(delivery_report.get("delivery_ready_scene_codes") or [])
    scene_map: Dict[str, dict] = {}
    for item in scenes:
        if not isinstance(item, dict):
            continue
        code = str(item.get("code") or item.get("key") or "").strip()
        if code and code in ready_codes:
            scene_map[code] = item

    candidate_leaves = [build_scene_nav_leaf(scene_map[key]) for key in role_candidates if key in scene_map]
    remaining = [v for k, v in scene_map.items() if k not in set(role_candidates)]
    remaining_leaves = [build_scene_nav_leaf(v) for v in remaining]
    grouped = build_scene_nav_grouped_nodes(
        remaining_leaves,
        group_labels=policy_labels,
        group_order=policy_order,
        group_aliases=policy_aliases,
    )

    primary_children = []
    if candidate_leaves:
        primary_children.append(build_scene_nav_group_node("role_primary", "我的场景", candidate_leaves))
    include_remaining = bool(data.get("include_remaining_nav_scenes"))
    if include_remaining or not candidate_leaves:
        primary_children.extend(grouped)

    root = build_scene_nav_root(primary_children)

    first_leaf = None
    for group in primary_children:
        for child in group.get("children") or []:
            first_leaf = child
            break
        if first_leaf:
            break

    default_scene_key = str((first_leaf or {}).get("scene_key") or "").strip()
    default_route = {
        "menu_id": (first_leaf or {}).get("menu_id"),
        "scene_key": default_scene_key or None,
        "route": (f"/s/{default_scene_key}" if default_scene_key else "/workbench"),
        "reason": "role_landing" if default_scene_key else "menu_fallback",
    }

    return {
        "source": "scene_contract_v1",
        "nav": [root],
        "default_route": default_route,
        "meta": {
            "scene_input_count": int(delivery_report.get("scene_input_count") or 0),
            "scene_count": int(delivery_report.get("scene_count") or 0),
            "excluded_scene_count": int(delivery_report.get("excluded_scene_count") or 0),
            "excluded_reason_counts": delivery_report.get("excluded_reason_counts") or {},
            "excluded_scenes_sample": (delivery_report.get("excluded_scenes") or [])[:20],
            "candidate_count": len(candidate_leaves),
            "group_count": len(primary_children),
            "remaining_group_count": len(grouped),
            "remaining_hidden": bool(candidate_leaves) and not include_remaining,
            "policy_applied": policy_applied,
            "nav_policy_source": str(nav_policy.get("source") or "platform_default"),
            "nav_policy_provider": str(nav_policy.get("provider_key") or "platform.default.scene_nav_v1"),
            "nav_policy_version": str(nav_policy.get("policy_version") or "v1"),
            "nav_policy_validation_ok": bool(policy_validation.get("ok", False)),
            "nav_policy_validation_issues": list(policy_validation.get("issues") or [])[:20],
        },
    }
