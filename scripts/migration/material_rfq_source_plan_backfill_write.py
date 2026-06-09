# -*- coding: utf-8 -*-
"""Backfill verifiable material-plan links for legacy material RFQ rows.

Run inside Odoo shell:
    odoo shell -d sc_demo < scripts/migration/material_rfq_source_plan_backfill_write.py
"""

from __future__ import annotations

import json
import sys
import traceback
import zlib
from collections import Counter, defaultdict


SOURCE_SYSTEM = "online_old_scbsly"
SOURCE_FACT_MODEL = "online_old_scbsly:direct_acceptance_fact"
RFQ_LABEL = "报价单"
PLAN_LABEL = "材料计划"
RFQ_FACT_TYPE = "direct_acceptance:报价单"
PLAN_FACT_TYPE = "direct_acceptance:材料计划"
PLAN_LINK_SOURCE_KEY = "GLYWID$CGXBJ_CGXJD_CB"


def _text(value) -> str:
    value = "" if value in (None, False) else str(value)
    value = value.replace("\r\n", "\n").replace("\r", "\n").strip()
    if value.lower() in {"false", "none", "null"}:
        return ""
    return value


def _norm(value) -> str:
    return _text(value).replace(" ", "").lower()


def _payload(record) -> dict:
    raw = _text(record.raw_payload)
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except Exception:
        return {}


def _payload_text(payload: dict, key: str) -> str:
    return _text(payload.get(key))


def _source_key(label: str, fact) -> int:
    token = f"{SOURCE_SYSTEM}:{label}:{fact.legacy_record_id or fact.id}".encode("utf-8")
    return zlib.crc32(token) & 0x7FFFFFFF


def _visible(record, index: int) -> str:
    return _text(getattr(record, "legacy_visible_%02d" % index, ""))


def _build_plan_index(plan_facts, plans_by_key):
    index = defaultdict(dict)
    for fact in plan_facts:
        payload = _payload(fact)
        plan = plans_by_key.get(_source_key(PLAN_LABEL, fact))
        if not plan:
            continue
        material = _norm(_visible(fact, 5) or payload.get("f_CLMC$T_JH_XMZJH"))
        spec = _norm(_visible(fact, 6) or payload.get("f_GGXH$T_JH_XMZJH"))
        for source_id in (_payload_text(payload, "Id"), _payload_text(payload, "ZBID$T_JH_XMZJH")):
            if source_id:
                index[(source_id, material, spec)][plan.id] = plan
    return index


def main():
    Fact = env["sc.legacy.direct.acceptance.fact"].sudo().with_context(active_test=False)  # noqa: F821
    Rfq = env["sc.material.rfq"].sudo().with_context(active_test=False)  # noqa: F821
    Plan = env["project.material.plan"].sudo().with_context(active_test=False)  # noqa: F821

    rfq_facts = Fact.search(
        [("source_system", "=", SOURCE_SYSTEM), ("acceptance_label", "=", RFQ_LABEL), ("active", "=", True)],
        order="document_no,legacy_record_id,id",
    )
    plan_facts = Fact.search(
        [("source_system", "=", SOURCE_SYSTEM), ("acceptance_label", "=", PLAN_LABEL), ("active", "=", True)]
    )
    rfqs_by_key = {
        rfq.legacy_fact_id: rfq
        for rfq in Rfq.search([("legacy_fact_model", "=", SOURCE_FACT_MODEL), ("legacy_fact_type", "=", RFQ_FACT_TYPE)])
    }
    plans_by_key = {
        plan.legacy_fact_id: plan
        for plan in Plan.search([("legacy_fact_model", "=", SOURCE_FACT_MODEL), ("legacy_fact_type", "=", PLAN_FACT_TYPE)])
    }
    plan_index = _build_plan_index(plan_facts, plans_by_key)

    status = Counter()
    updated = []
    skipped_samples = []
    for fact in rfq_facts:
        payload = _payload(fact)
        rfq = rfqs_by_key.get(_source_key(RFQ_LABEL, fact))
        if not rfq:
            status["missing_formal_rfq"] += 1
            continue

        plan_source_id = _payload_text(payload, PLAN_LINK_SOURCE_KEY)
        if not plan_source_id:
            status["no_plan_source"] += 1
            continue

        match_key = (
            plan_source_id,
            _norm(_visible(fact, 5) or payload.get("HWMC$CGXBJ_CGXJD_CB")),
            _norm(_visible(fact, 6) or payload.get("PPXH$CGXBJ_CGXJD_CB")),
        )
        plans = list(plan_index.get(match_key, {}).values())
        if len(plans) != 1:
            status["no_unique_plan_match"] += 1
            if len(skipped_samples) < 20:
                skipped_samples.append(
                    {
                        "fact_id": fact.id,
                        "document_no": _text(fact.document_no),
                        "plan_source_id": plan_source_id,
                        "material": match_key[1],
                        "spec": match_key[2],
                        "matched_plan_count": len(plans),
                    }
                )
            continue

        plan = plans[0]
        vals = {}
        if rfq.source_material_plan_id != plan:
            vals["source_material_plan_id"] = plan.id
        if vals:
            rfq.write(vals)
        plan_line = plan.line_ids[:1]
        if plan_line:
            for line in rfq.line_ids:
                if line.source_material_plan_line_id != plan_line:
                    line.write({"source_material_plan_line_id": plan_line.id})
        status["linked_unique_plan"] += 1
        updated.append({"rfq_id": rfq.id, "rfq_name": _text(rfq.name), "plan_id": plan.id})

    result = {
        "script": "material_rfq_source_plan_backfill_write",
        "status": "PASS",
        "counts": dict(sorted(status.items())),
        "updated_count": len(updated),
        "updated_sample": updated[:20],
        "skipped_sample": skipped_samples,
    }
    env.cr.commit()  # noqa: F821
    print("MATERIAL_RFQ_SOURCE_PLAN_BACKFILL: %s" % json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


try:
    sys.exit(main())
except Exception as err:
    result = {
        "script": "material_rfq_source_plan_backfill_write",
        "status": "FAIL",
        "error": str(err),
        "traceback": traceback.format_exc(),
    }
    print("MATERIAL_RFQ_SOURCE_PLAN_BACKFILL: %s" % json.dumps(result, ensure_ascii=False, sort_keys=True))
    sys.exit(1)
