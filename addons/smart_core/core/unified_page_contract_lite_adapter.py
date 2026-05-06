# -*- coding: utf-8 -*-
"""Pure adapter for Unified Semantic Page Contract Lite.

This module is intentionally side-effect free. It does not register an Odoo
model, does not touch public intents, and does not change ui.contract output.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, Iterable, List

from .source_authority import build_source_authority_contract

LITE_CONTRACT_VERSION = "2.0.0"
SOURCE_KIND = "unified_page_contract_lite_projection"
SOURCE_AUTHORITIES = ("legacy_ui_contract", "lite_contract_schema")
NO_BUSINESS_FACT_AUTHORITY = True


def source_authority_contract() -> Dict[str, Any]:
    return build_source_authority_contract(
        kind=SOURCE_KIND,
        authorities=SOURCE_AUTHORITIES,
        no_business_fact_authority=NO_BUSINESS_FACT_AUTHORITY,
        runtime_carrier="unified_page_contract_lite_adapter",
    )

LITE_TOP_LEVEL_KEYS = {
    "pageInfo",
    "layoutContract",
    "statusContract",
    "actionContract",
    "dataContract",
    "meta",
}
SUPPORTED_CLIENT_TYPES = {"web_pc", "wx_mini", "harmony_h5"}
SUPPORTED_VIEW_TYPES = {"form", "tree", "list", "kanban", "search", "gantt", "popup", "combine"}

ZONE_CONTAINER_TYPES = {
    "header_zone": "section",
    "summary_zone": "section",
    "detail_zone": "group",
    "relation_zone": "x2many",
    "action_zone": "section",
    "collaboration_zone": "section",
    "insight_zone": "section",
    "attachment_zone": "section",
}

BLOCK_TITLES = {
    "title_block": "标题",
    "status_block": "状态",
    "action_bar_block": "操作",
    "field_group_block": "字段",
    "notebook_block": "页签",
    "relation_table_block": "关联明细",
    "relation_card_block": "关联卡片",
    "stat_button_block": "统计按钮",
    "chatter_block": "协作",
    "attachment_block": "附件",
    "timeline_block": "时间线",
    "risk_alert_block": "风险",
    "ai_recommendation_block": "建议",
    "next_action_block": "下一步",
}

FIELD_TYPE_TO_WIDGET = {
    "char": "input",
    "text": "textarea",
    "html": "textarea",
    "selection": "select",
    "many2one": "select",
    "many2many": "table",
    "one2many": "table",
    "date": "date",
    "datetime": "date",
    "integer": "number",
    "float": "number",
    "monetary": "number",
    "boolean": "checkbox",
}


def _dict(value: Any) -> Dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _list(value: Any) -> List[Any]:
    return value if isinstance(value, list) else []


def _text(value: Any, default: str = "") -> str:
    text = str(value or "").strip()
    return text or default


def _safe_id(value: Any, default: str) -> str:
    raw = _text(value, default)
    out = []
    for char in raw:
        if char.isalnum() or char in "_.:-":
            out.append(char)
        elif char in " /":
            out.append(".")
    token = "".join(out).strip(".") or default
    if not token[0].isalpha():
        token = f"x.{token}"
    return token


def _view_type(value: Any) -> str:
    raw = _text(value, "form").split(",")[0].strip().lower() or "form"
    if raw == "tree":
        return "tree"
    return raw if raw in SUPPORTED_VIEW_TYPES else "form"


def _client_type(value: Any) -> str:
    raw = _text(value, "web_pc")
    return raw if raw in SUPPORTED_CLIENT_TYPES else "web_pc"


def _semantic_page(source: Dict[str, Any]) -> Dict[str, Any]:
    return _dict(source.get("semantic_page"))


def _source_model(source: Dict[str, Any], semantic_page: Dict[str, Any]) -> str:
    return _text(semantic_page.get("model"), "unknown.model")


def _source_view_type(source: Dict[str, Any], semantic_page: Dict[str, Any]) -> str:
    return _view_type(semantic_page.get("view_type"))


def _field_map(source: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    fields = _dict(source.get("fields"))
    out: Dict[str, Dict[str, Any]] = {}
    for name, desc in fields.items():
        key = _text(name)
        if not key:
            continue
        out[key] = dict(desc) if isinstance(desc, dict) else {"label": key}
    return out


def _field_label(name: str, desc: Dict[str, Any]) -> str:
    return _text(desc.get("label") or desc.get("string") or desc.get("name"), name)


def _widget_type(desc: Dict[str, Any]) -> str:
    raw = _text(desc.get("widgetType") or desc.get("widget_type"))
    if raw:
        return raw
    ftype = _text(desc.get("type") or desc.get("ttype")).lower()
    return FIELD_TYPE_TO_WIDGET.get(ftype, "input")


def _component_for_widget(widget_type: str) -> str:
    if widget_type in {"table", "tree"}:
        return "table"
    if widget_type == "gantt":
        return "gantt"
    if widget_type == "display":
        return "display"
    return widget_type


def _widget_for_field(field_name: str, desc: Dict[str, Any]) -> Dict[str, Any]:
    widget_type = _widget_type(desc)
    return {
        "widgetId": _safe_id(f"field.{field_name}", "field.unknown"),
        "widgetType": widget_type,
        "fieldCode": _safe_id(field_name, "field"),
        "label": _field_label(field_name, desc),
        "component": _component_for_widget(widget_type),
        "props": {},
    }


def _iter_fields_from_block(block: Dict[str, Any]) -> Iterable[str]:
    data = _dict(block.get("data"))
    for key in ("fields", "field_names", "columns"):
        raw = data.get(key)
        if isinstance(raw, list):
            for item in raw:
                if isinstance(item, str) and item.strip():
                    yield item.strip()
                elif isinstance(item, dict) and _text(item.get("name") or item.get("field")):
                    yield _text(item.get("name") or item.get("field"))
    layout = data.get("layout")
    if isinstance(layout, list):
        for item in layout:
            if isinstance(item, str) and item.strip():
                yield item.strip()
            elif isinstance(item, dict) and _text(item.get("name") or item.get("field")):
                yield _text(item.get("name") or item.get("field"))
    items = data.get("items")
    if isinstance(items, list):
        for item in items:
            if isinstance(item, dict) and _text(item.get("field")):
                yield _text(item.get("field"))


def _container_from_zone(zone: Dict[str, Any], fields: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    zone_key = _safe_id(zone.get("key"), "zone")
    blocks = _list(zone.get("blocks"))
    container = {
        "containerId": _safe_id(f"zone.{zone_key}", "zone.unknown"),
        "containerType": ZONE_CONTAINER_TYPES.get(zone_key, "section"),
        "title": _text(zone.get("title"), zone_key.replace("_", " ")),
        "children": [],
        "widgetList": [],
    }
    seen_fields: set[str] = set()
    for block_index, block in enumerate(blocks, start=1):
        if not isinstance(block, dict):
            continue
        block_type = _text(block.get("type"), f"block.{block_index}")
        block_fields = [field for field in _iter_fields_from_block(block) if field in fields]
        if block_fields:
            child = {
                "containerId": _safe_id(f"{zone_key}.{block_type}.{block_index}", "container.block"),
                "containerType": "x2many" if block_type in {"relation_table_block", "relation_card_block"} else "group",
                "title": BLOCK_TITLES.get(block_type, block_type),
                "children": [],
                "widgetList": [],
            }
            for field_name in block_fields:
                seen_fields.add(field_name)
                child["widgetList"].append(_widget_for_field(field_name, fields[field_name]))
            container["children"].append(child)
            continue
        if block_type in {"title_block", "status_block", "chatter_block", "attachment_block"}:
            widget_id = _safe_id(f"block.{zone_key}.{block_type}", "block.widget")
            container["widgetList"].append(
                {
                    "widgetId": widget_id,
                    "widgetType": "display",
                    "fieldCode": widget_id,
                    "label": BLOCK_TITLES.get(block_type, block_type),
                    "component": "display",
                    "props": {},
                }
            )
    if not container["children"] and not container["widgetList"] and fields:
        for field_name, desc in fields.items():
            if field_name in seen_fields:
                continue
            container["widgetList"].append(_widget_for_field(field_name, desc))
    return container


def _layout_contract(source: Dict[str, Any], semantic_page: Dict[str, Any]) -> Dict[str, Any]:
    fields = _field_map(source)
    zones = _list(semantic_page.get("zones"))
    containers = [
        _container_from_zone(zone, fields)
        for zone in zones
        if isinstance(zone, dict)
    ]
    if not containers:
        containers = [
            {
                "containerId": "main",
                "containerType": "group",
                "title": "Main",
                "children": [],
                "widgetList": [_widget_for_field(name, desc) for name, desc in fields.items()],
            }
        ]
    if _source_view_type(source, semantic_page) == "search" and fields and not any(_collect_widgets(containers)):
        containers.append(
            {
                "containerId": "search.fields",
                "containerType": "group",
                "title": "Search",
                "children": [],
                "widgetList": [_widget_for_field(name, desc) for name, desc in fields.items()],
            }
        )
    return {
        "layoutType": _source_view_type(source, semantic_page),
        "containerList": containers,
    }


def _collect_widgets(containers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    widgets: List[Dict[str, Any]] = []
    for container in containers:
        widgets.extend([row for row in _list(container.get("widgetList")) if isinstance(row, dict)])
        widgets.extend(_collect_widgets([row for row in _list(container.get("children")) if isinstance(row, dict)]))
    return widgets


def _bool_from_profiles(policy: Dict[str, Any], key: str, profile: str, default: bool) -> bool:
    values = policy.get(key)
    if isinstance(values, list):
        return profile in {_text(item).lower() for item in values}
    if isinstance(values, bool):
        return values
    return default


def _status_contract(source: Dict[str, Any], layout: Dict[str, Any]) -> Dict[str, Any]:
    fields = _field_map(source)
    field_policies = _dict(source.get("field_policies"))
    modifiers = _dict(source.get("modifiers") or source.get("field_modifiers"))
    access_policy = _dict(source.get("access_policy"))
    profile = _text(source.get("render_profile"), "edit").lower()
    write_allowed = bool(_dict(_dict(_semantic_page(source)).get("permission_verdicts")).get("write", {}).get("allowed", True))
    blocked_fields = {
        _text(row.get("field"))
        for row in _list(access_policy.get("blocked_fields")) + _list(access_policy.get("degraded_fields"))
        if isinstance(row, dict) and _text(row.get("field"))
    }

    widget_status = []
    for widget in _collect_widgets(_list(layout.get("containerList"))):
        widget_id = _text(widget.get("widgetId"))
        field_name = _text(widget.get("fieldCode"))
        desc = fields.get(field_name, {})
        policy = _dict(field_policies.get(field_name))
        field_modifiers = _dict(modifiers.get(field_name))
        visible = _bool_from_profiles(policy, "visible_profiles", profile, True)
        readonly = _bool_from_profiles(policy, "readonly_profiles", profile, not write_allowed)
        required = bool(desc.get("required", False))
        required = _bool_from_profiles(policy, "required_profiles", profile, required)
        if "invisible" in field_modifiers:
            visible = not bool(field_modifiers.get("invisible"))
        if "readonly" in field_modifiers:
            readonly = bool(field_modifiers.get("readonly"))
        if "required" in field_modifiers:
            required = bool(field_modifiers.get("required"))
        disabled = field_name in blocked_fields or access_policy.get("mode") == "block" and field_name == "__model__"
        widget_status.append(
            {
                "widgetId": _safe_id(widget_id, "field.unknown"),
                "visible": bool(visible),
                "readonly": bool(readonly),
                "required": bool(required),
                "disabled": bool(disabled),
            }
        )

    button_status = []
    for btn_id, policy in _dict(source.get("action_policies")).items():
        row = _dict(policy)
        button_status.append(
            {
                "btnId": _safe_id(f"btn.{btn_id}", "btn.action"),
                "visible": bool(row.get("visible", True)),
                "disabled": not bool(row.get("enabled", True)),
            }
        )
    actions = _dict(_semantic_page(source).get("actions"))
    for group_name in ("header_actions", "record_actions", "toolbar_actions"):
        for action in _list(actions.get(group_name)):
            if not isinstance(action, dict):
                continue
            key = _text(action.get("key"))
            if not key:
                continue
            btn_id = _safe_id(f"btn.{key}", "btn.action")
            if any(row.get("btnId") == btn_id for row in button_status):
                continue
            button_status.append(
                {
                    "btnId": btn_id,
                    "visible": True,
                    "disabled": not bool(action.get("enabled", True)),
                }
            )
    return {"widgetStatus": widget_status, "buttonStatus": button_status}


def _action_contract(source: Dict[str, Any]) -> Dict[str, Any]:
    rules: List[Dict[str, Any]] = []
    seen: set[str] = set()

    def add_rule(action_id: str, trigger: str, source_widget_id: str, refresh: str = "partial") -> None:
        stable_action_id = _safe_id(action_id, "action.unknown")
        if stable_action_id in seen:
            return
        seen.add(stable_action_id)
        rules.append(
            {
                "actionId": stable_action_id,
                "triggerType": trigger,
                "sourceWidgetId": _safe_id(source_widget_id, "field.unknown"),
                "dispatchMode": "server",
                "refreshMode": refresh,
            }
        )

    for field_name in _list(source.get("onchange_fields")):
        name = _text(field_name)
        if name:
            add_rule(f"field.{name}.change", "change", f"field.{name}")

    actions = _dict(_semantic_page(source).get("actions"))
    for group_name in ("header_actions", "record_actions", "toolbar_actions"):
        for action in _list(actions.get(group_name)):
            if not isinstance(action, dict):
                continue
            key = _text(action.get("key"))
            if key:
                add_rule(f"btn.{key}.click", "click", f"btn.{key}")

    for action_key in _dict(source.get("action_policies")):
        key = _text(action_key)
        if key:
            add_rule(f"btn.{key}.click", "click", f"btn.{key}")

    if not any(rule.get("actionId") == "form.save.submit" for rule in rules):
        add_rule("form.save.submit", "submit", "btn.save")
    return {"actionRuleList": rules}


def _data_contract(source: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "mainData": deepcopy(_dict(source.get("record"))),
        "relationData": deepcopy(_dict(source.get("relation_rows"))),
        "dictData": deepcopy(_dict(source.get("dict_data"))),
    }


def build_lite_contract(source: Dict[str, Any], *, client_type: str = "web_pc", trace_id: str = "") -> Dict[str, Any]:
    semantic_page = _semantic_page(source)
    model = _source_model(source, semantic_page)
    view_type = _source_view_type(source, semantic_page)
    page_id = _safe_id(source.get("page_id") or f"{model}.{view_type}", "page.form")
    scene_key = _safe_id(source.get("scene_key") or page_id, page_id)
    layout = _layout_contract(source, semantic_page)
    return {
        "pageInfo": {
            "pageId": page_id,
            "sceneKey": scene_key,
            "model": model,
            "viewType": view_type,
            "clientType": _client_type(client_type or source.get("client_type")),
            "contractVersion": LITE_CONTRACT_VERSION,
        },
        "layoutContract": layout,
        "statusContract": _status_contract(source, layout),
        "actionContract": _action_contract(source),
        "dataContract": _data_contract(source),
        "meta": {
            "etag": _text(source.get("etag"), f"lite-{page_id}"),
            "traceId": _safe_id(trace_id or source.get("trace_id"), f"trace.{page_id}"),
            "semanticAdapter": {
                "source": "odoo.semantic_page",
                "adapterVersion": LITE_CONTRACT_VERSION,
            },
        },
    }


def build_lite_patch(onchange_payload: Dict[str, Any], *, operation: str = "merge") -> Dict[str, Any]:
    patch = _dict(onchange_payload.get("patch"))
    modifiers_patch = _dict(onchange_payload.get("modifiers_patch"))
    button_status_patch = onchange_payload.get("button_status_patch")
    line_patches = _list(onchange_payload.get("line_patches"))
    widget_status = []
    for field_name, modifiers in modifiers_patch.items():
        row = _dict(modifiers)
        widget_status.append(
            {
                "widgetId": _safe_id(f"field.{field_name}", "field.unknown"),
                "visible": not bool(row.get("invisible", False)),
                "readonly": bool(row.get("readonly", False)),
                "required": bool(row.get("required", False)),
                "disabled": False,
            }
        )
    button_status = []
    if isinstance(button_status_patch, dict):
        items = button_status_patch.items()
    elif isinstance(button_status_patch, list):
        items = [
            (_text(row.get("btnId") or row.get("key") or row.get("button")), row)
            for row in button_status_patch
            if isinstance(row, dict)
        ]
    else:
        items = []
    for button_key, status in items:
        row = _dict(status)
        key = _text(button_key)
        if not key:
            continue
        button_status.append(
            {
                "btnId": _safe_id(key if key.startswith("btn.") else f"btn.{key}", "btn.action"),
                "visible": bool(row.get("visible", True)),
                "disabled": bool(row.get("disabled", not bool(row.get("enabled", True)))),
            }
        )
    relation_data: Dict[str, Any] = {}
    for row in line_patches:
        if not isinstance(row, dict):
            continue
        field_name = _text(row.get("field"))
        if not field_name:
            continue
        row_key = _safe_id(row.get("row_key") or row.get("row_id"), "row")
        for child_field, child_modifiers in _dict(row.get("modifiers_patch")).items():
            child_row = _dict(child_modifiers)
            widget_status.append(
                {
                    "widgetId": _safe_id(f"field.{field_name}.{row_key}.{child_field}", "field.row"),
                    "visible": not bool(child_row.get("invisible", False)),
                    "readonly": bool(child_row.get("readonly", False)),
                    "required": bool(child_row.get("required", False)),
                    "disabled": False,
                }
            )
        relation_data.setdefault(field_name, {"linePatches": []})
        relation_data[field_name]["linePatches"].append(
            {
                "field": field_name,
                "row_key": _text(row.get("row_key")),
                "row_id": row.get("row_id") if isinstance(row.get("row_id"), int) else 0,
                "patch": deepcopy(_dict(row.get("patch"))),
                "row_state": _text(row.get("row_state"), "keep"),
                "command_hint": deepcopy(_list(row.get("command_hint"))),
            }
        )
    return {
        "updateType": "partial",
        "operation": operation if operation in {"replace", "merge"} else "merge",
        "statusPatch": {"widgetStatus": widget_status, "buttonStatus": button_status},
        "dataPatch": {"mainData": deepcopy(patch), "relationData": relation_data, "dictData": {}},
        "layoutPatch": {},
    }
