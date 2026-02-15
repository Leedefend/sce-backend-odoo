# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any

CONTRACT_MODES = {"user", "hud"}
_USER_MODE_STRIP_KEYS = {
    "action_id",
    "menu_id",
    "view_id",
    "res_id",
    "id",
    "model",
    "res_model",
    "scene_key",
    "action_xmlid",
    "menu_xmlid",
}


def is_truthy(value: Any) -> bool:
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


def resolve_contract_mode(params: dict | None) -> str:
    params = params if isinstance(params, dict) else {}
    raw_mode = str(params.get("contract_mode") or "").strip().lower()
    if raw_mode in CONTRACT_MODES:
        return raw_mode
    if is_truthy(params.get("hud")) or is_truthy(params.get("debug_hud")):
        return "hud"
    return "user"


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
    key = _safe_text(item.get("key") or item.get("code")).lower()
    name = _safe_text(item.get("name")).lower()
    if item.get("is_test") or item.get("smoke_test"):
        tags.update({"internal", "smoke"})
    if "smoke" in key or "smoke" in name:
        tags.update({"internal", "smoke"})
    if "internal" in key or "internal" in name:
        tags.add("internal")
    return sorted(tags)


def is_internal_or_smoke(item: dict) -> bool:
    if not isinstance(item, dict):
        return False
    tags = _parse_tags(item.get("tags"))
    key = _safe_text(item.get("key") or item.get("code")).lower()
    name = _safe_text(item.get("name")).lower()
    if "internal" in tags or "smoke" in tags:
        return True
    if item.get("is_test") or item.get("smoke_test"):
        return True
    combined = f"{key} {name}"
    return "smoke" in combined or "internal" in combined


def normalize_capabilities(capabilities: list) -> list[dict]:
    out: list[dict] = []
    for cap in capabilities or []:
        if not isinstance(cap, dict):
            continue
        item = dict(cap)
        item["key"] = _safe_text(item.get("key"))
        item["name"] = _safe_text(item.get("name"), item.get("key") or "未命名能力")
        item["ui_label"] = _safe_text(item.get("ui_label"), item.get("name") or item.get("key") or "未命名能力")
        item["status"] = _safe_text(item.get("status"), "active")
        item["tags"] = _normalized_tags_for_item(item)
        out.append(item)
    return out


def _strip_user_mode_fields(obj: Any) -> Any:
    if isinstance(obj, list):
        return [_strip_user_mode_fields(item) for item in obj]
    if not isinstance(obj, dict):
        return obj
    out: dict[str, Any] = {}
    for key, value in obj.items():
        if str(key or "").strip().lower() in _USER_MODE_STRIP_KEYS:
            continue
        out[key] = _strip_user_mode_fields(value)
    return out


def _sanitize_capability_for_user(item: dict) -> dict:
    cap = dict(item)
    cap.pop("required_groups", None)
    cap.pop("required_flag", None)
    cap.pop("role_scope", None)
    cap.pop("capability_scope", None)
    payload = cap.get("default_payload")
    if isinstance(payload, dict):
        cap["default_payload"] = _strip_user_mode_fields(payload)
    return cap


def _sanitize_scene_for_user(item: dict) -> dict:
    scene = _strip_user_mode_fields(dict(item))
    target = scene.get("target")
    if isinstance(target, dict):
        scene["target"] = _strip_user_mode_fields(target)
    tiles = scene.get("tiles")
    if isinstance(tiles, list):
        cleaned_tiles = []
        for tile in tiles:
            if not isinstance(tile, dict):
                continue
            cleaned_tiles.append(_strip_user_mode_fields(tile))
        scene["tiles"] = cleaned_tiles
    return scene


def normalize_scenes(scenes: list) -> list[dict]:
    out: list[dict] = []
    for scene in scenes or []:
        if not isinstance(scene, dict):
            continue
        item = dict(scene)
        code = _safe_text(item.get("code") or item.get("key"))
        item["code"] = code or item.get("code")
        item["key"] = _safe_text(item.get("key"), code)
        item["name"] = _safe_text(item.get("name"), code or "未命名场景")
        item["tags"] = _normalized_tags_for_item(item)
        out.append(item)
    return out


def apply_contract_governance(
    data: dict | Any,
    contract_mode: str,
    *,
    inject_contract_mode: bool = True,
) -> dict | Any:
    if not isinstance(data, dict):
        return data

    if isinstance(data.get("capabilities"), list):
        capabilities = normalize_capabilities(data.get("capabilities") or [])
        if contract_mode == "user":
            capabilities = [item for item in capabilities if not is_internal_or_smoke(item)]
            capabilities = [_sanitize_capability_for_user(item) for item in capabilities]
        data["capabilities"] = capabilities

    if isinstance(data.get("scenes"), list):
        scenes = normalize_scenes(data.get("scenes") or [])
        if contract_mode == "user":
            scenes = [item for item in scenes if not is_internal_or_smoke(item)]
            scenes = [_sanitize_scene_for_user(item) for item in scenes]
        data["scenes"] = scenes

    if inject_contract_mode:
        data["contract_mode"] = contract_mode
    if contract_mode != "hud":
        data.pop("diagnostic", None)
    return data
