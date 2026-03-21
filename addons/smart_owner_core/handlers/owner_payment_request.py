# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo.addons.smart_core.core.base_handler import BaseIntentHandler


class _BaseOwnerPaymentRequestHandler(BaseIntentHandler):
    ETAG_ENABLED = False
    ACL_MODE = "explicit_check"
    REQUIRED_GROUPS = ["smart_core.group_smart_core_data_operator"]

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


class _BaseOwnerReadHandler(BaseIntentHandler):
    ETAG_ENABLED = False
    ACL_MODE = "explicit_check"
    REQUIRED_GROUPS = []

    def _response(self, action: str) -> dict:
        return {
            "ok": True,
            "data": {
                "accepted": True,
                "domain": "owner",
                "action": action,
            },
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
    REQUIRED_GROUPS = ["smart_core.group_smart_core_finance_approver"]

    def handle(self, payload=None, ctx=None):
        return self._build_response("approve")


class OwnerDashboardOpenHandler(_BaseOwnerReadHandler):
    INTENT_TYPE = "owner.dashboard.open"
    DESCRIPTION = "Open owner dashboard"
    VERSION = "0.1.0"

    def handle(self, payload=None, ctx=None):
        return self._response("dashboard_open")


class OwnerProjectsListHandler(_BaseOwnerReadHandler):
    INTENT_TYPE = "owner.projects.list"
    DESCRIPTION = "List owner projects"
    VERSION = "0.1.0"

    def handle(self, payload=None, ctx=None):
        return self._response("projects_list")


class OwnerProjectsDetailHandler(_BaseOwnerReadHandler):
    INTENT_TYPE = "owner.projects.detail"
    DESCRIPTION = "View owner project detail"
    VERSION = "0.1.0"

    def handle(self, payload=None, ctx=None):
        return self._response("projects_detail")


class OwnerRiskListHandler(_BaseOwnerReadHandler):
    INTENT_TYPE = "owner.risk.list"
    DESCRIPTION = "List owner risks"
    VERSION = "0.1.0"

    def handle(self, payload=None, ctx=None):
        return self._response("risk_list")


class OwnerReportOverviewHandler(_BaseOwnerReadHandler):
    INTENT_TYPE = "owner.report.overview"
    DESCRIPTION = "Open owner report overview"
    VERSION = "0.1.0"

    def handle(self, payload=None, ctx=None):
        return self._response("report_overview")


class OwnerApprovalCenterHandler(_BaseOwnerReadHandler):
    INTENT_TYPE = "owner.approval.center"
    DESCRIPTION = "Open owner approval center"
    VERSION = "0.1.0"

    def handle(self, payload=None, ctx=None):
        return self._response("approval_center")
