# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import os
from urllib.parse import parse_qs, urlparse
from typing import Callable
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

from odoo.addons.smart_core.utils.extension_hooks import call_extension_hook_first
from odoo.addons.smart_core.core.scene_registry_provider import (
    get_schema_version as registry_get_schema_version,
    get_scene_version as registry_get_scene_version,
    has_db_scenes as registry_has_db_scenes,
    load_scene_configs as registry_load_scene_configs,
)


SCENE_CHANNELS = {"stable", "beta", "dev"}
CRITICAL_SCENE_TARGET_OVERRIDES = {"workspace.home"}

CRITICAL_SCENE_TARGET_ROUTE_OVERRIDES = {}


def _critical_scene_target_overrides(env) -> set[str]:
    payload = call_extension_hook_first(env, "smart_core_critical_scene_target_overrides", env)
    if isinstance(payload, (list, tuple, set)):
        values = {str(item).strip() for item in payload if str(item).strip()}
        if values:
            return values
    return set(CRITICAL_SCENE_TARGET_OVERRIDES)


def _critical_scene_target_route_overrides(env) -> dict[str, str]:
    payload = call_extension_hook_first(env, "smart_core_critical_scene_target_route_overrides", env)
    if isinstance(payload, dict):
        values = {
            str(key).strip(): str(value).strip()
            for key, value in payload.items()
            if str(key).strip() and str(value).strip()
        }
        if values:
            return values
    return dict(CRITICAL_SCENE_TARGET_ROUTE_OVERRIDES)


def _normalize_scene_channel(value: str | None) -> str | None:
    if not value:
        return None
    raw = str(value).strip().lower()
    return raw if raw in SCENE_CHANNELS else None


def resolve_scene_channel(
    env,
    user,
    params: dict | None,
    *,
    get_header: Callable[[str], str | None] | None = None,
) -> tuple[str, str, str]:
    channel = None
    selector = "default"
    source_ref = "default"
    if isinstance(params, dict):
        channel = _normalize_scene_channel(params.get("scene_channel") or params.get("channel"))
        if channel:
            selector = "param"
            source_ref = "param:scene_channel"
            return channel, selector, source_ref
    header_val = _normalize_scene_channel(get_header("X-Scene-Channel") if callable(get_header) else None)
    if header_val:
        return header_val, "param", "header:X-Scene-Channel"

    try:
        config = env["ir.config_parameter"].sudo()
        user_val = None
        if user and user.id:
            user_val = _normalize_scene_channel(config.get_param(f"sc.scene.channel.user.{user.id}") or "")
        if user_val:
            return user_val, "user", f"user_id={user.id}"

        company_id = user.company_id.id if user and user.company_id else None
        if company_id:
            company_val = _normalize_scene_channel(config.get_param(f"sc.scene.channel.company.{company_id}") or "")
            if company_val:
                return company_val, "company", f"company_id={company_id}"

        default_val = _normalize_scene_channel(config.get_param("sc.scene.channel.default") or "")
        if default_val:
            return default_val, "config", "sc.scene.channel.default"
    except Exception:
        pass

    env_val = _normalize_scene_channel(os.environ.get("SCENE_CHANNEL"))
    if env_val:
        return env_val, "env", "SCENE_CHANNEL"

    return "stable", selector, source_ref


def _resolve_scene_contract_path(rel_path: str) -> str | None:
    roots = [
        os.environ.get("SCENE_CONTRACT_ROOT"),
        "/mnt/extra-addons",
        "/mnt/addons_external",
        "/mnt/odoo",
        "/mnt/e/sc-backend-odoo",
        "/mnt",
    ]
    for root in roots:
        if not root:
            continue
        candidate = os.path.join(root, rel_path)
        if os.path.exists(candidate):
            return candidate
    return None


def load_scene_contract(env, scene_channel: str, use_pinned: bool, *, logger=None) -> tuple[dict | None, str]:
    if use_pinned:
        ref = "stable/PINNED.json"
        try:
            param = env["ir.config_parameter"].sudo().get_param("sc.scene.contract.pinned")
            if param:
                return json.loads(param), ref
        except Exception:
            pass
        rel_path = "docs/contract/exports/scenes/stable/PINNED.json"
    else:
        rel_path = f"docs/contract/exports/scenes/{scene_channel}/LATEST.json"
        ref = f"{scene_channel}/LATEST.json"
    path = _resolve_scene_contract_path(rel_path)
    if not path:
        return None, ref
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh), ref
    except Exception as exc:
        if logger is not None:
            try:
                logger.warning("scene contract load failed: %s (%s)", path, exc)
            except Exception:
                pass
        return None, ref


def _resolve_scene_provider_payload(scene_key: str, runtime_context: dict | None = None) -> dict:
    runtime_payload = runtime_context if isinstance(runtime_context, dict) else {}
    try:
        from odoo.addons.smart_scene.core.scene_provider_registry import resolve_scene_provider_path
    except Exception:
        return {}

    provider_path = resolve_scene_provider_path(scene_key, Path(__file__).resolve())
    if not provider_path or not provider_path.exists() or not provider_path.is_file():
        return {}

    spec = spec_from_file_location(
        f"scene_provider_{scene_key.replace('.', '_')}",
        provider_path,
    )
    if spec is None or spec.loader is None:
        return {}
    module = module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except Exception:
        return {}

    builder = getattr(module, "build", None)
    if not callable(builder):
        builder = getattr(module, "get_scene_content", None)
    if not callable(builder):
        return {}
    try:
        payload = builder(scene_key=scene_key, runtime=runtime_payload, context={})
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def merge_missing_scenes_from_registry(env, scenes, warnings):
    critical_target_overrides = _critical_scene_target_overrides(env)
    critical_route_overrides = _critical_scene_target_route_overrides(env)
    def _capability_target_map() -> dict[str, dict]:
        out: dict[str, dict] = {}
        try:
            caps = env["sc.capability"].sudo().search([("active", "=", True)], order="sequence,id")
        except Exception:
            return out
        for cap in caps:
            payload = cap.default_payload or {}
            if not isinstance(payload, dict):
                continue
            action_id = int(payload.get("action_id") or 0)
            menu_id = int(payload.get("menu_id") or 0)
            if not action_id:
                continue
            scene_key = str(payload.get("scene_key") or "").strip()
            if not scene_key:
                route = str(payload.get("route") or "").strip()
                if route:
                    try:
                        parsed = urlparse(route)
                        query = parse_qs(parsed.query or "")
                        scene_key = str((query.get("scene") or [""])[0] or "").strip()
                    except Exception:
                        scene_key = ""
            if not scene_key or scene_key in out:
                continue
            target = {"action_id": action_id}
            if menu_id:
                target["menu_id"] = menu_id
            out[scene_key] = target
        return out

    def _ref_id(xmlid: str, model_name: str) -> int:
        ref = str(xmlid or "").strip()
        if not ref:
            return 0
        try:
            rec = env.ref(ref, raise_if_not_found=False)
        except Exception:
            rec = None
        if not rec:
            return 0
        if model_name and getattr(rec, "_name", "") != model_name:
            return 0
        try:
            return int(rec.id or 0)
        except Exception:
            return 0

    def _hydrate_target(target_payload: dict) -> dict:
        target = dict(target_payload) if isinstance(target_payload, dict) else {}
        if not target:
            return target

        action_id = int(target.get("action_id") or 0)
        menu_id = int(target.get("menu_id") or 0)

        if action_id <= 0:
            action_id = _ref_id(str(target.get("action_xmlid") or ""), "ir.actions.act_window")
            if action_id > 0:
                target["action_id"] = action_id

        if menu_id <= 0:
            menu_id = _ref_id(str(target.get("menu_xmlid") or ""), "ir.ui.menu")
            if menu_id > 0:
                target["menu_id"] = menu_id

        if action_id <= 0 and menu_id > 0:
            try:
                menu = env["ir.ui.menu"].sudo().browse(menu_id)
            except Exception:
                menu = None
            if menu and menu.exists() and menu.action and getattr(menu.action, "_name", "") == "ir.actions.act_window":
                try:
                    inferred_action_id = int(menu.action.id or 0)
                except Exception:
                    inferred_action_id = 0
                if inferred_action_id > 0:
                    target["action_id"] = inferred_action_id

        return target

    def _ensure_minimal_route_target(scene_payload: dict, scene_code: str) -> None:
        if not isinstance(scene_payload, dict):
            return
        code = str(scene_code or scene_payload.get("code") or scene_payload.get("key") or "").strip()
        if not code:
            return
        target = scene_payload.get("target") if isinstance(scene_payload.get("target"), dict) else {}
        hydrated = _hydrate_target(target)
        has_runtime_target = bool(
            int(hydrated.get("action_id") or 0)
            or int(hydrated.get("menu_id") or 0)
            or str(hydrated.get("model") or "").strip()
            or str(hydrated.get("route") or "").strip()
        )
        if not has_runtime_target:
            hydrated["route"] = f"/s/{code}"
        scene_payload["target"] = hydrated

    def _upgrade_target_identity_from_registry(scene_payload: dict, registry_payload: dict) -> bool:
        if not isinstance(scene_payload, dict) or not isinstance(registry_payload, dict):
            return False
        current_target = scene_payload.get("target") if isinstance(scene_payload.get("target"), dict) else {}
        registry_target = registry_payload.get("target") if isinstance(registry_payload.get("target"), dict) else {}
        if not isinstance(current_target, dict) or not isinstance(registry_target, dict):
            return False
        action_xmlid = str(registry_target.get("action_xmlid") or "").strip()
        menu_xmlid = str(registry_target.get("menu_xmlid") or "").strip()
        if not (action_xmlid or menu_xmlid):
            return False
        next_target = dict(current_target)
        if action_xmlid:
            next_target["action_xmlid"] = action_xmlid
            next_target.pop("action_id", None)
        if menu_xmlid:
            next_target["menu_xmlid"] = menu_xmlid
            next_target.pop("menu_id", None)
        for key in ("route", "model", "view_mode", "view_type", "record_id"):
            if next_target.get(key) in (None, "", [], {}):
                value = registry_target.get(key)
                if value not in (None, "", [], {}):
                    next_target[key] = value
        if next_target == current_target:
            return False
        scene_payload["target"] = next_target
        return True

    def _upgrade_target_identity_from_provider(scene_payload: dict, provider_payload: dict) -> bool:
        if not isinstance(scene_payload, dict) or not isinstance(provider_payload, dict):
            return False
        current_target = scene_payload.get("target") if isinstance(scene_payload.get("target"), dict) else {}
        if not isinstance(current_target, dict):
            current_target = {}
        primary_action = provider_payload.get("primary_action") if isinstance(provider_payload.get("primary_action"), dict) else {}
        fallback_strategy = provider_payload.get("fallback_strategy") if isinstance(provider_payload.get("fallback_strategy"), dict) else {}
        action_xmlid = str(primary_action.get("action_xmlid") or fallback_strategy.get("action_xmlid") or "").strip()
        menu_xmlid = str(fallback_strategy.get("menu_xmlid") or "").strip()
        target_route = str(current_target.get("route") or scene_payload.get("page", {}).get("route") or f"/s/{scene_payload.get('code') or scene_payload.get('key') or ''}").strip()
        if not (action_xmlid or menu_xmlid or target_route):
            return False
        next_target = dict(current_target)
        if action_xmlid:
            next_target["action_xmlid"] = action_xmlid
            next_target.pop("action_id", None)
        if menu_xmlid:
            next_target["menu_xmlid"] = menu_xmlid
            next_target.pop("menu_id", None)
        if target_route:
            next_target["route"] = target_route
        if next_target == current_target:
            return False
        scene_payload["target"] = next_target
        return True

    current = [scene for scene in (scenes or []) if isinstance(scene, dict)]
    dropped_pkg_variants = []
    filtered = []
    for scene in current:
        code = str(scene.get("code") or scene.get("key") or "").strip()
        if "__pkg" in code:
            dropped_pkg_variants.append(code)
            continue
        filtered.append(scene)
    current = filtered
    existing = {
        str(scene.get("code") or scene.get("key") or "").strip()
        for scene in current
        if isinstance(scene, dict)
    }
    existing = {code for code in existing if code}
    registry_scenes = registry_load_scene_configs(env) or []
    registry_map = {}
    for scene in registry_scenes:
        if not isinstance(scene, dict):
            continue
        code = str(scene.get("code") or scene.get("key") or "").strip()
        if not code or "__pkg" in code:
            continue
        registry_map.setdefault(code, scene)
    capability_map = _capability_target_map()

    reconciled = []
    for scene in current:
        if not isinstance(scene, dict):
            continue
        code = str(scene.get("code") or scene.get("key") or "").strip()
        if not code:
            continue

        route_override = critical_route_overrides.get(code)
        if route_override:
            current_target = scene.get("target")
            forced_target = {"route": route_override}
            if current_target != forced_target:
                scene["target"] = dict(forced_target)
                reconciled.append(code)
            continue

        if isinstance(scene.get("target"), dict):
            scene["target"] = _hydrate_target(scene.get("target"))
        _ensure_minimal_route_target(scene, code)

        if code not in critical_target_overrides:
            continue
        registry_scene = registry_map.get(code) or {}
        if _upgrade_target_identity_from_registry(scene, registry_scene):
            reconciled.append(code)
            if isinstance(scene.get("target"), dict):
                scene["target"] = _hydrate_target(scene.get("target"))
        provider_scene = _resolve_scene_provider_payload(code)
        if _upgrade_target_identity_from_provider(scene, provider_scene):
            reconciled.append(code)
            if isinstance(scene.get("target"), dict):
                scene["target"] = _hydrate_target(scene.get("target"))
        registry_target = registry_scene.get("target")
        if isinstance(registry_target, dict) and registry_target:
            current_target = scene.get("target")
            if current_target != registry_target:
                scene["target"] = dict(registry_target)
                reconciled.append(code)

        capability_target = capability_map.get(code)
        if not isinstance(capability_target, dict) or not capability_target:
            continue
        current_target = scene.get("target")
        if not isinstance(current_target, dict):
            scene["target"] = dict(capability_target)
            reconciled.append(code)
            continue
        current_action_id = int(current_target.get("action_id") or 0)
        capability_action_id = int(capability_target.get("action_id") or 0)
        if capability_action_id and current_action_id != capability_action_id:
            scene["target"] = dict(capability_target)
            reconciled.append(code)

    appended = []
    for scene in registry_scenes:
        if not isinstance(scene, dict):
            continue
        code = str(scene.get("code") or scene.get("key") or "").strip()
        if not code or "__pkg" in code or code in existing:
            continue
        item = dict(scene)
        target = item.get("target")
        if isinstance(target, dict):
            item["target"] = _hydrate_target(target)
        _ensure_minimal_route_target(item, code)
        current.append(item)
        existing.add(code)
        appended.append(code)

    for scene in current:
        if not isinstance(scene, dict):
            continue
        target = scene.get("target")
        if isinstance(target, dict):
            scene["target"] = _hydrate_target(target)
        code = str(scene.get("code") or scene.get("key") or "").strip()
        _ensure_minimal_route_target(scene, code)
    if appended and isinstance(warnings, list):
        warnings.append({
            "code": "SCENE_FALLBACK_MERGED",
            "severity": "info",
            "scene_key": "",
            "message": "missing scenes merged from registry fallback",
            "field": "scenes",
            "reason": "contract_gap",
            "count": len(appended),
            "scene_codes": appended[:20],
        })
    if dropped_pkg_variants and isinstance(warnings, list):
        warnings.append({
            "code": "SCENE_PKG_VARIANTS_DROPPED",
            "severity": "info",
            "scene_key": "",
            "message": "imported package variant scenes removed from runtime payload",
            "field": "scenes",
            "reason": "pkg_variant_noise",
            "count": len(dropped_pkg_variants),
            "scene_codes": dropped_pkg_variants[:20],
        })
    if reconciled and isinstance(warnings, list):
        warnings.append({
            "code": "SCENE_TARGET_RECONCILED",
            "severity": "warn",
            "scene_key": "",
            "message": "critical scene targets reconciled from registry defaults",
            "field": "scenes.target",
            "reason": "contract_target_drift",
            "count": len(reconciled),
            "scene_codes": sorted(set(reconciled))[:20],
        })
    return current


def load_scenes_from_db_or_fallback(env, *, drift=None, logger=None) -> dict:
    out = {
        "scenes": [],
        "scene_version": None,
        "schema_version": None,
        "loaded_from": "fallback",
    }
    try:
        scenes_payload = registry_load_scene_configs(env, drift=drift) or []
        out["scenes"] = scenes_payload if isinstance(scenes_payload, list) else []
        out["loaded_from"] = "db" if registry_has_db_scenes(env) else "fallback"
        out["scene_version"] = registry_get_scene_version(env)
        out["schema_version"] = registry_get_schema_version(env)
    except Exception as exc:
        if logger is not None:
            try:
                logger.warning("scene source load failed: %s", exc)
            except Exception:
                pass
    return out
