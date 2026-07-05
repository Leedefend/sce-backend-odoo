# -*- coding: utf-8 -*-
"""Record context selector intents.

The intent name remains project.context.search for client compatibility.
"""

from ..core.base_handler import BaseIntentHandler
from ..core.intent_execution_result import IntentExecutionResult
try:
    from ..core.project_context import build_record_context_contract
except ImportError:  # pragma: no cover - compatibility for lightweight boundary tests
    from ..core.project_context import build_project_context_contract as build_record_context_contract
from ..core.project_context import source_authority_contract
from ..core.request_params import parse_positive_int


class ProjectContextSearchHandler(BaseIntentHandler):
    INTENT_TYPE = "project.context.search"
    DESCRIPTION = "Search selectable records for current context"
    VERSION = "1.0.0"
    SOURCE_KIND = "record_context_projection"
    SOURCE_AUTHORITIES = ("odoo.orm", "ir.rule", "ir.model.access", "record_context_model")

    def handle(self, payload=None, ctx=None):
        params = {}
        if isinstance(payload, dict):
            inner = payload.get("params")
            if isinstance(inner, dict):
                params.update(inner)
            else:
                params.update(payload)
        if isinstance(getattr(self, "params", None), dict):
            params.update(self.params)
        search = str(params.get("search") or params.get("query") or "").strip()
        limit, limit_error = parse_positive_int(params.get("limit"), allow_empty=True)
        if limit_error:
            return self._err(400, "limit 无效")
        limit = limit or 20
        data = build_record_context_contract(self.env, params, search=search, limit=limit)
        return IntentExecutionResult(
            ok=True,
            status="success",
            data=data,
            meta={
                "intent": self.INTENT_TYPE,
                "version": self.VERSION,
                "source_kind": self.SOURCE_KIND,
                "source_authorities": list(self.SOURCE_AUTHORITIES),
                "source_authority": source_authority_contract(),
            },
        )

    def _err(self, code: int, message: str) -> IntentExecutionResult:
        return IntentExecutionResult(
            ok=False,
            error={"code": code, "message": message},
            meta={
                "intent": self.INTENT_TYPE,
                "version": self.VERSION,
                "source_authority": source_authority_contract(),
            },
            code=code,
        )
