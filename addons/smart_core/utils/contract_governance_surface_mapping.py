# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any


def _safe_text(value: Any, fallback: str = "") -> str:
    text = str(value or "").strip()
    if text.lower() in {"undefined", "null"}:
        text = ""
    return text or fallback


def _safe_lower(value: Any) -> str:
    return _safe_text(value).lower()


def _as_dict(value: Any) -> dict:
    return dict(value) if isinstance(value, dict) else {}


def deep_clone_json_like(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {k: deep_clone_json_like(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [deep_clone_json_like(v) for v in obj]
    return obj


def collect_layout_snapshot(layout: Any) -> dict[str, Any]:
    field_order: list[str] = []
    node_signatures: list[str] = []

    def walk(node: Any) -> None:
        if isinstance(node, list):
            for item in node:
                walk(item)
            return
        if not isinstance(node, dict):
            return
        node_type = _safe_lower(node.get("type"))
        node_name = _safe_text(node.get("name"))
        node_label = _safe_text(node.get("string") or node.get("label"))
        node_signatures.append(f"{node_type}:{node_name or node_label}")
        if node_type == "field":
            if node_name and node_name not in field_order:
                field_order.append(node_name)
        for key in ("children", "tabs", "pages", "nodes", "items"):
            walk(node.get(key))

    walk(layout)
    return {
        "field_order": field_order,
        "node_signatures": node_signatures,
    }


def collect_action_snapshot(rows: Any) -> list[str]:
    out: list[str] = []
    if not isinstance(rows, list):
        return out
    for row in rows:
        if not isinstance(row, dict):
            continue
        key = _safe_text(row.get("key"))
        name = _safe_text(row.get("name"))
        method = _safe_text(_as_dict(row.get("payload")).get("method"))
        label = _safe_text(row.get("label"))
        signature = key or name or method or label
        if signature and signature not in out:
            out.append(signature)
    return out


def collect_surface_snapshot(data: dict) -> dict[str, Any]:
    fields_map = _as_dict(data.get("fields"))
    views = _as_dict(data.get("views"))
    form = _as_dict(views.get("form"))
    layout = form.get("layout")
    layout_info = collect_layout_snapshot(layout if isinstance(layout, list) else [])
    field_modifiers = _as_dict(form.get("field_modifiers"))
    buttons = collect_action_snapshot(data.get("buttons"))
    header_buttons = collect_action_snapshot(form.get("header_buttons"))
    stat_buttons = collect_action_snapshot(form.get("stat_buttons"))

    return {
        "fields": list(fields_map.keys()),
        "layout_field_order": layout_info.get("field_order") or [],
        "layout_nodes": layout_info.get("node_signatures") or [],
        "buttons": buttons,
        "header_buttons": header_buttons,
        "stat_buttons": stat_buttons,
        "field_modifiers": list(field_modifiers.keys()),
    }


def build_surface_mapping(native_snapshot: dict[str, Any], governed_snapshot: dict[str, Any]) -> dict[str, Any]:
    native_fields = [x for x in native_snapshot.get("fields", []) if _safe_text(x)]
    governed_fields = [x for x in governed_snapshot.get("fields", []) if _safe_text(x)]
    native_layout_fields = [x for x in native_snapshot.get("layout_field_order", []) if _safe_text(x)]
    governed_layout_fields = [x for x in governed_snapshot.get("layout_field_order", []) if _safe_text(x)]

    def diff(native_rows: list[str], governed_rows: list[str]) -> dict[str, Any]:
        native_set = set(native_rows)
        governed_set = set(governed_rows)
        removed = sorted([x for x in native_rows if x not in governed_set])
        added = sorted([x for x in governed_rows if x not in native_set])
        reordered = bool(native_rows and governed_rows and native_rows != governed_rows and not removed and not added)
        return {
            "native_count": len(native_rows),
            "governed_count": len(governed_rows),
            "removed": removed,
            "added": added,
            "reordered": reordered,
        }

    return {
        "native_to_governed": {
            "fields": diff(native_fields, governed_fields),
            "layout_fields": diff(native_layout_fields, governed_layout_fields),
            "layout_nodes": diff(
                [x for x in native_snapshot.get("layout_nodes", []) if _safe_text(x)],
                [x for x in governed_snapshot.get("layout_nodes", []) if _safe_text(x)],
            ),
            "buttons": diff(
                [x for x in native_snapshot.get("buttons", []) if _safe_text(x)],
                [x for x in governed_snapshot.get("buttons", []) if _safe_text(x)],
            ),
            "header_buttons": diff(
                [x for x in native_snapshot.get("header_buttons", []) if _safe_text(x)],
                [x for x in governed_snapshot.get("header_buttons", []) if _safe_text(x)],
            ),
            "stat_buttons": diff(
                [x for x in native_snapshot.get("stat_buttons", []) if _safe_text(x)],
                [x for x in governed_snapshot.get("stat_buttons", []) if _safe_text(x)],
            ),
            "field_modifiers": diff(
                [x for x in native_snapshot.get("field_modifiers", []) if _safe_text(x)],
                [x for x in governed_snapshot.get("field_modifiers", []) if _safe_text(x)],
            ),
        }
    }
