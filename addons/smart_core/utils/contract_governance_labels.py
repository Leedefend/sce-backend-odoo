# -*- coding: utf-8 -*-
from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

try:
    from .contract_governance_registry import (
        _BUSINESS_FIELD_LABEL_OVERRIDES,
        _LEGACY_FIELD_PRESENTATION_REGISTRY,
    )
except ImportError:
    spec = importlib.util.spec_from_file_location(
        "contract_governance_registry",
        Path(__file__).with_name("contract_governance_registry.py"),
    )
    if spec is None or spec.loader is None:
        raise
    registry = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(registry)
    _BUSINESS_FIELD_LABEL_OVERRIDES = registry._BUSINESS_FIELD_LABEL_OVERRIDES
    _LEGACY_FIELD_PRESENTATION_REGISTRY = registry._LEGACY_FIELD_PRESENTATION_REGISTRY


def _safe_text(value: Any, fallback: str = "") -> str:
    text = str(value or "").strip()
    if text.lower() in {"undefined", "null"}:
        text = ""
    return text or fallback


def _as_dict(value: Any) -> dict:
    return dict(value) if isinstance(value, dict) else {}


def business_field_label(field_name: str, current_label: Any = "", model_name: str = "") -> str:
    name = _safe_text(field_name)
    label = _safe_text(current_label)
    if not name:
        return label
    presentation = dict(_LEGACY_FIELD_PRESENTATION_REGISTRY.get((_safe_text(model_name), name)) or {})
    if presentation.get("label"):
        return presentation["label"]
    override = _BUSINESS_FIELD_LABEL_OVERRIDES.get(name)
    if override:
        return override
    return label


def normalize_business_field_labels(data: dict) -> None:
    head = _as_dict(data.get("head"))
    model_name = _safe_text(head.get("model") or data.get("model"))

    def _normalize_column(row: dict) -> None:
        name = _safe_text(row.get("name") or row.get("field"))
        label = business_field_label(name, row.get("label") or row.get("string"), model_name)
        if not name or not label:
            return
        row["label"] = label
        if "string" in row:
            row["string"] = label

    fields_map = _as_dict(data.get("fields"))
    for field_name, raw_descriptor in list(fields_map.items()):
        descriptor = _as_dict(raw_descriptor)
        label = business_field_label(field_name, descriptor.get("string"), model_name)
        if label:
            descriptor["string"] = label
        fields_map[field_name] = descriptor
    if fields_map:
        data["fields"] = fields_map

    views = _as_dict(data.get("views"))
    for view_key in ("tree", "list"):
        view = _as_dict(views.get(view_key))
        schema_rows = view.get("columns_schema")
        if isinstance(schema_rows, list):
            for row in schema_rows:
                if isinstance(row, dict):
                    _normalize_column(row)
            view["columns_schema"] = schema_rows
            views[view_key] = view
    if views:
        data["views"] = views

    list_profile = _as_dict(data.get("list_profile"))
    column_labels = _as_dict(list_profile.get("column_labels"))
    for field_name in list(column_labels.keys()):
        label = business_field_label(field_name, column_labels.get(field_name), model_name)
        if label:
            column_labels[field_name] = label
    if column_labels:
        list_profile["column_labels"] = column_labels
        data["list_profile"] = list_profile

    semantic_page = _as_dict(data.get("semantic_page"))
    list_semantics = _as_dict(semantic_page.get("list_semantics"))
    columns = list_semantics.get("columns")
    if isinstance(columns, list):
        for row in columns:
            if isinstance(row, dict):
                _normalize_column(row)
        list_semantics["columns"] = columns
        semantic_page["list_semantics"] = list_semantics
        data["semantic_page"] = semantic_page


def native_node_label(node: dict) -> str:
    attributes = node.get("attributes") if isinstance(node.get("attributes"), dict) else {}
    label = _safe_text(attributes.get("string") or node.get("string"))
    translations = {
        "description": "描述",
        "settings": "设置",
    }
    return translations.get(label.strip().lower(), label)


def preserve_native_layout_labels(data: dict) -> None:
    views = data.get("views") if isinstance(data.get("views"), dict) else {}
    form = views.get("form") if isinstance(views.get("form"), dict) else {}
    layout = form.get("layout")
    if not isinstance(layout, list):
        return

    def visit(nodes):
        for node in nodes or []:
            if not isinstance(node, dict):
                continue
            if _safe_text(node.get("type")).lower() == "page":
                label = native_node_label(node)
                if label:
                    node["title"] = label
                    node["label"] = label
            for key in ("children", "tabs", "pages", "nodes", "items"):
                nested = node.get(key)
                if isinstance(nested, list):
                    visit(nested)

    visit(layout)
    form["layout"] = layout
    views["form"] = form
    data["views"] = views


def emit_relation_entry_semantics(data: dict) -> None:
    fields_map = data.get("fields") if isinstance(data.get("fields"), dict) else {}
    entries: list[dict[str, Any]] = []
    for field_name, descriptor_raw in fields_map.items():
        descriptor = _as_dict(descriptor_raw)
        relation_entry = _as_dict(descriptor.get("relation_entry"))
        if not relation_entry:
            continue
        field = _safe_text(field_name)
        if not field:
            continue
        entries.append(
            {
                "field": field,
                "model": _safe_text(relation_entry.get("model") or descriptor.get("relation")),
                "create_mode": _safe_text(relation_entry.get("create_mode"), "disabled"),
                "can_read": bool(relation_entry.get("can_read", True)),
                "can_create": bool(relation_entry.get("can_create", False)),
                "delete_policy": _as_dict(relation_entry.get("delete_policy")),
                "reason_code": _safe_text(relation_entry.get("reason_code")),
                "default_vals": _as_dict(relation_entry.get("default_vals")),
                "inline_create": _as_dict(relation_entry.get("inline_create")),
                "action_id": relation_entry.get("action_id"),
                "menu_id": relation_entry.get("menu_id"),
                "source": _safe_text(relation_entry.get("source"), "field.relation_entry"),
            }
        )
    if not entries:
        return
    semantic_page = _as_dict(data.get("semantic_page"))
    semantic_page["relation_entries"] = entries
    semantic_page["relation_entries_owner_layer"] = "scene_orchestration"
    data["semantic_page"] = semantic_page
