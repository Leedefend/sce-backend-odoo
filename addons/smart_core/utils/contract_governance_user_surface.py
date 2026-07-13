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


def _as_dict(value: Any) -> dict:
    return dict(value) if isinstance(value, dict) else {}


def view_type_tokens(*values: Any) -> set[str]:
    tokens: set[str] = set()
    for value in values:
        for item in safe_lower(value).replace(";", ",").split(","):
            token = item.strip()
            if token:
                tokens.add(token)
    return tokens


def apply_user_surface_policies(
    data: dict,
    *,
    primary_model: str,
    record_context_clear_models: set[str],
    delete_only_models: set[str],
    mark_model_policy: Any,
    filter_max: int,
    action_max: int,
    primary_filter_max: int,
    primary_action_max: int,
) -> None:
    head = _as_dict(data.get("head"))
    view_types = view_type_tokens(head.get("view_type"), data.get("view_type"))
    model = safe_text(head.get("model") or data.get("model"))
    fields_map = _as_dict(data.get("fields"))
    views = _as_dict(data.get("views"))
    has_list_view = bool(_as_dict(views.get("tree") or views.get("list")))
    active_field = "active" if "active" in fields_map else ""
    filters_primary_max = primary_filter_max
    actions_primary_max = primary_action_max
    record_open_policy = {
        "carry_query_mode": "preserve",
    }
    batch_policy = {
        "enabled": False,
        "active_field": "",
        "archive_value": None,
        "activate_value": None,
        "delete_allowed": False,
        "delete_only_mode": False,
        "delete_mode": "none",
        "available_actions": [],
    }
    if "form" in view_types and not (view_types & {"tree", "list"} or has_list_view):
        filters_primary_max = 0
        actions_primary_max = 3
    if view_types & {"tree", "list"} or has_list_view:
        permissions = _as_dict(data.get("permissions"))
        effective = _as_dict(permissions.get("effective"))
        rights = _as_dict(effective.get("rights"))
        write_allowed = bool(rights.get("write"))
        unlink_right_allowed = bool(rights.get("unlink"))
        delete_policy = _as_dict(data.get("delete_policy"))
        unlink_allowed = bool(delete_policy.get("allowed")) and safe_lower(delete_policy.get("delete_mode")) == "unlink"
        if model in record_context_clear_models:
            mark_model_policy(data, f"{model}.record_open_context")
        if model in delete_only_models:
            mark_model_policy(data, f"{model}.delete_only")
        delete_allowed = bool(unlink_right_allowed and unlink_allowed)
        delete_only_mode = bool(delete_allowed and model in delete_only_models)
        available_actions = []
        if write_allowed and active_field and not delete_only_mode:
            available_actions.extend(["archive", "activate"])
        if delete_allowed:
            available_actions.append("delete")
        if model in record_context_clear_models:
            record_open_policy = {
                "carry_query_mode": "clear_scene_context",
            }
        batch_policy = {
            "enabled": bool(available_actions),
            "active_field": active_field,
            "archive_value": False if active_field else None,
            "activate_value": True if active_field else None,
            "delete_allowed": delete_allowed,
            "delete_only_mode": delete_only_mode,
            "delete_mode": "unlink" if delete_allowed and "delete" in available_actions else "none",
            "available_actions": available_actions,
        }
        if not write_allowed and not unlink_right_allowed:
            batch_policy["available_actions"] = []
            batch_policy["enabled"] = False
            batch_policy["delete_mode"] = "none"
    if model and primary_model and model == primary_model:
        filters_primary_max = min(filters_primary_max, 4)
        actions_primary_max = min(actions_primary_max, 3)
    data["surface_policies"] = {
        "filters_primary_max": filters_primary_max,
        "actions_primary_max": actions_primary_max,
        "filters_max": filter_max,
        "actions_max": action_max,
        "delete_mode": batch_policy.get("delete_mode") or "none",
        "batch_policy": batch_policy,
        "record_open_policy": record_open_policy,
    }
