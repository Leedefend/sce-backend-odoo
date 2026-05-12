# -*- coding: utf-8 -*-
from __future__ import annotations

import re
from copy import deepcopy
from hashlib import sha1
from typing import Any

from .source_authority import build_source_authority_contract

CONTRACT_VERSION = "2.1.0"
SOURCE_KIND = "unified_page_contract_v2_assembler_projection"
SOURCE_AUTHORITIES = ("ui_contract", "page_orchestration", "scene_contract", "unified_page_contract_v2_schema")
NO_BUSINESS_FACT_AUTHORITY = True


def source_authority_contract() -> dict[str, Any]:
    return build_source_authority_contract(
        kind=SOURCE_KIND,
        authorities=SOURCE_AUTHORITIES,
        no_business_fact_authority=NO_BUSINESS_FACT_AUTHORITY,
        runtime_carrier="unified_page_contract_v2_assembler",
    )

PATCH_VERSION = "2.1.0"
STABLE_CLIENT_TYPES = {"web_pc", "wx_mini", "harmony_h5"}


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _text(value: Any, default: str = "") -> str:
    text = str(value or "").strip()
    return text or default


def _stable_id(value: Any, fallback: str) -> str:
    raw = _text(value, fallback)
    out = []
    for char in raw:
        if char.isalnum() or char in "_.:-":
            out.append(char)
        elif char in " /":
            out.append(".")
    normalized = "".join(out).strip(".")
    if not normalized:
        normalized = fallback
    if not normalized[0].isalpha():
        normalized = f"id.{normalized}"
    return normalized


def _fingerprint(value: Any) -> str:
    import json

    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)
    return sha1(payload.encode("utf-8")).hexdigest()[:12]


def _resolve_source_type(source: dict[str, Any], explicit: str = "") -> str:
    if explicit:
        return explicit
    if _dict(source.get("scene_contract_v1")):
        return "scene_contract_v1"
    if _dict(source.get("page_orchestration_v1")):
        return "page_orchestration_v1"
    if "meta_fields" in source or source.get("view_type"):
        return "ui.contract"
    if source.get("schema_version") == "v1" and ("patch" in source or "modifiers_patch" in source):
        return "api.onchange"
    if _dict(source.get("page")) and _list(source.get("zones")):
        return "page_orchestration_v1"
    if _dict(source.get("identity")) and _dict(source.get("page")):
        return "scene_contract_v1"
    return "unknown"


def _component_key(widget_type: str) -> str:
    normalized = _text(widget_type).lower()
    if normalized.endswith("many2one"):
        return "sc.select.remote"
    mapping = {
        "input": "sc.input.text",
        "textarea": "sc.input.textarea",
        "number": "sc.input.number",
        "select": "sc.select.remote",
        "checkbox": "sc.input.boolean",
        "date": "sc.input.date",
        "datetime": "sc.input.datetime",
        "table": "sc.table.data",
        "tree": "sc.tree.data",
        "many2many_tags": "sc.select.tags",
        "button": "sc.button.action",
        "display": "sc.display.text",
    }
    return mapping.get(widget_type, "sc.display.text")


def _widget_type_from_field(field: dict[str, Any]) -> str:
    ttype = _text(field.get("ttype") or field.get("type")).lower()
    if ttype in {"selection", "many2one"}:
        return "select"
    if ttype in {"date", "datetime"}:
        return ttype
    if ttype in {"integer", "float", "monetary"}:
        return "number"
    if ttype in {"one2many", "many2many"}:
        widget_options = _dict(field.get("widget_options") or field.get("options"))
        if ttype == "many2many" and widget_options.get("color_field"):
            return "many2many_tags"
        return "table"
    if ttype in {"text", "html"}:
        return "textarea"
    if ttype in {"boolean"}:
        return "checkbox"
    return "input"


def _component_registry(component_keys: set[str]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for key in sorted(component_keys):
        out[key] = {
            "version": "1.0",
            "adapter": {
                "web_pc": _adapter_for(key, "web_pc"),
                "wx_mini": _adapter_for(key, "wx_mini"),
                "harmony_h5": _adapter_for(key, "harmony_h5"),
            },
        }
    return out


def _adapter_for(component_key: str, client_type: str) -> str:
    prefix = {"web_pc": "El", "wx_mini": "Wx", "harmony_h5": "H5"}.get(client_type, "H5")
    if "table" in component_key:
        return f"{prefix}Table"
    if "tree" in component_key:
        return f"{prefix}Tree"
    if "select" in component_key:
        return f"{prefix}Select"
    if "button" in component_key:
        return f"{prefix}Button"
    return f"{prefix}Input"


def _base_contract(
    *,
    page_id: str,
    scene_key: str,
    page_name: str,
    model: str,
    view_type: str,
    layout_type: str,
    client_type: str,
    source_type: str,
    source_payload: dict[str, Any],
    request_id: str,
) -> dict[str, Any]:
    client = client_type if client_type in STABLE_CLIENT_TYPES else "web_pc"
    fp = _fingerprint(source_payload)
    return {
        "pageInfo": {
            "pageId": _stable_id(page_id, "page.generated"),
            "sceneKey": _stable_id(scene_key, _stable_id(page_id, "scene.generated")),
            "pageName": page_name or page_id,
            "model": model,
            "viewType": view_type,
            "layoutType": layout_type,
            "renderMode": "governed",
            "contractVersion": CONTRACT_VERSION,
            "clientType": client,
        },
        "layoutContract": {
            "pageId": _stable_id(page_id, "page.generated"),
            "layoutType": layout_type,
            "adaptMode": "pc" if client == "web_pc" else "mobile",
            "containerTree": [],
            "layoutHints": {},
            "componentRegistry": {},
        },
        "statusContract": {
            "globalStatus": {"pageVisible": True, "pageAuth": "read"},
            "containerStatus": [],
            "widgetStatus": [],
            "buttonStatus": [],
            "selectorStatus": [],
        },
        "actionContract": {"actionRuleList": [], "dependencyGraph": {}},
        "dataContract": {
            "mainData": {},
            "tableRows": {},
            "relationRows": {},
            "dictData": {},
            "pagination": {},
            "dataSource": {},
            "dataMeta": {},
        },
        "runtimeContract": {
            "patchStrategy": "incremental",
            "cachePolicy": "etag",
            "optimistic": False,
            "lazyContainer": [],
            "virtualization": {},
            "retryPolicy": {"maxRetries": 1},
        },
        "meta": {
            "etag": f"upc-v2-{fp}",
            "snapshotId": f"snapshot.upc.v2.{fp}",
            "traceId": f"trace.upc.v2.{fp}",
            "requestId": _stable_id(request_id, f"request.upc.v2.{fp}"),
            "sourceType": source_type,
        },
    }


def assemble_unified_page_contract_v2(
    source_contract: dict[str, Any],
    *,
    source_type: str = "",
    client_type: str = "web_pc",
    request_id: str = "request.upc.v2.assembler",
) -> dict[str, Any]:
    source = _dict(source_contract)
    resolved = _resolve_source_type(source, source_type)
    payload = _extract_source_payload(source, resolved)
    if resolved == "scene_contract_v1":
        return _assemble_scene_contract(payload, client_type=client_type, request_id=request_id)
    if resolved == "page_orchestration_v1":
        return _assemble_page_orchestration(payload, client_type=client_type, request_id=request_id)
    if resolved == "ui.contract":
        return _assemble_ui_contract(source, client_type=client_type, request_id=request_id)
    return _assemble_unknown(source, client_type=client_type, request_id=request_id)


def assemble_unified_page_patch_v2(
    onchange_payload: dict[str, Any],
    *,
    action_id: str = "api.onchange.patch",
    request_id: str = "request.upc.v2.patch",
) -> dict[str, Any]:
    source = _dict(onchange_payload)
    data_patch = {}
    if _dict(source.get("patch")):
        data_patch["mainData"] = deepcopy(source.get("patch"))
    status_patch = {"widgetStatus": []}
    for field_name, modifiers in _dict(source.get("modifiers_patch")).items():
        row = {"widgetId": f"field.{_stable_id(field_name, 'field')}"}
        if isinstance(modifiers, dict):
            if "readonly" in modifiers:
                row["readonly"] = bool(modifiers.get("readonly"))
            if "required" in modifiers:
                row["required"] = bool(modifiers.get("required"))
            if "invisible" in modifiers:
                row["visible"] = not bool(modifiers.get("invisible"))
        status_patch["widgetStatus"].append(row)
    line_patches = _list(source.get("line_patches"))
    if line_patches:
        data_patch["relationRows"] = {"line_patches": deepcopy(line_patches)}
    fp = _fingerprint(source)
    return {
        "updateType": "partial",
        "layoutPatch": {},
        "statusPatch": status_patch,
        "dataPatch": data_patch,
        "runtimePatch": {},
        "meta": {
            "contractVersion": PATCH_VERSION,
            "etag": f"upc-v2-patch-{fp}",
            "snapshotId": f"snapshot.upc.v2.patch.{fp}",
            "traceId": f"trace.upc.v2.patch.{fp}",
            "requestId": _stable_id(request_id, f"request.upc.v2.patch.{fp}"),
            "actionId": _stable_id(action_id, "api.onchange.patch"),
            "sourceType": "api.onchange",
        },
    }


def _extract_source_payload(source: dict[str, Any], source_type: str) -> dict[str, Any]:
    if source_type == "scene_contract_v1":
        return _dict(source.get("scene_contract_v1")) or source
    if source_type == "page_orchestration_v1":
        return _dict(source.get("page_orchestration_v1")) or source
    return source


def _assemble_scene_contract(source: dict[str, Any], *, client_type: str, request_id: str) -> dict[str, Any]:
    identity = _dict(source.get("identity"))
    page = _dict(source.get("page"))
    state = _dict(source.get("state"))
    actions = _dict(source.get("actions"))
    page_id = _stable_id(identity.get("scene_key"), "scene.page")
    contract = _base_contract(
        page_id=page_id,
        scene_key=identity.get("scene_key") or page_id,
        page_name=_text(identity.get("title"), page_id),
        model="",
        view_type="combine",
        layout_type="combine",
        client_type=client_type,
        source_type="scene_contract_v1",
        source_payload=source,
        request_id=request_id,
    )
    blocks = [item for item in _list(page.get("blocks")) if isinstance(item, dict)]
    widgets = []
    component_keys = set()
    for block in blocks:
        widget = _block_widget(block)
        widgets.append(widget)
        component_keys.add(widget["componentKey"])
        contract["statusContract"]["widgetStatus"].append(
            {
                "widgetId": widget["widgetId"],
                "visible": True,
                "readonly": True,
                "required": False,
                "disabled": False,
                "auth": "read",
            }
        )
    container_id = f"container.{page_id}.primary"
    contract["layoutContract"]["containerTree"] = [
        {
            "containerId": container_id,
            "containerType": "section",
            "title": _text(identity.get("title"), page_id),
            "span": 12,
            "styleToken": "sceneSection",
            "children": [],
            "widgetList": widgets,
        }
    ]
    contract["layoutContract"]["componentRegistry"] = _component_registry(component_keys or {"sc.display.text"})
    contract["statusContract"]["containerStatus"].append({"containerId": container_id, "visible": True, "disabled": False})
    contract["statusContract"]["globalStatus"]["reasonCode"] = _text(state.get("reason_code"), "SCENE_READY")
    _append_actions(contract, actions.get("primary_actions"), source_widget_id=widgets[0]["widgetId"] if widgets else "page.root")
    _append_actions(contract, actions.get("secondary_actions"), source_widget_id=widgets[0]["widgetId"] if widgets else "page.root")
    return contract


def _block_widget(block: dict[str, Any]) -> dict[str, Any]:
    block_key = _stable_id(block.get("key"), "block")
    return {
        "widgetId": f"block.{block_key}",
        "widgetType": "display",
        "fieldCode": block_key,
        "label": _text(block.get("title"), block_key),
        "span": 12,
        "componentKey": "sc.display.text",
        "capabilities": [],
        "componentConfig": {"blockType": _text(block.get("block_type"), "runtime_block")},
    }


def _assemble_page_orchestration(source: dict[str, Any], *, client_type: str, request_id: str) -> dict[str, Any]:
    page = _dict(source.get("page"))
    page_id = _stable_id(page.get("scene_key") or page.get("key"), "page.orchestration")
    contract = _base_contract(
        page_id=page_id,
        scene_key=page.get("scene_key") or page_id,
        page_name=_text(page.get("title"), page_id),
        model="",
        view_type="combine",
        layout_type="combine",
        client_type=client_type,
        source_type="page_orchestration_v1",
        source_payload=source,
        request_id=request_id,
    )
    component_keys = set()
    containers = []
    for zone in _list(source.get("zones")):
        if not isinstance(zone, dict):
            continue
        container_id = f"zone.{_stable_id(zone.get('key'), 'zone')}"
        widgets = []
        for block in _list(zone.get("blocks")):
            if not isinstance(block, dict):
                continue
            widget = _block_widget(block)
            widgets.append(widget)
            component_keys.add(widget["componentKey"])
            contract["statusContract"]["widgetStatus"].append(
                {
                    "widgetId": widget["widgetId"],
                    "visible": True,
                    "readonly": True,
                    "required": False,
                    "disabled": False,
                    "auth": "read",
                }
            )
        containers.append(
            {
                "containerId": container_id,
                "containerType": "section",
                "title": _text(zone.get("title"), container_id),
                "span": 12,
                "styleToken": _text(zone.get("display_mode"), "zone"),
                "children": [],
                "widgetList": widgets,
            }
        )
        contract["statusContract"]["containerStatus"].append({"containerId": container_id, "visible": True, "disabled": False})
    contract["layoutContract"]["containerTree"] = containers
    contract["layoutContract"]["componentRegistry"] = _component_registry(component_keys or {"sc.display.text"})
    contract["dataContract"]["dataSource"] = deepcopy(_dict(source.get("data_sources")))
    action_schema = _dict(source.get("action_schema")).get("actions")
    _append_action_schema(contract, _dict(action_schema), source_widget_id="page.root")
    return contract


def _assemble_ui_contract(source: dict[str, Any], *, client_type: str, request_id: str) -> dict[str, Any]:
    ui = _dict(source)
    head = _dict(source.get("head") or ui.get("head"))
    model = _text(source.get("model") or ui.get("model"))
    view_type = _text(source.get("view_type") or ui.get("view_type"), "form")
    record_id = _positive_int(source.get("record_id") or source.get("recordId") or ui.get("record_id") or ui.get("recordId"), 0)
    layout_type = "table" if view_type in {"tree", "list"} else view_type if view_type in {"form", "kanban", "gantt"} else "form"
    page_id = _stable_id(f"{model}.{view_type}" if model else f"ui.{view_type}", "ui.contract")
    contract = _base_contract(
        page_id=page_id,
        scene_key=page_id,
        page_name=_text(ui.get("title") or source.get("title") or head.get("title") or source.get("case"), page_id),
        model=model,
        view_type="list" if view_type == "tree" else view_type,
        layout_type=layout_type,
        client_type=client_type,
        source_type="ui.contract",
        source_payload=source,
        request_id=request_id,
    )
    fields = _field_rows(source, ui, view_type=view_type)
    raw_field_map = _dict(ui.get("fields") or source.get("fields"))
    fields_by_name: dict[str, dict[str, Any]] = {}
    for key, value in raw_field_map.items():
        if not isinstance(value, dict):
            continue
        name = _text(key or value.get("name"))
        if not name:
            continue
        fields_by_name[name] = deepcopy(value)
        fields_by_name[name].setdefault("name", name)
    for row in fields:
        if not isinstance(row, dict):
            continue
        name = _text(row.get("name"))
        if not name or name in fields_by_name:
            continue
        fields_by_name[name] = deepcopy(row)
    widgets = []
    component_keys = set()
    form_layout = _dict(_dict(ui.get("views")).get("form"))
    layout_rows = form_layout.get("layout") if isinstance(form_layout.get("layout"), list) else []
    form_subviews = _dict(form_layout.get("subviews"))
    if layout_type == "form" and layout_rows:
        container_tree = _normalize_native_layout_nodes(
            [row for row in layout_rows if isinstance(row, dict)],
            fields_by_name,
            layout_type=layout_type,
            form_subviews=form_subviews,
            component_keys=component_keys,
                container_status=contract["statusContract"]["containerStatus"],
                widget_status=contract["statusContract"]["widgetStatus"],
            )
    elif layout_type == "form":
        container_id = "main.form"
        sheet_id = f"{container_id}.sheet"
        group_id = f"{container_id}.group"
        field_nodes = [
            _native_field_node(
                {"type": "field", "name": _text(field.get("name"), "")},
                _dict(field),
                layout_type=layout_type,
            )
            for field in fields[:60]
            if _text(field.get("name"))
        ]
        container_tree = [
            {
                "type": "sheet",
                "name": sheet_id,
                "containerId": sheet_id,
                "containerType": "sheet",
                "string": contract["pageInfo"]["pageName"],
                "label": contract["pageInfo"]["pageName"],
                "span": 12,
                "children": [
                    {
                        "type": "group",
                        "name": group_id,
                        "containerId": group_id,
                        "containerType": "group",
                        "string": contract["pageInfo"]["pageName"],
                        "label": contract["pageInfo"]["pageName"],
                        "children": field_nodes,
                        "widgetList": [
                            _field_widget(_dict(field), layout_type=layout_type)
                            for field in fields[:60]
                            if _text(field.get("name"))
                        ],
                    }
                ],
                "widgetList": [],
            }
        ]
        for widget in container_tree[0]["children"][0]["widgetList"]:
            component_keys.add(widget["componentKey"])
            contract["statusContract"]["widgetStatus"].append(_field_status(
                next((row for row in fields if _text(row.get("name")) == _text(widget.get("fieldCode"))), {}),
                widget["widgetId"],
            ))
        contract["statusContract"]["containerStatus"].extend([
            {"containerId": sheet_id, "visible": True, "disabled": False},
            {"containerId": group_id, "visible": True, "disabled": False},
        ])
    else:
        container_id = "main.table"
        widgets = []
        for field in fields[:60]:
            widget = _field_widget(field, layout_type=layout_type)
            widgets.append(widget)
            component_keys.add(widget["componentKey"])
            contract["statusContract"]["widgetStatus"].append(_field_status(field, widget["widgetId"]))
        container_tree = [
            {
                "type": "section",
                "name": container_id,
                "containerId": container_id,
                "containerType": "section",
                "string": contract["pageInfo"]["pageName"],
                "label": contract["pageInfo"]["pageName"],
                "span": 12,
                "styleToken": "tableSection",
                "children": [],
                "widgetList": widgets,
            }
        ]
        contract["statusContract"]["containerStatus"].append({"containerId": container_id, "visible": True, "disabled": False})
    contract["layoutContract"]["containerTree"] = container_tree
    contract["layoutContract"]["componentRegistry"] = _component_registry(component_keys or {"sc.display.text"})
    contract["dataContract"]["dataMeta"]["fieldCount"] = len(fields)
    source_context = _ui_source_context(_dict(source), _dict(ui))
    if source_context:
        contract["dataContract"]["dataMeta"]["sourceContext"] = deepcopy(source_context)
        contract["runtimeContract"]["sourceContext"] = deepcopy(source_context)
        render_profile = _text(source_context.get("renderProfile")).lower()
        contract["statusContract"]["globalStatus"]["pageAuth"] = _ui_contract_page_auth(
            _dict(source),
            _dict(ui),
            render_profile,
            view_type,
        )
        if source_context.get("renderProfile") == "create":
            defaults = _default_values_from_context(_dict(source_context.get("context")))
            if defaults:
                contract["dataContract"]["mainData"].update(defaults)
    source_record = _dict(source.get("record"))
    if source_record:
        contract["dataContract"]["mainData"].update(deepcopy(source_record))
    _decorate_button_display_labels(
        contract["layoutContract"]["containerTree"],
        contract["dataContract"]["mainData"],
        fields_by_name,
    )
    data_source = _ui_contract_data_source(model=model, view_type=view_type, fields=fields, record_id=record_id, source=source, ui=ui)
    if data_source:
        contract["dataContract"]["dataSource"]["primary"] = data_source
    search_contract = _ui_search_contract(source, ui)
    if search_contract:
        contract["searchContract"] = search_contract
        contract["dataContract"]["search"] = deepcopy(search_contract)
    _append_ui_contract_actions(contract, ui, source_widget_id="page.root", main_data=contract["dataContract"]["mainData"])
    _append_ui_contract_row_actions(contract, ui)
    _append_project_kanban_row_action(contract, model=model, view_type=view_type)
    return contract


def _ui_search_contract(source: dict[str, Any], ui: dict[str, Any]) -> dict[str, Any]:
    raw = ui.get("search") if isinstance(ui.get("search"), dict) else source.get("search")
    search = _dict(raw)
    if not search:
        return {}
    out: dict[str, Any] = {}
    for key in ("default_sort", "default_order", "mode"):
        value = search.get(key)
        if _text(value):
            out[key] = deepcopy(value)
    for key in ("filters", "group_by", "fields"):
        value = search.get(key)
        if isinstance(value, list):
            out[key] = deepcopy(value)
    for key in ("search_panel", "searchpanel", "favorites", "custom", "ui_labels", "defaults"):
        value = search.get(key)
        if isinstance(value, dict):
            out[key] = deepcopy(value)
    return out


def _field_rows(source: dict[str, Any], ui: dict[str, Any], *, view_type: str = "") -> list[dict[str, Any]]:
    rows = source.get("meta_fields")
    if isinstance(rows, list) and rows:
        if view_type in {"tree", "list", "kanban"}:
            view_fields = _view_field_names(ui, view_type)
            schema_by_name = _view_column_schema_by_name(ui, view_type)
            row_by_name: dict[str, dict[str, Any]] = {}
            for row in rows:
                if not isinstance(row, dict):
                    continue
                name = _text(row.get("name") or row.get("field") or row.get("fieldCode"))
                if name and name not in row_by_name:
                    row_by_name[name] = row
            if view_fields:
                out = []
                for name in view_fields:
                    row = row_by_name.get(name)
                    item = dict(row) if isinstance(row, dict) else {}
                    item.setdefault("name", name)
                    schema = schema_by_name.get(name)
                    if schema:
                        item.update(schema)
                        item.setdefault("name", name)
                    out.append(item)
                return out
            out = []
            for row in rows:
                if not isinstance(row, dict):
                    continue
                item = dict(row)
                name = _text(item.get("name") or item.get("field") or item.get("fieldCode"))
                schema = schema_by_name.get(name)
                if schema:
                    item.update(schema)
                    item.setdefault("name", name)
                out.append(item)
            return out
        return [row for row in rows if isinstance(row, dict)]
    fields = ui.get("fields") or source.get("fields")
    layout_labels = _form_layout_field_labels(ui) if view_type == "form" else {}
    if isinstance(fields, dict) and view_type == "form" and layout_labels:
        out = []
        for name, label in layout_labels.items():
            value = fields.get(name)
            row = dict(value) if isinstance(value, dict) else {}
            row.setdefault("name", name)
            row["string"] = label
            row["label"] = label
            out.append(row)
        return out
    if isinstance(fields, dict) and view_type in {"tree", "list", "kanban"}:
        view_fields = _view_field_names(ui, view_type)
        schema_by_name = _view_column_schema_by_name(ui, view_type)
        if view_fields:
            out = []
            for name in view_fields:
                value = fields.get(name)
                row = dict(value) if isinstance(value, dict) else {}
                schema = schema_by_name.get(name)
                if schema:
                    row.update(schema)
                row.setdefault("name", name)
                out.append(row)
            return out
    if isinstance(fields, dict):
        out = []
        for key, value in fields.items():
            row = dict(value) if isinstance(value, dict) else {}
            row.setdefault("name", key)
            label = layout_labels.get(key)
            if label:
                row["string"] = label
                row["label"] = label
            out.append(row)
        return out
    return []


def _form_layout_field_labels(ui: dict[str, Any]) -> dict[str, str]:
    form = _dict(_dict(ui.get("views")).get("form"))
    labels: dict[str, str] = {}

    def walk(obj: Any) -> None:
        if isinstance(obj, dict):
            node_type = _text(obj.get("type") or obj.get("kind")).lower()
            name = _text(obj.get("name") or obj.get("field"))
            if node_type == "field" and name and name not in labels:
                field_info = _dict(obj.get("fieldInfo") or obj.get("field_info"))
                label = _text(obj.get("string") or obj.get("label") or field_info.get("string") or field_info.get("label"))
                if label:
                    labels[name] = label
            for value in obj.values():
                walk(value)
            return
        if isinstance(obj, list):
            for value in obj:
                walk(value)

    walk(form.get("layout"))
    return labels


def _view_field_names(ui: dict[str, Any], view_type: str) -> list[str]:
    views = _dict(ui.get("views"))
    candidates = [view_type]
    if view_type == "tree":
        candidates.append("list")
    if view_type == "list":
        candidates.append("tree")
    out: list[str] = []
    for key in candidates:
        view = _dict(views.get(key))
        for raw_name in _list(view.get("columns") or view.get("fields")):
            name = _text(raw_name)
            if name and name not in out:
                out.append(name)
        for row in _list(view.get("columnsSchema") or view.get("columns_schema")):
            if not isinstance(row, dict):
                continue
            name = _text(row.get("name") or row.get("field") or row.get("fieldCode"))
            if name and name not in out:
                out.append(name)
        if key == "kanban":
            kanban = _dict(view.get("kanban"))
            template = _text(kanban.get("template_qweb") or view.get("template_qweb") or view.get("arch"))
            for name in re.findall(r"\brecord\.([A-Za-z_][A-Za-z0-9_]*)\b", template):
                if name and name not in out:
                    out.append(name)
        if out:
            return out
    return out


def _view_column_schema_by_name(ui: dict[str, Any], view_type: str) -> dict[str, dict[str, Any]]:
    views = _dict(ui.get("views"))
    candidates = [view_type]
    if view_type == "tree":
        candidates.append("list")
    if view_type == "list":
        candidates.append("tree")
    for key in candidates:
        view = _dict(views.get(key))
        out: dict[str, dict[str, Any]] = {}
        for row in _list(view.get("columnsSchema") or view.get("columns_schema")):
            if not isinstance(row, dict):
                continue
            name = _text(row.get("name") or row.get("field") or row.get("fieldCode"))
            if not name or name in out:
                continue
            out[name] = dict(row)
            out[name].setdefault("name", name)
        if out:
            return out
    return {}


def _field_widget(field: dict[str, Any], *, layout_type: str) -> dict[str, Any]:
    field_name = _stable_id(field.get("name"), "field")
    explicit_widget = _text(field.get("widget"))
    widget_type = "table" if layout_type == "table" else explicit_widget or _widget_type_from_field(field)
    component_key = _component_key(widget_type)
    capabilities = ["sortable", "filterable"] if layout_type == "table" else []
    if widget_type == "select":
        capabilities.append("searchable")
    component_config = {}
    for key in ("optional", "invisible", "column_invisible", "readonly", "required"):
        if key in field:
            component_config[key] = deepcopy(field.get(key))
    field_type = _text(field.get("ttype") or field.get("type")).lower()
    if field_type:
        component_config["fieldType"] = field_type
    if _text(field.get("relation")):
        component_config["relation"] = _text(field.get("relation"))
    relation_entry = _dict(field.get("relation_entry"))
    if relation_entry:
        component_config["relationEntry"] = deepcopy(relation_entry)
    widget_options = _dict(field.get("widget_options") or field.get("options"))
    if widget_options:
        component_config["widgetOptions"] = deepcopy(widget_options)
    return {
        "widgetId": f"field.{field_name}",
        "widgetType": widget_type,
        "fieldCode": field_name,
        "label": _text(field.get("string") or field.get("label"), field_name),
        "span": 12 if layout_type == "table" else 6,
        "componentKey": component_key,
        "capabilities": capabilities,
        "componentConfig": component_config,
    }


def _native_field_node(node: dict[str, Any], field: dict[str, Any], *, layout_type: str) -> dict[str, Any]:
    field_name = _stable_id(node.get("name") or node.get("field") or field.get("name"), "field")
    label = _text(
        node.get("string")
        or node.get("label")
        or node.get("title")
        or _dict(node.get("fieldInfo")).get("label")
        or _dict(node.get("field_info")).get("label")
        or field.get("string")
        or field.get("label"),
        field_name,
    )
    field_source = deepcopy(field)
    field_info = _dict(node.get("fieldInfo") or node.get("field_info"))
    field_source.update({k: deepcopy(v) for k, v in field_info.items() if k not in {"label", "string"}})
    field_source["name"] = field_name
    field_source.setdefault("string", label)
    field_source.setdefault("label", label)
    if _text(node.get("widget")):
        field_source["widget"] = _text(node.get("widget"))
    widget = _field_widget(field_source, layout_type=layout_type)
    component_config = deepcopy(widget.get("componentConfig") or {})
    field_info["name"] = field_name
    field_info["label"] = label
    field_info["widget"] = widget["widgetType"]
    for key in ("type", "ttype", "relation", "relation_entry", "widget_options", "options"):
        if key in field_source and key not in field_info:
            field_info[key] = deepcopy(field_source.get(key))
    out = deepcopy(node)
    out["type"] = "field"
    out["name"] = field_name
    out["string"] = label
    out["label"] = label
    out["fieldInfo"] = field_info
    out["widget"] = widget["widgetType"]
    out["componentKey"] = widget["componentKey"]
    out["componentConfig"] = component_config
    out["widgetId"] = widget["widgetId"]
    out.setdefault("field_info", field_info)
    return out


def _direct_field_widgets_from_nodes(
    nodes: list[dict[str, Any]],
    fields_by_name: dict[str, dict[str, Any]],
    *,
    layout_type: str,
) -> list[dict[str, Any]]:
    widgets: list[dict[str, Any]] = []
    for node in nodes:
        if not isinstance(node, dict):
            continue
        if _text(node.get("type") or node.get("kind")).lower() != "field":
            continue
        field_name = _stable_id(node.get("name") or node.get("field"), "field")
        field = _dict(fields_by_name.get(field_name))
        if not field:
            field = {"name": field_name, "string": _text(node.get("string") or node.get("label"), field_name)}
        field_source = deepcopy(field)
        field_source["name"] = field_name
        field_source.setdefault("string", _text(node.get("string") or node.get("label"), field_name))
        field_source.setdefault("label", field_source.get("string", field_name))
        if _text(node.get("widget")):
            field_source["widget"] = _text(node.get("widget"))
        widgets.append(_field_widget(field_source, layout_type=layout_type))
    return widgets


def _normalize_native_layout_nodes(
    rows: list[dict[str, Any]],
    fields_by_name: dict[str, dict[str, Any]],
    *,
    layout_type: str,
    form_subviews: dict[str, Any] | None = None,
    component_keys: set[str],
    container_status: list[dict[str, Any]],
    widget_status: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        node = deepcopy(row)
        node_type = _text(node.get("type") or node.get("kind"), "group").lower()
        node["type"] = node_type
        node_name = _text(node.get("name") or node.get("field"))
        if node_name:
            node["name"] = node_name
        label = _text(node.get("string") or node.get("label") or node.get("title"))
        if label:
            node["string"] = label
            node["label"] = label
        if node_type == "field":
            field = _dict(fields_by_name.get(node_name)) if node_name else {}
            normalized = _native_field_node(node, field, layout_type=layout_type)
            if node_name:
                subview = _dict((form_subviews or {}).get(node_name))
                if subview:
                    field_info = _dict(normalized.get("fieldInfo"))
                    field_info["subview"] = deepcopy(subview)
                    normalized["fieldInfo"] = field_info
                    normalized["field_info"] = deepcopy(field_info)
            widget = _field_widget({**field, "name": node_name or field.get("name"), "string": normalized.get("string"), "label": normalized.get("label"), "widget": normalized.get("widget")}, layout_type=layout_type)
            component_keys.add(widget["componentKey"])
            widget_status.append(_field_status({**field, "name": node_name or field.get("name"), "string": normalized.get("string"), "label": normalized.get("label"), "widget": normalized.get("widget")}, widget["widgetId"]))
            out.append(normalized)
            continue
        container_id = _text(node.get("containerId") or node.get("container_id") or node_name)
        if not container_id:
            container_id = _stable_id(node.get("title") or node.get("string") or node.get("label") or node_type, node_type)
        node["containerId"] = container_id
        node["containerType"] = node_type
        node.setdefault("title", _text(node.get("title") or node.get("string") or node.get("label") or container_id, container_id))
        node.setdefault("label", _text(node.get("label") or node.get("string") or node.get("title") or container_id, container_id))
        container_status.append({"containerId": container_id, "visible": True, "disabled": False})
        for key in ("children", "pages", "tabs", "nodes", "items"):
            child_rows = _list(node.get(key))
            if child_rows:
                node[key] = _normalize_native_layout_nodes(
                    [item for item in child_rows if isinstance(item, dict)],
                    fields_by_name,
                    layout_type=layout_type,
                    form_subviews=form_subviews,
                    component_keys=component_keys,
                    container_status=container_status,
                    widget_status=widget_status,
                )
        direct_widgets: list[dict[str, Any]] = []
        for key in ("children", "pages", "tabs", "nodes", "items"):
            direct_widgets.extend(_direct_field_widgets_from_nodes(_list(node.get(key)), fields_by_name, layout_type=layout_type))
        if direct_widgets:
            node["widgetList"] = direct_widgets
            for widget in direct_widgets:
                component_keys.add(widget["componentKey"])
        elif not isinstance(node.get("widgetList"), list):
            node["widgetList"] = []
        out.append(node)
    return out


def _badge_count(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return int(value)
    if isinstance(value, list):
        return len(value)
    if isinstance(value, tuple):
        return len(value)
    if isinstance(value, str):
        text = value.strip()
        if text.isdigit():
            return int(text)
    return None


def _button_badge_count_source(
    badge: dict[str, Any],
    main_data: dict[str, Any],
    fields_by_name: dict[str, dict[str, Any]],
    layout_nodes: list[dict[str, Any]],
) -> tuple[int | None, str, str]:
    field_name = _text(badge.get("count_field") or badge.get("field") or badge.get("fieldCode"))
    badge_label = _text(badge.get("label"))
    if field_name and field_name in main_data:
        return _badge_count(main_data.get(field_name)), badge_label, field_name
    short_label = badge_label or field_name
    if short_label:
        short_label = re.sub(r"管理$", "", short_label).strip() or short_label
    def _matches_candidate(candidate_name: str, candidate_label: str) -> bool:
        return bool(short_label and (short_label in candidate_label or short_label in candidate_name))
    def _walk_layout(nodes: list[dict[str, Any]]):
        for row in nodes:
            if not isinstance(row, dict):
                continue
            row_type = _text(row.get("type") or row.get("kind")).lower()
            if row_type == "field":
                candidate_name = _text(row.get("name") or row.get("field"))
                candidate_meta = _dict(row.get("fieldInfo") or row.get("field_info"))
                candidate_label = _text(
                    row.get("label")
                    or row.get("string")
                    or candidate_meta.get("label")
                    or candidate_meta.get("string")
                    or candidate_name
                )
                candidate_type = _text(candidate_meta.get("type") or candidate_meta.get("ttype") or row.get("widget")).lower()
                if candidate_name in main_data and candidate_type in {"one2many", "many2many"} and _matches_candidate(candidate_name, candidate_label):
                    return candidate_name
            for key in ("children", "pages", "tabs", "nodes", "items"):
                child_rows = row.get(key)
                if isinstance(child_rows, list):
                    candidate = _walk_layout(child_rows)
                    if candidate:
                        return candidate
        return ""
    layout_candidate = _walk_layout(layout_nodes or [])
    if layout_candidate:
        return _badge_count(main_data.get(layout_candidate)), short_label, layout_candidate
    for candidate_name, candidate_meta in fields_by_name.items():
        candidate_type = _text(candidate_meta.get("type") or candidate_meta.get("ttype")).lower()
        if candidate_type not in {"one2many", "many2many"}:
            continue
        candidate_label = _text(candidate_meta.get("string") or candidate_meta.get("label") or candidate_name)
        if short_label and (short_label in candidate_label or short_label in candidate_name):
            return _badge_count(main_data.get(candidate_name)), short_label, candidate_name
    return None, short_label, ""


def _button_display_label(
    node: dict[str, Any],
    main_data: dict[str, Any],
    fields_by_name: dict[str, dict[str, Any]],
    layout_nodes: list[dict[str, Any]],
) -> str:
    action = _dict(node.get("action"))
    badge = _dict(action.get("badge") or node.get("badge"))
    field_name = _text(badge.get("field") or badge.get("fieldCode"))
    badge_label = _text(node.get("displayLabel") or action.get("displayLabel") or badge.get("label"))
    if not field_name and not badge_label:
        return ""
    count, resolved_label, source_field = _button_badge_count_source(badge, main_data, fields_by_name, layout_nodes)
    if count is None:
        return ""
    return f"{count}{resolved_label or badge_label}"


def _decorate_button_display_labels(
    nodes: list[dict[str, Any]],
    main_data: dict[str, Any],
    fields_by_name: dict[str, dict[str, Any]],
    layout_nodes: list[dict[str, Any]] | None = None,
) -> None:
    root_nodes = layout_nodes or nodes
    for node in nodes:
        if not isinstance(node, dict):
            continue
        if _text(node.get("type") or node.get("kind")).lower() == "button":
            action = _dict(node.get("action"))
            badge = _dict(action.get("badge") or node.get("badge"))
            count, resolved_label, source_field = _button_badge_count_source(badge, main_data, fields_by_name, root_nodes)
            if _text(badge.get("field")) and not _text(badge.get("count_field")):
                badge["count_field"] = _text(badge.get("field"))
            if source_field:
                badge["source_field"] = source_field
            if count is not None:
                display_label = f"{count}{resolved_label or _text(node.get('displayLabel') or action.get('displayLabel') or badge.get('label'))}"
                node["displayLabel"] = display_label
                action["displayLabel"] = display_label
            action["badge"] = badge
            if action:
                node["action"] = action
        for key in ("children", "pages", "tabs", "nodes", "items"):
            child_rows = node.get(key)
            if isinstance(child_rows, list) and child_rows:
                _decorate_button_display_labels(child_rows, main_data, fields_by_name, root_nodes)


def _ui_contract_data_source(
    *,
    model: str,
    view_type: str,
    fields: list[dict[str, Any]],
    record_id: int = 0,
    source: dict[str, Any] | None = None,
    ui: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if not model:
        return {}
    field_names = _record_data_fields(fields)
    if "id" not in field_names:
        field_names.insert(0, "id")
    extra_params = _ui_data_source_extra_params(_dict(source), _dict(ui))
    if view_type == "form":
        if record_id <= 0:
            return {}
        return {
            "query": "api.data",
            "intent": "api.data",
            "cachePolicy": "none",
            "consistency": "strong",
            "params": {
                "op": "read",
                "model": model,
                "ids": [record_id],
                "fields": field_names[:40],
                **extra_params,
            },
        }
    if view_type not in {"tree", "list", "kanban"}:
        return {}
    return {
        "query": "api.data",
        "intent": "api.data",
        "cachePolicy": "none",
        "consistency": "strong",
        "params": {
            "op": "list",
            "model": model,
            "fields": field_names[:20],
            "limit": 20,
            "offset": 0,
            "need_total": True,
            **extra_params,
        },
        "pagination": {
            "mode": "offset",
            "limit": 20,
            "offsetParam": "offset",
            "nextOffsetField": "next_offset",
            "totalField": "total",
        },
    }


def _ui_data_source_extra_params(source: dict[str, Any], ui: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    source_meta = _dict(source.get("source_meta"))
    action = _dict(ui.get("action"))
    search = _dict(ui.get("search"))
    search_defaults = _dict(search.get("defaults"))
    for key in ("domain_raw", "domainRaw"):
        value = source.get(key) or source_meta.get(key) or ui.get(key) or action.get(key) or search_defaults.get(key)
        if _text(value):
            out["domain_raw"] = value
            break
    for key in ("context_raw", "contextRaw"):
        value = source.get(key) or source_meta.get(key) or ui.get(key) or action.get(key) or search_defaults.get(key)
        if _text(value):
            out["context_raw"] = value
            break
    domain = source.get("domain") or source_meta.get("domain") or ui.get("domain") or action.get("domain")
    if isinstance(domain, list):
        out.setdefault("domain", deepcopy(domain))
    context = source.get("context") or source_meta.get("context") or ui.get("context") or action.get("context")
    if isinstance(context, dict):
        out.setdefault("context", deepcopy(context))
    order = source.get("order") or source_meta.get("order") or ui.get("order") or search_defaults.get("order")
    if _text(order):
        out["order"] = _text(order)
    limit = source.get("limit") or source_meta.get("limit") or ui.get("limit") or search_defaults.get("limit")
    parsed_limit = _positive_int(limit, 0)
    if parsed_limit:
        out["limit"] = parsed_limit
    return out


def _ui_source_context(source: dict[str, Any], ui: dict[str, Any]) -> dict[str, Any]:
    out = _ui_data_source_extra_params(source, ui)
    source_meta = _dict(source.get("source_meta"))
    action = _dict(ui.get("action"))
    head = _dict(ui.get("head"))
    render_profile = _text(
        source.get("render_profile")
        or source.get("renderProfile")
        or source_meta.get("render_profile")
        or source_meta.get("renderProfile")
        or ui.get("render_profile")
        or ui.get("renderProfile")
        or head.get("render_profile")
        or head.get("renderProfile")
        or action.get("render_profile")
        or action.get("renderProfile")
    ).lower()
    if render_profile in {"read", "view"}:
        render_profile = "readonly"
    if render_profile in {"create", "edit", "readonly"}:
        out["renderProfile"] = render_profile
    context = source.get("context") or source_meta.get("context") or ui.get("context") or head.get("context") or action.get("context")
    if isinstance(context, dict):
        out.setdefault("context", deepcopy(context))
    domain = source.get("domain") or source_meta.get("domain") or ui.get("domain") or head.get("domain") or action.get("domain")
    if isinstance(domain, list):
        out.setdefault("domain", deepcopy(domain))
    return out


def _ui_contract_page_auth(source: dict[str, Any], ui: dict[str, Any], render_profile: str, view_type: str) -> str:
    if render_profile == "readonly":
        return "read"
    source_context = _ui_source_context(source, ui)
    context = _dict(source_context.get("context"))
    if (
        context.get("sc_runtime_user_management") is True
        and render_profile in {"create", "edit"}
    ):
        return "edit"
    permission_sources = [
        _dict(_dict(ui.get("head")).get("permissions")),
        _dict(_dict(source.get("head")).get("permissions")),
        _dict(ui.get("permissions")),
        _dict(source.get("permissions")),
        _dict(_dict(source.get("permission_surface")).get("rights")),
        _dict(_dict(_dict(source.get("permission_surface")).get("effective")).get("rights")),
    ]
    rights: dict[str, Any] = {}
    for row in permission_sources:
        if row:
            rights = row
            break
    if rights:
        return "edit" if rights.get("write") is True or rights.get("create") is True else "read"
    if render_profile in {"create", "edit"}:
        return "edit"
    return "read" if view_type in {"tree", "list", "kanban"} else "edit"


def _default_values_from_context(context: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in context.items():
        if not isinstance(key, str) or not key.startswith("default_"):
            continue
        field_name = _stable_id(key[len("default_") :], "")
        if field_name:
            out[field_name] = deepcopy(value)
    return out


def _record_data_fields(fields: list[dict[str, Any]]) -> list[str]:
    out: list[str] = []
    technical_prefixes = ("access_", "activity_", "message_", "website_")
    technical_fields = {"active", "create_date", "create_uid", "display_name", "write_date", "write_uid"}
    for field in fields:
        name = _stable_id(field.get("name"), "")
        if not name or name == "id" or name.startswith("__"):
            continue
        if name in technical_fields or any(name.startswith(prefix) for prefix in technical_prefixes):
            continue
        if name not in out:
            out.append(name)
    return out or ["display_name"]


def _positive_int(value: Any, fallback: int = 0) -> int:
    try:
        parsed = int(value)
        if parsed > 0:
            return parsed
    except Exception:
        pass
    return fallback


def _modifier_true(value: Any) -> bool:
    if value is True:
        return True
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes"}
    return False


def _field_status(field: dict[str, Any], widget_id: str) -> dict[str, Any]:
    readonly = bool(field.get("readonly") is True)
    visible = not (_modifier_true(field.get("invisible")) or _modifier_true(field.get("column_invisible")))
    return {
        "widgetId": widget_id,
        "visible": visible,
        "readonly": readonly,
        "required": bool(field.get("required") is True),
        "disabled": False,
        "auth": "read" if readonly else "edit",
    }


def _append_actions(contract: dict[str, Any], rows: Any, *, source_widget_id: str) -> None:
    for row in _list(rows):
        if not isinstance(row, dict):
            continue
        key = _stable_id(row.get("key") or row.get("intent"), "action")
        action_id = f"action.{key}"
        label = _text(row.get("label") or row.get("name") or row.get("title"), key)
        intent = _text(row.get("intent"), "ui.contract")
        contract["actionContract"]["actionRuleList"].append(
            {
                "actionId": action_id,
                "actionKey": key,
                "label": label,
                "intent": intent,
                "target": deepcopy(_dict(row.get("target"))),
                "button": deepcopy(_dict(row.get("button"))),
                "triggerType": _text(row.get("trigger") or row.get("display_mode"), "click"),
                "sourceWidgetId": source_widget_id,
                "targetIds": [],
                "dispatchMode": "server",
                "targetScope": _text(row.get("target_scope") or row.get("level"), "page"),
                "refreshMode": "partial",
            }
        )
        contract["actionContract"]["dependencyGraph"].setdefault(source_widget_id, []).append(action_id)
        contract["statusContract"]["buttonStatus"].append({"btnId": f"btn.{key}", "visible": True, "disabled": False})


def _append_action_schema(contract: dict[str, Any], actions: dict[str, Any], *, source_widget_id: str) -> None:
    for key, row in actions.items():
        action_key = _stable_id(key, "action")
        action_id = f"action.{action_key}"
        source_row = _dict(row)
        contract["actionContract"]["actionRuleList"].append(
            {
                "actionId": action_id,
                "actionKey": action_key,
                "label": _text(source_row.get("label") or source_row.get("name") or source_row.get("title"), action_key),
                "intent": _text(source_row.get("intent"), "ui.contract"),
                "target": deepcopy(_dict(source_row.get("target"))),
                "button": deepcopy(_dict(source_row.get("button"))),
                "triggerType": "click",
                "sourceWidgetId": source_widget_id,
                "targetIds": [],
                "dispatchMode": "server",
                "targetScope": "page",
                "refreshMode": "partial",
            }
        )
        contract["statusContract"]["buttonStatus"].append({"btnId": f"btn.{action_key}", "visible": True, "disabled": False})


def _append_ui_contract_actions(
    contract: dict[str, Any],
    ui: dict[str, Any],
    *,
    source_widget_id: str,
    main_data: dict[str, Any] | None = None,
) -> None:
    rows: list[dict[str, Any]] = []
    for key in ("buttons", "business_actions"):
        for row in _list(ui.get(key)):
            if isinstance(row, dict):
                rows.append(row)
    toolbar = _dict(ui.get("toolbar"))
    for key in ("header", "sidebar", "footer"):
        for row in _list(toolbar.get(key)):
            if isinstance(row, dict):
                rows.append(row)
    for group in _list(ui.get("action_groups")):
        group_row = _dict(group)
        for row in _list(group_row.get("actions")):
            if isinstance(row, dict):
                rows.append(row)
    seen: set[str] = set()
    normalized: list[dict[str, Any]] = []
    for row in rows:
        key = _stable_id(row.get("key") or row.get("name") or row.get("type") or row.get("string"), "action")
        if key in seen:
            continue
        seen.add(key)
        kind = _text(row.get("kind") or row.get("type"))
        payload = _dict(row.get("payload"))
        intent = _text(row.get("intent"))
        badge = _dict(row.get("badge"))
        display_label = _text(row.get("displayLabel") or row.get("display_label"))
        if badge and not display_label and main_data:
            badge_field = _text(badge.get("field") or badge.get("fieldCode"))
            badge_label = _text(badge.get("label"))
            count = _badge_count(main_data.get(badge_field)) if badge_field else None
            if count is not None and badge_label:
                display_label = f"{count}{badge_label}"
        if kind == "open" or intent == "open":
            action_intent = "ui.contract"
            target = {
                "action_id": payload.get("action_id"),
                "model": row.get("target_model") or row.get("model"),
                "view_type": _text(payload.get("view_mode"), "tree").split(",")[0],
                "domain_raw": payload.get("domain_raw"),
                "context_raw": payload.get("context_raw"),
            }
            button = {}
        elif kind == "server" or payload.get("server_action_id"):
            action_intent = "execute_button"
            target = {}
            button = {
                "name": _text(row.get("name") or row.get("key"), key),
                "type": "server_action",
                "server_action_id": payload.get("server_action_id"),
                "xml_id": payload.get("xml_id"),
            }
        else:
            action_intent = _text(row.get("intent"), "execute_button")
            target = deepcopy(_dict(row.get("target")))
            button = {
                "name": _text(row.get("name") or row.get("button_name") or row.get("method_name"), key),
                "type": _text(row.get("type") or row.get("button_type"), "object"),
            }
        normalized.append(
            {
                "key": key,
                "label": _text(row.get("label") or row.get("string") or row.get("name"), key),
                "displayLabel": display_label,
                "intent": action_intent,
                "target": target,
                "button": button,
                "badge": badge or None,
            }
        )
    _append_actions(contract, normalized, source_widget_id=source_widget_id)


def _append_ui_contract_row_actions(contract: dict[str, Any], ui: dict[str, Any]) -> None:
    views = _dict(ui.get("views"))
    rows: list[dict[str, Any]] = []
    for view_key in ("kanban", "tree", "list"):
        view = _dict(views.get(view_key))
        for row in _list(view.get("row_actions")):
            if isinstance(row, dict):
                rows.append(row)
    normalized: list[dict[str, Any]] = []
    seen: set[str] = set()
    for row in rows:
        key = _stable_id(row.get("key") or row.get("name") or row.get("intent"), "row_action")
        if key in seen:
            continue
        seen.add(key)
        target = _dict(row.get("target"))
        payload = _dict(row.get("payload"))
        if not target and payload:
            target = payload
        normalized.append({
            "key": key,
            "name": row.get("name") or key,
            "label": _text(row.get("label") or row.get("string") or row.get("name"), key),
            "intent": _text(row.get("intent"), "open"),
            "target": target,
            "button": _dict(row.get("button")),
            "trigger": _text(row.get("trigger") or row.get("display_mode"), "row_click"),
            "level": _text(row.get("level"), "row"),
            "target_scope": _text(row.get("target_scope"), "row"),
        })
    _append_actions(contract, normalized, source_widget_id="page.row")


def _append_project_kanban_row_action(contract: dict[str, Any], *, model: str, view_type: str) -> None:
    if model != "project.project" or view_type != "kanban":
        return
    rows = _list(_dict(contract.get("actionContract")).get("actionRuleList"))
    for row in rows:
        if not isinstance(row, dict):
            continue
        if _text(row.get("triggerType")) == "row_click" or _text(row.get("sourceWidgetId")) == "page.row":
            return
    _append_actions(
        contract,
        [{
            "key": "open_project_dashboard",
            "name": "open_project_dashboard",
            "label": "进入项目驾驶舱",
            "intent": "open_scene",
            "target": {
                "route": "/s/project.management",
                "scene_key": "project.management",
                "entry_intent": "project.dashboard.enter",
                "project_id": "${id}",
            },
            "trigger": "row_click",
            "level": "row",
            "target_scope": "row",
        }],
        source_widget_id="page.row",
    )


def _assemble_unknown(source: dict[str, Any], *, client_type: str, request_id: str) -> dict[str, Any]:
    return _base_contract(
        page_id="unknown.contract",
        scene_key="unknown.contract",
        page_name="Unknown Contract",
        model="",
        view_type="combine",
        layout_type="combine",
        client_type=client_type,
        source_type="unknown",
        source_payload=source,
        request_id=request_id,
    )
