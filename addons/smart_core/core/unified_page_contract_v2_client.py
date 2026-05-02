# -*- coding: utf-8 -*-
from __future__ import annotations

from copy import deepcopy
from typing import Any


STABLE_CLIENT_TYPES = ("web_pc", "wx_mini", "harmony_h5")
RESERVED_CLIENT_TYPES = ("mobile_app",)
MOBILE_CLIENT_TYPES = {"wx_mini", "harmony_h5"}


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _text(value: Any, default: str = "") -> str:
    text = str(value or "").strip()
    return text or default


def resolve_client_type(headers: dict[str, Any] | None = None, params: dict[str, Any] | None = None) -> str:
    source_headers = _dict(headers)
    source_params = _dict(params)
    raw = (
        source_headers.get("X-SC-Client-Type")
        or source_headers.get("x-sc-client-type")
        or source_params.get("client_type")
        or source_params.get("clientType")
    )
    client_type = _text(raw, "web_pc")
    return client_type if client_type in STABLE_CLIENT_TYPES else "web_pc"


def trim_unified_page_contract_v2(contract: dict[str, Any], *, client_type: str) -> dict[str, Any]:
    client = client_type if client_type in STABLE_CLIENT_TYPES else "web_pc"
    out = deepcopy(_dict(contract))
    page_info = _dict(out.get("pageInfo"))
    page_info["clientType"] = client
    out["pageInfo"] = page_info

    layout = _dict(out.get("layoutContract"))
    layout["adaptMode"] = "mobile" if client in MOBILE_CLIENT_TYPES else "pc"
    hints = _dict(layout.get("layoutHints"))
    hints["clientDensity"] = "comfortable" if client == "web_pc" else "compact"
    hints["columns"] = 12 if client == "web_pc" else 1
    hints["mobileCollapse"] = client in MOBILE_CLIENT_TYPES
    layout["layoutHints"] = hints
    layout["containerTree"] = [_trim_container(row, client) for row in _list(layout.get("containerTree")) if isinstance(row, dict)]
    layout["componentRegistry"] = _trim_component_registry(_dict(layout.get("componentRegistry")), client)
    out["layoutContract"] = layout

    runtime = _dict(out.get("runtimeContract"))
    virtualization = _dict(runtime.get("virtualization"))
    if client in MOBILE_CLIENT_TYPES:
        virtualization.setdefault("mobile", {"enabled": True, "strategy": "windowed"})
        runtime["renderStrategy"] = runtime.get("renderStrategy") or "scheduled"
    else:
        runtime["renderStrategy"] = runtime.get("renderStrategy") or "sync"
    runtime["virtualization"] = virtualization
    out["runtimeContract"] = runtime
    return out


def _trim_container(row: dict[str, Any], client_type: str) -> dict[str, Any]:
    out = deepcopy(row)
    if client_type in MOBILE_CLIENT_TYPES:
        out["span"] = 1
    out["children"] = [_trim_container(child, client_type) for child in _list(out.get("children")) if isinstance(child, dict)]
    out["widgetList"] = [_trim_widget(widget, client_type) for widget in _list(out.get("widgetList")) if isinstance(widget, dict)]
    return out


def _trim_widget(row: dict[str, Any], client_type: str) -> dict[str, Any]:
    out = deepcopy(row)
    if client_type in MOBILE_CLIENT_TYPES:
        out["span"] = 1
        config = _dict(out.get("componentConfig"))
        config.setdefault("mobile", {"fullWidth": True})
        out["componentConfig"] = config
    return out


def _trim_component_registry(registry: dict[str, Any], client_type: str) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, row in registry.items():
        if not isinstance(row, dict):
            continue
        copied = deepcopy(row)
        adapter = _dict(copied.get("adapter"))
        selected = _text(adapter.get(client_type) or copied.get("fallback") or adapter.get("web_pc"))
        copied["selectedAdapter"] = selected
        copied["adapter"] = adapter
        out[key] = copied
    return out


def collect_semantic_signature(contract: dict[str, Any]) -> dict[str, list[str]]:
    payload = _dict(contract)
    layout = _dict(payload.get("layoutContract"))
    action = _dict(payload.get("actionContract"))
    data = _dict(payload.get("dataContract"))
    status = _dict(payload.get("statusContract"))
    containers: list[str] = []
    widgets: list[str] = []
    fields: list[str] = []
    component_keys: list[str] = []
    _collect_layout_signature(layout.get("containerTree"), containers, widgets, fields, component_keys)
    return {
        "pageId": [_text(_dict(payload.get("pageInfo")).get("pageId"))],
        "sceneKey": [_text(_dict(payload.get("pageInfo")).get("sceneKey"))],
        "containerId": sorted(containers),
        "widgetId": sorted(widgets),
        "fieldCode": sorted(fields),
        "componentKey": sorted(component_keys),
        "actionId": sorted(
            _text(row.get("actionId"))
            for row in _list(action.get("actionRuleList"))
            if isinstance(row, dict) and _text(row.get("actionId"))
        ),
        "dataKey": sorted(
            set(_dict(data.get("tableRows")).keys())
            | set(_dict(data.get("relationRows")).keys())
            | set(_dict(data.get("dictData")).keys())
            | set(_dict(data.get("dataSource")).keys())
        ),
        "selector": sorted(
            _text(row.get("selector"))
            for row in _list(status.get("selectorStatus"))
            if isinstance(row, dict) and _text(row.get("selector"))
        ),
    }


def _collect_layout_signature(rows: Any, containers: list[str], widgets: list[str], fields: list[str], component_keys: list[str]) -> None:
    for row in _list(rows):
        if not isinstance(row, dict):
            continue
        if _text(row.get("containerId")):
            containers.append(_text(row.get("containerId")))
        for widget in _list(row.get("widgetList")):
            if not isinstance(widget, dict):
                continue
            if _text(widget.get("widgetId")):
                widgets.append(_text(widget.get("widgetId")))
            if _text(widget.get("fieldCode")):
                fields.append(_text(widget.get("fieldCode")))
            if _text(widget.get("componentKey")):
                component_keys.append(_text(widget.get("componentKey")))
        _collect_layout_signature(row.get("children"), containers, widgets, fields, component_keys)


def find_client_semantic_drift(matrix: dict[str, dict[str, Any]]) -> list[str]:
    issues: list[str] = []
    baseline = None
    baseline_client = ""
    for client in STABLE_CLIENT_TYPES:
        contract = matrix.get(client)
        if not contract:
            issues.append(f"missing client contract {client}")
            continue
        signature = collect_semantic_signature(contract)
        if baseline is None:
            baseline = signature
            baseline_client = client
            continue
        for key, values in signature.items():
            if values != baseline.get(key):
                issues.append(f"{client}.{key} drift from {baseline_client}: {values} != {baseline.get(key)}")
    return issues
