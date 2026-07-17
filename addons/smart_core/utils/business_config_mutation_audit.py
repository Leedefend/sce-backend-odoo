# -*- coding: utf-8 -*-
from __future__ import annotations

import hashlib
import json


def record_business_config_mutation(records, operation: str, values=None) -> None:
    if records.env.context.get("skip_business_config_mutation_audit"):
        return
    raw = json.dumps(values or {}, ensure_ascii=False, sort_keys=True, default=str, separators=(",", ":"))
    value_hash = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    trace_id = str(records.env.context.get("business_config_audit_trace") or "").strip() or False
    rows = [{
        "operation": operation, "target_model": records._name, "target_res_id": int(record.id or 0),
        "trace_id": trace_id, "value_hash": value_hash, "user_id": records.env.user.id,
        "company_id": records.env.company.id,
    } for record in records]
    if rows:
        records.env["ui.business.config.mutation.audit"].sudo().with_context(
            skip_business_config_mutation_audit=True,
        ).create(rows)
