# -*- coding: utf-8 -*-
from __future__ import annotations

from uuid import uuid4

from odoo.addons.smart_core.core.base_handler import BaseIntentHandler
from odoo.addons.smart_core.handlers.reason_codes import (
    REASON_MISSING_PARAMS,
    failure_meta_for_reason,
)

from .payment_request_approval import (
    PaymentRequestApproveHandler,
    PaymentRequestDoneHandler,
    PaymentRequestRejectHandler,
    PaymentRequestSubmitHandler,
)


class PaymentRequestExecuteHandler(BaseIntentHandler):
    INTENT_TYPE = "payment.request.execute"
    DESCRIPTION = "Execute payment request semantic action via one intent"
    VERSION = "1.0.0"
    ETAG_ENABLED = False

    _ACTION_TO_HANDLER = {
        "submit": PaymentRequestSubmitHandler,
        "approve": PaymentRequestApproveHandler,
        "reject": PaymentRequestRejectHandler,
        "done": PaymentRequestDoneHandler,
    }

    def _trace_id(self) -> str:
        if isinstance(self.context, dict):
            value = str(self.context.get("trace_id") or "").strip()
            if value:
                return value
        return f"pay_req_exec_{uuid4().hex[:12]}"

    def _error(self, *, message: str, trace_id: str, code: int = 400):
        reason_code = REASON_MISSING_PARAMS
        return {
            "ok": False,
            "data": {
                "success": False,
                "reason_code": reason_code,
                "message": str(message or ""),
            },
            "error": {
                "code": reason_code,
                "reason_code": reason_code,
                "message": str(message or ""),
                **failure_meta_for_reason(reason_code),
            },
            "code": int(code),
            "meta": {"intent": self.INTENT_TYPE, "trace_id": trace_id},
        }

    def handle(self, payload=None, ctx=None):
        params = payload or self.params or {}
        if isinstance(params, dict) and isinstance(params.get("params"), dict):
            params = params.get("params") or {}

        trace_id = self._trace_id()
        action = str((params or {}).get("action") or "").strip().lower()
        if not action:
            return self._error(message="missing action", trace_id=trace_id, code=400)
        handler_cls = self._ACTION_TO_HANDLER.get(action)
        if not handler_cls:
            return self._error(message="unsupported action", trace_id=trace_id, code=400)

        delegated_params = dict(params or {})
        delegated_params.pop("action", None)
        delegated_params["intent_action"] = action
        if not str(delegated_params.get("request_id") or "").strip():
            delegated_params["request_id"] = f"pay_req_exec_{action}_{uuid4().hex[:8]}"

        delegated = handler_cls(self.env, payload=delegated_params, request=self.request)
        result = delegated.handle(payload=delegated_params, ctx=ctx)
        if not isinstance(result, dict):
            return self._error(message="unexpected delegate response", trace_id=trace_id, code=500)

        meta = result.get("meta") if isinstance(result.get("meta"), dict) else {}
        meta.setdefault("intent", self.INTENT_TYPE)
        meta.setdefault("trace_id", trace_id)
        result["meta"] = meta
        data = result.get("data") if isinstance(result.get("data"), dict) else {}
        data.setdefault("intent_action", action)
        result["data"] = data
        return result

