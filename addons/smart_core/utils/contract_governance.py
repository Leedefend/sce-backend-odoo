# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any

CONTRACT_MODES = {"user", "hud"}
_NON_HUD_STRIP_KEYS = {
    "diagnostic",
    "scene_diagnostics",
    "scene_channel_selector",
    "scene_channel_source_ref",
}
_USER_MODE_STRIP_KEYS = {
    "action_xmlid",
    "menu_xmlid",
    "scene_key",
    "res_id",
    "id",
}
_USER_CAPABILITY_KEYS = {
    "key",
    "name",
    "ui_label",
    "ui_hint",
    "intent",
    "status",
    "state",
    "reason",
    "reason_code",
    "version",
    "tags",
    "default_payload",
}
_USER_SCENE_KEYS = {
    "code",
    "key",
    "name",
    "title",
    "label",
    "icon",
    "route",
    "target",
    "layout",
    "tiles",
    "capabilities",
    "required_capabilities",
    "breadcrumbs",
    "list_profile",
    "filters",
    "default_sort",
    "access",
    "status",
    "state",
    "version",
    "tags",
}
_USER_SCENE_TARGET_KEYS = {
    "route",
    "action_id",
    "menu_id",
    "model",
    "view_mode",
    "view_type",
    "record_id",
}
_USER_SCENE_TILE_KEYS = {
    "key",
    "title",
    "subtitle",
    "icon",
    "status",
    "state",
    "reason",
    "reason_code",
    "route",
    "intent",
    "payload",
    "capabilities",
    "required_capabilities",
    "requiredCapabilities",
    "allowed",
    "tags",
}
_USER_SCENE_ACCESS_KEYS = {
    "allowed",
    "state",
    "reason_code",
    "reason",
    "required_capabilities",
    "suggested_action",
}

_PROJECT_FORM_PRIMARY_FIELDS = [
    "name",
    "project_code",
    "project_type_id",
    "project_category_id",
    "lifecycle_state",
    "stage_id",
    "manager_id",
    "user_id",
    "owner_id",
    "company_id",
    "start_date",
    "end_date",
    "contract_no",
    "budget_total",
    "location",
]
_PROJECT_FORM_FIELD_MAX = 25
_PROJECT_FORM_HEADER_ACTION_MAX = 3
_PROJECT_FORM_SMART_ACTION_MAX = 4
_PROJECT_FORM_ACTION_DEMOTE_KEYWORDS = {
    "设置阶段",
    "评分",
    "cron",
    "ir_cron",
    "演示",
    "showcase",
}
_PROJECT_FORM_ACTION_PRIORITIES = (
    "提交",
    "进入下一阶段",
    "创建项目",
    "保存",
    "查看任务",
)


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


def _contains_demo_marker(value: Any) -> bool:
    text = _safe_text(value).lower()
    if not text:
        return False
    return any(marker in text for marker in ("demo", "showcase", "smart_construction_demo"))


def _has_demo_semantics(item: dict) -> bool:
    if not isinstance(item, dict):
        return False
    tags = _parse_tags(item.get("tags"))
    if any(_contains_demo_marker(tag) for tag in tags):
        return True
    for key in ("key", "code", "name", "title", "label", "scene_key"):
        if _contains_demo_marker(item.get(key)):
            return True
    target = item.get("target") if isinstance(item.get("target"), dict) else {}
    for key in ("menu_xmlid", "action_xmlid", "route"):
        if _contains_demo_marker(target.get(key)):
            return True
    return False


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
    if "showcase" in combined or "demo" in combined or "smart_construction_demo" in combined:
        tags.add("demo")
    return sorted(tags)


def is_internal_or_smoke(item: dict) -> bool:
    if not isinstance(item, dict):
        return False
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
    if "internal" in tags or "smoke" in tags or "demo" in tags:
        return True
    if item.get("is_test") or item.get("smoke_test"):
        return True
    combined = f"{key} {code} {name} {target_text}"
    return (
        "smoke" in combined
        or "internal" in combined
        or "showcase" in combined
        or "demo" in combined
        or "smart_construction_demo" in combined
    )


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


def _pick_fields(raw: dict, allowed_keys: set[str]) -> dict:
    out: dict[str, Any] = {}
    for key in allowed_keys:
        if key in raw:
            out[key] = raw.get(key)
    return out


def _sanitize_capability_for_user(item: dict) -> dict:
    cap = _pick_fields(dict(item), _USER_CAPABILITY_KEYS)
    payload = cap.get("default_payload")
    if isinstance(payload, dict):
        cap["default_payload"] = _strip_user_mode_fields(payload)
    return cap


def _sanitize_scene_for_user(item: dict) -> dict:
    scene = _pick_fields(dict(item), _USER_SCENE_KEYS)
    scene = _strip_user_mode_fields(scene)
    scene["code"] = _safe_text(scene.get("code") or scene.get("key"))
    scene["key"] = _safe_text(scene.get("key"), scene.get("code"))
    scene["name"] = _safe_text(scene.get("name"), scene.get("code") or "未命名场景")
    target = scene.get("target")
    if isinstance(target, dict):
        scene["target"] = _strip_user_mode_fields(_pick_fields(target, _USER_SCENE_TARGET_KEYS))
    access = scene.get("access")
    if isinstance(access, dict):
        scene["access"] = _strip_user_mode_fields(_pick_fields(access, _USER_SCENE_ACCESS_KEYS))
    tiles = scene.get("tiles")
    if isinstance(tiles, list):
        cleaned_tiles = []
        for tile in tiles:
            if not isinstance(tile, dict):
                continue
            cleaned_tiles.append(_strip_user_mode_fields(_pick_fields(tile, _USER_SCENE_TILE_KEYS)))
        scene["tiles"] = cleaned_tiles
    scene["tags"] = _normalized_tags_for_item(scene)
    return scene


def _as_dict(value: Any) -> dict:
    return dict(value) if isinstance(value, dict) else {}


def _safe_lower(value: Any) -> str:
    return _safe_text(value).lower()


def _is_project_form_contract(data: dict) -> bool:
    head = _as_dict(data.get("head"))
    views = _as_dict(data.get("views"))
    form_view = _as_dict(views.get("form"))
    permissions = _as_dict(data.get("permissions"))
    model = _safe_text(
        head.get("model")
        or data.get("model")
        or form_view.get("model")
        or permissions.get("model")
    )
    view_type = _safe_text(head.get("view_type") or data.get("view_type")).lower()
    if not view_type and isinstance(views.get("form"), dict):
        view_type = "form"
    return model == "project.project" and view_type == "form"


def _is_technical_field(name: str, descriptor: dict) -> bool:
    low = _safe_lower(name)
    if not low:
        return True
    if low in {"id", "__last_update", "display_name"}:
        return True
    if low.startswith(("create_", "write_", "message_", "activity_", "access_", "alias_", "website_")):
        return True
    if low.endswith(("_ids", "_id_count")) and low not in {
        "project_type_id",
        "project_category_id",
        "stage_id",
        "manager_id",
        "user_id",
        "owner_id",
        "company_id",
    }:
        return True
    ttype = _safe_lower(descriptor.get("type") or descriptor.get("ttype"))
    if ttype in {"one2many", "many2many", "properties_definition"}:
        return True
    return False


def _pick_project_form_fields(data: dict) -> list[str]:
    fields_map = _as_dict(data.get("fields"))
    if not fields_map:
        return []
    layout = _as_dict(_as_dict(data.get("views")).get("form")).get("layout") or []
    ordered_fields: list[str] = []
    for node in layout if isinstance(layout, list) else []:
        if not isinstance(node, dict):
            continue
        if _safe_lower(node.get("type")) != "field":
            continue
        name = _safe_text(node.get("name"))
        if name and name not in ordered_fields:
            ordered_fields.append(name)

    selected: list[str] = []
    for name in _PROJECT_FORM_PRIMARY_FIELDS:
        descriptor = _as_dict(fields_map.get(name))
        if descriptor and not _is_technical_field(name, descriptor) and name not in selected:
            selected.append(name)

    for name in ordered_fields:
        if len(selected) >= _PROJECT_FORM_FIELD_MAX:
            break
        descriptor = _as_dict(fields_map.get(name))
        if not descriptor or _is_technical_field(name, descriptor):
            continue
        if name not in selected:
            selected.append(name)

    for name, descriptor_raw in fields_map.items():
        if len(selected) >= _PROJECT_FORM_FIELD_MAX:
            break
        descriptor = _as_dict(descriptor_raw)
        if _is_technical_field(name, descriptor):
            continue
        required = bool(descriptor.get("required"))
        readonly = bool(descriptor.get("readonly"))
        if required and not readonly and name not in selected:
            selected.append(name)

    if "name" in fields_map and "name" not in selected:
        selected.insert(0, "name")
    return selected[:_PROJECT_FORM_FIELD_MAX]


def _filter_project_form_layout(data: dict, selected_fields: set[str]) -> None:
    views = _as_dict(data.get("views"))
    form = _as_dict(views.get("form"))
    layout = form.get("layout")
    if not isinstance(layout, list):
        return
    filtered_layout: list[dict] = []
    for node in layout:
        if not isinstance(node, dict):
            continue
        node_type = _safe_lower(node.get("type"))
        if node_type == "field":
            name = _safe_text(node.get("name"))
            if name and name in selected_fields:
                filtered_layout.append(node)
            continue
        filtered_layout.append(node)

    if not any(_safe_lower(item.get("type")) == "field" for item in filtered_layout):
        for name in _PROJECT_FORM_PRIMARY_FIELDS:
            if name in selected_fields:
                filtered_layout.append({"type": "field", "name": name})
    form["layout"] = filtered_layout
    views["form"] = form
    data["views"] = views


def _action_priority(action: dict) -> int:
    label = _safe_text(action.get("label"))
    for idx, key in enumerate(_PROJECT_FORM_ACTION_PRIORITIES):
        if key and key in label:
            return idx
    return len(_PROJECT_FORM_ACTION_PRIORITIES) + 1


def _is_noisy_project_action(action: dict) -> bool:
    key = _safe_lower(action.get("key"))
    label = _safe_lower(action.get("label"))
    kind = _safe_lower(action.get("kind"))
    if kind == "server":
        return True
    if not label and not key:
        return True
    if label.isdigit():
        return True
    for marker in _PROJECT_FORM_ACTION_DEMOTE_KEYWORDS:
        if marker in key or marker in label:
            return True
    return False


def _govern_project_form_actions(data: dict) -> None:
    toolbar = _as_dict(data.get("toolbar"))
    if isinstance(toolbar.get("header"), list):
        toolbar["header"] = []
    data["toolbar"] = toolbar

    rows = data.get("buttons")
    if not isinstance(rows, list):
        return
    header_rows: list[dict] = []
    smart_rows: list[dict] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        if _is_noisy_project_action(row):
            continue
        level = _safe_lower(row.get("level"))
        if level == "header":
            header_rows.append(row)
        elif level in {"smart", "row"}:
            smart_rows.append(row)

    header_rows = sorted(header_rows, key=lambda item: (_action_priority(item), _safe_text(item.get("label"))))
    smart_rows = sorted(smart_rows, key=lambda item: (_action_priority(item), _safe_text(item.get("label"))))
    data["buttons"] = header_rows[:_PROJECT_FORM_HEADER_ACTION_MAX] + smart_rows[:_PROJECT_FORM_SMART_ACTION_MAX]


def _govern_project_form_contract_for_user(data: dict) -> None:
    selected = _pick_project_form_fields(data)
    selected_set = set(selected)
    fields_map = _as_dict(data.get("fields"))
    data["fields"] = {name: fields_map.get(name) for name in selected if name in fields_map}

    permissions = _as_dict(data.get("permissions"))
    field_groups = _as_dict(permissions.get("field_groups"))
    if field_groups:
        permissions["field_groups"] = {name: val for name, val in field_groups.items() if name in selected_set}
    data["permissions"] = permissions

    _filter_project_form_layout(data, selected_set)
    _govern_project_form_actions(data)


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

    nested_payload = data.get("data")
    if isinstance(nested_payload, dict):
        data["data"] = apply_contract_governance(nested_payload, contract_mode, inject_contract_mode=False)

    if isinstance(data.get("capabilities"), list):
        capabilities = normalize_capabilities(data.get("capabilities") or [])
        if contract_mode == "user":
            capabilities = [item for item in capabilities if not is_internal_or_smoke(item)]
            capabilities = [item for item in capabilities if not _has_demo_semantics(item)]
            capabilities = [_sanitize_capability_for_user(item) for item in capabilities]
        data["capabilities"] = capabilities

    if isinstance(data.get("scenes"), list):
        scenes = normalize_scenes(data.get("scenes") or [])
        if contract_mode == "user":
            scenes = [item for item in scenes if not is_internal_or_smoke(item)]
            scenes = [item for item in scenes if not _has_demo_semantics(item)]
            scenes = [_sanitize_scene_for_user(item) for item in scenes]
            scenes = [item for item in scenes if not _has_demo_semantics(item)]
        data["scenes"] = scenes

    if contract_mode == "user" and _is_project_form_contract(data):
        _govern_project_form_contract_for_user(data)

    if inject_contract_mode:
        data["contract_mode"] = contract_mode
    if contract_mode != "hud":
        for key in _NON_HUD_STRIP_KEYS:
            data.pop(key, None)
    return data
