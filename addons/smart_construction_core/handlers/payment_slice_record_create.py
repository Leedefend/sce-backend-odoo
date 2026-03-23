# -*- coding: utf-8 -*-
from __future__ import annotations

import time
from typing import Any, Dict

from odoo.exceptions import UserError

from odoo.addons.smart_core.core.base_handler import BaseIntentHandler
from odoo.addons.smart_construction_core.services.payment_slice_service import PaymentSliceService


class PaymentSliceRecordCreateHandler(BaseIntentHandler):
    INTENT_TYPE = "payment.record.create"
    DESCRIPTION = "创建最小项目付款记录"
    VERSION = "1.0.0"
    ETAG_ENABLED = False
    REQUIRED_GROUPS = ["base.group_user"]
    ACL_MODE = "explicit_check"

    @staticmethod
    def _coerce_project_id(raw: Any) -> int:
        try:
            value = int(raw or 0)
        except Exception:
            return 0
        return value if value > 0 else 0

    def _resolve_project_id(self, params: Dict[str, Any], ctx: Dict[str, Any]) -> int:
        candidates = [
            (params or {}).get("project_id"),
            ((params or {}).get("project_context") or {}).get("project_id")
            if isinstance((params or {}).get("project_context"), dict)
            else None,
            (ctx or {}).get("project_id"),
            (ctx or {}).get("record_id"),
        ]
        for item in candidates:
            project_id = self._coerce_project_id(item)
            if project_id > 0:
                return project_id
        return 0

    def handle(self, payload=None, ctx=None):
        ts0 = time.time()
        params = payload or self.params or {}
        if isinstance(params, dict) and isinstance(params.get("params"), dict):
            params = params.get("params") or {}
        ctx = ctx or {}
        trace_id = str((self.context or {}).get("trace_id") or "")
        project_id = self._resolve_project_id(params, ctx)
        if project_id <= 0:
            return {
                "ok": False,
                "error": {
                    "code": "PROJECT_CONTEXT_MISSING",
                    "message": "缺少 project_id，无法创建付款记录",
                    "suggested_action": "fix_input",
                },
                "meta": {"intent": self.INTENT_TYPE, "elapsed_ms": int((time.time() - ts0) * 1000), "trace_id": trace_id},
            }

        service = PaymentSliceService(self.env)
        project, _diag = service.resolve_project_with_diagnostics(project_id)
        if not project:
            return {
                "ok": False,
                "error": {
                    "code": "PROJECT_NOT_FOUND",
                    "message": "项目不存在或当前账号不可访问",
                    "suggested_action": "fix_input",
                },
                "meta": {"intent": self.INTENT_TYPE, "elapsed_ms": int((time.time() - ts0) * 1000), "trace_id": trace_id},
            }

        try:
            result = service.create_payment_entry(project=project, values=params, context=ctx)
        except UserError as exc:
            return {
                "ok": False,
                "error": {
                    "code": "PAYMENT_ENTRY_CREATE_FAILED",
                    "message": str(exc),
                    "suggested_action": "fix_input",
                },
                "meta": {"intent": self.INTENT_TYPE, "elapsed_ms": int((time.time() - ts0) * 1000), "trace_id": trace_id},
            }

        return {
            "ok": True,
            "data": result,
            "meta": {"intent": self.INTENT_TYPE, "elapsed_ms": int((time.time() - ts0) * 1000), "trace_id": trace_id},
        }
