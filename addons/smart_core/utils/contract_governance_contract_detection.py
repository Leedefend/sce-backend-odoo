# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any


def _safe_text(value: Any, fallback: str = "") -> str:
    text = str(value or "").strip()
    if text.lower() in {"undefined", "null"}:
        text = ""
    return text or fallback


def _as_dict(value: Any) -> dict:
    return dict(value) if isinstance(value, dict) else {}


def _resolve_model_and_view(data: dict, *, surface_key: str) -> tuple[str, str, bool]:
    head = _as_dict(data.get("head"))
    views = _as_dict(data.get("views"))
    surface = _as_dict(views.get(surface_key))
    permissions = _as_dict(data.get("permissions"))
    model = _safe_text(
        head.get("model")
        or data.get("model")
        or surface.get("model")
        or permissions.get("model")
    )
    has_surface = isinstance(views.get(surface_key), dict)
    view_type = _safe_text(head.get("view_type") or data.get("view_type")).lower()
    if not view_type and has_surface:
        view_type = surface_key
    return model, view_type, has_surface


def is_project_form_contract(
    data: dict,
    *,
    primary_model: str,
    project_form_models: set[str],
) -> bool:
    model, view_type, has_form_view = _resolve_model_and_view(data, surface_key="form")
    if primary_model not in project_form_models:
        return False
    if not primary_model or model != primary_model:
        return False
    if has_form_view:
        return "form" in view_type if view_type else True
    return view_type == "form"


def is_enterprise_company_form_contract(data: dict, *, primary_model: str) -> bool:
    model, view_type, _has_form_view = _resolve_model_and_view(data, surface_key="form")
    return bool(primary_model == "res.company" and model == "res.company" and "form" in view_type)


def is_enterprise_user_form_contract(data: dict, *, primary_model: str) -> bool:
    model, view_type, _has_form_view = _resolve_model_and_view(data, surface_key="form")
    return bool(primary_model == "res.users" and model == "res.users" and "form" in view_type)


def is_project_kanban_contract(
    data: dict,
    *,
    primary_model: str,
    project_kanban_models: set[str],
    create_profile: str,
    edit_profile: str,
    readonly_profile: str,
) -> bool:
    head = _as_dict(data.get("head"))
    views = _as_dict(data.get("views"))
    kanban_view = _as_dict(views.get("kanban"))
    permissions = _as_dict(data.get("permissions"))
    model = _safe_text(
        head.get("model")
        or data.get("model")
        or kanban_view.get("model")
        or permissions.get("model")
    )
    current_view_type = _safe_text(data.get("view_type")).lower()
    if current_view_type and current_view_type not in {"kanban", "tree", "list"}:
        return False
    render_profile = _safe_text(data.get("render_profile")).lower()
    if render_profile in {create_profile, edit_profile, readonly_profile}:
        return False
    if _safe_text(data.get("record_id") or data.get("res_id")) and isinstance(views.get("form"), dict):
        return False
    view_type = _safe_text(current_view_type or head.get("view_type")).lower()
    if not view_type and isinstance(views.get("kanban"), dict):
        view_type = "kanban"
    return bool(
        primary_model
        and primary_model in project_kanban_models
        and model == primary_model
        and ("kanban" in view_type or isinstance(views.get("kanban"), dict))
    )


def is_project_task_form_contract(
    data: dict,
    *,
    primary_model: str,
    task_form_models: set[str],
) -> bool:
    model, view_type, _has_form_view = _resolve_model_and_view(data, surface_key="form")
    return bool(
        primary_model
        and primary_model in task_form_models
        and model == primary_model
        and "form" in view_type
    )


def is_model_tree_contract(data: dict, *, primary_model: str, model_name: str) -> bool:
    head = _as_dict(data.get("head"))
    views = _as_dict(data.get("views"))
    tree_view = _as_dict(views.get("tree") or views.get("list"))
    has_tree_surface = bool(tree_view)
    permissions = _as_dict(data.get("permissions"))
    model = _safe_text(
        head.get("model")
        or data.get("model")
        or tree_view.get("model")
        or permissions.get("model")
    )
    view_type = _safe_text(head.get("view_type") or data.get("view_type")).lower()
    if not view_type and has_tree_surface:
        view_type = "tree"
    return bool(
        primary_model == model_name
        and model == model_name
        and ("tree" in view_type or "list" in view_type or has_tree_surface)
    )


def is_form_contract(data: dict) -> bool:
    head = _as_dict(data.get("head"))
    views = _as_dict(data.get("views"))
    view_type = _safe_text(head.get("view_type") or data.get("view_type")).lower()
    if view_type == "form":
        return True
    return isinstance(views.get("form"), dict)
