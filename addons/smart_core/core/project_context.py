# -*- coding: utf-8 -*-
"""Current project context contract helpers."""

from __future__ import annotations

import logging
from typing import Any

from odoo.exceptions import AccessError
_logger = logging.getLogger(__name__)

PROJECT_MODEL = "project.project"


def _model_available(env) -> bool:
    try:
        return PROJECT_MODEL in env.registry.models
    except Exception:
        return False


def _as_int(value: Any) -> int:
    try:
        parsed = int(value or 0)
    except Exception:
        return 0
    return parsed if parsed > 0 else 0


def _field_text(record, field_name: str) -> str:
    if field_name not in getattr(record, "_fields", {}):
        return ""
    try:
        value = record[field_name]
    except Exception:
        return ""
    if hasattr(value, "display_name"):
        return str(value.display_name or "").strip()
    return str(value or "").strip()


def format_project_option(record) -> dict:
    name = str(getattr(record, "display_name", "") or _field_text(record, "name") or "").strip()
    code = _field_text(record, "code") or _field_text(record, "project_code") or _field_text(record, "x_code")
    stage = _field_text(record, "stage_id")
    owner_id = 0
    owner_name = ""
    if "owner_id" in getattr(record, "_fields", {}):
        try:
            owner = record.owner_id
            owner_id = int(owner.id or 0)
            owner_name = str(owner.display_name or "").strip()
        except Exception:
            owner_id = 0
            owner_name = ""
    operation_strategy = _field_text(record, "operation_strategy")
    operation_strategy_label = operation_strategy
    field = getattr(record, "_fields", {}).get("operation_strategy")
    if field and getattr(field, "selection", None):
        try:
            operation_strategy_label = dict(field.selection).get(operation_strategy, operation_strategy)
        except Exception:
            operation_strategy_label = operation_strategy
    return {
        "id": int(record.id),
        "name": name,
        "display_name": name,
        "code": code,
        "stage": stage,
        "owner_id": owner_id,
        "owner_name": owner_name,
        "operation_strategy": operation_strategy,
        "operation_strategy_label": operation_strategy_label,
        "active": bool(getattr(record, "active", True)),
    }


def _project_domain(Project, search: str) -> list:
    term = str(search or "").strip()
    if not term:
        return []
    conditions = [
        (field_name, "ilike", term)
        for field_name in ("name", "code", "project_code", "x_code")
        if field_name in Project._fields
    ]
    if not conditions:
        return [("id", "=", 0)]
    if len(conditions) == 1:
        return [conditions[0]]
    return ["|"] * (len(conditions) - 1) + conditions


def _selected_id_from_params(params: dict | None) -> int:
    params = params if isinstance(params, dict) else {}
    for key in ("current_project_id", "project_id", "selected_id", "id"):
        candidate = _as_int(params.get(key))
        if candidate:
            return candidate
    return 0


def _current_project_id_from_source(source: dict | None) -> int:
    source = source if isinstance(source, dict) else {}
    for key in ("current_project_id", "selected_project_id"):
        candidate = _as_int(source.get(key))
        if candidate:
            return candidate
    nested = source.get("context")
    if isinstance(nested, dict):
        return _current_project_id_from_source(nested)
    return 0


def selected_project_id_from_context(params: dict | None = None, context: dict | None = None) -> int:
    candidate = _current_project_id_from_source(params)
    if candidate:
        return candidate
    return _current_project_id_from_source(context)


def project_scope_domain(env_model, project_id: int) -> list:
    selected_id = _as_int(project_id)
    if not selected_id:
        return []
    model_name = str(getattr(env_model, "_name", "") or "").strip()
    if model_name == PROJECT_MODEL:
        return [("id", "=", selected_id)]
    fields = getattr(env_model, "_fields", {}) or {}
    project_field = fields.get("project_id")
    if project_field and str(getattr(project_field, "comodel_name", "") or "") == PROJECT_MODEL:
        return [("project_id", "=", selected_id)]
    projects_field = fields.get("project_ids")
    if projects_field and str(getattr(projects_field, "comodel_name", "") or "") == PROJECT_MODEL:
        return [("project_ids", "in", [selected_id])]
    return []


def apply_project_scope_domain(env_model, domain: list | None, project_id: int) -> tuple[list, dict]:
    base_domain = list(domain or [])
    scope_domain = project_scope_domain(env_model, project_id)
    meta = {
        "enabled": bool(_as_int(project_id)),
        "project_id": _as_int(project_id) or None,
        "applied": bool(scope_domain),
        "domain": scope_domain,
        "model": str(getattr(env_model, "_name", "") or ""),
    }
    if not scope_domain:
        return base_domain, meta
    return scope_domain + base_domain, meta


def record_in_project_scope(env_model, record_id: int, project_id: int) -> tuple[bool, dict]:
    scoped_domain, meta = apply_project_scope_domain(env_model, [("id", "=", _as_int(record_id))], project_id)
    if not _as_int(record_id):
        return False, meta
    if not meta.get("applied"):
        return True, meta
    try:
        return bool(env_model.search_count(scoped_domain)), meta
    except Exception:
        return False, meta


def project_scope_denied_response(scope_meta: dict | None = None, *, message: str = "") -> dict:
    meta = scope_meta if isinstance(scope_meta, dict) else {}
    return {
        "ok": False,
        "error": {
            "code": "PROJECT_SCOPE_DENIED",
            "message": message or "当前项目上下文不允许访问或修改其他项目的数据",
            "reason_code": "PROJECT_SCOPE_DENIED",
            "kind": "permission",
            "project_scope": meta,
        },
        "code": 403,
    }


def build_project_context_contract(env, params: dict | None = None, *, search: str = "", limit: int = 20) -> dict:
    safe_limit = min(max(_as_int(limit) or 20, 1), 50)
    selected_id = _selected_id_from_params(params)
    selector = {
        "intent": "project.context.search",
        "search_param": "search",
        "selected_id_param": "selected_id",
        "limit": safe_limit,
        "label": "当前项目",
        "placeholder": "搜索项目名称",
    }
    base = {
        "contract_version": "v1",
        "enabled": False,
        "source": "system.init.project_context",
        "model": PROJECT_MODEL,
        "selected": None,
        "options": [],
        "total": 0,
        "selector": selector,
        "persistence": {
            "scope": "browser_session",
            "server_preference": False,
        },
    }
    if not _model_available(env):
        return {
            **base,
            "reason_code": "PROJECT_MODEL_NOT_INSTALLED",
            "message": "项目模型未安装",
        }

    try:
        Project = env[PROJECT_MODEL].with_context(active_test=False)
        domain = _project_domain(Project, search)
        records = Project.search(domain, limit=safe_limit, order="write_date desc, id desc")
        selected = None
        if selected_id:
            selected_record = Project.browse(selected_id)
            if selected_record.exists():
                selected = format_project_option(selected_record)
        options = [format_project_option(record) for record in records]
        if selected and all(option.get("id") != selected.get("id") for option in options):
            options = [selected, *options]
        total = Project.search_count(domain)
        return {
            **base,
            "enabled": True,
            "selected": selected,
            "options": options,
            "total": int(total or 0),
            "query": str(search or "").strip(),
            "reason_code": "",
            "message": "",
        }
    except AccessError:
        return {
            **base,
            "enabled": True,
            "reason_code": "PROJECT_CONTEXT_ACCESS_DENIED",
            "message": "当前账号无权读取项目列表",
        }
    except Exception as exc:
        _logger.exception("build project context contract failed")
        return {
            **base,
            "enabled": True,
            "reason_code": "PROJECT_CONTEXT_ERROR",
            "message": str(exc),
        }
