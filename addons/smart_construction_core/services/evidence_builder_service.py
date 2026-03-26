# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo import api, models


class EvidenceBuilderService(models.AbstractModel):
    _name = "sc.evidence.builder"
    _description = "Smart Construction Evidence Builder"

    @api.model
    def build(self, records, event_code="evidence_synced"):
        Evidence = self.env["sc.business.evidence"].sudo()
        built = Evidence.browse()
        for record in records:
            model_name = str(getattr(record, "_name", "") or "")
            if model_name == "payment.request":
                built |= self._build_payment(record, event_code=event_code)
            elif model_name == "project.cost.ledger":
                built |= self._build_cost(record, event_code=event_code)
            elif model_name == "sc.settlement.order":
                built |= self._build_settlement(record, event_code=event_code)
            elif model_name == "project.task":
                built |= self._build_progress(record, event_code=event_code)
        return built

    def _build_payment(self, record, *, event_code):
        if not record.project_id:
            return self.env["sc.business.evidence"].sudo().browse()
        relation_chain = {
            "event_code": str(event_code or "payment_request_updated"),
            "payment_request_id": int(record.id),
            "payment_request_name": str(record.name or ""),
            "payment_request_state": str(record.state or ""),
            "payment_type": str(record.type or ""),
            "project_id": int(record.project_id.id),
            "project_name": str(record.project_id.display_name or ""),
            "settlement_id": int(record.settlement_id.id) if record.settlement_id else False,
            "settlement_name": str(record.settlement_id.display_name or "") if record.settlement_id else False,
            "partner_id": int(record.partner_id.id) if record.partner_id else False,
            "partner_name": str(record.partner_id.display_name or "") if record.partner_id else False,
            "paid_amount_total": float(record.paid_amount_total or 0.0),
            "unpaid_amount": float(record.unpaid_amount or 0.0),
            "is_fully_paid": bool(record.is_fully_paid),
            "ledger_ids": record.ledger_line_ids.ids,
            "ledger_count": len(record.ledger_line_ids),
            "trace": [
                "payment.request#%s" % int(record.id),
                *["payment.ledger#%s" % int(ledger.id) for ledger in record.ledger_line_ids],
            ],
        }
        return self.env["sc.business.evidence"].sudo().upsert_evidence(
            name="Payment Evidence %s" % (record.name or record.id),
            business_model="project.project",
            business_id=int(record.project_id.id),
            evidence_type="payment",
            source_model=record._name,
            source_id=int(record.id),
            amount=float(record.amount or 0.0),
            quantity=1.0,
            operator=self.env.user,
            relation_chain=relation_chain,
        )

    def _build_cost(self, record, *, event_code):
        if not record.project_id:
            return self.env["sc.business.evidence"].sudo().browse()
        trace = ["project.cost.ledger#%s" % int(record.id)]
        if record.source_model and record.source_id:
            trace.append("%s#%s" % (record.source_model, int(record.source_id)))
        relation_chain = {
            "event_code": str(event_code or "cost_ledger_updated"),
            "cost_ledger_id": int(record.id),
            "project_id": int(record.project_id.id),
            "project_name": str(record.project_id.display_name or ""),
            "cost_code_id": int(record.cost_code_id.id) if record.cost_code_id else False,
            "cost_code_name": str(record.cost_code_id.display_name or "") if record.cost_code_id else False,
            "period": str(record.period or ""),
            "date": str(record.date or ""),
            "source_model": str(record.source_model or ""),
            "source_id": int(record.source_id or 0),
            "source_line_id": int(record.source_line_id or 0),
            "trace": trace,
        }
        return self.env["sc.business.evidence"].sudo().upsert_evidence(
            name="Cost Evidence %s" % int(record.id),
            business_model="project.project",
            business_id=int(record.project_id.id),
            evidence_type="cost",
            source_model=record._name,
            source_id=int(record.id),
            amount=float(record.amount or 0.0),
            quantity=float(record.qty or 0.0),
            operator=self.env.user,
            relation_chain=relation_chain,
        )

    def _build_settlement(self, record, *, event_code):
        if not record.project_id or str(record.state or "") not in {"approve", "done"}:
            return self.env["sc.business.evidence"].sudo().browse()
        relation_chain = {
            "event_code": str(event_code or "settlement_done"),
            "settlement_id": int(record.id),
            "settlement_name": str(record.name or ""),
            "settlement_state": str(record.state or ""),
            "project_id": int(record.project_id.id),
            "project_name": str(record.project_id.display_name or ""),
            "settlement_type": str(record.settlement_type or ""),
            "paid_amount": float(record.paid_amount or 0.0),
            "remaining_amount": float(record.remaining_amount or 0.0),
            "payment_request_ids": record.payment_request_ids.ids,
            "line_count": len(record.line_ids),
            "trace": [
                "sc.settlement.order#%s" % int(record.id),
                *["payment.request#%s" % int(request.id) for request in record.payment_request_ids],
            ],
        }
        return self.env["sc.business.evidence"].sudo().upsert_evidence(
            name="Settlement Evidence %s" % (record.name or record.id),
            business_model="project.project",
            business_id=int(record.project_id.id),
            evidence_type="settlement",
            source_model=record._name,
            source_id=int(record.id),
            amount=float(record.amount_total or 0.0),
            quantity=float(len(record.line_ids)),
            operator=self.env.user,
            relation_chain=relation_chain,
        )

    def _build_progress(self, record, *, event_code):
        if not record.project_id:
            return self.env["sc.business.evidence"].sudo().browse()
        progress_ratio = record._get_progress_ratio()
        relation_chain = {
            "event_code": str(event_code or "task_updated"),
            "project_id": int(record.project_id.id),
            "task_id": int(record.id),
            "task_name": str(record.display_name or record.name or ""),
            "task_state": str(record.sc_state or ""),
            "readiness_status": str(record.readiness_status or ""),
            "deadline": str(record.date_deadline or ""),
            "progress_ratio": float(progress_ratio or 0.0) if progress_ratio is not None else 0.0,
        }
        return self.env["sc.business.evidence"].sudo().upsert_evidence(
            business_model="project.project",
            business_id=int(record.project_id.id),
            evidence_type="progress",
            source_model=record._name,
            source_id=int(record.id),
            name="Progress Evidence %s" % (record.display_name or record.name or record.id),
            amount=float(progress_ratio or 0.0) if progress_ratio is not None else 0.0,
            quantity=1.0,
            operator=self.env.user,
            relation_chain=relation_chain,
        )
