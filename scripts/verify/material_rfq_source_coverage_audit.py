# -*- coding: utf-8 -*-
"""Audit material RFQ source-field coverage from accepted legacy quote data.

Run inside Odoo shell:
    odoo shell -d sc_demo < scripts/verify/material_rfq_source_coverage_audit.py
"""

from __future__ import annotations

import json
import os
import sys
import traceback
import zlib
from collections import Counter, defaultdict
from pathlib import Path


SOURCE_SYSTEM = "online_old_scbsly"
SOURCE_FACT_MODEL = "online_old_scbsly:direct_acceptance_fact"
RFQ_LABEL = "报价单"
PLAN_LABEL = "材料计划"
RFQ_FACT_TYPE = "direct_acceptance:报价单"
PLAN_FACT_TYPE = "direct_acceptance:材料计划"

DEADLINE_SOURCE_KEYS = ("JHQ", "BJJZRQ", "YQBJSJ", "YQBJQX", "date_deadline")
PURCHASE_REQUEST_SOURCE_KEYS = ("CGDID", "CGDID$CGXBJ_CGXJD_CB", "CGDH$CGXBJ_CGXJD_CB")
PLAN_LINK_SOURCE_KEY = "GLYWID$CGXBJ_CGXJD_CB"


def artifact_root() -> Path:
    root = Path(os.getenv("MIGRATION_ARTIFACT_ROOT", "artifacts/migration"))
    try:
        root.mkdir(parents=True, exist_ok=True)
    except PermissionError:
        root = Path("/tmp/sce-migration-artifacts")
        root.mkdir(parents=True, exist_ok=True)
    return root


OUTPUT_JSON = artifact_root() / "material_rfq_source_coverage_audit_result_v1.json"


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


def _build_plan_index(facts, plans_by_key):
    index = defaultdict(dict)
    for fact in facts:
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


def _expected_matches(rfq_facts, rfqs_by_key, plan_index):
    expected = {}
    status = Counter()
    samples = defaultdict(list)
    source_deadline_count = 0
    source_purchase_request_count = 0

    for fact in rfq_facts:
        payload = _payload(fact)
        rfq = rfqs_by_key.get(_source_key(RFQ_LABEL, fact))
        if not rfq:
            status["missing_formal_rfq"] += 1
            if len(samples["missing_formal_rfq"]) < 20:
                samples["missing_formal_rfq"].append({"fact_id": fact.id, "document_no": _text(fact.document_no)})
            continue

        if any(_payload_text(payload, key) for key in DEADLINE_SOURCE_KEYS):
            source_deadline_count += 1
        if any(_payload_text(payload, key) for key in PURCHASE_REQUEST_SOURCE_KEYS):
            source_purchase_request_count += 1

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
        if len(plans) == 1:
            expected[rfq.id] = plans[0]
            status["unique_plan_match"] += 1
        elif not plans:
            status["plan_source_without_material_spec_match"] += 1
            if len(samples["plan_source_without_material_spec_match"]) < 20:
                samples["plan_source_without_material_spec_match"].append(
                    {
                        "fact_id": fact.id,
                        "document_no": _text(fact.document_no),
                        "plan_source_id": plan_source_id,
                        "material": match_key[1],
                        "spec": match_key[2],
                    }
                )
        else:
            status["ambiguous_plan_match"] += 1
            if len(samples["ambiguous_plan_match"]) < 20:
                samples["ambiguous_plan_match"].append(
                    {
                        "fact_id": fact.id,
                        "document_no": _text(fact.document_no),
                        "plan_source_id": plan_source_id,
                        "plan_ids": [plan.id for plan in plans],
                    }
                )

    return expected, status, samples, source_deadline_count, source_purchase_request_count


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
    rfqs = Rfq.search([("legacy_fact_model", "=", SOURCE_FACT_MODEL), ("legacy_fact_type", "=", RFQ_FACT_TYPE)])
    plans = Plan.search([("legacy_fact_model", "=", SOURCE_FACT_MODEL), ("legacy_fact_type", "=", PLAN_FACT_TYPE)])

    rfqs_by_key = {rfq.legacy_fact_id: rfq for rfq in rfqs}
    plans_by_key = {plan.legacy_fact_id: plan for plan in plans}
    plan_index = _build_plan_index(plan_facts, plans_by_key)
    expected, status, samples, source_deadline_count, source_purchase_request_count = _expected_matches(
        rfq_facts,
        rfqs_by_key,
        plan_index,
    )

    failures = []
    linked_match_count = 0
    line_linked_match_count = 0
    wrong_plan_links = []
    missing_plan_links = []
    missing_plan_line_links = []
    unexpected_plan_links = []

    for rfq in rfqs:
        expected_plan = expected.get(rfq.id)
        if expected_plan:
            if rfq.source_material_plan_id == expected_plan:
                linked_match_count += 1
            else:
                missing_plan_links.append(
                    {
                        "rfq_id": rfq.id,
                        "rfq_name": _text(rfq.name),
                        "expected_plan_id": expected_plan.id,
                        "actual_plan_id": rfq.source_material_plan_id.id or False,
                    }
                )
            plan_line = expected_plan.line_ids[:1]
            rfq_lines = rfq.line_ids
            if plan_line and rfq_lines and all(line.source_material_plan_line_id == plan_line for line in rfq_lines):
                line_linked_match_count += 1
            else:
                missing_plan_line_links.append(
                    {
                        "rfq_id": rfq.id,
                        "rfq_name": _text(rfq.name),
                        "expected_plan_line_id": plan_line.id if plan_line else False,
                        "actual_plan_line_ids": [line.source_material_plan_line_id.id or False for line in rfq_lines],
                    }
                )
        elif rfq.source_material_plan_id:
            unexpected_plan_links.append(
                {"rfq_id": rfq.id, "rfq_name": _text(rfq.name), "actual_plan_id": rfq.source_material_plan_id.id}
            )

    if len(rfq_facts) != len(rfqs):
        failures.append({"check": "source_formal_count", "source_count": len(rfq_facts), "formal_count": len(rfqs)})
    if source_deadline_count:
        failures.append({"check": "unexpected_source_deadline", "source_deadline_count": source_deadline_count})
    if source_purchase_request_count:
        failures.append(
            {"check": "unexpected_source_purchase_request", "source_purchase_request_count": source_purchase_request_count}
        )
    if missing_plan_links:
        failures.append(
            {
                "check": "unique_source_plan_link_projected",
                "missing": len(missing_plan_links),
                "sample": missing_plan_links[:20],
            }
        )
    if wrong_plan_links:
        failures.append({"check": "wrong_source_plan_link", "wrong": len(wrong_plan_links), "sample": wrong_plan_links[:20]})
    if missing_plan_line_links:
        failures.append(
            {
                "check": "unique_source_plan_line_link_projected",
                "missing": len(missing_plan_line_links),
                "sample": missing_plan_line_links[:20],
            }
        )
    if unexpected_plan_links:
        failures.append(
            {
                "check": "unexpected_unverifiable_source_plan_link",
                "unexpected": len(unexpected_plan_links),
                "sample": unexpected_plan_links[:20],
            }
        )

    result = {
        "audit": "material_rfq_source_coverage_audit",
        "status": "PASS" if not failures else "FAIL",
        "source_count": len(rfq_facts),
        "formal_count": len(rfqs),
        "source_deadline_count": source_deadline_count,
        "source_purchase_request_count": source_purchase_request_count,
        "match_status_counts": dict(sorted(status.items())),
        "unique_plan_match_count": len(expected),
        "linked_plan_match_count": linked_match_count,
        "linked_plan_line_match_count": line_linked_match_count,
        "covered_business_fields": ["due_date", "purchase_request_id", "source_material_plan_id"],
        "source_scope_notes": [
            {
                "fields": ["due_date"],
                "decision": "legacy quote source does not carry a distinct quote deadline; do not backfill from rfq_date",
                "source_keys_checked": list(DEADLINE_SOURCE_KEYS),
            },
            {
                "fields": ["purchase_request_id"],
                "decision": "legacy quote source does not carry a stable purchase request reference in accepted data",
                "source_keys_checked": list(PURCHASE_REQUEST_SOURCE_KEYS),
            },
            {
                "fields": ["source_material_plan_id"],
                "decision": "only rows with a unique GLYWID + material + spec match are linked to a formal material plan",
                "source_key": PLAN_LINK_SOURCE_KEY,
            },
        ],
        "samples": {key: value for key, value in sorted(samples.items())},
        "failures": failures,
    }
    OUTPUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    print("MATERIAL_RFQ_SOURCE_COVERAGE_AUDIT: %s" % json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if not failures else 1


try:
    sys.exit(main())
except Exception as err:
    result = {
        "audit": "material_rfq_source_coverage_audit",
        "status": "FAIL",
        "error": str(err),
        "traceback": traceback.format_exc(),
    }
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    print("MATERIAL_RFQ_SOURCE_COVERAGE_AUDIT: %s" % json.dumps(result, ensure_ascii=False, sort_keys=True))
    sys.exit(1)
