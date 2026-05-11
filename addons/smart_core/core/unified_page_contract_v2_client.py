# -*- coding: utf-8 -*-
from __future__ import annotations

from copy import deepcopy
from typing import Any

from .source_authority import build_source_authority_contract

STABLE_CLIENT_TYPES = ("web_pc", "wx_mini", "harmony_h5")
SOURCE_KIND = "unified_page_contract_v2_client_projection"
SOURCE_AUTHORITIES = ("http.headers", "request_params", "unified_page_contract_v2")
NO_BUSINESS_FACT_AUTHORITY = True


def source_authority_contract() -> dict[str, Any]:
    return build_source_authority_contract(
        kind=SOURCE_KIND,
        authorities=SOURCE_AUTHORITIES,
        no_business_fact_authority=NO_BUSINESS_FACT_AUTHORITY,
        runtime_carrier="unified_page_contract_v2_client",
    )

RESERVED_CLIENT_TYPES = ("mobile_app",)
MOBILE_CLIENT_TYPES = {"wx_mini", "harmony_h5"}
COMPACT_DELIVERY_PROFILES = {"mobile_compact", "mobile_primary"}
DEFAULT_MOBILE_WIDGET_LIMIT = 12
DEFAULT_MOBILE_ACTION_LIMIT = 4
DEFAULT_MOBILE_CONTAINER_LIMIT = 6


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


def resolve_delivery_profile(client_type: str, params: dict[str, Any] | None = None) -> str:
    source = _dict(params)
    requested = _text(source.get("delivery_profile") or source.get("deliveryProfile"))
    if requested in {"full", "mobile_compact", "mobile_primary"}:
        return requested
    return "mobile_compact" if client_type in MOBILE_CLIENT_TYPES else "full"


def trim_unified_page_contract_v2(
    contract: dict[str, Any],
    *,
    client_type: str,
    delivery_profile: str = "",
    max_widgets: int | None = None,
    max_actions: int | None = None,
    max_containers: int | None = None,
) -> dict[str, Any]:
    client = client_type if client_type in STABLE_CLIENT_TYPES else "web_pc"
    profile = delivery_profile if delivery_profile in {"full", "mobile_compact", "mobile_primary"} else resolve_delivery_profile(client)
    out = deepcopy(_dict(contract))
    compact = client in MOBILE_CLIENT_TYPES and profile in COMPACT_DELIVERY_PROFILES
    widget_limit = _positive_int(max_widgets, DEFAULT_MOBILE_WIDGET_LIMIT)
    action_limit = _positive_int(max_actions, DEFAULT_MOBILE_ACTION_LIMIT)
    container_limit = _positive_int(max_containers, DEFAULT_MOBILE_CONTAINER_LIMIT)
    trim_meta: dict[str, Any] = {
        "clientType": client,
        "deliveryProfile": profile,
        "compact": compact,
        "limits": {
            "containers": container_limit if compact else None,
            "widgets": widget_limit if compact else None,
            "actions": action_limit if compact else None,
        },
        "original": {},
        "delivered": {},
        "omitted": {},
    }
    page_info = _dict(out.get("pageInfo"))
    page_info["clientType"] = client
    page_info["deliveryProfile"] = profile
    out["pageInfo"] = page_info

    layout = _dict(out.get("layoutContract"))
    layout["adaptMode"] = "mobile" if client in MOBILE_CLIENT_TYPES else "pc"
    hints = _dict(layout.get("layoutHints"))
    hints["clientDensity"] = "comfortable" if client == "web_pc" else "compact"
    hints["columns"] = 12 if client == "web_pc" else 1
    hints["mobileCollapse"] = client in MOBILE_CLIENT_TYPES
    hints["deliveryProfile"] = profile
    if compact:
        hints["maxVisibleContainers"] = container_limit
        hints["maxVisibleWidgets"] = widget_limit
    layout["layoutHints"] = hints
    container_budget = {"containers": container_limit, "widgets": widget_limit} if compact else None
    container_rows = [row for row in _list(layout.get("containerTree")) if isinstance(row, dict)]
    trim_meta["original"]["containers"] = _count_containers(container_rows)
    trim_meta["original"]["widgets"] = _count_widgets(container_rows)
    layout["containerTree"] = [_trim_container(row, client, budget=container_budget) for row in container_rows]
    if compact:
        layout["containerTree"] = [row for row in layout["containerTree"] if row]
    trim_meta["delivered"]["containers"] = _count_containers(layout["containerTree"])
    trim_meta["delivered"]["widgets"] = _count_widgets(layout["containerTree"])
    trim_meta["omitted"]["containers"] = max(0, trim_meta["original"]["containers"] - trim_meta["delivered"]["containers"])
    trim_meta["omitted"]["widgets"] = max(0, trim_meta["original"]["widgets"] - trim_meta["delivered"]["widgets"])
    layout["componentRegistry"] = _trim_component_registry(_dict(layout.get("componentRegistry")), client)
    out["layoutContract"] = layout

    if compact:
        delivered_widget_ids = set(_collect_widget_ids(layout.get("containerTree")))
        out["statusContract"] = _trim_status_contract(_dict(out.get("statusContract")), delivered_widget_ids)
        out["actionContract"] = _trim_action_contract(_dict(out.get("actionContract")), action_limit, trim_meta=trim_meta)
    else:
        action_rows = _list(_dict(out.get("actionContract")).get("actionRuleList"))
        trim_meta["original"]["actions"] = len(action_rows)
        trim_meta["delivered"]["actions"] = len(action_rows)
        trim_meta["omitted"]["actions"] = 0

    runtime = _dict(out.get("runtimeContract"))
    virtualization = _dict(runtime.get("virtualization"))
    if client in MOBILE_CLIENT_TYPES:
        virtualization.setdefault("mobile", {"enabled": True, "strategy": "windowed"})
        runtime["renderStrategy"] = runtime.get("renderStrategy") or "scheduled"
    else:
        runtime["renderStrategy"] = runtime.get("renderStrategy") or "sync"
    runtime["virtualization"] = virtualization
    runtime["deliveryProfile"] = profile
    out["runtimeContract"] = runtime

    meta = _dict(out.get("meta"))
    meta["deliveryTrim"] = trim_meta
    out["meta"] = meta
    return out


def _positive_int(value: Any, fallback: int) -> int:
    try:
        parsed = int(value)
        if parsed > 0:
            return parsed
    except Exception:
        pass
    return fallback


def _fingerprint(value: Any) -> str:
    import json
    from hashlib import sha1

    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)
    return sha1(payload.encode("utf-8")).hexdigest()[:12]


def _trim_container(row: dict[str, Any], client_type: str, *, budget: dict[str, int] | None = None) -> dict[str, Any]:
    if budget is not None:
        if int(budget.get("containers") or 0) <= 0:
            return {}
        budget["containers"] = int(budget.get("containers") or 0) - 1
    out = deepcopy(row)
    if client_type in MOBILE_CLIENT_TYPES:
        out["span"] = 1
    out["children"] = [_trim_container(child, client_type, budget=budget) for child in _list(out.get("children")) if isinstance(child, dict)]
    out["children"] = [child for child in out["children"] if child]
    widgets = []
    for widget in _list(out.get("widgetList")):
        if not isinstance(widget, dict):
            continue
        if budget is not None:
            if int(budget.get("widgets") or 0) <= 0:
                continue
            budget["widgets"] = int(budget.get("widgets") or 0) - 1
        widgets.append(_trim_widget(widget, client_type))
    out["widgetList"] = widgets
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


def _count_containers(rows: Any) -> int:
    total = 0
    for row in _list(rows):
        if not isinstance(row, dict):
            continue
        total += 1
        total += _count_containers(row.get("children"))
    return total


def _count_widgets(rows: Any) -> int:
    total = 0
    for row in _list(rows):
        if not isinstance(row, dict):
            continue
        total += len([item for item in _list(row.get("widgetList")) if isinstance(item, dict)])
        total += _count_widgets(row.get("children"))
    return total


def _collect_widget_ids(rows: Any) -> list[str]:
    out: list[str] = []
    for row in _list(rows):
        if not isinstance(row, dict):
            continue
        for widget in _list(row.get("widgetList")):
            if isinstance(widget, dict) and _text(widget.get("widgetId")):
                out.append(_text(widget.get("widgetId")))
        out.extend(_collect_widget_ids(row.get("children")))
    return out


def _trim_status_contract(status: dict[str, Any], widget_ids: set[str]) -> dict[str, Any]:
    out = deepcopy(status)
    out["widgetStatus"] = [
        row for row in _list(out.get("widgetStatus"))
        if isinstance(row, dict) and _text(row.get("widgetId")) in widget_ids
    ]
    return out


def _trim_action_contract(action: dict[str, Any], action_limit: int, *, trim_meta: dict[str, Any]) -> dict[str, Any]:
    out = deepcopy(action)
    rows = [row for row in _list(out.get("actionRuleList")) if isinstance(row, dict)]
    delivered = rows[:action_limit]
    delivered_ids = {_text(row.get("actionId")) for row in delivered if _text(row.get("actionId"))}
    graph = _dict(out.get("dependencyGraph"))
    out["actionRuleList"] = delivered
    out["dependencyGraph"] = {
        key: [action_id for action_id in _list(value) if _text(action_id) in delivered_ids]
        for key, value in graph.items()
        if isinstance(value, list)
    }
    trim_meta["original"]["actions"] = len(rows)
    trim_meta["delivered"]["actions"] = len(delivered)
    trim_meta["omitted"]["actions"] = max(0, len(rows) - len(delivered))
    return out


def trim_navigation_contract_for_client(
    contract: dict[str, Any],
    *,
    client_type: str,
    delivery_profile: str = "",
    max_items: int | None = None,
    max_depth: int | None = None,
) -> dict[str, Any]:
    client = client_type if client_type in STABLE_CLIENT_TYPES else "web_pc"
    profile = delivery_profile if delivery_profile in {"full", "mobile_compact", "mobile_primary"} else resolve_delivery_profile(client)
    compact = client in MOBILE_CLIENT_TYPES and profile in COMPACT_DELIVERY_PROFILES
    item_limit = _positive_int(max_items, 8)
    depth_limit = _positive_int(max_depth, 2)
    out = deepcopy(_dict(contract))
    if not compact:
        return out
    budget = {"items": item_limit}
    sections = []
    source_sections = [row for row in _list(out.get("sections")) if isinstance(row, dict)]
    for section in source_sections:
        if int(budget.get("items") or 0) <= 0:
            break
        trimmed = _trim_nav_node(section, budget=budget, max_depth=depth_limit, depth=1)
        if trimmed and (_list(trimmed.get("children")) or _nav_node_openable(trimmed)):
            sections.append(trimmed)
    out["sections"] = sections
    meta = _dict(out.get("meta"))
    meta["clientType"] = client
    meta["deliveryProfile"] = profile
    meta["deliveryTrim"] = {
        "surface": "navigation",
        "original": {"items": _count_nav_items(source_sections)},
        "delivered": {"items": _count_nav_items(sections)},
        "omitted": {"items": max(0, _count_nav_items(source_sections) - _count_nav_items(sections))},
        "limits": {"items": item_limit, "depth": depth_limit},
    }
    out["meta"] = meta
    return out


def _trim_nav_node(row: dict[str, Any], *, budget: dict[str, int], max_depth: int, depth: int) -> dict[str, Any]:
    if int(budget.get("items") or 0) <= 0:
        return {}
    budget["items"] = int(budget.get("items") or 0) - 1
    out = deepcopy(row)
    if depth >= max_depth:
        out["children"] = []
        return out
    children = []
    for child in _list(row.get("children")):
        if not isinstance(child, dict) or int(budget.get("items") or 0) <= 0:
            continue
        trimmed = _trim_nav_node(child, budget=budget, max_depth=max_depth, depth=depth + 1)
        if trimmed and (_list(trimmed.get("children")) or _nav_node_openable(trimmed)):
            children.append(trimmed)
    out["children"] = children
    return out


def _nav_node_openable(row: dict[str, Any]) -> bool:
    meta = _dict(row.get("meta"))
    open_payload = _dict(meta.get("open"))
    return bool(
        open_payload
        or _text(meta.get("feature"))
        or _text(meta.get("scene_key") or row.get("scene_key"))
    )


def _count_nav_items(rows: Any) -> int:
    total = 0
    for row in _list(rows):
        if not isinstance(row, dict):
            continue
        total += 1
        total += _count_nav_items(row.get("children"))
    return total


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
