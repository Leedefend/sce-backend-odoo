# -*- coding: utf-8 -*-
from __future__ import annotations

import json

from odoo import api, models


class EvidenceExceptionService(models.AbstractModel):
    _name = "sc.evidence.exception.service"
    _description = "Evidence Exception Service"

    EXCEPTION_SEVERITIES = {"high", "critical"}

    @staticmethod
    def _safe_int(value):
        try:
            return int(value or 0)
        except Exception:
            return 0

    @staticmethod
    def _normalize_refs(refs):
        normalized = []
        for item in refs or []:
            if not isinstance(item, dict):
                continue
            normalized.append(
                {
                    "business_model": str(item.get("business_model") or ""),
                    "business_id": int(item.get("business_id") or 0),
                    "evidence_type": str(item.get("evidence_type") or ""),
                }
            )
        return normalized

    @api.model
    def sync_for_project(self, project, risks):
        if not project:
            return self.env["sc.evidence.exception"]
        Exception = self.env["sc.evidence.exception"].sudo()
        RiskAction = self.env["project.risk.action"].sudo()
        synced = Exception.browse()
        for risk in risks or []:
            severity = str((risk or {}).get("severity") or "").strip().lower()
            if severity not in self.EXCEPTION_SEVERITIES:
                continue
            risk_code = str((risk or {}).get("risk_code") or "").strip()
            if not risk_code:
                continue
            existing = Exception.search(
                [
                    ("project_id", "=", int(project.id)),
                    ("risk_code", "=", risk_code),
                    ("status", "in", ["open", "processing"]),
                ],
                limit=1,
            )
            risk_action = existing.risk_action_id if existing else RiskAction.browse()
            if not risk_action:
                risk_action = RiskAction.create(
                    {
                        "name": str((risk or {}).get("reason") or risk_code),
                        "project_id": int(project.id),
                        "state": "open",
                        "risk_level": "critical" if severity == "critical" else "high",
                        "note": str((risk or {}).get("reason") or ""),
                    }
                )
            payload = {
                "name": str((risk or {}).get("reason") or risk_code),
                "project_id": int(project.id),
                "risk_code": risk_code,
                "severity": severity,
                "evidence_refs": json.dumps(self._normalize_refs((risk or {}).get("evidence_refs") or []), ensure_ascii=False),
                "risk_action_id": int(risk_action.id or 0),
            }
            if existing:
                existing.write(payload)
                synced |= existing
            else:
                synced |= Exception.create(payload)
        return synced
