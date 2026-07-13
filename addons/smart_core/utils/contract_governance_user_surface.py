# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any

try:
    from .contract_governance_registry import (
        _PROJECT_FORM_ACTION_GROUP_LIMIT,
        _USER_CAPABILITY_KEYS,
        _USER_MODE_STRIP_KEYS,
        _USER_SCENE_ACCESS_KEYS,
        _USER_SCENE_KEYS,
        _USER_SCENE_TARGET_KEYS,
        _USER_SCENE_TILE_KEYS,
        _USER_SURFACE_ACTION_GROUP_LABELS,
        _USER_SURFACE_ACTION_MAX,
        _USER_SURFACE_FILTER_MAX,
        _USER_SURFACE_NOISE_MARKERS,
    )
except ImportError:
    import importlib.util
    from pathlib import Path

    spec = importlib.util.spec_from_file_location(
        "contract_governance_registry",
        Path(__file__).with_name("contract_governance_registry.py"),
    )
    if spec is None or spec.loader is None:
        raise
    registry = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(registry)
    _PROJECT_FORM_ACTION_GROUP_LIMIT = registry._PROJECT_FORM_ACTION_GROUP_LIMIT
    _USER_CAPABILITY_KEYS = registry._USER_CAPABILITY_KEYS
    _USER_MODE_STRIP_KEYS = registry._USER_MODE_STRIP_KEYS
    _USER_SCENE_ACCESS_KEYS = registry._USER_SCENE_ACCESS_KEYS
    _USER_SCENE_KEYS = registry._USER_SCENE_KEYS
    _USER_SCENE_TARGET_KEYS = registry._USER_SCENE_TARGET_KEYS
    _USER_SCENE_TILE_KEYS = registry._USER_SCENE_TILE_KEYS
    _USER_SURFACE_ACTION_GROUP_LABELS = registry._USER_SURFACE_ACTION_GROUP_LABELS
    _USER_SURFACE_ACTION_MAX = registry._USER_SURFACE_ACTION_MAX
    _USER_SURFACE_FILTER_MAX = registry._USER_SURFACE_FILTER_MAX
    _USER_SURFACE_NOISE_MARKERS = registry._USER_SURFACE_NOISE_MARKERS


def safe_text(value: Any, fallback: str = "") -> str:
    text = str(value or "").strip()
    if text.lower() in {"undefined", "null"}:
        text = ""
    return text or fallback


def safe_lower(value: Any) -> str:
    return safe_text(value).lower()


def parse_tags(raw: Any) -> set[str]:
    if isinstance(raw, list):
        items = raw
    else:
        items = str(raw or "").split(",")
    out: set[str] = set()
    for item in items:
        val = safe_text(item).lower()
        if val:
            out.add(val)
    return out


def normalized_tags_for_item(item: dict) -> list[str]:
    tags = parse_tags(item.get("tags"))
    key = safe_text(item.get("key")).lower()
    code = safe_text(item.get("code")).lower()
    name = safe_text(item.get("name")).lower()
    target = item.get("target") if isinstance(item.get("target"), dict) else {}
    target_text = " ".join(
        [
            safe_text(target.get("menu_xmlid")).lower(),
            safe_text(target.get("action_xmlid")).lower(),
            safe_text(target.get("route")).lower(),
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


def strip_user_mode_fields(obj: Any) -> Any:
    if isinstance(obj, list):
        return [strip_user_mode_fields(item) for item in obj]
    if not isinstance(obj, dict):
        return obj
    out: dict[str, Any] = {}
    for key, value in obj.items():
        if str(key or "").strip() in _USER_MODE_STRIP_KEYS:
            continue
        out[key] = strip_user_mode_fields(value)
    return out


def pick_fields(raw: dict, allowed_keys: tuple[str, ...] | list[str]) -> dict:
    out: dict[str, Any] = {}
    for key in allowed_keys:
        if key in raw:
            out[key] = raw.get(key)
    return out


def sanitize_capability_for_user(item: dict) -> dict:
    cap = pick_fields(dict(item), _USER_CAPABILITY_KEYS)
    payload = cap.get("default_payload")
    if isinstance(payload, dict):
        cap["default_payload"] = strip_user_mode_fields(payload)
    return cap


def sanitize_scene_for_user(item: dict) -> dict:
    scene = pick_fields(dict(item), _USER_SCENE_KEYS)
    scene = strip_user_mode_fields(scene)
    scene["code"] = safe_text(scene.get("code") or scene.get("key"))
    scene["key"] = safe_text(scene.get("key"), scene.get("code"))
    scene["name"] = safe_text(scene.get("name"), scene.get("code") or "未命名场景")
    target = scene.get("target")
    if isinstance(target, dict):
        scene["target"] = strip_user_mode_fields(pick_fields(target, _USER_SCENE_TARGET_KEYS))
    access = scene.get("access")
    if isinstance(access, dict):
        scene["access"] = strip_user_mode_fields(pick_fields(access, _USER_SCENE_ACCESS_KEYS))
    tiles = scene.get("tiles")
    if isinstance(tiles, list):
        cleaned_tiles = []
        for tile in tiles:
            if not isinstance(tile, dict):
                continue
            cleaned_tiles.append(strip_user_mode_fields(pick_fields(tile, _USER_SCENE_TILE_KEYS)))
        scene["tiles"] = cleaned_tiles
    scene["tags"] = normalized_tags_for_item(scene)
    return scene


def is_numeric_token(value: Any) -> bool:
    text = safe_text(value)
    return bool(text) and text.isdigit()


def contains_noise_marker(*values: Any) -> bool:
    merged = " ".join(safe_lower(item) for item in values if safe_text(item))
    if not merged:
        return False
    return any(marker in merged for marker in _USER_SURFACE_NOISE_MARKERS)


def is_noisy_filter_row(row: dict) -> bool:
    key = safe_text(row.get("key"))
    label = safe_text(row.get("label") or key)
    if not key or not label:
        return True
    if is_numeric_token(key) or is_numeric_token(label):
        return True
    return contains_noise_marker(key, label, row.get("domain_raw"), row.get("context_raw"))


def sanitize_user_search_filters(data: dict) -> None:
    search = dict(data.get("search")) if isinstance(data.get("search"), dict) else {}
    rows = search.get("filters")
    if not isinstance(rows, list):
        return
    out: list[dict] = []
    seen: set[str] = set()
    for row in rows:
        if not isinstance(row, dict):
            continue
        if is_noisy_filter_row(row):
            continue
        key = safe_text(row.get("key"))
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(row)
        if len(out) >= _USER_SURFACE_FILTER_MAX:
            break
    search["filters"] = out
    data["search"] = search


def is_noisy_action_row(row: dict) -> bool:
    key = safe_text(row.get("key"))
    label = safe_text(row.get("label") or key)
    if not key or not label:
        return True
    selection = safe_lower(row.get("selection"))
    if selection == "multi":
        return False
    if is_numeric_token(key) or is_numeric_token(label):
        return True
    return contains_noise_marker(key, label, row.get("name"), row.get("xml_id"))


def classify_user_surface_action_group(action: dict) -> str:
    key = safe_lower(action.get("key"))
    label = safe_lower(action.get("label"))
    merged = f"{key} {label}"
    if any(marker in merged for marker in ("提交", "审批", "transition", "workflow", "lifecycle", "阶段")):
        return "workflow"
    if any(marker in merged for marker in ("查看", "open", "dashboard", "看板", "列表", "台账")):
        return "drilldown"
    if any(marker in merged for marker in ("创建", "保存", "新增", "submit", "create", "save")):
        return "basic"
    return "other"


def build_user_surface_action_groups(rows: list[dict]) -> list[dict]:
    grouped: dict[str, list[dict]] = {"basic": [], "workflow": [], "drilldown": [], "other": []}
    for row in rows:
        if not isinstance(row, dict):
            continue
        grouped.setdefault(classify_user_surface_action_group(row), []).append(row)
    result: list[dict] = []
    for key in ("basic", "workflow", "drilldown", "other"):
        actions = grouped.get(key) or []
        if not actions:
            continue
        primary = actions[:_PROJECT_FORM_ACTION_GROUP_LIMIT]
        overflow = actions[_PROJECT_FORM_ACTION_GROUP_LIMIT:]
        result.append(
            {
                "key": key,
                "label": _USER_SURFACE_ACTION_GROUP_LABELS.get(key, key),
                "actions": primary,
                "overflow_actions": overflow,
                "overflow_count": len(overflow),
            }
        )
    return result


def sanitize_user_action_rows(rows: Any, max_count: int = _USER_SURFACE_ACTION_MAX) -> list[dict]:
    if not isinstance(rows, list):
        return []
    cleaned: list[dict] = []
    seen: set[str] = set()
    for row in rows:
        if not isinstance(row, dict):
            continue
        if is_noisy_action_row(row):
            continue
        key = safe_text(row.get("key"))
        if not key or key in seen:
            continue
        seen.add(key)
        cleaned.append(row)
    if len(cleaned) <= max_count:
        return cleaned

    multi_rows = [row for row in cleaned if safe_lower(row.get("selection")) == "multi"]
    other_rows = [row for row in cleaned if safe_lower(row.get("selection")) != "multi"]
    if len(multi_rows) >= max_count:
        return multi_rows
    return multi_rows + other_rows[: max_count - len(multi_rows)]


def apply_user_surface_noise_reduction(data: dict) -> None:
    sanitize_user_search_filters(data)
    action_rows: list[dict] = []
    if isinstance(data.get("buttons"), list):
        data["buttons"] = sanitize_user_action_rows(data.get("buttons"))
        action_rows.extend(data["buttons"])
    toolbar = dict(data.get("toolbar")) if isinstance(data.get("toolbar"), dict) else {}
    if toolbar:
        for section in ("header", "sidebar", "footer"):
            if isinstance(toolbar.get(section), list):
                toolbar[section] = sanitize_user_action_rows(toolbar.get(section), max_count=4)
                action_rows.extend(toolbar[section])
        data["toolbar"] = toolbar
    if action_rows and not isinstance(data.get("action_groups"), list):
        data["action_groups"] = build_user_surface_action_groups(action_rows)
