# -*- coding: utf-8 -*-
from __future__ import annotations

import json

from odoo import api, models


class EvidenceTimelineService(models.AbstractModel):
    _name = "sc.evidence.timeline.service"
    _description = "Smart Construction Evidence Timeline Service"

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
    def build_timeline(self, business_model, business_id, *, limit=100):
        business_model = str(business_model or "").strip()
        business_id = self._safe_int(business_id)
        empty = {
            "business_model": business_model,
            "business_id": business_id,
            "count": 0,
            "items": [],
        }
        if not business_model or business_id <= 0:
            return empty

        Evidence = self.env["sc.business.evidence"].sudo()
        evidences = Evidence.search(
            [
                ("business_model", "=", business_model),
                ("business_id", "=", business_id),
            ],
            order="operate_time asc,id asc",
            limit=max(self._safe_int(limit), 0) or 100,
        )
        items = []
        for evidence in evidences:
            relation_chain = self._parse_relation_chain(getattr(evidence, "relation_chain", ""))
            risk_code = str(relation_chain.get("risk_code") or "").strip()
            source_model = str(getattr(evidence, "source_model", "") or "")
            source_id = self._safe_int(getattr(evidence, "source_id", 0))
            evidence_type = str(getattr(evidence, "evidence_type", "") or "")
            items.append(
                {
                    "time": str(getattr(evidence, "operate_time", "") or ""),
                    "type": evidence_type,
                    "title": str(getattr(evidence, "name", "") or "")
                    or "%s#%s" % (source_model or "evidence", source_id),
                    "amount": self._safe_float(getattr(evidence, "amount", 0.0)),
                    "source_ref": "%s#%s" % (source_model or "unknown", source_id),
                    "operator": {
                        "id": self._safe_int(getattr(getattr(evidence, "operator_id", None), "id", 0)),
                        "name": str(getattr(getattr(evidence, "operator_id", None), "display_name", "") or ""),
                    },
                    "checksum": str(getattr(evidence, "checksum", "") or ""),
                    "risk_codes": [risk_code] if risk_code else [],
                    "evidence_ref": "sc.business.evidence#%s" % self._safe_int(getattr(evidence, "id", 0)),
                    "trace_action": {
                        "intent": "business.evidence.trace",
                        "payload": {
                            "business_model": business_model,
                            "business_id": business_id,
                            "evidence_type": evidence_type,
                        },
                    },
                }
            )
        return {
            "business_model": business_model,
            "business_id": business_id,
            "count": len(items),
            "items": items,
        }
