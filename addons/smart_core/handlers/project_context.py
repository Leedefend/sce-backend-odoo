# -*- coding: utf-8 -*-
"""Project context selector intents."""

from ..core.base_handler import BaseIntentHandler
from ..core.intent_execution_result import IntentExecutionResult
from ..core.project_context import build_project_context_contract, source_authority_contract


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
        limit = params.get("limit") or 20
        data = build_project_context_contract(self.env, params, search=search, limit=limit)
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
