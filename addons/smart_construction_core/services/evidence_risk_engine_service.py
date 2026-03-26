# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo import api, models


class EvidenceRiskEngineService(models.AbstractModel):
    _name = "sc.evidence.risk.engine"
    _description = "Smart Construction Evidence Risk Engine"

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
            "evidence_summary": summary,
        }
