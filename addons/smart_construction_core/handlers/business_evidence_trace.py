# -*- coding: utf-8 -*-
from __future__ import annotations

import time

from odoo.addons.smart_core.core.base_handler import BaseIntentHandler
from odoo.addons.smart_construction_core.services.evidence_chain_service import EvidenceChainService


class BusinessEvidenceTraceHandler(BaseIntentHandler):
    INTENT_TYPE = "business.evidence.trace"
    DESCRIPTION = "返回业务对象的证据链与汇总"
    VERSION = "1.0.0"
    ETAG_ENABLED = False
    REQUIRED_GROUPS = ["base.group_user"]

    def handle(self, payload=None, ctx=None):
        ts0 = time.time()
        params = payload or self.params or {}
        if isinstance(params, dict) and isinstance(params.get("params"), dict):
            params = params.get("params") or {}

        business_model = str((params or {}).get("business_model") or "").strip()
        try:
            business_id = int((params or {}).get("business_id") or 0)
        except Exception:
            business_id = 0
        if not business_model or business_id <= 0:
            return {
                "ok": False,
                "error": {
                    "code": "INVALID_EVIDENCE_TRACE_INPUT",
                    "message": "business_model 和 business_id 必须有效",
                },
                "meta": {
                    "intent": self.INTENT_TYPE,
                    "elapsed_ms": int((time.time() - ts0) * 1000),
                    "trace_id": str((self.context or {}).get("trace_id") or ""),
                },
            }

        evidence_chain = EvidenceChainService(self.env).build_chain(business_model, business_id)
        timeline = self.env["sc.evidence.timeline.service"].build_timeline(business_model, business_id)
        evidence_type = str((params or {}).get("evidence_type") or "").strip()
        return {
            "ok": True,
            "data": {
                "business_model": business_model,
                "business_id": business_id,
                "requested_evidence_type": evidence_type,
                "trace_entry": {
                    "intent": self.INTENT_TYPE,
                    "payload": {
                        "business_model": business_model,
                        "business_id": business_id,
                        "evidence_type": evidence_type,
                    },
                },
                "evidence_chain": evidence_chain.get("groups") or {},
                "summary": evidence_chain.get("summary") or {},
                "evidence_refs": evidence_chain.get("evidence_refs") or [],
                "timeline": timeline,
            },
            "meta": {
                "intent": self.INTENT_TYPE,
                "elapsed_ms": int((time.time() - ts0) * 1000),
                "trace_id": str((self.context or {}).get("trace_id") or ""),
            },
        }
