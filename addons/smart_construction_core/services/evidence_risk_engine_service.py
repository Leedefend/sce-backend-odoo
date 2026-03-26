# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo import api, models


class EvidenceRiskEngineService(models.AbstractModel):
    _name = "sc.evidence.risk.engine"
    _description = "Smart Construction Evidence Risk Engine"

    @staticmethod
    def _trace_action(project, evidence_type):
        return {
            "intent": "business.evidence.trace",
            "payload": {
                "business_model": "project.project",
                "business_id": int(getattr(project, "id", 0) or 0),
                "evidence_type": str(evidence_type or ""),
            },
        }

    def _risk(self, *, project, risk_code, severity, reason, evidence_types):
        refs = [
            {
                "business_model": "project.project",
                "business_id": int(getattr(project, "id", 0) or 0),
                "evidence_type": str(evidence_type or ""),
            }
            for evidence_type in (evidence_types or [])
        ]
        return {
            "risk_code": str(risk_code or ""),
            "severity": str(severity or "medium"),
            "reason": str(reason or ""),
            "evidence_refs": refs,
            "trace_action": self._trace_action(project, (evidence_types or [""])[0]),
        }

    @api.model
    def analyze(self, project):
        summary = self.env["sc.evidence.summary.service"].summary_for_project(project)
        lifecycle_state = str(getattr(project, "lifecycle_state", "") or "").strip().lower() if project else ""
        signals = {
            "is_draft": lifecycle_state == "draft",
            "no_tasks": lifecycle_state in {"in_progress", "closing", "warranty", "done"} and int(summary.get("progress_count") or 0) <= 0,
            "no_cost": lifecycle_state in {"in_progress", "closing", "warranty", "done"} and int(summary.get("cost_count") or 0) <= 0,
            "no_payment": lifecycle_state in {"in_progress", "closing", "warranty", "done"} and int(summary.get("cost_count") or 0) > 0 and int(summary.get("pay_count") or 0) <= 0,
            "payment_exceeds_cost": float(summary.get("pay_total") or 0.0) > float(summary.get("cost_total") or 0.0) and float(summary.get("pay_total") or 0.0) > 0.0,
            "ready_for_settlement": int(summary.get("cost_count") or 0) > 0 and int(summary.get("pay_count") or 0) > 0,
            "settlement_blocked": lifecycle_state in {"closing", "warranty", "done"} and int(summary.get("pay_count") or 0) <= 0,
            "settlement_completed": lifecycle_state in {"done", "warranty", "closed"} and int(summary.get("settlement_done_count") or 0) > 0,
            "progress_missing": int(summary.get("progress_count") or 0) <= 0 or float(summary.get("progress_percent") or 0.0) <= 0.0,
        }
        risks = []
        if signals.get("is_draft"):
            risks.append(
                self._risk(
                    project=project,
                    risk_code="draft_project",
                    severity="low",
                    reason="project.lifecycle_state == draft, execution pipeline has not started",
                    evidence_types=["progress"],
                )
            )
        if signals.get("no_tasks"):
            risks.append(
                self._risk(
                    project=project,
                    risk_code="no_tasks",
                    severity="high",
                    reason="lifecycle_state is active but progress evidence_count == 0",
                    evidence_types=["progress"],
                )
            )
        if signals.get("no_cost"):
            risks.append(
                self._risk(
                    project=project,
                    risk_code="no_cost",
                    severity="high",
                    reason="lifecycle_state is active but cost evidence_count == 0",
                    evidence_types=["cost"],
                )
            )
        if signals.get("no_payment"):
            risks.append(
                self._risk(
                    project=project,
                    risk_code="no_payment",
                    severity="medium",
                    reason="cost evidence exists but pay_done evidence_count == 0",
                    evidence_types=["cost", "payment"],
                )
            )
        if signals.get("payment_exceeds_cost"):
            risks.append(
                self._risk(
                    project=project,
                    risk_code="payment_exceeds_cost",
                    severity="high",
                    reason="payment_total > cost_total based on evidence summary",
                    evidence_types=["payment", "cost"],
                )
            )
        if signals.get("settlement_blocked"):
            risks.append(
                self._risk(
                    project=project,
                    risk_code="settlement_blocked",
                    severity="medium",
                    reason="project is closing but settlement/payment evidence is incomplete",
                    evidence_types=["settlement", "payment"],
                )
            )
        if signals.get("progress_missing") and not any(item.get("risk_code") == "no_tasks" for item in risks):
            risks.append(
                self._risk(
                    project=project,
                    risk_code="progress_missing",
                    severity="medium",
                    reason="progress_percent <= 0 or progress evidence_count == 0",
                    evidence_types=["progress"],
                )
            )
        if project:
            self.env["sc.evidence.exception.service"].sync_for_project(project, risks)
        risk_codes = [item.get("risk_code") for item in risks if item.get("risk_code")]
        return {
            "lifecycle_state": lifecycle_state,
            "task_count": int(summary.get("progress_count") or 0),
            "cost_count": int(summary.get("cost_count") or 0),
            "payment_count": int(summary.get("pay_count") or 0),
            "settlement_count": int(summary.get("settlement_count") or 0),
            "settlement_done_count": int(summary.get("settlement_done_count") or 0),
            "cost_total": float(summary.get("cost_total") or 0.0),
            "payment_total": float(summary.get("pay_total") or 0.0),
            "progress_percent": float(summary.get("progress_percent") or 0.0),
            "signals": signals,
            "risk_count": len(risk_codes),
            "risk_codes": risk_codes,
            "risks": risks,
            "evidence_summary": summary,
        }
