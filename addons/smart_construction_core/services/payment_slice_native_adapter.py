# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo import fields


class PaymentSliceNativeAdapter:
    """Prepared payment adapter backed by payment.request draft facts."""

    SUPPORTED_TYPES = ("pay",)

    def __init__(self, env):
        self.env = env

    def _model(self, model_name):
        try:
            return self.env[model_name]
        except Exception:
            return None

    def _has_fields(self, model_name, field_names):
        model = self._model(model_name)
        if model is None:
            return False
        model_fields = getattr(model, "_fields", {})
        return all(str(name) in model_fields for name in (field_names or ()))

    def request_domain(self, project):
        if not project or not self._has_fields("payment.request", ["project_id", "type"]):
            return [("id", "=", 0)]
        return [
            ("project_id", "=", int(project.id)),
            ("type", "in", list(self.SUPPORTED_TYPES)),
        ]

    def recent_requests(self, project, *, limit=20):
        PaymentRequest = self._model("payment.request")
        if PaymentRequest is None or not project:
            return []
        PaymentRequest = PaymentRequest.sudo()
        try:
            rows = PaymentRequest.search(self.request_domain(project), order="date_request desc,id desc", limit=max(int(limit or 0), 0))
        except Exception:
            return []
        return [self._request_payload(row) for row in rows]

    def ledger_domain(self, project):
        if not project or not self._has_fields("payment.ledger", ["project_id"]):
            return [("id", "=", 0)]
        return [("project_id", "=", int(project.id))]

    def summary(self, project):
        summary = {
            "project_id": int(getattr(project, "id", 0) or 0),
            "carrier_model": "payment.request",
            "secondary_context_model": "project.project",
            "supported_types": list(self.SUPPORTED_TYPES),
            "request_count": 0,
            "draft_request_count": 0,
            "approved_request_count": 0,
            "total_payment_amount": 0.0,
            "draft_payment_amount": 0.0,
            "approved_payment_amount": 0.0,
            "ledger_count": 0,
            "executed_payment_amount": 0.0,
            "currency_name": "",
            "latest_request_date": "",
            "latest_paid_at": "",
            "as_of_date": str(fields.Date.today()),
            "prepared_boundary": "project_payment_request_draft_tracking_only",
        }
        requests = self.recent_requests(project, limit=20)
        PaymentRequest = self._model("payment.request")
        PaymentLedger = self._model("payment.ledger")
        if PaymentRequest is None or not project:
            summary["recent_requests"] = requests
            return summary
        PaymentRequest = PaymentRequest.sudo()
        try:
            all_requests = PaymentRequest.search(self.request_domain(project), order="date_request desc,id desc")
        except Exception:
            summary["recent_requests"] = requests
            return summary

        draft_amount = 0.0
        approved_amount = 0.0
        latest_request_date = ""
        currency_name = ""
        request_count = 0
        draft_request_count = 0
        approved_request_count = 0
        approved_states = {"approve", "approved", "done"}
        total_amount = 0.0
        for request in all_requests:
            request_count += 1
            amount = round(float(getattr(request, "amount", 0.0) or 0.0), 2)
            total_amount += amount
            state = str(getattr(request, "state", "") or "")
            if state == "draft":
                draft_request_count += 1
                draft_amount += amount
            if state in approved_states:
                approved_request_count += 1
                approved_amount += amount
            if not latest_request_date:
                latest_request_date = str(getattr(request, "date_request", "") or "")
            if not currency_name:
                currency_name = str(getattr(getattr(request, "currency_id", None), "name", "") or "")

        summary.update(
            {
                "request_count": request_count,
                "draft_request_count": draft_request_count,
                "approved_request_count": approved_request_count,
                "total_payment_amount": round(total_amount, 2),
                "draft_payment_amount": round(draft_amount, 2),
                "approved_payment_amount": round(approved_amount, 2),
                "currency_name": currency_name,
                "latest_request_date": latest_request_date,
                "recent_requests": requests,
            }
        )
        if PaymentLedger is not None and project:
            PaymentLedger = PaymentLedger.sudo()
            try:
                ledgers = PaymentLedger.search(self.ledger_domain(project), order="paid_at desc,id desc")
            except Exception:
                ledgers = []
            if ledgers:
                executed_amount = 0.0
                latest_paid_at = ""
                for ledger in ledgers:
                    executed_amount += round(float(getattr(ledger, "amount", 0.0) or 0.0), 2)
                    if not latest_paid_at:
                        latest_paid_at = str(getattr(ledger, "paid_at", "") or "")
                    if not currency_name:
                        currency_name = str(getattr(getattr(ledger, "currency_id", None), "name", "") or "")
                summary.update(
                    {
                        "ledger_count": len(ledgers),
                        "executed_payment_amount": round(executed_amount, 2),
                        "latest_paid_at": latest_paid_at,
                        "currency_name": currency_name,
                    }
                )
        return summary

    def _request_payload(self, request):
        project = getattr(request, "project_id", None)
        partner = getattr(request, "partner_id", None)
        return {
            "payment_request_id": int(getattr(request, "id", 0) or 0),
            "name": str(getattr(request, "name", "") or ""),
            "date": str(getattr(request, "date_request", "") or ""),
            "state": str(getattr(request, "state", "") or ""),
            "type": str(getattr(request, "type", "") or ""),
            "amount": round(float(getattr(request, "amount", 0.0) or 0.0), 2),
            "currency_name": str(getattr(getattr(request, "currency_id", None), "name", "") or ""),
            "description": str(getattr(request, "note", "") or ""),
            "partner_name": str(getattr(partner, "display_name", "") or ""),
            "project_id": int(getattr(project, "id", 0) or 0),
            "project_name": str(getattr(project, "display_name", "") or ""),
        }
