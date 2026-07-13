# -*- coding: utf-8 -*-
from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

try:
    from .contract_governance_registry import (
        _CAPABILITY_GROUP_DEFAULTS,
        _CAPABILITY_GROUP_PROFILE_REGISTRY,
    )
except ImportError:
    spec = importlib.util.spec_from_file_location(
        "contract_governance_registry",
        Path(__file__).with_name("contract_governance_registry.py"),
    )
    if spec is None or spec.loader is None:
        raise
    registry = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(registry)
    _CAPABILITY_GROUP_DEFAULTS = registry._CAPABILITY_GROUP_DEFAULTS
    _CAPABILITY_GROUP_PROFILE_REGISTRY = registry._CAPABILITY_GROUP_PROFILE_REGISTRY


def _safe_text(value: Any, fallback: str = "") -> str:
    text = str(value or "").strip()
    if text.lower() in {"undefined", "null"}:
        text = ""
    return text or fallback


def _parse_tags(raw: Any) -> set[str]:
    if isinstance(raw, list):
        items = raw
    else:
        items = str(raw or "").split(",")
    out: set[str] = set()
    for item in items:
        val = _safe_text(item).lower()
        if val:
            out.add(val)
    return out


def _normalized_tags_for_item(item: dict) -> list[str]:
    tags = _parse_tags(item.get("tags"))
    key = _safe_text(item.get("key")).lower()
    code = _safe_text(item.get("code")).lower()
    name = _safe_text(item.get("name")).lower()
    target = item.get("target") if isinstance(item.get("target"), dict) else {}
    target_text = " ".join(
        [
            _safe_text(target.get("menu_xmlid")).lower(),
            _safe_text(target.get("action_xmlid")).lower(),
            _safe_text(target.get("route")).lower(),
        ]
    ).strip()
    if item.get("is_test") or item.get("smoke_test"):
        tags.update({"internal", "smoke"})
    if "smoke" in key or "smoke" in code or "smoke" in name:
        tags.update({"internal", "smoke"})
    if "internal" in key or "internal" in code or "internal" in name:
        tags.add("internal")
    combined = f"{key} {code} {name} {target_text}"
    if "showcase" in combined or "demo" in combined or "domain_demo" in combined:
        tags.add("demo")
    return sorted(tags)


def _has_demo_semantics(item: dict) -> bool:
    if not isinstance(item, dict):
        return False
    if item.get("is_demo") is True:
        return True
    tags = _parse_tags(item.get("tags"))
    return "demo" in tags or "showcase" in tags


def is_internal_or_smoke(item: dict) -> bool:
    if not isinstance(item, dict):
        return False
    if item.get("is_internal") is True or item.get("is_smoke") is True:
        return True
    tags = _parse_tags(item.get("tags"))
    if "internal" in tags or "smoke" in tags or "demo" in tags or "showcase" in tags:
        return True
    return bool(item.get("is_test") or item.get("smoke_test"))


def normalize_capabilities(capabilities: list) -> list[dict]:
    def _normalize_capability_status(value: Any) -> str:
        status = _safe_text(value).lower()
        if status in {"ga", "beta", "alpha"}:
            return status
        if status in {"active", "enabled", "ready"}:
            return "ga"
        if status in {"preview", "pilot", "pending"}:
            return "beta"
        if status in {"disabled", "inactive", "blocked"}:
            return "alpha"
        return "ga"

    def _infer_capability_group_key(capability_key: str) -> str:
        key = _safe_text(capability_key).lower()
        if not key:
            return "others"
        for group_key, profile in _CAPABILITY_GROUP_PROFILE_REGISTRY.items():
            prefixes = profile.get("key_prefixes") if isinstance(profile, dict) else ()
            if prefixes and key.startswith(tuple(prefixes)):
                return group_key
        if key.startswith(("usage.", "report.", "dashboard.", "analytics.")):
            return "analytics"
        if key.startswith(("scene.", "portal.", "config.", "permission.", "subscription.", "pack.")):
            return "governance"
        return "others"

    def _normalize_capability_state(value: Any) -> str:
        state = _safe_text(value).lower()
        if state in {"allow", "readonly", "deny", "pending", "coming_soon"}:
            return state
        return ""

    def _derive_capability_state(status: str, state: str, tags: list[str], reason_code: str) -> str:
        if state:
            return state
        tag_set = {str(tag or "").strip().lower() for tag in tags if str(tag or "").strip()}
        if "readonly" in tag_set or "read_only" in tag_set:
            return "readonly"
        if reason_code in {"PERMISSION_DENIED", "ACCESS_DENIED", "FORBIDDEN"}:
            return "deny"
        if status == "alpha":
            return "coming_soon"
        if status == "beta":
            return "pending"
        return "allow"

    def _extract_scene_key_from_route(route: Any) -> str:
        route_text = _safe_text(route)
        if not route_text:
            return ""
        if route_text.startswith("/s/"):
            return route_text.replace("/s/", "", 1).strip("/")
        marker = "scene="
        idx = route_text.find(marker)
        if idx < 0:
            return ""
        tail = route_text[idx + len(marker):]
        scene = tail.split("&", 1)[0].strip()
        return scene

    def _entry_target_payload(item: dict) -> dict:
        entry_target = item.get("entry_target") if isinstance(item.get("entry_target"), dict) else {}
        if not entry_target:
            return {}
        payload: dict[str, Any] = {}
        scene_key = _safe_text(entry_target.get("scene_key"))
        route = _safe_text(entry_target.get("route"))
        if not route and scene_key:
            route = f"/s/{scene_key}"
        if route:
            payload["route"] = route
        if _safe_text(entry_target.get("model")):
            payload["model"] = _safe_text(entry_target.get("model"))
        record_entry = entry_target.get("record_entry") if isinstance(entry_target.get("record_entry"), dict) else {}
        if _safe_text(record_entry.get("model")) and "model" not in payload:
            payload["model"] = _safe_text(record_entry.get("model"))
        refs = entry_target.get("compatibility_refs") if isinstance(entry_target.get("compatibility_refs"), dict) else {}
        for key in ("action_id", "menu_id", "record_id"):
            value = entry_target.get(key)
            if value is None:
                value = record_entry.get(key)
            if value is None:
                value = refs.get(key)
            if value is not None:
                payload[key] = value
        return payload

    def _ensure_default_payload(item: dict) -> None:
        payload = item.get("default_payload")
        if isinstance(payload, dict) and any(payload.get(key) for key in ("route", "action_id", "menu_id", "model", "scene_key")):
            return
        derived = _entry_target_payload(item)
        if derived:
            item["default_payload"] = derived

    def _derive_target_scene_key(item: dict) -> str:
        direct = _safe_text(item.get("target_scene_key"))
        if direct:
            return direct
        payload = item.get("default_payload")
        if isinstance(payload, dict):
            payload_scene = _safe_text(payload.get("scene_key"))
            if payload_scene:
                return payload_scene
            route_scene = _extract_scene_key_from_route(payload.get("route"))
            if route_scene:
                return route_scene
        entry_target = item.get("entry_target") if isinstance(item.get("entry_target"), dict) else {}
        entry_scene = _safe_text(entry_target.get("scene_key"))
        if entry_scene:
            return entry_scene
        route_scene = _extract_scene_key_from_route(entry_target.get("route") if isinstance(entry_target, dict) else "")
        if route_scene:
            return route_scene
        return ""

    def _derive_entry_kind(item: dict, target_scene_key: str) -> str:
        explicit = _safe_text(item.get("entry_kind")).lower()
        if explicit in {"exclusive", "alias"}:
            return explicit
        payload = item.get("default_payload") if isinstance(item.get("default_payload"), dict) else {}
        has_direct_entry = bool(payload.get("action_id") or payload.get("menu_id") or payload.get("route"))
        if target_scene_key and has_direct_entry:
            return "exclusive"
        return "alias"

    def _derive_delivery_level(item: dict, target_scene_key: str, entry_kind: str) -> str:
        explicit = _safe_text(item.get("delivery_level")).lower()
        if explicit in {"exclusive", "shared", "placeholder"}:
            return explicit
        payload = item.get("default_payload") if isinstance(item.get("default_payload"), dict) else {}
        has_entry = bool(target_scene_key or payload.get("route") or payload.get("action_id") or payload.get("menu_id"))
        if not has_entry:
            return "placeholder"
        if entry_kind == "exclusive":
            return "exclusive"
        return "shared"

    out: list[dict] = []
    for cap in capabilities or []:
        if not isinstance(cap, dict):
            continue
        item = dict(cap)
        item["key"] = _safe_text(item.get("key"))
        item["name"] = _safe_text(item.get("name"), item.get("key") or "未命名能力")
        item["ui_label"] = _safe_text(item.get("ui_label"), item.get("name") or item.get("key") or "未命名能力")
        item["status"] = _normalize_capability_status(item.get("status"))
        item["group_key"] = _safe_text(item.get("group_key"), _infer_capability_group_key(item.get("key")))
        group_meta = (
            _CAPABILITY_GROUP_PROFILE_REGISTRY.get(item["group_key"])
            or _CAPABILITY_GROUP_DEFAULTS.get(item["group_key"])
            or _CAPABILITY_GROUP_DEFAULTS["others"]
        )
        item["group_label"] = _safe_text(item.get("group_label"), group_meta.get("label") or item["group_key"])
        item["group_icon"] = _safe_text(item.get("group_icon"), group_meta.get("icon") or "")
        try:
            item["group_sequence"] = int(item.get("group_sequence") or 0)
        except Exception:
            item["group_sequence"] = 0
        _ensure_default_payload(item)
        item["tags"] = _normalized_tags_for_item(item)
        state = _normalize_capability_state(item.get("capability_state"))
        reason_code = _safe_text(item.get("reason_code")).upper()
        item["capability_state"] = _derive_capability_state(
            status=item["status"],
            state=state,
            tags=item["tags"],
            reason_code=reason_code,
        )
        item["state"] = _safe_text(item.get("state")).upper()
        if item["state"] not in {"READY", "LOCKED", "PREVIEW"}:
            if item["capability_state"] in {"deny"}:
                item["state"] = "LOCKED"
            elif item["capability_state"] in {"pending", "coming_soon"}:
                item["state"] = "PREVIEW"
            else:
                item["state"] = "READY"
        reason = _safe_text(item.get("capability_state_reason"))
        if not reason:
            if item["capability_state"] == "readonly":
                reason = "当前能力为只读模式"
            elif item["capability_state"] == "pending":
                reason = "能力处于试运行阶段"
            elif item["capability_state"] == "coming_soon":
                reason = "能力尚在建设中，即将开放"
        item["capability_state_reason"] = reason
        target_scene_key = _derive_target_scene_key(item)
        item["target_scene_key"] = target_scene_key
        item["entry_kind"] = _derive_entry_kind(item, target_scene_key)
        item["delivery_level"] = _derive_delivery_level(item, target_scene_key, item["entry_kind"])
        out.append(item)
    return out
