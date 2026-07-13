# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Callable


_ENTERPRISE_COMPANY_FIELD_LABELS: dict[str, str] = {}
_ENTERPRISE_USER_FIELD_LABELS: dict[str, str] = {}


def _safe_text(value: Any, fallback: str = "") -> str:
    text = str(value or "").strip()
    if text.lower() in {"undefined", "null"}:
        text = ""
    return text or fallback


def _safe_lower(value: Any) -> str:
    return _safe_text(value).lower()


def _as_dict(value: Any) -> dict:
    return dict(value) if isinstance(value, dict) else {}


def collect_layout_field_names(nodes: Any) -> list[str]:
    ordered: list[str] = []

    def _iter_children(node: dict) -> list[list]:
        rows: list[list] = []
        for key in ("children", "tabs", "pages", "nodes", "items"):
            candidate = node.get(key)
            if isinstance(candidate, list):
                rows.append(candidate)
        return rows

    def _collect(items: list) -> None:
        for node in items:
            if not isinstance(node, dict):
                continue
            if _safe_lower(node.get("type")) == "field":
                name = _safe_text(node.get("name"))
                if name and name not in ordered:
                    ordered.append(name)
            for children in _iter_children(node):
                _collect(children)

    if isinstance(nodes, list):
        _collect(nodes)
    elif isinstance(nodes, dict):
        _collect([nodes])
    return ordered


def find_layout_sheet_node(nodes: Any) -> dict | None:
    if isinstance(nodes, dict):
        nodes = [nodes]
    if not isinstance(nodes, list):
        return None
    for node in nodes:
        if not isinstance(node, dict):
            continue
        if _safe_lower(node.get("type")) == "sheet":
            return node
        for key in ("children", "tabs", "pages", "nodes", "items"):
            candidate = node.get(key)
            if isinstance(candidate, list):
                found = find_layout_sheet_node(candidate)
                if found:
                    return found
    return None


def make_labeled_field_node(
    name: str,
    fields_map: dict[str, Any],
    preferred_labels: dict[str, str] | None = None,
) -> dict[str, Any]:
    descriptor = _as_dict(fields_map.get(name))
    label = _safe_text((preferred_labels or {}).get(name), "")
    if not label:
        label = _safe_text(_ENTERPRISE_USER_FIELD_LABELS.get(name) or _ENTERPRISE_COMPANY_FIELD_LABELS.get(name), "")
    if not label:
        label = _safe_text(descriptor.get("string") if descriptor else "", name)
    ttype = _safe_lower(descriptor.get("type") or descriptor.get("ttype"))
    widget = _safe_text(descriptor.get("widget"))
    if not widget:
        widget = {
            "many2one": "many2one",
            "one2many": "one2many_list",
            "many2many": "many2many_tags",
            "boolean": "boolean",
            "date": "date",
            "datetime": "datetime",
            "text": "textarea",
            "html": "html",
            "binary": "image",
        }.get(ttype, "")
    node = {"type": "field", "name": name}
    if label:
        node["string"] = label
    node["fieldInfo"] = {
        "name": name,
        "label": label or name,
    }
    if widget:
        node["fieldInfo"]["widget"] = widget
    return node


def backfill_form_layout_from_visible_fields(
    data: dict,
    *,
    is_form_contract: Callable[[dict], bool],
    is_technical_field: Callable[[str, dict], bool],
) -> None:
    if not is_form_contract(data):
        return
    fields_map = _as_dict(data.get("fields"))
    if not fields_map:
        return
    visible_fields = [
        _safe_text(name)
        for name in (data.get("visible_fields") or [])
        if _safe_text(name) in fields_map
    ]
    if not visible_fields:
        return

    views = _as_dict(data.get("views"))
    form = _as_dict(views.get("form"))
    layout = form.get("layout")
    if not isinstance(layout, list) or not layout:
        return

    existing = set(collect_layout_field_names(layout))
    missing = [
        name
        for name in visible_fields
        if name not in existing and not is_technical_field(name, _as_dict(fields_map.get(name)))
    ]
    if not missing:
        return

    backfill_group = {
        "type": "group",
        "name": "visible_fields_backfill_group",
        "string": "补充业务信息",
        "children": [
            make_labeled_field_node(name, fields_map)
            for name in missing
        ],
    }

    target = find_layout_sheet_node(layout)
    if target:
        children = target.get("children")
        if not isinstance(children, list):
            children = []
        children.append(backfill_group)
        target["children"] = children
    else:
        layout.append(backfill_group)
    form["layout"] = layout
    views["form"] = form
    data["views"] = views
