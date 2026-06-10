# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Dict


SOURCE_KIND = "navigation_entry_target_projection"
SOURCE_AUTHORITIES = ("scene_registry", "ir.ui.menu", "ir.actions", "odoo_action_result")
NO_BUSINESS_FACT_AUTHORITY = True


def _text(value) -> str:
    return str(value or "").strip()


def _to_int(value) -> int:
    try:
        parsed = int(value)
    except Exception:
        return 0
    return parsed if parsed > 0 else 0


def _view_modes(value) -> list[str]:
    if isinstance(value, list):
        return [_text(item) for item in value if _text(item)]
    if isinstance(value, str):
        return [_text(item) for item in value.split(",") if _text(item)]
    return []


def build_scene_entry_target(
    *,
    scene_key: str,
    route: str = "",
    menu_id=None,
    action_id=None,
    model: str = "",
    view_modes=None,
    record_id=None,
) -> dict:
    normalized_scene_key = _text(scene_key)
    normalized_route = _text(route)
    if not normalized_scene_key and normalized_route.startswith("/s/"):
        normalized_scene_key = normalized_route.replace("/s/", "", 1).strip("/")
    if not normalized_scene_key:
        return {}
    normalized_route = normalized_route or f"/s/{normalized_scene_key}"
    entry_target = {
        "type": "scene",
        "scene_key": normalized_scene_key,
        "route": normalized_route,
    }
    compatibility_refs = _build_compatibility_refs(
        menu_id=menu_id,
        action_id=action_id,
        model=model,
        view_modes=view_modes,
    )
    if compatibility_refs:
        entry_target["compatibility_refs"] = compatibility_refs
    record_entry = _build_record_entry(model=model, record_id=record_id, action_id=action_id, menu_id=menu_id)
    if record_entry:
        entry_target["record_entry"] = record_entry
    return entry_target


def build_compatibility_entry_target(
    *,
    route: str = "",
    menu_id=None,
    action_id=None,
    model: str = "",
    view_modes=None,
    record_id=None,
    url: str = "",
    target_type: str = "",
    delivery_mode: str = "",
) -> dict:
    normalized_action_id = _to_int(action_id)
    normalized_url = _text(url)
    normalized_route = _text(route)
    if not normalized_route and normalized_url:
        normalized_route = normalized_url
    if not normalized_route and normalized_action_id:
        normalized_route = f"/a/{normalized_action_id}"

    compatibility_refs = _build_compatibility_refs(
        menu_id=menu_id,
        action_id=normalized_action_id,
        model=model,
        view_modes=view_modes,
    )
    if normalized_url:
        compatibility_refs["url"] = normalized_url
    if _text(target_type):
        compatibility_refs["target_type"] = _text(target_type)
    if _text(delivery_mode):
        compatibility_refs["delivery_mode"] = _text(delivery_mode)
    if not compatibility_refs and not normalized_route:
        return {}

    entry_target = {
        "type": "compatibility",
        "route": normalized_route,
        "compatibility_refs": compatibility_refs,
    }
    record_entry = _build_record_entry(model=model, record_id=record_id, action_id=normalized_action_id, menu_id=menu_id)
    if record_entry:
        entry_target["record_entry"] = record_entry
    return entry_target


def normalize_entry_target(
    *,
    env=None,
    entry_target=None,
    scene_key: str = "",
    route: str = "",
    menu_id=None,
    action_id=None,
    model: str = "",
    view_modes=None,
    record_id=None,
    url: str = "",
    target_type: str = "",
    delivery_mode: str = "",
) -> dict:
    if isinstance(entry_target, dict) and _text(entry_target.get("type")):
        return entry_target
    resolved_scene_key = _text(scene_key) or resolve_scene_key(
        env,
        menu_id=menu_id,
        action_id=action_id,
        model=model,
        view_modes=view_modes,
    )
    if resolved_scene_key:
        return build_scene_entry_target(
            scene_key=resolved_scene_key,
            route=route,
            menu_id=menu_id,
            action_id=action_id,
            model=model,
            view_modes=view_modes,
            record_id=record_id,
        )
    return build_compatibility_entry_target(
        route=route,
        menu_id=menu_id,
        action_id=action_id,
        model=model,
        view_modes=view_modes,
        record_id=record_id,
        url=url,
        target_type=target_type,
        delivery_mode=delivery_mode,
    )


def normalize_odoo_action_result(env, result, *, menu_id=None, source_model: str = "", source_record_id=None, _depth: int = 0) -> dict | None:
    if not isinstance(result, dict):
        return None
    payload = dict(result)
    if isinstance(payload.get("entry_target"), dict) and _text(payload["entry_target"].get("type")):
        return payload
    params = payload.get("params") if isinstance(payload.get("params"), dict) else {}
    next_action = params.get("next") if isinstance(params.get("next"), dict) else None
    nested_entry_target = {}
    if next_action and _depth < 2:
        normalized_next = normalize_odoo_action_result(
            env,
            next_action,
            menu_id=menu_id,
            source_model=source_model,
            source_record_id=source_record_id,
            _depth=_depth + 1,
        ) or next_action
        nested_entry_target = normalized_next.get("entry_target") if isinstance(normalized_next.get("entry_target"), dict) else {}
        payload["params"] = {
            **params,
            "next": normalized_next,
        }

    action_type = _text(payload.get("type"))
    model = _text(payload.get("res_model") or source_model)
    action_id = _to_int(payload.get("id") or payload.get("action_id")) or _resolve_action_id_for_model(env, model)
    if action_id:
        payload.setdefault("id", action_id)
        payload.setdefault("action_id", action_id)
    record_id = _to_int(payload.get("res_id") or source_record_id)
    view_modes = payload.get("view_mode") or payload.get("view_modes")
    url = _text(payload.get("url")) if action_type == "ir.actions.act_url" else ""
    route = url if url else ""
    entry_target = nested_entry_target or normalize_entry_target(
        env=env,
        menu_id=menu_id,
        action_id=action_id,
        model=model,
        view_modes=view_modes,
        record_id=record_id,
        url=url,
        route=route,
        target_type="url" if url else "action",
        delivery_mode="external_url" if url else "odoo_action_result",
    )
    if entry_target:
        payload["entry_target"] = entry_target
    return payload


def resolve_scene_key(env, *, menu_id=None, action_id=None, model: str = "", view_modes=None) -> str:
    normalized_menu_id = _to_int(menu_id)
    normalized_action_id = _to_int(action_id)
    normalized_model = _text(model)
    normalized_view_modes = [_normalize_view_mode(item) for item in _view_modes(view_modes)]
    normalized_view_modes = [item for item in normalized_view_modes if item]

    for row in _load_scene_configs(env):
        scene_key = _text(row.get("scene_key") or row.get("code") or row.get("key"))
        if not scene_key:
            continue
        target = row.get("target") if isinstance(row.get("target"), dict) else {}
        if normalized_menu_id and _to_int(target.get("menu_id") or row.get("menu_id")) == normalized_menu_id:
            return scene_key
        if normalized_action_id and _to_int(target.get("action_id") or row.get("action_id")) == normalized_action_id:
            return scene_key
        target_model = _text(target.get("model") or row.get("model"))
        target_view = _normalize_view_mode(target.get("view_mode") or target.get("view_type") or row.get("view_mode"))
        if normalized_model and target_model == normalized_model and target_view in normalized_view_modes:
            return scene_key
    return ""


def _resolve_action_id_for_model(env, model: str) -> int:
    normalized_model = _text(model)
    if env is None or not normalized_model:
        return 0
    try:
        action = env["ir.actions.act_window"].sudo().search([("res_model", "=", normalized_model)], order="id", limit=1)
        return _to_int(action.id)
    except Exception:
        return 0


def _load_scene_configs(env) -> list[dict]:
    if env is None:
        return []
    try:
        from odoo.addons.smart_core.core.scene_registry_provider import load_scene_configs

        rows = load_scene_configs(env) or []
        return [row for row in rows if isinstance(row, dict)]
    except Exception:
        return []


def _normalize_view_mode(value) -> str:
    normalized = _text(value).lower()
    if normalized in {"tree", "list", "kanban"}:
        return "list"
    if normalized == "form":
        return "form"
    return normalized


def _build_compatibility_refs(*, menu_id=None, action_id=None, model: str = "", view_modes=None) -> Dict[str, Any]:
    refs: Dict[str, Any] = {}
    normalized_menu_id = _to_int(menu_id)
    normalized_action_id = _to_int(action_id)
    normalized_model = _text(model)
    normalized_view_modes = _view_modes(view_modes)
    if normalized_menu_id:
        refs["menu_id"] = normalized_menu_id
    if normalized_action_id:
        refs["action_id"] = normalized_action_id
    if normalized_model:
        refs["model"] = normalized_model
    if normalized_view_modes:
        refs["view_modes"] = normalized_view_modes
    return refs


def _build_record_entry(*, model: str = "", record_id=None, action_id=None, menu_id=None) -> dict:
    normalized_model = _text(model)
    normalized_record_id = _to_int(record_id)
    if not normalized_model or not normalized_record_id:
        return {}
    record_entry = {
        "model": normalized_model,
        "record_id": normalized_record_id,
    }
    normalized_action_id = _to_int(action_id)
    normalized_menu_id = _to_int(menu_id)
    if normalized_action_id:
        record_entry["action_id"] = normalized_action_id
    if normalized_menu_id:
        record_entry["menu_id"] = normalized_menu_id
    return record_entry
