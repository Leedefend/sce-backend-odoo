# -*- coding: utf-8 -*-
from __future__ import annotations

import json


class EvidenceChainService:
    """Build traceable evidence chains for project-level business facts."""

    ORDER = ("payment", "cost", "settlement", "progress")

    def __init__(self, env):
        self.env = env

    def _model(self, model_name):
        try:
            return self.env[model_name]
        except Exception:
            return None

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
    def _parse_relation_chain(raw):
        text = str(raw or "").strip()
        if not text:
            return {}
        try:
            value = json.loads(text)
        except Exception:
            return {"raw": text}
        return value if isinstance(value, dict) else {"value": value}

    def _evidence_payload(self, evidence):
        operator = getattr(evidence, "operator_id", None)
        return {
            "evidence_id": self._safe_int(getattr(evidence, "id", 0)),
            "name": str(getattr(evidence, "name", "") or ""),
            "business_model": str(getattr(evidence, "business_model", "") or ""),
            "business_id": self._safe_int(getattr(evidence, "business_id", 0)),
            "evidence_type": str(getattr(evidence, "evidence_type", "") or ""),
            "amount": self._safe_float(getattr(evidence, "amount", 0.0)),
            "quantity": self._safe_float(getattr(evidence, "quantity", 0.0)),
            "source_model": str(getattr(evidence, "source_model", "") or ""),
            "source_id": self._safe_int(getattr(evidence, "source_id", 0)),
            "operator_id": self._safe_int(getattr(operator, "id", 0)),
            "operator_name": str(getattr(operator, "display_name", "") or ""),
            "operate_time": str(getattr(evidence, "operate_time", "") or ""),
            "relation_chain": self._parse_relation_chain(getattr(evidence, "relation_chain", "")),
            "ref": "%s#%s" % (
                str(getattr(evidence, "source_model", "") or "unknown"),
                self._safe_int(getattr(evidence, "source_id", 0)),
            ),
        }

    def build_chain(self, business_model, business_id, *, limit=100):
        Evidence = self._model("sc.business.evidence")
        if Evidence is None:
            return {
                "business_model": str(business_model or ""),
                "business_id": self._safe_int(business_id),
                "groups": {key: [] for key in self.ORDER},
                "summary": {
                    "evidence_count": 0,
                    "payment_total": 0.0,
                    "cost_total": 0.0,
                    "settlement_total": 0.0,
                    "progress_quantity": 0.0,
                },
                "evidence_refs": [],
            }

        domain = [
            ("business_model", "=", str(business_model or "")),
            ("business_id", "=", self._safe_int(business_id)),
        ]
        evidences = Evidence.sudo().search(domain, order="operate_time desc,id desc", limit=max(self._safe_int(limit), 0) or 100)
        groups = {key: [] for key in self.ORDER}
        refs = []
        for evidence in evidences:
            payload = self._evidence_payload(evidence)
            evidence_type = payload.get("evidence_type") or "progress"
            groups.setdefault(evidence_type, []).append(payload)
            refs.append(payload["ref"])

        summary = {
            "evidence_count": sum(len(groups.get(key) or []) for key in groups.keys()),
            "payment_total": round(sum(item.get("amount") or 0.0 for item in groups.get("payment", [])), 2),
            "cost_total": round(sum(item.get("amount") or 0.0 for item in groups.get("cost", [])), 2),
            "settlement_total": round(sum(item.get("amount") or 0.0 for item in groups.get("settlement", [])), 2),
            "progress_quantity": round(sum(item.get("quantity") or 0.0 for item in groups.get("progress", [])), 2),
            "payment_count": len(groups.get("payment", [])),
            "cost_count": len(groups.get("cost", [])),
            "settlement_count": len(groups.get("settlement", [])),
            "progress_count": len(groups.get("progress", [])),
        }
        ordered_groups = {key: groups.get(key, []) for key in self.ORDER}
        for key in groups.keys():
            if key not in ordered_groups:
                ordered_groups[key] = groups.get(key, [])
        return {
            "business_model": str(business_model or ""),
            "business_id": self._safe_int(business_id),
            "groups": ordered_groups,
            "summary": summary,
            "evidence_refs": refs[:10],
        }

    def build_project_chain(self, project_id, *, limit=100):
        return self.build_chain("project.project", project_id, limit=limit)
