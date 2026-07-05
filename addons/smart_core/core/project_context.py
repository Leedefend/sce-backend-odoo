# -*- coding: utf-8 -*-
"""Current record context contract helpers.

Project-named APIs in this module are legacy compatibility adapters.
"""

from __future__ import annotations

import logging
from typing import Any

from odoo.exceptions import AccessError
from odoo.addons.smart_core.utils.extension_hooks import call_extension_hook_first
_logger = logging.getLogger(__name__)

LEGACY_PROJECT_CONTEXT_MODEL = "project.project"
PROJECT_MODEL = LEGACY_PROJECT_CONTEXT_MODEL
DEFAULT_RECORD_CONTEXT_CONFIG: dict[str, str] = {}
_LEGACY_PROJECT_SCOPE_MODELS: set[str] = set()
_OPERATION_STRATEGIES: set[str] = set()
_BUSINESS_SCOPE_EXEMPT_MODELS: set[str] = set()
_LEGACY_DIRECT_ACCEPTANCE_SCOPE_MODELS: dict[str, str] = {}
SOURCE_KIND = "record_context_projection"
SOURCE_AUTHORITIES = ("odoo.orm", "ir.rule", "ir.model.access", "record_context_model", "legacy_project_context_adapter")
NO_BUSINESS_FACT_AUTHORITY = True
LEGACY_PROJECT_SCOPE_ADAPTER_SOURCE_KIND = "legacy_project_scope_adapter"
VALID_OPERATION_STRATEGIES: tuple[str, ...] = ()
BUSINESS_SCOPE_EXEMPT_MODELS: set[str] = _BUSINESS_SCOPE_EXEMPT_MODELS


def register_legacy_project_scope_model(model_name: str) -> None:
    normalized = str(model_name or "").strip()
    if normalized:
        _LEGACY_PROJECT_SCOPE_MODELS.add(normalized)


def register_operation_strategy(strategy: str) -> None:
    normalized = str(strategy or "").strip()
    if normalized:
        _OPERATION_STRATEGIES.add(normalized)


def register_business_scope_exempt_model(model_name: str) -> None:
    normalized = str(model_name or "").strip()
    if normalized:
        _BUSINESS_SCOPE_EXEMPT_MODELS.add(normalized)


def register_legacy_direct_acceptance_scope_model(model_name: str, *, direct_strategy: str = "") -> None:
    normalized = str(model_name or "").strip()
    direct = str(direct_strategy or "").strip()
    if normalized:
        _LEGACY_DIRECT_ACCEPTANCE_SCOPE_MODELS[normalized] = direct


def _registered_legacy_project_scope_models() -> tuple[str, ...]:
    return tuple(sorted(_LEGACY_PROJECT_SCOPE_MODELS))


def _registered_operation_strategies() -> tuple[str, ...]:
    return tuple(sorted(_OPERATION_STRATEGIES))


def _registered_business_scope_exempt_models() -> tuple[str, ...]:
    return tuple(sorted(_BUSINESS_SCOPE_EXEMPT_MODELS))


def _registered_legacy_direct_acceptance_scope_models() -> tuple[str, ...]:
    return tuple(sorted(_LEGACY_DIRECT_ACCEPTANCE_SCOPE_MODELS))


def _primary_legacy_project_scope_model() -> str:
    models = _registered_legacy_project_scope_models()
    return models[0] if models else ""


def _is_legacy_project_scope_model(model_name: str) -> bool:
    normalized = str(model_name or "").strip()
    return bool(normalized and normalized in _LEGACY_PROJECT_SCOPE_MODELS)


def _field_targets_legacy_project_scope(field) -> bool:
    return _is_legacy_project_scope_model(str(getattr(field, "comodel_name", "") or ""))


def source_authority_contract() -> dict[str, Any]:
    return {
        "kind": SOURCE_KIND,
        "authorities": list(SOURCE_AUTHORITIES),
        "projection_only": True,
        "no_business_fact_authority": NO_BUSINESS_FACT_AUTHORITY,
        "default_record_context_model": DEFAULT_RECORD_CONTEXT_CONFIG.get("model", ""),
        "legacy_default_model": LEGACY_PROJECT_CONTEXT_MODEL,
        "legacy_scope_adapter": LEGACY_PROJECT_SCOPE_ADAPTER_SOURCE_KIND,
        "registered_legacy_scope_models": list(_registered_legacy_project_scope_models()),
        "registered_operation_strategies": list(_registered_operation_strategies()),
        "business_scope_exempt_models": list(_registered_business_scope_exempt_models()),
        "runtime_carrier": "system_init_record_context",
    }


def legacy_project_scope_source_authority_contract() -> dict[str, Any]:
    return {
        "kind": LEGACY_PROJECT_SCOPE_ADAPTER_SOURCE_KIND,
        "authorities": ["record_context_projection", "odoo_field_metadata"],
        "projection_only": True,
        "no_business_fact_authority": True,
        "legacy_compatibility": True,
        "legacy_default_model": LEGACY_PROJECT_CONTEXT_MODEL,
        "registered_legacy_scope_models": list(_registered_legacy_project_scope_models()),
        "registered_operation_strategies": list(_registered_operation_strategies()),
    }


def _resolve_record_context_config(env, params: dict | None = None) -> dict[str, str]:
    raw_params = params if isinstance(params, dict) else {}
    explicit_model = str(
        raw_params.get("record_context_model")
        or raw_params.get("context_model")
        or raw_params.get("project_context_model")
        or ""
    ).strip()
    hook_payload = None
    if not explicit_model:
        hook_result = call_extension_hook_first(env, "smart_core_resolve_record_context_config", env, raw_params)
        hook_payload = hook_result if isinstance(hook_result, dict) else None
    cfg_model = ""
    try:
        cfg_model = env["ir.config_parameter"].sudo().get_param("sc.record.context.model") if env is not None else ""
    except Exception:
        cfg_model = ""
    default_model = str(DEFAULT_RECORD_CONTEXT_CONFIG.get("model") or "").strip()
    model = explicit_model or str((hook_payload or {}).get("model") or cfg_model or default_model or LEGACY_PROJECT_CONTEXT_MODEL).strip() or LEGACY_PROJECT_CONTEXT_MODEL
    return {
        "model": model,
        "source": "params" if explicit_model else "extension_hook" if hook_payload else "config" if str(cfg_model or "").strip() else "legacy_default",
        "label": str((hook_payload or {}).get("label") or "当前记录").strip(),
        "placeholder": str((hook_payload or {}).get("placeholder") or "搜索记录").strip(),
        "selected_id_param": str((hook_payload or {}).get("selected_id_param") or ("selected_id")).strip(),
    }


def _model_available(env, model_name: str = "") -> bool:
    try:
        return str(model_name or "").strip() in env.registry.models
    except Exception:
        return False


def _as_int(value: Any) -> int:
    try:
        parsed = int(value or 0)
    except Exception:
        return 0
    return parsed if parsed > 0 else 0


def _as_operation_strategy(value: Any) -> str:
    normalized = str(value or "").strip()
    return normalized if normalized in _OPERATION_STRATEGIES else ""


def _selected_company_id_from_source(source: dict | None) -> int:
    source = source if isinstance(source, dict) else {}
    candidate = _as_int(source.get("company_id") or source.get("current_company_id"))
    if candidate:
        return candidate
    allowed = source.get("allowed_company_ids")
    if isinstance(allowed, (list, tuple)) and len(allowed) == 1:
        return _as_int(allowed[0])
    nested = source.get("context")
    if isinstance(nested, dict):
        return _selected_company_id_from_source(nested)
    return 0


def selected_company_id_from_context(params: dict | None = None, context: dict | None = None) -> int:
    candidate = _selected_company_id_from_source(params)
    if candidate:
        return candidate
    return _selected_company_id_from_source(context)


def _selected_operation_strategy_from_source(source: dict | None) -> str:
    source = source if isinstance(source, dict) else {}
    candidate = _as_operation_strategy(
        source.get("operation_strategy")
        or source.get("operationStrategy")
        or source.get("current_operation_strategy")
        or source.get("currentOperationStrategy")
    )
    if candidate:
        return candidate
    project_context = source.get("project_context")
    if isinstance(project_context, dict):
        candidate = _as_operation_strategy(project_context.get("operation_strategy") or project_context.get("operationStrategy"))
        if candidate:
            return candidate
    nested = source.get("context")
    if isinstance(nested, dict):
        return _selected_operation_strategy_from_source(nested)
    return ""


def selected_operation_strategy_from_context(params: dict | None = None, context: dict | None = None) -> str:
    candidate = _selected_operation_strategy_from_source(params)
    if candidate:
        return candidate
    return _selected_operation_strategy_from_source(context)


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
    company_id = 0
    company_name = ""
    if "company_id" in getattr(record, "_fields", {}):
        try:
            company = record.company_id
            company_id = int(company.id or 0)
            company_name = str(company.display_name or company.name or "").strip()
        except Exception:
            company_id = 0
            company_name = ""
    return {
        "id": int(record.id),
        "name": name,
        "display_name": name,
        "code": code,
        "company_id": company_id,
        "company_name": company_name,
        "stage": stage,
        "owner_id": owner_id,
        "owner_name": owner_name,
        "operation_strategy": operation_strategy,
        "operation_strategy_label": operation_strategy_label,
        "active": bool(getattr(record, "active", True)),
    }


def _company_options(env, active_company_id: int = 0) -> list[dict[str, Any]]:
    selected_id = _as_int(active_company_id) or _as_int(getattr(env.company, "id", 0))
    try:
        companies = env.user.company_ids.sorted(key=lambda item: item.id)
    except Exception:
        companies = env["res.company"].browse([])
    return [
        {
            "company_id": int(company.id),
            "company_name": str(company.display_name or company.name or "").strip(),
            "active": int(company.id) == selected_id,
        }
        for company in companies
    ]


def _operation_strategy_label(Project, operation_strategy: str) -> str:
    selected = _as_operation_strategy(operation_strategy)
    if not selected:
        return ""
    field = getattr(Project, "_fields", {}).get("operation_strategy")
    try:
        selection = field.selection if field else []
        if callable(selection):
            selection = selection(Project)
        return str(dict(selection or []).get(selected, selected))
    except Exception:
        return selected


def _operation_options(Project, active_operation_strategy: str = "") -> list[dict[str, Any]]:
    active = _as_operation_strategy(active_operation_strategy)
    return [{
        "operation_strategy": "",
        "operation_strategy_label": "全部",
        "active": not active,
        "disabled": False,
        "disabled_reason": "",
    }] + [
        {
            "operation_strategy": strategy,
            "operation_strategy_label": _operation_strategy_label(Project, strategy) or strategy,
            "active": strategy == active,
            "disabled": False,
            "disabled_reason": "",
        }
        for strategy in _registered_operation_strategies()
    ]


def _record_context_domain(Model, search: str) -> list:
    term = str(search or "").strip()
    if not term:
        return []
    fields = getattr(Model, "_fields", {}) or {}
    conditions = [
        (field_name, "ilike", term)
        for field_name in ("name", "display_name", "code", "project_code", "x_code")
        if _field_searchable(fields.get(field_name))
    ]
    if not conditions:
        return [("id", "=", 0)]
    if len(conditions) == 1:
        return [conditions[0]]
    return ["|"] * (len(conditions) - 1) + conditions


def _field_searchable(field) -> bool:
    if not field:
        return False
    return bool(getattr(field, "store", False) or getattr(field, "search", None))


def _project_domain(Project, search: str) -> list:
    return _record_context_domain(Project, search)


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


def selected_record_context_id_from_context(params: dict | None = None, context: dict | None = None) -> int:
    return selected_project_id_from_context(params, context)


def selected_business_scope_from_context(params: dict | None = None, context: dict | None = None) -> dict[str, Any]:
    return {
        "company_id": selected_company_id_from_context(params, context),
        "project_id": selected_record_context_id_from_context(params, context),
        "operation_strategy": selected_operation_strategy_from_context(params, context),
    }


def project_scope_domain(env_model, project_id: int) -> list:
    selected_id = _as_int(project_id)
    if not selected_id:
        return []
    model_name = str(getattr(env_model, "_name", "") or "").strip()
    if _is_legacy_project_scope_model(model_name):
        return [("id", "=", selected_id)]
    fields = getattr(env_model, "_fields", {}) or {}
    project_field = fields.get("project_id")
    if project_field and _field_targets_legacy_project_scope(project_field):
        return [("project_id", "=", selected_id)]
    projects_field = fields.get("project_ids")
    if projects_field and _field_targets_legacy_project_scope(projects_field):
        return [("project_ids", "in", [selected_id])]
    return []


def _company_scope_domain(env_model, company_id: int) -> list:
    selected_id = _as_int(company_id)
    if not selected_id:
        return []
    model_name = str(getattr(env_model, "_name", "") or "").strip()
    if model_name == "res.company":
        return [("id", "=", selected_id)]
    fields = getattr(env_model, "_fields", {}) or {}
    company_field = fields.get("company_id")
    project_field = fields.get("project_id")
    if (
        company_field
        and str(getattr(company_field, "comodel_name", "") or "") == "res.company"
        and project_field
        and _field_targets_legacy_project_scope(project_field)
    ):
        return ["|", ("company_id", "=", selected_id), ("project_id.company_id", "=", selected_id)]
    if company_field and str(getattr(company_field, "comodel_name", "") or "") == "res.company":
        return [("company_id", "=", selected_id)]
    if project_field and _field_targets_legacy_project_scope(project_field):
        return [("project_id.company_id", "=", selected_id)]
    projects_field = fields.get("project_ids")
    if projects_field and _field_targets_legacy_project_scope(projects_field):
        return [("project_ids.company_id", "=", selected_id)]
    return []


def _operation_strategy_scope_domain(env_model, operation_strategy: str) -> list:
    selected = _as_operation_strategy(operation_strategy)
    if not selected:
        return []
    fields = getattr(env_model, "_fields", {}) or {}
    project_field = fields.get("project_id")
    if project_field and _field_targets_legacy_project_scope(project_field):
        if "operation_strategy" in fields:
            return [
                "|",
                "&",
                ("project_id", "!=", False),
                ("project_id.operation_strategy", "=", selected),
                "&",
                ("project_id", "=", False),
                ("operation_strategy", "=", selected),
            ]
        return [("project_id.operation_strategy", "=", selected)]
    projects_field = fields.get("project_ids")
    if projects_field and _field_targets_legacy_project_scope(projects_field):
        if "operation_strategy" in fields:
            return ["|", ("project_ids.operation_strategy", "=", selected), ("operation_strategy", "=", selected)]
        return [("project_ids.operation_strategy", "=", selected)]
    if "operation_strategy" in fields:
        return [("operation_strategy", "=", selected)]
    return []


def business_scope_domain(env_model, scope: dict | None = None, *, company_id: int = 0, project_id: int = 0, operation_strategy: str = "") -> list:
    model_name = str(getattr(env_model, "_name", "") or "").strip()
    if model_name in _BUSINESS_SCOPE_EXEMPT_MODELS:
        return []
    scope = scope if isinstance(scope, dict) else {}
    selected_company_id = _as_int(scope.get("company_id") or company_id)
    selected_project_id = _as_int(scope.get("project_id") or project_id)
    selected_operation_strategy = _as_operation_strategy(scope.get("operation_strategy") or operation_strategy)
    direct_acceptance_strategy = _LEGACY_DIRECT_ACCEPTANCE_SCOPE_MODELS.get(model_name, "")
    if direct_acceptance_strategy and not selected_project_id:
        if selected_operation_strategy == direct_acceptance_strategy:
            return ["|", ("project_id", "=", False), ("project_id.operation_strategy", "=", direct_acceptance_strategy)]
        if selected_operation_strategy:
            return [("project_id.operation_strategy", "=", selected_operation_strategy)]
        if selected_company_id:
            return ["|", ("project_id", "=", False), ("project_id.company_id", "=", selected_company_id)]
    domain = []
    domain += _company_scope_domain(env_model, selected_company_id)
    domain += project_scope_domain(env_model, selected_project_id)
    domain += _operation_strategy_scope_domain(env_model, selected_operation_strategy)
    return domain


def business_scope_meta(env_model, scope: dict | None = None, *, applied_domain: list | None = None) -> dict:
    scope = scope if isinstance(scope, dict) else {}
    domain = list(applied_domain or [])
    company_id = _as_int(scope.get("company_id"))
    project_id = _as_int(scope.get("project_id"))
    operation_strategy = _as_operation_strategy(scope.get("operation_strategy"))
    project_operation_strategy = ""
    project_scope_model = _primary_legacy_project_scope_model()
    if project_id and operation_strategy and project_scope_model:
        try:
            project = env_model.env[project_scope_model].sudo().browse(project_id).exists()
            project_operation_strategy = _as_operation_strategy(getattr(project, "operation_strategy", ""))
        except Exception:
            project_operation_strategy = ""
    return {
        "enabled": bool(company_id or project_id or operation_strategy),
        "company_id": company_id or None,
        "project_id": project_id or None,
        "record_context_id": project_id or None,
        "operation_strategy": operation_strategy or "",
        "project_operation_strategy": project_operation_strategy or "",
        "project_operation_strategy_mismatch": bool(
            project_id
            and operation_strategy
            and project_operation_strategy
            and project_operation_strategy != operation_strategy
        ),
        "operation_strategy_values": list(_registered_operation_strategies()),
        "applied": bool(domain),
        "domain": domain,
        "model": str(getattr(env_model, "_name", "") or ""),
        "legacy_project_scope": True,
        "business_scope": True,
        "source_authority": legacy_project_scope_source_authority_contract(),
    }


def apply_business_scope_domain(env_model, domain: list | None, params: dict | None = None, context: dict | None = None) -> tuple[list, dict]:
    base_domain = list(domain or [])
    scope = selected_business_scope_from_context(params, context)
    scope_domain = business_scope_domain(env_model, scope)
    meta = business_scope_meta(env_model, scope, applied_domain=scope_domain)
    if not scope_domain:
        return base_domain, meta
    return scope_domain + base_domain, meta


def apply_project_scope_domain(env_model, domain: list | None, project_id: int) -> tuple[list, dict]:
    base_domain = list(domain or [])
    scope_domain = project_scope_domain(env_model, project_id)
    meta = {
        "enabled": bool(_as_int(project_id)),
        "project_id": _as_int(project_id) or None,
        "record_context_id": _as_int(project_id) or None,
        "applied": bool(scope_domain),
        "domain": scope_domain,
        "model": str(getattr(env_model, "_name", "") or ""),
        "legacy_project_scope": True,
        "source_authority": legacy_project_scope_source_authority_contract(),
    }
    if not scope_domain:
        return base_domain, meta
    return scope_domain + base_domain, meta


def record_in_business_scope(env_model, record_id: int, params: dict | None = None, context: dict | None = None) -> tuple[bool, dict]:
    scoped_domain, meta = apply_business_scope_domain(env_model, [("id", "=", _as_int(record_id))], params, context)
    if not _as_int(record_id):
        return False, meta
    if not meta.get("applied"):
        return True, meta
    try:
        return bool(env_model.search_count(scoped_domain)), meta
    except Exception:
        return False, meta


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


def record_scope_denied_response(scope_meta: dict | None = None, *, message: str = "") -> dict:
    meta = scope_meta if isinstance(scope_meta, dict) else {}
    return {
        "ok": False,
        "error": {
            "code": "PROJECT_SCOPE_DENIED",
            "message": message or "当前记录上下文不允许访问或修改其他记录的数据",
            "reason_code": "PROJECT_SCOPE_DENIED",
            "kind": "permission",
            "project_scope": meta,
            "record_scope": meta,
        },
        "code": 403,
    }


def project_scope_denied_response(scope_meta: dict | None = None, *, message: str = "") -> dict:
    return record_scope_denied_response(scope_meta, message=message)


def build_record_context_contract(env, params: dict | None = None, *, search: str = "", limit: int = 20) -> dict:
    safe_limit = min(max(_as_int(limit) or 20, 1), 50)
    selected_id = _selected_id_from_params(params)
    context_config = _resolve_record_context_config(env, params)
    context_model = context_config["model"]
    is_legacy_project_context = _is_legacy_project_scope_model(context_model)
    selected_company_id = selected_company_id_from_context(params, env.context)
    selected_operation_strategy = selected_operation_strategy_from_context(params, env.context)
    if not selected_company_id:
        selected_company_id = _as_int(getattr(env.company, "id", 0))
    selector = {
        "intent": "project.context.search",
        "search_param": "search",
        "selected_id_param": context_config.get("selected_id_param") or "selected_id",
        "limit": safe_limit,
        "label": context_config.get("label") or "当前记录",
        "placeholder": context_config.get("placeholder") or "搜索记录",
    }
    base = {
        "contract_version": "v1",
        "enabled": False,
        "source": "system.init.record_context",
        "source_authority": source_authority_contract(),
        "model": context_model,
        "context_model": context_model,
        "context_model_source": context_config.get("source") or "",
        "company_id": selected_company_id or None,
        "company_name": "",
        "company_options": _company_options(env, selected_company_id),
        "operation_strategy": selected_operation_strategy,
        "operation_strategy_label": "",
        "operation_options": [],
        "legacy_project_context": is_legacy_project_context,
        "selected": None,
        "options": [],
        "total": 0,
        "selector": selector,
        "persistence": {
            "scope": "browser_session",
            "server_preference": False,
        },
    }
    if not _model_available(env, context_model):
        return {
            **base,
            "reason_code": "RECORD_CONTEXT_MODEL_NOT_INSTALLED",
            "message": "上下文模型未安装",
        }

    try:
        Model = env[context_model]
        domain = _record_context_domain(Model, search)
        if is_legacy_project_context:
            if selected_company_id:
                domain += [("company_id", "=", selected_company_id)]
            if selected_operation_strategy:
                domain += [("operation_strategy", "=", selected_operation_strategy)]
        records = Model.search(domain, limit=safe_limit, order="write_date desc, id desc")
        selected = None
        if selected_id:
            selected_record = Model.browse(selected_id)
            selected_record = selected_record.exists()
            if selected_record and is_legacy_project_context:
                if selected_company_id and getattr(selected_record, "company_id", None).id != selected_company_id:
                    selected_record = Model.browse([])
                if selected_operation_strategy and getattr(selected_record, "operation_strategy", "") != selected_operation_strategy:
                    selected_record = Model.browse([])
            if selected_record:
                selected = format_project_option(selected_record)
        options = [format_project_option(record) for record in records]
        if selected and all(option.get("id") != selected.get("id") for option in options):
            options = [selected, *options]
        total = Model.search_count(domain)
        company = env["res.company"].browse(selected_company_id).exists() if selected_company_id else env["res.company"].browse([])
        return {
            **base,
            "enabled": True,
            "company_id": selected_company_id or None,
            "company_name": str(company.display_name or company.name or "").strip() if company else "",
            "company_options": _company_options(env, selected_company_id),
            "operation_strategy": selected_operation_strategy,
            "operation_strategy_label": _operation_strategy_label(Model, selected_operation_strategy),
            "operation_options": _operation_options(Model, selected_operation_strategy) if is_legacy_project_context else [],
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
            "reason_code": "RECORD_CONTEXT_ACCESS_DENIED",
            "message": "当前账号无权读取上下文记录",
        }
    except Exception as exc:
        _logger.exception("build record context contract failed")
        return {
            **base,
            "enabled": True,
            "reason_code": "RECORD_CONTEXT_ERROR",
            "message": str(exc),
        }


def build_project_context_contract(env, params: dict | None = None, *, search: str = "", limit: int = 20) -> dict:
    return build_record_context_contract(env, params, search=search, limit=limit)
