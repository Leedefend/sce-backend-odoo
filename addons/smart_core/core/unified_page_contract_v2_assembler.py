# -*- coding: utf-8 -*-
from __future__ import annotations

from copy import deepcopy
from hashlib import sha1
from typing import Any


CONTRACT_VERSION = "2.1.0"
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
    if _dict(source.get("ui_contract")) or "meta_fields" in source or source.get("view_type"):
        return "ui.contract"
    if source.get("schema_version") == "v1" and ("patch" in source or "modifiers_patch" in source):
        return "api.onchange"
    if _dict(source.get("page")) and _list(source.get("zones")):
        return "page_orchestration_v1"
    if _dict(source.get("identity")) and _dict(source.get("page")):
        return "scene_contract_v1"
    return "unknown"


def _component_key(widget_type: str) -> str:
    mapping = {
        "input": "sc.input.text",
        "textarea": "sc.input.textarea",
        "number": "sc.input.number",
        "select": "sc.select.remote",
        "date": "sc.input.date",
        "datetime": "sc.input.datetime",
        "table": "sc.table.data",
        "tree": "sc.tree.data",
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
            "compat": {source_type.replace(".", "_"): deepcopy(source_payload)},
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
            "compat": {"api_onchange": deepcopy(source)},
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
    ui = _dict(source.get("ui_contract")) or _dict(source.get("ui_contract_raw"))
    model = _text(source.get("model") or ui.get("model"))
    view_type = _text(source.get("view_type") or ui.get("view_type"), "form")
    layout_type = "table" if view_type in {"tree", "list"} else view_type if view_type in {"form", "kanban", "gantt"} else "form"
    page_id = _stable_id(f"{model}.{view_type}" if model else f"ui.{view_type}", "ui.contract")
    contract = _base_contract(
        page_id=page_id,
        scene_key=page_id,
        page_name=_text(ui.get("title") or source.get("case"), page_id),
        model=model,
        view_type="list" if view_type == "tree" else view_type,
        layout_type=layout_type,
        client_type=client_type,
        source_type="ui.contract",
        source_payload=source,
        request_id=request_id,
    )
    fields = _field_rows(source, ui)
    widgets = []
    component_keys = set()
    for field in fields[:60]:
        widget = _field_widget(field, layout_type=layout_type)
        widgets.append(widget)
        component_keys.add(widget["componentKey"])
        contract["statusContract"]["widgetStatus"].append(_field_status(field, widget["widgetId"]))
    container_id = "main.form" if layout_type == "form" else "main.table"
    contract["layoutContract"]["containerTree"] = [
        {
            "containerId": container_id,
            "containerType": "group" if layout_type == "form" else "section",
            "title": contract["pageInfo"]["pageName"],
            "span": 12,
            "styleToken": "defaultGroup" if layout_type == "form" else "tableSection",
            "children": [],
            "widgetList": widgets,
        }
    ]
    contract["layoutContract"]["componentRegistry"] = _component_registry(component_keys or {"sc.display.text"})
    contract["statusContract"]["containerStatus"].append({"containerId": container_id, "visible": True, "disabled": False})
    contract["dataContract"]["dataMeta"]["fieldCount"] = len(fields)
    return contract


def _field_rows(source: dict[str, Any], ui: dict[str, Any]) -> list[dict[str, Any]]:
    rows = source.get("meta_fields")
    if isinstance(rows, list) and rows:
        return [row for row in rows if isinstance(row, dict)]
    fields = ui.get("fields") or source.get("fields")
    if isinstance(fields, dict):
        out = []
        for key, value in fields.items():
            row = dict(value) if isinstance(value, dict) else {}
            row.setdefault("name", key)
            out.append(row)
        return out
    return []


def _field_widget(field: dict[str, Any], *, layout_type: str) -> dict[str, Any]:
    field_name = _stable_id(field.get("name"), "field")
    widget_type = "table" if layout_type == "table" else _widget_type_from_field(field)
    component_key = _component_key(widget_type)
    capabilities = ["sortable", "filterable"] if layout_type == "table" else []
    if widget_type == "select":
        capabilities.append("searchable")
    return {
        "widgetId": f"field.{field_name}",
        "widgetType": widget_type,
        "fieldCode": field_name,
        "label": _text(field.get("string") or field.get("label"), field_name),
        "span": 12 if layout_type == "table" else 6,
        "componentKey": component_key,
        "capabilities": capabilities,
        "componentConfig": {},
    }


def _field_status(field: dict[str, Any], widget_id: str) -> dict[str, Any]:
    readonly = bool(field.get("readonly") is True)
    return {
        "widgetId": widget_id,
        "visible": True,
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
        contract["actionContract"]["actionRuleList"].append(
            {
                "actionId": action_id,
                "triggerType": "click",
                "sourceWidgetId": source_widget_id,
                "targetIds": [],
                "dispatchMode": "server",
                "targetScope": "page",
                "refreshMode": "partial",
            }
        )
        contract["actionContract"]["dependencyGraph"].setdefault(source_widget_id, []).append(action_id)
        contract["statusContract"]["buttonStatus"].append({"btnId": f"btn.{key}", "visible": True, "disabled": False})


def _append_action_schema(contract: dict[str, Any], actions: dict[str, Any], *, source_widget_id: str) -> None:
    for key, row in actions.items():
        action_key = _stable_id(key, "action")
        action_id = f"action.{action_key}"
        contract["actionContract"]["actionRuleList"].append(
            {
                "actionId": action_id,
                "triggerType": "click",
                "sourceWidgetId": source_widget_id,
                "targetIds": [],
                "dispatchMode": "server",
                "targetScope": "page",
                "refreshMode": "partial",
            }
        )
        contract["statusContract"]["buttonStatus"].append({"btnId": f"btn.{action_key}", "visible": True, "disabled": False})


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
