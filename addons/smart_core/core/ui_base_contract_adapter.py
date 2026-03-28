# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Dict, List


def _text(value: Any) -> str:
    return str(value or "").strip()


def _as_dict(value: Any) -> Dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _as_list(value: Any) -> List[Any]:
    return list(value) if isinstance(value, list) else []


def _extract_actions(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []

    actions_root = _as_dict(payload.get("actions"))
    for key in ("items", "toolbar", "buttons", "actions", "header", "sidebar", "footer"):
        for row in _as_list(actions_root.get(key)):
            if isinstance(row, dict):
                out.append(dict(row))

    for key in ("toolbar", "buttons"):
        root = payload.get(key)
        if isinstance(root, list):
            for row in root:
                if isinstance(row, dict):
                    out.append(dict(row))
        elif isinstance(root, dict):
            for nested in ("items", "actions", "buttons", "header", "sidebar", "footer"):
                for row in _as_list(root.get(nested)):
                    if isinstance(row, dict):
                        out.append(dict(row))

    dedup: List[Dict[str, Any]] = []
    seen: set[str] = set()
    for row in out:
        key = _text(row.get("key") or row.get("name") or row.get("id") or row.get("label"))
        if not key or key in seen:
            continue
        seen.add(key)
        dedup.append(row)
    return dedup


def adapt_ui_base_contract(payload: Dict[str, Any] | None, *, scene_key: str = "") -> Dict[str, Any]:
    base = _as_dict(payload)
    views = _as_dict(base.get("views"))
    fields = _as_dict(base.get("fields"))
    search = _as_dict(base.get("search"))
    permissions = _as_dict(base.get("permissions"))
    workflow = _as_dict(base.get("workflow"))
    validation = _as_dict(base.get("validator") or base.get("validation"))
    parser_contract = _as_dict(base.get("parser_contract"))
    view_semantics = _as_dict(base.get("view_semantics"))
    native_view = _as_dict(base.get("native_view"))
    semantic_page = _as_dict(base.get("semantic_page"))
    actions = _extract_actions(base)

    view_fact = {
        "model": _text(base.get("model")),
        "view_modes": [
            key for key in ("tree", "form", "kanban", "search")
            if isinstance(views.get(key), dict) and bool(views.get(key))
        ],
        "views": views,
    }
    field_fact = {
        "model": _text(base.get("model")),
        "fields": fields,
    }
    search_fact = {
        "default_sort": _text(search.get("default_sort") or base.get("default_sort")),
        "filters": _as_list(search.get("filters")),
        "group_by": _as_list(search.get("group_by")),
        "fields": _as_list(search.get("fields")),
        "searchpanel": _as_list(search.get("searchpanel")),
        "mode": _text(search.get("mode")),
    }
    action_fact = {
        "items": actions,
    }
    parser_fact = {
        "parser_contract": parser_contract,
        "view_semantics": view_semantics,
        "native_view": native_view,
        "semantic_page": semantic_page,
    }
    permission_fact = permissions
    workflow_fact = workflow
    validation_fact = validation

    orchestrator_input = {
        "scene_key": _text(scene_key),
        "model": _text(base.get("model")),
        "view_fact": view_fact,
        "field_fact": field_fact,
        "search_fact": search_fact,
        "action_fact": action_fact,
        "parser_fact": parser_fact,
        "permission_fact": permission_fact,
        "workflow_fact": workflow_fact,
        "validation_fact": validation_fact,
    }

    normalized_contract = {
        "model": _text(base.get("model")),
        "views": views,
        "fields": fields,
        "search": search_fact,
        "permissions": permission_fact,
        "workflow": workflow_fact,
        "validation": validation_fact,
        "validator": validation_fact,
        "actions": {"items": actions},
        "parser_contract": parser_contract,
        "view_semantics": view_semantics,
        "native_view": native_view,
        "semantic_page": semantic_page,
    }

    return {
        "orchestrator_input": orchestrator_input,
        "normalized_contract": normalized_contract,
    }
