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
TRACE_FIELD_TOKENS = ("legacy", "source", "origin", "external", "import", "migration", "trace", "old_")
NOTE_FIELD_TOKENS = ("note", "remark", "description", "memo", "comment", "说明", "备注")
_KANBAN_ROW_ACTION_REGISTRY: dict[tuple[str, str], dict[str, Any]] = {}


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


def register_kanban_row_action(model_name: str, action: dict[str, Any], *, view_type: str = "kanban") -> None:
    model = _text(model_name)
    view = _text(view_type, "kanban")
    if model and isinstance(action, dict):
        _KANBAN_ROW_ACTION_REGISTRY[(model, view)] = deepcopy(action)


def _formal_container_type(value: Any, default: str = "section") -> str:
    node_type = _text(value, default).lower()
    return "section" if node_type == "sheet" else node_type


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
            "listProfile": {},
            "componentRegistry": {},
        },
        "statusContract": {
            "globalStatus": {"pageVisible": True, "pageAuth": "read"},
            "containerStatus": [],
            "widgetStatus": [],
            "buttonStatus": [],
            "selectorStatus": [],
        },
        "actionContract": {
            "actionRuleList": [],
            "dependencyGraph": {},
            "deletePolicy": {},
            "surfacePolicies": {},
        },
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
    source_context = _ui_source_context(_dict(source), _dict(ui))
    source_context_context = _dict(source_context.get("context"))
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
    native_layout_rows = [row for row in layout_rows if isinstance(row, dict)]
    if not any(_text(row.get("type") or row.get("kind")).lower() == "header" for row in native_layout_rows):
        header_buttons = []
        for button_source in (form_layout.get("header_buttons"), source.get("header_buttons")):
            if isinstance(button_source, list):
                header_buttons.extend(button_source)
        button_children = []
        for button in header_buttons:
            if not isinstance(button, dict):
                continue
            button_name = _text(button.get("name") or button.get("method") or _dict(button.get("payload")).get("method"))
            if not button_name:
                continue
            button_label = _text(button.get("label") or button.get("string") or button_name, button_name)
            button_kind = _text(button.get("kind") or _dict(button.get("payload")).get("type"), "object")
            button_children.append({
                "type": "button",
                "name": button_name,
                "label": button_label,
                "string": button_label,
                "buttonType": button_kind,
                "action": deepcopy(button),
            })
        if button_children:
            native_layout_rows.insert(0, {
                "type": "header",
                "children": button_children,
                "sourceAuthority": {
                    "kind": SOURCE_KIND,
                    "runtime_carrier": "ui_contract_form_header_buttons",
                    "no_business_fact_authority": True,
                },
            })
    form_subviews = _dict(form_layout.get("subviews"))
    form_structure_contract = _dict(source.get("formStructureContract") or source.get("form_structure_contract"))
    preserve_governed_form_layout = (
        layout_type == "form"
        and bool(native_layout_rows)
        and _has_governed_form_layout_overlay(source)
    )
    form_structure_applied = False
    if layout_type == "form" and form_structure_contract and not preserve_governed_form_layout:
        render_profile = _text(source_context.get("renderProfile")).lower()
        structure_rows = _form_structure_contract_layout_rows(
            form_structure_contract,
            fields_by_name,
            native_layout_rows=native_layout_rows,
            page_title=contract["pageInfo"]["pageName"],
            render_profile=render_profile,
        )
        container_tree = _normalize_native_layout_nodes(
            structure_rows,
            fields_by_name,
            layout_type=layout_type,
            form_subviews=form_subviews,
            component_keys=component_keys,
            container_status=contract["statusContract"]["containerStatus"],
            widget_status=contract["statusContract"]["widgetStatus"],
            context=source_context_context,
        )
        form_structure_applied = True
    elif layout_type == "form" and native_layout_rows:
        container_tree = _normalize_native_layout_nodes(
            native_layout_rows,
            fields_by_name,
            layout_type=layout_type,
            form_subviews=form_subviews,
            component_keys=component_keys,
            container_status=contract["statusContract"]["containerStatus"],
            widget_status=contract["statusContract"]["widgetStatus"],
            context=source_context_context,
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
                "containerType": _formal_container_type("sheet"),
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
    if layout_type == "form":
        _apply_form_structure_columns_to_tree(container_tree, form_structure_contract)
        container_tree = _remove_attachment_field_nodes(container_tree, fields_by_name)
    _standardize_business_form_default_tabs(
        container_tree,
        model=model,
        view_type=view_type,
        container_status=contract["statusContract"]["containerStatus"],
    )
    _standardize_form_container_semantics(container_tree, model=model, view_type=view_type, source=source)
    if layout_type == "form":
        _apply_form_structure_columns_to_tree(container_tree, form_structure_contract)
    contract["layoutContract"]["containerTree"] = container_tree
    contract["layoutContract"]["componentRegistry"] = _component_registry(component_keys or {"sc.display.text"})
    if form_structure_contract and form_structure_applied:
        contract["formStructureContract"] = deepcopy(form_structure_contract)
    contract["dataContract"]["dataMeta"]["fieldCount"] = len(fields)
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
    _inject_collaboration_runtime_contract(contract, _dict(source.get("collaboration")))
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
    business_operation_profile = _dict(source.get("business_operation_profile"))
    if business_operation_profile:
        profile_projection = deepcopy(business_operation_profile)
        profile_projection["sourceAuthority"] = _metadata_projection_source_authority(
            runtime_carrier="ui.contract.v2.dataMeta.businessOperationProfile",
            source_key="business_operation_profile",
        )
        contract["dataContract"]["dataMeta"]["businessOperationProfile"] = profile_projection
    visible_fields = [
        _text(item)
        for item in _list(source.get("visible_fields"))
        if _text(item)
    ]
    if visible_fields:
        contract["dataContract"]["dataMeta"]["visibleFields"] = {
            "fields": visible_fields,
            "sourceAuthority": _metadata_projection_source_authority(
                runtime_carrier="ui.contract.v2.dataMeta.visibleFields",
                source_key="visible_fields",
            ),
        }
    field_groups = [deepcopy(item) for item in _list(source.get("field_groups")) if isinstance(item, dict)]
    if field_groups:
        contract["dataContract"]["dataMeta"]["fieldGroups"] = {
            "groups": field_groups,
            "sourceAuthority": _metadata_projection_source_authority(
                runtime_carrier="ui.contract.v2.dataMeta.fieldGroups",
                source_key="field_groups",
            ),
        }
    _append_ui_contract_actions(contract, ui, source_widget_id="page.root", main_data=contract["dataContract"]["mainData"])
    _append_ui_contract_row_actions(contract, ui)
    _append_registered_kanban_row_action(contract, model=model, view_type=view_type)
    return contract


def _has_governed_form_layout_overlay(source: dict[str, Any]) -> bool:
    governance = _dict(source.get("governance"))
    view_governance = _dict(governance.get("view_orchestration"))
    source_trace = _dict(source.get("source_trace"))
    view_trace = _dict(source_trace.get("view_orchestration"))
    return bool(view_trace.get("form_layout_overlay") or view_governance.get("form_layout_overlay"))


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
    for key in ("filters", "saved_filters", "group_by", "fields"):
        value = search.get(key)
        if isinstance(value, list):
            out[key] = deepcopy(value)
    for key in ("search_panel", "searchpanel", "favorites", "custom", "ui_labels", "defaults"):
        value = search.get(key)
        if isinstance(value, dict):
            out[key] = deepcopy(value)
    return out


def _inject_collaboration_runtime_contract(contract: dict[str, Any], collaboration: dict[str, Any]) -> None:
    if not collaboration:
        return
    runtime = _dict(contract.get("runtimeContract"))
    if not runtime:
        runtime = {}
        contract["runtimeContract"] = runtime
    normalized: dict[str, Any] = {}
    for key in ("chatter", "attachments", "timeline", "sourceAuthority"):
        value = collaboration.get(key)
        if isinstance(value, dict):
            normalized[key] = deepcopy(value)
    if normalized:
        runtime["collaboration"] = normalized


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
    selection = field.get("selection")
    if field_type == "selection" and isinstance(selection, (list, tuple)):
        component_config["selection"] = deepcopy(list(selection))
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


def _field_source_with_node_info(node: dict[str, Any], field: dict[str, Any], *, fallback_name: str = "") -> dict[str, Any]:
    field_name = _stable_id(node.get("name") or node.get("field") or field.get("name") or fallback_name, "field")
    field_source = deepcopy(field) if isinstance(field, dict) else {}
    field_info = _dict(node.get("fieldInfo") or node.get("field_info"))
    field_source.update({k: deepcopy(v) for k, v in field_info.items() if k not in {"label", "string"}})
    field_modifiers = _dict(field_info.get("modifiers"))
    for key in ("readonly", "required", "invisible", "column_invisible"):
        if key in field_modifiers and key not in field_source:
            field_source[key] = deepcopy(field_modifiers.get(key))
    for key in ("readonly", "required", "invisible", "column_invisible"):
        if key in node:
            field_source[key] = deepcopy(node.get(key))
    field_source["name"] = field_name
    field_source.setdefault("string", _text(node.get("string") or node.get("label") or field_info.get("label"), field_name))
    field_source.setdefault("label", field_source.get("string", field_name))
    if _text(node.get("widget")):
        field_source["widget"] = _text(node.get("widget"))
    return field_source


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
        field_source = _field_source_with_node_info(node, field, fallback_name=field_name)
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
    context: dict[str, Any] | None = None,
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
        invisible = _apply_contextual_invisible_modifier(node, context or {})
        if invisible is not None:
            node["invisible"] = invisible
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
            widget_source = _field_source_with_node_info(normalized, field, fallback_name=node_name or _text(field.get("name")))
            widget = _field_widget(widget_source, layout_type=layout_type)
            component_keys.add(widget["componentKey"])
            widget_status.append(_field_status(widget_source, widget["widgetId"], context=context))
            out.append(normalized)
            continue
        container_id = _text(node.get("containerId") or node.get("container_id") or node_name)
        if not container_id:
            container_id = _stable_id(node.get("title") or node.get("string") or node.get("label") or node_type, node_type)
        node["containerId"] = container_id
        node["containerType"] = _formal_container_type(node_type)
        node.setdefault("title", _text(node.get("title") or node.get("string") or node.get("label") or container_id, container_id))
        node.setdefault("label", _text(node.get("label") or node.get("string") or node.get("title") or container_id, container_id))
        container_status.append({"containerId": container_id, "visible": not bool(invisible), "disabled": False})
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
                    context=context,
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


def _walk_native_nodes(nodes: list[dict[str, Any]]):
    for node in nodes:
        if not isinstance(node, dict):
            continue
        yield node
        for key in ("children", "pages", "tabs", "nodes", "items"):
            child_rows = node.get(key)
            if isinstance(child_rows, list):
                yield from _walk_native_nodes([item for item in child_rows if isinstance(item, dict)])


def _layout_contains_node_type(nodes: list[dict[str, Any]], node_types: set[str]) -> bool:
    for node in _walk_native_nodes(nodes):
        if _text(node.get("containerType") or node.get("type") or node.get("kind")).lower() in node_types:
            return True
    return False


def _node_field_names(node: dict[str, Any]) -> list[str]:
    out: list[str] = []
    for item in _walk_native_nodes([node]):
        if _text(item.get("type") or item.get("kind")).lower() != "field":
            continue
        field_name = _text(item.get("name") or item.get("field"))
        if field_name and field_name not in out:
            out.append(field_name)
    return out


def _node_field_types(node: dict[str, Any]) -> list[str]:
    out: list[str] = []
    for item in _walk_native_nodes([node]):
        if _text(item.get("type") or item.get("kind")).lower() != "field":
            continue
        field_info = _dict(item.get("fieldInfo") or item.get("field_info"))
        field_type = _text(field_info.get("type") or field_info.get("ttype") or item.get("widget")).lower()
        if field_type:
            out.append(field_type)
    return out


def _node_text_fingerprint(node: dict[str, Any]) -> str:
    values: list[str] = []
    for item in _walk_native_nodes([node]):
        values.extend([
            _text(item.get("name") or item.get("field")).lower(),
            _text(item.get("string") or item.get("label") or item.get("title")).lower(),
        ])
        field_info = _dict(item.get("fieldInfo") or item.get("field_info"))
        values.extend([
            _text(field_info.get("string") or field_info.get("label")).lower(),
            _text(field_info.get("name")).lower(),
        ])
    return " ".join(item for item in values if item)


def _node_has_token(node: dict[str, Any], tokens: tuple[str, ...]) -> bool:
    fingerprint = _node_text_fingerprint(node)
    return any(token.lower() in fingerprint for token in tokens)


def _node_has_x2many(node: dict[str, Any]) -> bool:
    return any(field_type in {"one2many", "many2many"} for field_type in _node_field_types(node))


def _node_has_direct_group_child(node: dict[str, Any]) -> bool:
    for key in ("children", "pages", "tabs", "nodes", "items"):
        child_rows = node.get(key)
        if not isinstance(child_rows, list):
            continue
        for child in child_rows:
            if not isinstance(child, dict):
                continue
            child_type = _text(child.get("type") or child.get("kind") or child.get("containerType")).lower()
            if child_type == "group":
                return True
    return False


def _is_generic_container_label(node: dict[str, Any]) -> bool:
    node_type = _text(node.get("containerType") or node.get("type") or node.get("kind")).lower()
    labels = {
        _text(node.get("title")).lower(),
        _text(node.get("label")).lower(),
        _text(node.get("string")).lower(),
    }
    generic = {"", node_type}
    container_id = _text(node.get("containerId")).lower()
    node_name = _text(node.get("name")).lower()
    if _is_technical_container_identifier(container_id):
        generic.add(container_id)
    if _is_technical_container_identifier(node_name):
        generic.add(node_name)
    return bool(labels & generic) or all(not label for label in labels)


def _is_technical_container_identifier(value: str) -> bool:
    if not value:
        return False
    return bool(re.fullmatch(r"[a-z0-9_.:-]+", value))


def _semantic_group_label(node: dict[str, Any], *, level: int, index: int) -> str:
    fingerprint = _node_text_fingerprint(node)
    field_names = set(_node_field_names(node))
    if level <= 1 and _node_has_direct_group_child(node):
        return "主信息"
    if _node_has_token(node, TRACE_FIELD_TOKENS):
        return "来源追溯"
    if _node_has_token(node, NOTE_FIELD_TOKENS):
        return "备注说明"
    if _node_has_x2many(node):
        return "业务明细"
    if any(token in fingerprint for token in ("amount", "price", "cost", "budget", "fee", "money", "金额", "费用", "成本", "预算")):
        return "金额信息"
    if any(token in fingerprint for token in ("date", "time", "deadline", "start", "end", "日期", "时间", "截止")):
        return "时间信息"
    if any(token in fingerprint for token in ("partner", "supplier", "owner", "manager", "user", "负责人", "供应", "往来", "经理")):
        return "责任与往来"
    if level <= 1 or field_names & {"name", "code", "project_id", "state", "company_id"}:
        return "主信息" if level == 0 else "基础信息"
    return f"业务信息 {index + 1}"


def _apply_semantic_container_label(node: dict[str, Any], label: str) -> None:
    _apply_semantic_container_annotation(node, label)


def _apply_semantic_container_annotation(node: dict[str, Any], label: str) -> None:
    node["semanticTitle"] = label
    node["semanticAnchor"] = _stable_id(label, "semantic.group")
    source = _dict(node.get("sourceAuthority"))
    source.update({
        "kind": SOURCE_KIND,
        "projection_only": True,
        "no_business_fact_authority": True,
        "runtime_carrier": "business_form_semantic_label_standardizer",
    })
    node["sourceAuthority"] = source


def _business_group_label_for_node(source: dict[str, Any], node: dict[str, Any]) -> str:
    groups = _list(source.get("field_groups"))
    business_groups: list[tuple[str, str, set[str]]] = []
    for group in groups:
        if not isinstance(group, dict):
            continue
        name = _text(group.get("name")).lower()
        if not name.startswith("business_"):
            continue
        fields = {_text(item) for item in _list(group.get("fields")) if _text(item)}
        if not fields:
            continue
        label = _text(group.get("label") or group.get("title") or group.get("string"))
        if label:
            business_groups.append((name, label, fields))
    if not business_groups:
        return ""
    node_fields = set(_node_field_names(node))
    if not node_fields:
        return ""
    ranked = sorted(
        (
            (len(node_fields & fields), name, label)
            for name, label, fields in business_groups
            if node_fields & fields
        ),
        key=lambda item: (
            item[0],
            4 if item[1] == "business_collaboration" else 3 if item[1] == "business_details" else 2 if item[1] == "business_amount" else 1,
        ),
        reverse=True,
    )
    return ranked[0][2] if ranked else ""


def _standardize_form_container_semantics(nodes: list[dict[str, Any]], *, model: str, view_type: str, source: dict[str, Any] | None = None) -> None:
    if view_type != "form" or not model:
        return

    def visit(rows: list[dict[str, Any]], *, level: int) -> None:
        group_index = 0
        for node in rows:
            if not isinstance(node, dict):
                continue
            node_type = _text(node.get("containerType") or node.get("type") or node.get("kind")).lower()
            if node_type == "group":
                if _is_generic_container_label(node):
                    business_label = _business_group_label_for_node(_dict(source), node)
                    _apply_semantic_container_label(
                        node,
                        business_label or _semantic_group_label(node, level=level, index=group_index),
                    )
                else:
                    semantic_title = _text(node.get("semanticTitle"))
                    visible_label = _text(node.get("title") or node.get("label") or node.get("string"))
                    if not semantic_title and visible_label:
                        _apply_semantic_container_annotation(node, visible_label)
                group_index += 1
            for key in ("children", "pages", "tabs", "nodes", "items"):
                child_rows = node.get(key)
                if isinstance(child_rows, list):
                    visit([item for item in child_rows if isinstance(item, dict)], level=level + 1)

    visit(nodes, level=0)


def _node_is_button_box(node: dict[str, Any]) -> bool:
    classes = _text(_dict(node.get("attributes")).get("class") or node.get("class")).split()
    if "oe_button_box" in classes:
        return True
    for item in _walk_native_nodes([node]):
        if _text(item.get("type") or item.get("kind")).lower() != "button":
            continue
        action = _dict(item.get("action"))
        if _text(action.get("level")).lower() == "smart":
            return True
        item_classes = _text(_dict(item.get("attributes")).get("class") or item.get("class")).split()
        if "oe_stat_button" in item_classes:
            return True
    return False


def _append_container_status_once(container_status: list[dict[str, Any]], container_id: str) -> None:
    if not container_id:
        return
    if any(_text(row.get("containerId")) == container_id for row in container_status if isinstance(row, dict)):
        return
    container_status.append({"containerId": container_id, "visible": True, "disabled": False})


def _standardize_business_form_default_tabs(
    container_tree: list[dict[str, Any]],
    *,
    model: str,
    view_type: str,
    container_status: list[dict[str, Any]],
) -> None:
    # Odoo native form views only expose notebook/page captions as visible
    # structure.  Generic tabs such as "主信息" or "业务明细" are semantic
    # guesses, so they must not be projected as user-visible page titles.
    return


def _form_structure_contract_layout_rows(
    structure_contract: dict[str, Any],
    fields_by_name: dict[str, dict[str, Any]],
    *,
    native_layout_rows: list[dict[str, Any]],
    page_title: str,
    render_profile: str = "",
) -> list[dict[str, Any]]:
    if not structure_contract:
        return native_layout_rows
    available = {name for name in fields_by_name if _text(name)}
    native_field_nodes: dict[str, dict[str, Any]] = {}
    native_group_layouts: list[dict[str, Any]] = []

    def normalize_layout_columns(value: Any) -> int | None:
        try:
            columns = int(value)
        except (TypeError, ValueError):
            return None
        return columns if columns > 0 else None

    def node_layout_columns(node: dict[str, Any]) -> int | None:
        attrs = _dict(node.get("attributes") or node.get("attrs"))
        return (
            normalize_layout_columns(node.get("cols"))
            or normalize_layout_columns(node.get("columns"))
            or normalize_layout_columns(node.get("col"))
            or normalize_layout_columns(attrs.get("columns"))
            or normalize_layout_columns(attrs.get("cols"))
            or normalize_layout_columns(attrs.get("col"))
        )

    def collect_node_field_names(nodes: Any, out: list[str] | None = None) -> list[str]:
        names = out if out is not None else []
        for node in _list(nodes):
            if not isinstance(node, dict):
                continue
            node_type = _text(node.get("type") or node.get("kind")).lower()
            node_name = _text(node.get("name") or node.get("field"))
            if node_type == "field" and node_name and node_name not in names:
                names.append(node_name)
            for key in ("children", "pages", "tabs", "nodes", "items", "groups", "fields"):
                child_rows = node.get(key)
                if isinstance(child_rows, list) and child_rows:
                    collect_node_field_names(child_rows, names)
        return names

    def collect_native_field_nodes(nodes: Any) -> None:
        for node in _list(nodes):
            if not isinstance(node, dict):
                continue
            node_type = _text(node.get("type") or node.get("kind")).lower()
            node_name = _text(node.get("name") or node.get("field"))
            if node_type == "field" and node_name and node_name not in native_field_nodes:
                native_field_nodes[node_name] = deepcopy(node)
            if node_type == "group":
                columns = node_layout_columns(node)
                if columns:
                    title = _text(node.get("string") or node.get("label") or node.get("title"))
                    native_group_layouts.append({
                        "title": title,
                        "fields": collect_node_field_names(node.get("children")),
                        "cols": columns,
                    })
            for key in ("children", "pages", "tabs", "nodes", "items", "groups", "fields"):
                child_rows = node.get(key)
                if isinstance(child_rows, list) and child_rows:
                    collect_native_field_nodes(child_rows)

    def dominant_native_group_columns() -> int | None:
        counts: dict[int, int] = {}
        for row in native_group_layouts:
            columns = normalize_layout_columns(row.get("cols"))
            if columns:
                counts[columns] = counts.get(columns, 0) + 1
        if not counts:
            return None
        return sorted(counts.items(), key=lambda item: (-item[1], item[0]))[0][0]

    def native_field_hidden(node: dict[str, Any]) -> bool:
        if node.get("invisible") is True:
            return True
        modifiers = _dict(node.get("modifiers"))
        if modifiers.get("invisible") is True:
            return True
        attrs = _dict(node.get("attrs") or node.get("attributes"))
        if attrs.get("invisible") is True:
            return True
        return False

    collect_native_field_nodes(native_layout_rows)

    field_roles = _dict(structure_contract.get("fieldRoles") or structure_contract.get("field_roles"))
    normalized_render_profile = _text(render_profile).lower()

    def skip_field_for_create(name: str, native_node: dict[str, Any] | None = None) -> bool:
        if normalized_render_profile != "create":
            return False
        field_meta = _dict(fields_by_name.get(name))
        node_meta = _dict(native_node or {})
        node_field_info = _dict(node_meta.get("fieldInfo") or node_meta.get("field_info"))
        role = _dict(field_roles.get(name))
        fingerprint = " ".join(
            _text(value).lower()
            for value in (
                name,
                field_meta.get("string"),
                field_meta.get("label"),
                node_meta.get("string"),
                node_meta.get("label"),
                node_field_info.get("label"),
                node_field_info.get("string"),
                role.get("role"),
                role.get("slot"),
                role.get("group"),
            )
            if _text(value)
        )
        return any(
            token in fingerprint
            for token in ("legacy", "history", "history_check", "provenance", "source", "snapshot", "历史", "来源", "追溯", "快照", "迁移")
        )

    def field_nodes(names: list[Any], *, readonly: bool = False) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        seen: set[str] = set()
        for item in names:
            name = _text(item)
            if not name or name in seen or name not in available:
                continue
            native_node = native_field_nodes.get(name)
            if native_node and native_field_hidden(native_node):
                continue
            if skip_field_for_create(name, native_node):
                continue
            seen.add(name)
            row: dict[str, Any] = deepcopy(native_node) if native_node else {"type": "field", "name": name}
            row["type"] = "field"
            row["name"] = name
            if readonly:
                row["readonly"] = True
                modifiers = _dict(row.get("modifiers"))
                modifiers["readonly"] = True
                row["modifiers"] = modifiers
            role = _dict(field_roles.get(name))
            if role:
                row["formStructureRole"] = deepcopy(role)
            rows.append(row)
        return rows

    def group_node(group: dict[str, Any], *, readonly: bool = False, slot_name: str = "") -> dict[str, Any]:
        name = _stable_id(group.get("name") or group.get("title") or "business_group", "group")
        title = _text(group.get("title") or group.get("label") or group.get("string") or name, name)
        field_refs = _list(group.get("fieldRefs") or group.get("field_refs") or group.get("fields"))
        children = field_nodes(field_refs, readonly=readonly)
        if not children:
            return {}
        child_names = [row.get("name") for row in children if _text(row.get("name"))]
        configured_columns = node_layout_columns(group)
        inherited_columns = configured_columns or next(
            (
                row.get("cols")
                for row in native_group_layouts
                if row.get("title") and _text(row.get("title")) == title
            ),
            None,
        ) or next(
            (
                row.get("cols")
                for row in native_group_layouts
                if row.get("fields") and child_names and set(row.get("fields") or []) == set(child_names)
            ),
            None,
        ) or dominant_native_group_columns()
        layout_attrs = {"col": str(inherited_columns)} if inherited_columns else {}
        node = {
            "type": "group",
            "name": name,
            "string": title,
            "label": title,
            "formStructure": {
                "slot": slot_name,
                "group": name,
                "role": _text(group.get("role") or name, name),
            },
            "children": children,
            "sourceAuthority": {
                "kind": SOURCE_KIND,
                "runtime_carrier": "form_structure_contract",
                "no_business_fact_authority": True,
            },
        }
        if inherited_columns:
            node["cols"] = inherited_columns
            node["attributes"] = layout_attrs
        return node

    header_rows = [
        deepcopy(row)
        for row in native_layout_rows
        if _text(row.get("type") or row.get("kind")).lower() == "header"
    ]
    children: list[dict[str, Any]] = []
    slots = [_dict(item) for item in _list(structure_contract.get("slots")) if isinstance(item, dict)]
    summary = next(
        (
            slot
            for slot in slots
            if _text(slot.get("slot") or slot.get("name")).lower() in {"overview", "summary", "business_overview"}
        ),
        _dict(structure_contract.get("summary")),
    )
    show_summary_group = _text(render_profile).lower() == "readonly"
    summary_group = group_node(summary, readonly=True) if summary and show_summary_group else {}
    if summary_group:
        children.append(summary_group)

    tabs: list[dict[str, Any]] = []
    flatten_task_groups = normalized_render_profile != "readonly"

    def skip_group_for_create(group_row: dict[str, Any]) -> bool:
        if normalized_render_profile != "create":
            return False
        form_structure = _dict(group_row.get("formStructure"))
        fingerprint = " ".join(
            _text(value).lower()
            for value in (
                group_row.get("name"),
                group_row.get("label"),
                group_row.get("string"),
                form_structure.get("slot"),
                form_structure.get("group"),
                form_structure.get("role"),
            )
            if _text(value)
        )
        return any(
            token in fingerprint
            for token in ("provenance", "history", "history_check", "source", "legacy", "追溯", "历史", "来源")
        )
    page_slots = [
        slot
        for slot in slots
        if _text(slot.get("slot") or slot.get("name")).lower() not in {"overview", "summary", "business_overview"}
    ]
    legacy_pages = [_dict(item) for item in _list(structure_contract.get("pages")) if isinstance(item, dict)]
    for page_dict in page_slots or legacy_pages:
        page_name = _stable_id(
            page_dict.get("slot") or page_dict.get("name") or page_dict.get("title") or "business_page",
            "page",
        )
        page_title = _text(page_dict.get("title") or page_dict.get("label") or page_dict.get("string") or page_name, page_name)
        page_role = _text(page_dict.get("role") or page_name, page_name)
        page_children: list[dict[str, Any]] = []
        for group in _list(page_dict.get("groups")):
            group_row = group_node(_dict(group), readonly=bool(page_dict.get("readonly")), slot_name=page_name)
            if group_row:
                page_children.append(group_row)
        if not page_children:
            direct_group = group_node({
                "name": f"{page_name}.fields",
                "title": page_title,
                "fieldRefs": _list(page_dict.get("fieldRefs") or page_dict.get("field_refs") or page_dict.get("fields")),
                "role": page_role,
            }, readonly=bool(page_dict.get("readonly")), slot_name=page_name)
            if direct_group:
                page_children.append(direct_group)
        if not page_children:
            continue
        if flatten_task_groups:
            children.extend([row for row in page_children if not skip_group_for_create(row)])
            continue
        tabs.append({
            "type": "page",
            "name": page_name,
            "string": page_title,
            "label": page_title,
            "formStructure": {
                "slot": page_name,
                "role": page_role,
            },
            "children": page_children,
            "sourceAuthority": {
                "kind": SOURCE_KIND,
                "runtime_carrier": "form_structure_contract",
                "no_business_fact_authority": True,
            },
        })
    if tabs:
        navigation = _dict(structure_contract.get("navigation"))
        notebook_title = _text(navigation.get("title") or structure_contract.get("taskTitle") or "业务办理", "业务办理")
        children.append({
            "type": "notebook",
            "name": "form_structure_task_tabs",
            "string": notebook_title,
            "label": notebook_title,
            "tabs": tabs,
            "sourceAuthority": {
                "kind": SOURCE_KIND,
                "runtime_carrier": "form_structure_contract",
                "no_business_fact_authority": True,
            },
        })
    if not children:
        return native_layout_rows
    sheet = {
        "type": "sheet",
        "name": "business_orchestrated_sheet",
        "string": page_title,
        "label": page_title,
        "children": children,
        "sourceAuthority": {
            "kind": SOURCE_KIND,
            "runtime_carrier": "form_structure_contract",
            "no_business_fact_authority": True,
        },
    }
    return header_rows + [sheet]


def _form_structure_layout_columns(value: Any) -> int | None:
    try:
        columns = int(value)
    except (TypeError, ValueError):
        return None
    return columns if columns > 0 else None


def _form_structure_node_columns(node: dict[str, Any]) -> int | None:
    attrs = _dict(node.get("attributes") or node.get("attrs"))
    return (
        _form_structure_layout_columns(node.get("cols"))
        or _form_structure_layout_columns(node.get("columns"))
        or _form_structure_layout_columns(node.get("col"))
        or _form_structure_layout_columns(attrs.get("columns"))
        or _form_structure_layout_columns(attrs.get("cols"))
        or _form_structure_layout_columns(attrs.get("col"))
    )


def _form_structure_field_refs(node: dict[str, Any]) -> list[str]:
    refs: list[str] = []

    def collect(value: Any) -> None:
        for item in _list(value):
            if not isinstance(item, dict):
                continue
            node_type = _text(item.get("type") or item.get("kind")).lower()
            name = _text(item.get("name") or item.get("field"))
            if node_type == "field" and name and name not in refs:
                refs.append(name)
            for key in ("children", "pages", "tabs", "nodes", "items", "groups", "fields"):
                collect(item.get(key))

    collect(node.get("children"))
    return refs


def _apply_form_structure_columns_to_tree(container_tree: list[dict[str, Any]], structure_contract: dict[str, Any]) -> None:
    if not container_tree or not structure_contract:
        return
    default_columns = _form_structure_node_columns(structure_contract)
    group_policies: list[dict[str, Any]] = []
    for slot in _list(structure_contract.get("slots")):
        if not isinstance(slot, dict):
            continue
        for group in _list(slot.get("groups")):
            if not isinstance(group, dict):
                continue
            columns = _form_structure_node_columns(group)
            if not columns:
                continue
            group_policies.append({
                "title": _text(group.get("title") or group.get("label") or group.get("string") or group.get("name")),
                "fields": [
                    _text(item)
                    for item in _list(group.get("fieldRefs") or group.get("field_refs") or group.get("fields"))
                    if _text(item)
                ],
                "columns": columns,
            })

    def apply(node: dict[str, Any]) -> None:
        node_type = _text(node.get("type") or node.get("kind") or node.get("containerType")).lower()
        if node_type == "group":
            title = _text(node.get("string") or node.get("label") or node.get("title") or node.get("name"))
            node_fields = _form_structure_field_refs(node)
            columns = next(
                (
                    int(row["columns"])
                    for row in group_policies
                    if row.get("title") and row.get("title") == title
                ),
                None,
            )
            if columns is None and node_fields:
                node_field_set = set(node_fields)
                columns = next(
                    (
                        int(row["columns"])
                        for row in group_policies
                        if row.get("fields") and set(row.get("fields") or []) == node_field_set
                    ),
                    None,
                )
            columns = columns or default_columns
            if columns:
                node["cols"] = columns
                node["columns"] = columns
                attrs = _dict(node.get("attributes") or node.get("attrs"))
                attrs["col"] = str(columns)
                node["attributes"] = attrs
        for key in ("children", "pages", "tabs", "nodes", "items", "groups"):
            for child in _list(node.get(key)):
                if isinstance(child, dict):
                    apply(child)

    for row in container_tree:
        if isinstance(row, dict):
            apply(row)


def _is_attachment_field_name(name: str, fields_by_name: dict[str, dict[str, Any]]) -> bool:
    if not name:
        return False
    field = _dict(fields_by_name.get(name))
    field_type = _text(field.get("type") or field.get("ttype")).lower()
    relation = _text(field.get("relation") or field.get("comodel_name") or field.get("comodel")).lower()
    return name == "attachment_ids" or (field_type == "many2many" and relation == "ir.attachment")


def _remove_attachment_field_nodes(nodes: list[dict[str, Any]], fields_by_name: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    cleaned: list[dict[str, Any]] = []
    for node in nodes:
        if not isinstance(node, dict):
            continue
        node_type = _text(node.get("type") or node.get("kind")).lower()
        node_name = _text(node.get("name") or node.get("field"))
        if node_type == "field" and _is_attachment_field_name(node_name, fields_by_name):
            continue
        next_node = deepcopy(node)
        for key in ("children", "pages", "tabs", "nodes", "items", "groups", "fields"):
            child_rows = next_node.get(key)
            if isinstance(child_rows, list):
                next_node[key] = _remove_attachment_field_nodes(
                    [row for row in child_rows if isinstance(row, dict)],
                    fields_by_name,
                )
        widgets = next_node.get("widgetList")
        if isinstance(widgets, list):
            next_node["widgetList"] = [
                widget
                for widget in widgets
                if not _is_attachment_field_name(_text(_dict(widget).get("fieldCode")), fields_by_name)
            ]
        cleaned.append(next_node)
    return cleaned


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
    source_authority = _data_source_authority(model=model, view_type=view_type)
    if view_type == "form":
        if record_id <= 0:
            return {
                "query": "api.data",
                "intent": "api.data",
                "cachePolicy": "none",
                "consistency": "strong",
                "sourceAuthority": source_authority,
                "params": {
                    "op": "default_get",
                    "model": model,
                    "fields": field_names[:80],
                    **extra_params,
                },
            }
        return {
            "query": "api.data",
            "intent": "api.data",
            "cachePolicy": "none",
            "consistency": "strong",
            "sourceAuthority": source_authority,
            "params": {
                "op": "read",
                "model": model,
                "ids": [record_id],
                "fields": field_names[:80],
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
        "sourceAuthority": source_authority,
        "params": {
            "op": "list",
            "model": model,
            "fields": field_names[:40],
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


def _data_source_authority(*, model: str, view_type: str) -> dict[str, Any]:
    return {
        "kind": SOURCE_KIND,
        "runtime_carrier": "ui.contract.v2.dataContract.dataSource",
        "projection_only": True,
        "no_business_fact_authority": True,
        "fact_authority": "odoo.model",
        "model": model,
        "view_type": view_type,
    }


def _metadata_projection_source_authority(*, runtime_carrier: str, source_key: str) -> dict[str, Any]:
    return {
        "kind": SOURCE_KIND,
        "runtime_carrier": runtime_carrier,
        "projection_only": True,
        "no_business_fact_authority": True,
        "formal_projection": True,
        "fact_authority": "source_contract_projection",
        "source_key": source_key,
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


def _contextual_modifier_true(value: Any, context: dict[str, Any]) -> bool | None:
    if value is True:
        return True
    if value is False or value is None:
        return False if value is False else None
    if not isinstance(value, str):
        return None
    expr = value.strip()
    if not expr:
        return None
    static = expr.lower()
    if static in {"1", "true", "yes"}:
        return True
    if static in {"0", "false", "no"}:
        return False
    match = re.fullmatch(
        r"context\.get\(\s*['\"]([A-Za-z_][A-Za-z0-9_]*)['\"]\s*\)\s*(==|!=)\s*['\"]([^'\"]*)['\"]",
        expr,
    )
    if not match:
        return None
    key, operator, expected = match.groups()
    actual = context.get(key)
    if operator == "==":
        return str(actual or "") == expected
    return str(actual or "") != expected


def _apply_contextual_invisible_modifier(node: dict[str, Any], context: dict[str, Any]) -> bool | None:
    attributes = _dict(node.get("attributes"))
    attribute_modifiers = _dict(attributes.get("modifiers"))
    modifiers = _dict(node.get("modifiers"))
    candidates = [
        node.get("invisible"),
        attributes.get("invisible"),
        attribute_modifiers.get("invisible"),
        modifiers.get("invisible"),
    ]
    resolved: bool | None = None
    for candidate in candidates:
        resolved = _contextual_modifier_true(candidate, context)
        if resolved is not None:
            break
    if resolved is None:
        return None
    node["invisible"] = resolved
    if attributes:
        attributes["invisible"] = resolved
        if attribute_modifiers:
            attribute_modifiers["invisible"] = resolved
            attributes["modifiers"] = attribute_modifiers
        node["attributes"] = attributes
    if modifiers:
        modifiers["invisible"] = resolved
        node["modifiers"] = modifiers
    return resolved


def _field_status(field: dict[str, Any], widget_id: str, *, context: dict[str, Any] | None = None) -> dict[str, Any]:
    readonly = bool(field.get("readonly") is True or _modifier_true(field.get("readonly")))
    invisible = _contextual_modifier_true(field.get("invisible"), context or {})
    if invisible is None:
        invisible = _modifier_true(field.get("invisible"))
    column_invisible = _contextual_modifier_true(field.get("column_invisible"), context or {})
    if column_invisible is None:
        column_invisible = _modifier_true(field.get("column_invisible"))
    visible = not (invisible or column_invisible)
    return {
        "widgetId": widget_id,
        "visible": visible,
        "readonly": readonly,
        "required": bool(field.get("required") is True or _modifier_true(field.get("required"))),
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
        source_id = _text(row.get("sourceWidgetId") or row.get("source_widget_id"), source_widget_id)
        contract["actionContract"]["actionRuleList"].append(
            {
                "actionId": action_id,
                "actionKey": key,
                "label": label,
                "intent": intent,
                "target": deepcopy(_dict(row.get("target"))),
                "button": deepcopy(_dict(row.get("button"))),
                "triggerType": _text(row.get("trigger") or row.get("display_mode"), "click"),
                "sourceWidgetId": source_id,
                "targetIds": [],
                "dispatchMode": "server",
                "targetScope": _text(row.get("target_scope") or row.get("level"), "page"),
                "refreshMode": "partial",
            }
        )
        contract["actionContract"]["dependencyGraph"].setdefault(source_id, []).append(action_id)
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
                "url": payload.get("url"),
                "route": payload.get("route"),
                "target": payload.get("target"),
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
                "name": _text(row.get("name") or row.get("button_name") or row.get("method_name") or payload.get("method"), key),
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
                "sourceWidgetId": _text(row.get("sourceWidgetId") or row.get("source_widget_id")),
                "target_scope": _text(row.get("target_scope") or row.get("level"), "page"),
                "trigger": _text(row.get("trigger"), "click"),
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


def _append_registered_kanban_row_action(contract: dict[str, Any], *, model: str, view_type: str) -> None:
    action = _KANBAN_ROW_ACTION_REGISTRY.get((_text(model), _text(view_type)))
    if not action:
        return
    rows = _list(_dict(contract.get("actionContract")).get("actionRuleList"))
    for row in rows:
        if not isinstance(row, dict):
            continue
        if _text(row.get("triggerType")) == "row_click" or _text(row.get("sourceWidgetId")) == "page.row":
            return
    _append_actions(
        contract,
        [deepcopy(action)],
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
