# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any


def _text(value: Any) -> str:
    return str(value or "").strip()


def _as_dict(value: Any) -> dict:
    return value if isinstance(value, dict) else {}


def _as_list(value: Any) -> list:
    return value if isinstance(value, list) else []


def _normalize_views(payload: dict) -> dict:
    views = _as_dict(payload.get("views"))
    out = {
        "tree": _as_dict(views.get("tree")),
        "form": _as_dict(views.get("form")),
        "kanban": _as_dict(views.get("kanban")),
        "search": _as_dict(views.get("search")),
    }
    for key, value in views.items():
        if key not in out and isinstance(value, dict):
            out[key] = value
    return out


def _action_identity(action: dict, fallback_index: int) -> str:
    key = _text(action.get("key"))
    if key:
        return f"key:{key}"
    name = _text(action.get("name"))
    if name:
        return f"name:{name}"
    label = _text(action.get("label"))
    payload = _as_dict(action.get("payload"))
    method = _text(payload.get("method"))
    ref = _text(payload.get("ref"))
    if label or method or ref:
        return f"sig:{label}|{method}|{ref}"
    return f"idx:{fallback_index}"


def _append_action(out: list[dict], seen: set[str], row: Any) -> None:
    if not isinstance(row, dict):
        return
    item = dict(row)
    idx = len(out)
    ident = _action_identity(item, idx)
    if ident in seen:
        return
    seen.add(ident)
    out.append(item)


def _normalize_actions(payload: dict) -> dict:
    actions = _as_dict(payload.get("actions"))
    out: dict[str, Any] = {"items": []}
    seen: set[str] = set()

    for row in _as_list(actions.get("items")):
        _append_action(out["items"], seen, row)

    for key in ("toolbar", "buttons"):
        for row in _as_list(payload.get(key)):
            _append_action(out["items"], seen, row)

    toolbar = _as_dict(payload.get("toolbar"))
    for key in ("items", "actions", "buttons", "header"):
        for row in _as_list(toolbar.get(key)):
            _append_action(out["items"], seen, row)

    for key, value in actions.items():
        if key == "items":
            continue
        out[key] = value
    return out


def _normalize_permissions(payload: dict) -> dict:
    permissions = _as_dict(payload.get("permissions"))
    effective = _as_dict(permissions.get("effective"))
    rights = _as_dict(effective.get("rights"))
    if rights:
        permissions["effective"] = {**effective, "rights": rights}
    elif effective:
        permissions["effective"] = effective
    return permissions


def _normalize_search(payload: dict) -> dict:
    search = _as_dict(payload.get("search"))
    out = {
        "filters": _as_list(search.get("filters")),
        "group_by": _as_list(search.get("group_by") or search.get("group_bys")),
        "fields": _as_list(search.get("fields")),
    }
    for key, value in search.items():
        if key not in out:
            out[key] = value
    return out


def _normalize_workflow(payload: dict) -> dict:
    workflow = _as_dict(payload.get("workflow"))
    state_field = _text(workflow.get("state_field"))
    if not state_field:
        form = _as_dict(_as_dict(payload.get("views")).get("form"))
        statusbar = _as_dict(form.get("statusbar"))
        state_field = _text(statusbar.get("field"))
    states = _as_list(workflow.get("states"))
    transitions = _as_list(workflow.get("transitions"))
    out = dict(workflow)
    if state_field:
        out["state_field"] = state_field
    out["states"] = states
    out["transitions"] = transitions
    return out


def _normalize_validator(payload: dict) -> dict:
    validator = _as_dict(payload.get("validator"))
    out = dict(validator)
    out["required_fields"] = _as_list(validator.get("required_fields"))
    out["field_rules"] = _as_dict(validator.get("field_rules"))
    out["record_rules"] = _as_dict(validator.get("record_rules"))
    return out


def canonicalize_ui_base_contract(payload: dict | None) -> dict:
    base = _as_dict(payload)
    views = _normalize_views(base)
    fields = _as_dict(base.get("fields"))
    search = _normalize_search(base)
    permissions = _normalize_permissions(base)
    workflow = _normalize_workflow({**base, "views": views})
    validator = _normalize_validator(base)
    actions = _normalize_actions(base)
    canonical = dict(base)
    canonical.update(
        {
            "views": views,
            "fields": fields,
            "search": search,
            "permissions": permissions,
            "workflow": workflow,
            "validator": validator,
            "actions": actions,
            "toolbar": _as_dict(base.get("toolbar")),
            "buttons": _as_list(base.get("buttons")),
        }
    )
    coverage = {
        "views": bool(views),
        "fields": bool(fields),
        "search": bool(search),
        "permissions": bool(permissions),
        "workflow": bool(workflow),
        "validator": bool(validator),
        "actions": bool(_as_list(actions.get("items"))),
    }
    canonical["base_fact_coverage"] = coverage
    return canonical
