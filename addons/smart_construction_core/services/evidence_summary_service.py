# -*- coding: utf-8 -*-
from __future__ import annotations

import json

from odoo import api, models


class EvidenceSummaryService(models.AbstractModel):
    _name = "sc.evidence.summary.service"
    _description = "Smart Construction Evidence Summary Service"

    @staticmethod
    def _safe_float(value):
        try:
            return round(float(value or 0.0), 2)
        except Exception:
            return 0.0

    @staticmethod
    def _safe_int(value):
        try:
            return int(value or 0)
        except Exception:
            return 0

    @staticmethod
    def _parse_relation_chain(raw_value):
        text = str(raw_value or "").strip()
        if not text:
            return {}
        try:
            payload = json.loads(text)
        except Exception:
            return {}
        return payload if isinstance(payload, dict) else {}

    @api.model
    def summary_for_project(self, project):
        empty = {
            "evidence_count": 0,
            "cost_count": 0,
            "cost_total": 0.0,
            "payment_count": 0,
            "payment_total": 0.0,
            "pay_count": 0,
            "pay_total": 0.0,
            "pay_done_count": 0,
            "pay_done_total": 0.0,
            "pay_pending_total": 0.0,
            "receive_count": 0,
            "receive_total": 0.0,
            "receive_done_total": 0.0,
            "receive_pending_total": 0.0,
            "settlement_count": 0,
            "settlement_total": 0.0,
            "settlement_done_count": 0,
            "progress_count": 0,
            "progress_percent": 0.0,
            "risk_codes": [],
        }
        if not project:
            return empty

        Evidence = self.env["sc.business.evidence"].sudo()
        evidences = Evidence.search(
            [
                ("business_model", "=", "project.project"),
                ("business_id", "=", int(project.id)),
            ]
        )
        if not evidences:
            return empty

        summary = dict(empty)
        progress_values = []
        risk_codes = set()
        done_states = {"approve", "approved", "done"}
        pending_states = {"draft", "submit", "submitted", "pending", "confirm"}
        for evidence in evidences:
            evidence_type = str(evidence.evidence_type or "")
            relation_chain = self._parse_relation_chain(evidence.relation_chain)
            amount = self._safe_float(evidence.amount)
            summary["evidence_count"] += 1
            if evidence_type == "cost":
                summary["cost_count"] += 1
                summary["cost_total"] = self._safe_float(summary["cost_total"] + amount)
            elif evidence_type == "payment":
                payment_type = str(relation_chain.get("payment_type") or "")
                payment_state = str(relation_chain.get("payment_request_state") or "")
                summary["payment_count"] += 1
                summary["payment_total"] = self._safe_float(summary["payment_total"] + amount)
                if payment_type == "receive":
                    summary["receive_count"] += 1
                    summary["receive_total"] = self._safe_float(summary["receive_total"] + amount)
                    if payment_state in done_states:
                        summary["receive_done_total"] = self._safe_float(summary["receive_done_total"] + amount)
                    elif payment_state in pending_states:
                        summary["receive_pending_total"] = self._safe_float(summary["receive_pending_total"] + amount)
                else:
                    summary["pay_count"] += 1
                    summary["pay_total"] = self._safe_float(summary["pay_total"] + amount)
                    if payment_state in done_states:
                        summary["pay_done_count"] += 1
                        summary["pay_done_total"] = self._safe_float(summary["pay_done_total"] + amount)
                    elif payment_state in pending_states:
                        summary["pay_pending_total"] = self._safe_float(summary["pay_pending_total"] + amount)
            elif evidence_type == "settlement":
                settlement_state = str(relation_chain.get("settlement_state") or "")
                summary["settlement_count"] += 1
                summary["settlement_total"] = self._safe_float(summary["settlement_total"] + amount)
                if settlement_state == "done":
                    summary["settlement_done_count"] += 1
            elif evidence_type == "progress":
                summary["progress_count"] += 1
                progress_values.append(self._safe_float(evidence.amount))
            code = str(relation_chain.get("risk_code") or "").strip()
            if code:
                risk_codes.add(code)

        if progress_values:
            summary["progress_percent"] = self._safe_float(sum(progress_values) / float(len(progress_values)))
        summary["risk_codes"] = sorted(risk_codes)
        return summary
