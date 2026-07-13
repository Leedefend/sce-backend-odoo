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


def normalize_legacy_project_form_profile(profile: dict, *, default_max_fields: int) -> dict[str, Any]:
    max_fields = int(profile.get("max_fields") or default_max_fields)
    return {
        "primary_fields": [
            _safe_text(name)
            for name in (profile.get("primary_fields") or [])
            if _safe_text(name)
        ],
        "create_hidden_fields": [
            _safe_text(name)
            for name in (profile.get("create_hidden_fields") or [])
            if _safe_text(name)
        ],
        "action_priorities": [
            _safe_text(name)
            for name in (profile.get("action_priorities") or [])
            if _safe_text(name)
        ],
        "action_noise_markers": [
            _safe_lower(name)
            for name in (profile.get("action_noise_markers") or [])
            if _safe_text(name)
        ],
        "search_noise_markers": [
            _safe_lower(name)
            for name in (profile.get("search_noise_markers") or [])
            if _safe_text(name)
        ],
        "action_group_labels": {
            _safe_text(key): _safe_text(value)
            for key, value in _as_dict(profile.get("action_group_labels")).items()
            if _safe_text(key) and _safe_text(value)
        },
        "max_fields": max_fields if max_fields > 0 else default_max_fields,
    }


def pick_project_form_fields(
    data: dict,
    *,
    profile: dict,
    iter_field_order: Any,
    is_technical_field: Any,
    default_max_fields: int,
) -> list[str]:
    fields_map = _as_dict(data.get("fields"))
    if not fields_map:
        return []
    primary_fields = profile.get("primary_fields") or []
    max_fields = int(profile.get("max_fields") or default_max_fields)
    ordered_fields = iter_field_order(data)

    def _collect_page_fields(nodes: list, current_page: str = "", out: list[str] | None = None) -> list[str]:
        collected = out or []
        for node in nodes:
            if not isinstance(node, dict):
                continue
            node_type = _safe_lower(node.get("type") or node.get("kind"))
            page_name = current_page
            if node_type == "page":
                page_name = _safe_text(node.get("name") or node.get("label") or node.get("string"))
            if node_type == "field" and page_name:
                name = _safe_text(node.get("name"))
                descriptor = _as_dict(fields_map.get(name))
                if name and descriptor and not is_technical_field(name, descriptor) and name not in collected:
                    collected.append(name)
            for key in ("children", "tabs", "pages", "nodes", "items"):
                candidate = node.get(key)
                if isinstance(candidate, list):
                    _collect_page_fields(candidate, page_name, collected)
        return collected

    views = _as_dict(data.get("views"))
    form = _as_dict(views.get("form"))
    layout = form.get("layout")
    page_fields = _collect_page_fields(layout if isinstance(layout, list) else [])

    selected: list[str] = []
    for name in primary_fields:
        descriptor = _as_dict(fields_map.get(name))
        if descriptor and not is_technical_field(name, descriptor) and name not in selected:
            selected.append(name)

    for name in page_fields:
        if len(selected) >= max_fields:
            break
        if name not in selected:
            selected.append(name)

    for name in ordered_fields:
        if len(selected) >= max_fields:
            break
        descriptor = _as_dict(fields_map.get(name))
        if not descriptor or is_technical_field(name, descriptor):
            continue
        if name not in selected:
            selected.append(name)

    for name, descriptor_raw in fields_map.items():
        if len(selected) >= max_fields:
            break
        descriptor = _as_dict(descriptor_raw)
        if is_technical_field(name, descriptor):
            continue
        required = bool(descriptor.get("required"))
        readonly = bool(descriptor.get("readonly"))
        if required and not readonly and name not in selected:
            selected.append(name)

    if "name" in fields_map and "name" not in selected:
        selected.insert(0, "name")
    return selected[:max_fields]


def filter_project_form_layout(data: dict, selected_fields: list[str], *, profile: dict) -> None:
    views = _as_dict(data.get("views"))
    form = _as_dict(views.get("form"))
    layout = form.get("layout")
    if not isinstance(layout, list):
        return

    def _iter_children(node: dict) -> list[list]:
        rows: list[list] = []
        for key in ("children", "tabs", "pages", "nodes", "items"):
            candidate = node.get(key)
            if isinstance(candidate, list):
                rows.append(candidate)
        return rows

    def _collect_layout_field_names(nodes: list, out: list[str]) -> None:
        for node in nodes:
            if not isinstance(node, dict):
                continue
            node_type = _safe_lower(node.get("type"))
            if node_type == "field":
                name = _safe_text(node.get("name"))
                if name and name not in out:
                    out.append(name)
            for children in _iter_children(node):
                _collect_layout_field_names(children, out)

    def _prune_layout(nodes: list, allowed: set[str]) -> list[dict]:
        cleaned: list[dict] = []
        for node in nodes:
            if not isinstance(node, dict):
                continue
            node_type = _safe_lower(node.get("type"))
            if node_type == "field":
                name = _safe_text(node.get("name"))
                if name and name in allowed:
                    cleaned.append(node)
                continue
            copied = dict(node)
            structured_children_present = False
            for key in ("children", "tabs", "pages", "nodes", "items"):
                raw_children = node.get(key)
                if not isinstance(raw_children, list):
                    continue
                pruned_children = _prune_layout(raw_children, allowed)
                copied[key] = pruned_children
                if key in {"children", "tabs", "pages"} and pruned_children:
                    structured_children_present = True
            keep_node = True
            if node_type in {"group", "page", "notebook", "sheet", "header"}:
                has_structured_key = any(isinstance(node.get(key), list) for key in ("children", "tabs", "pages"))
                if has_structured_key and not structured_children_present:
                    keep_node = False
            if keep_node:
                cleaned.append(copied)
        return cleaned

    selected_order = [name for name in selected_fields if _safe_text(name)]
    selected_set = set(selected_order)
    filtered_layout = _prune_layout(layout, selected_set)

    existing_field_names: list[str] = []
    _collect_layout_field_names(filtered_layout, existing_field_names)
    if not existing_field_names:
        primary_fields = profile.get("primary_fields") or []
        for name in primary_fields:
            if name in selected_fields:
                filtered_layout.append({"type": "field", "name": name})
        _collect_layout_field_names(filtered_layout, existing_field_names)

    existing_set = set(existing_field_names)
    missing_selected = [name for name in selected_order if name and name not in existing_set]
    for name in missing_selected:
        filtered_layout.append({"type": "field", "name": name})
    form["layout"] = filtered_layout
    views["form"] = form
    data["views"] = views


def build_project_lifecycle_summary(data: dict) -> None:
    workflow = _as_dict(data.get("workflow"))
    states = workflow.get("states")
    transitions = workflow.get("transitions")
    if not isinstance(states, list):
        states = []
    if not isinstance(transitions, list):
        transitions = []

    state_keys = []
    for row in states:
        if not isinstance(row, dict):
            continue
        key = _safe_text(row.get("key"))
        label = _safe_text(row.get("label"), key)
        if not key:
            continue
        state_keys.append({"key": key, "label": label})

    transition_rows = []
    for row in transitions:
        if not isinstance(row, dict):
            continue
        trigger = _as_dict(row.get("trigger"))
        label = _safe_text(trigger.get("label") or trigger.get("name"))
        if not label:
            continue
        transition_rows.append({
            "label": label,
            "kind": _safe_text(trigger.get("kind")),
        })

    data["lifecycle"] = {
        "state_field": _safe_text(workflow.get("state_field"), "stage_id"),
        "current_state": "",
        "steps": state_keys,
        "allowed_transitions": transition_rows[:8],
        "blockers": [],
        "progress_percent": 0 if state_keys else None,
    }
    data["workflow_surface"] = {
        "owner_layer": "business_fact",
        "source": "contract_governance.workflow_facts",
        "state_field": _safe_text(workflow.get("state_field"), "stage_id"),
        "states": state_keys,
        "transitions": transitions[:8],
        "highlight_states": workflow.get("highlight_states") if isinstance(workflow.get("highlight_states"), list) else [],
    }
