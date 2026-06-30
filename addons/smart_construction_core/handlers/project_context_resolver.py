# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Dict, List


def coerce_positive_id(raw: Any) -> int:
    try:
        value = int(raw or 0)
    except Exception:
        return 0
    return value if value > 0 else 0


def resolve_project_id(
    params: Dict[str, Any] | None,
    ctx: Dict[str, Any] | None,
    *,
    payload: Dict[str, Any] | None = None,
    include_param_record_id: bool = True,
    include_project_context: bool = True,
    include_ctx_record_id: bool = True,
    ctx_record_model_only: str = "",
) -> int:
    params = params or {}
    ctx = ctx or {}
    payload = payload or {}
    candidates: List[Any] = [params.get("project_id")]
    if payload:
        candidates.append(payload.get("project_id"))
    if include_param_record_id:
        candidates.append(params.get("record_id"))
    if include_project_context:
        project_context = params.get("project_context")
        if isinstance(project_context, dict):
            candidates.append(project_context.get("project_id"))
    candidates.append(ctx.get("project_id"))
    if include_ctx_record_id:
        if not ctx_record_model_only or str(ctx.get("model") or "").strip() == ctx_record_model_only:
            candidates.append(ctx.get("record_id"))
    for item in candidates:
        project_id = coerce_positive_id(item)
        if project_id > 0:
            return project_id
    return 0


def resolve_company_id(params: Dict[str, Any] | None, ctx: Dict[str, Any] | None) -> int:
    params = params or {}
    ctx = ctx or {}
    for raw in (params.get("company_id"), params.get("current_company_id"), ctx.get("company_id")):
        company_id = coerce_positive_id(raw)
        if company_id > 0:
            return company_id
    return 0


def resolve_operation_strategy(params: Dict[str, Any] | None, ctx: Dict[str, Any] | None) -> str:
    for source in (params or {}, ctx or {}):
        value = str(source.get("operation_strategy") or source.get("operationStrategy") or "").strip()
        if value in {"direct", "joint"}:
            return value
    return ""


class ProjectContextResolverMixin:
    PROJECT_ID_PARAM_RECORD_ID = True
    PROJECT_ID_PROJECT_CONTEXT = True
    PROJECT_ID_CTX_RECORD_ID = True
    PROJECT_ID_CTX_RECORD_MODEL_ONLY = ""
    PROJECT_ID_INCLUDE_HANDLER_PAYLOAD = False

    @staticmethod
    def _coerce_project_id(raw: Any) -> int:
        return coerce_positive_id(raw)

    def _resolve_project_id(self, params: Dict[str, Any], ctx: Dict[str, Any]) -> int:
        payload = getattr(self, "payload", None)
        return resolve_project_id(
            params,
            ctx,
            payload=payload if self.PROJECT_ID_INCLUDE_HANDLER_PAYLOAD and isinstance(payload, dict) else None,
            include_param_record_id=bool(self.PROJECT_ID_PARAM_RECORD_ID),
            include_project_context=bool(self.PROJECT_ID_PROJECT_CONTEXT),
            include_ctx_record_id=bool(self.PROJECT_ID_CTX_RECORD_ID),
            ctx_record_model_only=str(self.PROJECT_ID_CTX_RECORD_MODEL_ONLY or ""),
        )

    def _resolve_company_id(self, params: Dict[str, Any], ctx: Dict[str, Any]) -> int:
        return resolve_company_id(params, ctx)

    @staticmethod
    def _resolve_operation_strategy(params: Dict[str, Any], ctx: Dict[str, Any]) -> str:
        return resolve_operation_strategy(params, ctx)
