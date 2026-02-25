# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo.addons.smart_core.core.base_handler import BaseIntentHandler


class _BaseOwnerPaymentRequestHandler(BaseIntentHandler):
    ETAG_ENABLED = False
    ACL_MODE = "explicit_check"
    REQUIRED_GROUPS = ["smart_core.group_sc_data_operator"]

    def _build_response(self, action: str) -> dict:
        params = self.params if isinstance(self.params, dict) else {}
        payload = {
            "accepted": True,
            "action": action,
            "domain": "owner",
            "request_id": str(params.get("request_id") or ""),
            "record_id": int(params.get("record_id") or 0),
            "model": str(params.get("model") or "owner.payment.request"),
        }
        return {
            "ok": True,
            "data": payload,
            "meta": {"intent": self.INTENT_TYPE, "domain": "owner"},
        }


class OwnerPaymentRequestSubmitHandler(_BaseOwnerPaymentRequestHandler):
    INTENT_TYPE = "owner.payment.request.submit"
    DESCRIPTION = "Submit owner payment request"
    VERSION = "0.1.0"

    def handle(self, payload=None, ctx=None):
        return self._build_response("submit")


class OwnerPaymentRequestApproveHandler(_BaseOwnerPaymentRequestHandler):
    INTENT_TYPE = "owner.payment.request.approve"
    DESCRIPTION = "Approve owner payment request"
    VERSION = "0.1.0"
    REQUIRED_GROUPS = ["smart_core.group_sc_finance_approver"]

    def handle(self, payload=None, ctx=None):
        return self._build_response("approve")

