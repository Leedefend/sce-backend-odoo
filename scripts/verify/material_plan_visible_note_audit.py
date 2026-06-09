# -*- coding: utf-8 -*-
"""Audit material plan visible note coverage from direct-acceptance source.

Run inside Odoo shell:
    odoo shell -d sc_demo < scripts/verify/material_plan_visible_note_audit.py
"""

from __future__ import annotations

import json
import os
import sys
import traceback
import zlib
from pathlib import Path


SOURCE_SYSTEM = "online_old_scbsly"
SOURCE_FACT_MODEL = "online_old_scbsly:direct_acceptance_fact"
ACCEPTANCE_LABEL = "材料计划"
LEGACY_FACT_TYPE = "direct_acceptance:材料计划"


def artifact_root() -> Path:
    root = Path(os.getenv("MIGRATION_ARTIFACT_ROOT", "artifacts/migration"))
    try:
        root.mkdir(parents=True, exist_ok=True)
    except PermissionError:
        root = Path("/tmp/sce-migration-artifacts")
        root.mkdir(parents=True, exist_ok=True)
    return root


OUTPUT_JSON = artifact_root() / "material_plan_visible_note_audit_result_v1.json"


def _text(value) -> str:
    value = "" if value in (None, False) else str(value)
    value = value.replace("\r\n", "\n").replace("\r", "\n").strip()
    if value.lower() in {"false", "none", "null"}:
        return ""
    return value


def _source_key(fact) -> int:
    token = f"{SOURCE_SYSTEM}:{ACCEPTANCE_LABEL}:{fact.legacy_record_id or fact.id}".encode("utf-8")
    return zlib.crc32(token) & 0x7FFFFFFF


def _line_notes(plan) -> list[str]:
    notes = []
    for line in plan.line_ids:
        note = _text(line.note)
        if note and note not in notes:
            notes.append(note)
    return notes


def main():
    Fact = env["sc.legacy.direct.acceptance.fact"].sudo().with_context(active_test=False)  # noqa: F821
    Plan = env["project.material.plan"].sudo().with_context(active_test=False)  # noqa: F821

    facts = Fact.search(
        [
            ("source_system", "=", SOURCE_SYSTEM),
            ("acceptance_label", "=", ACCEPTANCE_LABEL),
            ("active", "=", True),
        ],
        order="document_no,legacy_record_id,id",
    )
    plans = Plan.search(
        [
            ("legacy_fact_model", "=", SOURCE_FACT_MODEL),
            ("legacy_fact_type", "=", LEGACY_FACT_TYPE),
        ],
        order="id",
    )
    plans_by_key = {plan.legacy_fact_id: plan for plan in plans}

    failures = []
    missing_plan = []
    duplicate_plan_keys = {}
    source_note_count = 0
    source_note_empty_count = 0
    source_note_projected_count = 0
    source_note_missing_count = 0
    source_note_line_missing_count = 0
    source_note_summary_missing_count = 0
    source_note_missing_sample = []
    source_note_line_missing_sample = []
    source_note_summary_missing_sample = []

    seen_keys = {}
    for plan in plans:
        seen_keys.setdefault(plan.legacy_fact_id, []).append(plan.id)
    duplicate_plan_keys = {
        str(key): ids
        for key, ids in seen_keys.items()
        if key and len(ids) > 1
    }

    for fact in facts:
        key = _source_key(fact)
        plan = plans_by_key.get(key)
        if not plan:
            missing_plan.append({"fact_id": fact.id, "legacy_record_id": _text(fact.legacy_record_id), "source_key": key})
            continue
        source_note = _text(fact.legacy_visible_10)
        plan_note = _text(plan.legacy_visible_10)
        line_notes = _line_notes(plan)
        summary_note = _text(plan.line_note_summary)
        if source_note:
            source_note_count += 1
            if plan_note == source_note:
                source_note_projected_count += 1
            else:
                source_note_missing_count += 1
                if len(source_note_missing_sample) < 20:
                    source_note_missing_sample.append(
                        {
                            "plan_id": plan.id,
                            "fact_id": fact.id,
                            "source_note": source_note,
                            "plan_legacy_visible_10": plan_note,
                        }
                    )
            if source_note not in line_notes:
                source_note_line_missing_count += 1
                if len(source_note_line_missing_sample) < 20:
                    source_note_line_missing_sample.append(
                        {
                            "plan_id": plan.id,
                            "fact_id": fact.id,
                            "source_note": source_note,
                            "line_notes": line_notes,
                        }
                    )
            if source_note not in summary_note:
                source_note_summary_missing_count += 1
                if len(source_note_summary_missing_sample) < 20:
                    source_note_summary_missing_sample.append(
                        {
                            "plan_id": plan.id,
                            "fact_id": fact.id,
                            "source_note": source_note,
                            "line_note_summary": summary_note,
                        }
                    )
        else:
            source_note_empty_count += 1

    extra_plans = [
        {"plan_id": plan.id, "legacy_fact_id": plan.legacy_fact_id}
        for plan in plans
        if plan.legacy_fact_id not in {_source_key(fact) for fact in facts}
    ]

    if len(facts) != len(plans):
        failures.append({"check": "source_formal_count", "source_count": len(facts), "formal_count": len(plans)})
    if missing_plan:
        failures.append({"check": "missing_formal_plan", "missing": len(missing_plan), "sample": missing_plan[:20]})
    if extra_plans:
        failures.append({"check": "extra_formal_plan", "extra": len(extra_plans), "sample": extra_plans[:20]})
    if duplicate_plan_keys:
        failures.append({"check": "duplicate_formal_plan_key", "duplicates": duplicate_plan_keys})
    if source_note_missing_count:
        failures.append(
            {
                "check": "legacy_visible_10_matches_source_note",
                "missing": source_note_missing_count,
                "sample": source_note_missing_sample,
            }
        )
    if source_note_line_missing_count:
        failures.append(
            {
                "check": "line_note_matches_source_note",
                "missing": source_note_line_missing_count,
                "sample": source_note_line_missing_sample,
            }
        )
    if source_note_summary_missing_count:
        failures.append(
            {
                "check": "line_note_summary_matches_source_note",
                "missing": source_note_summary_missing_count,
                "sample": source_note_summary_missing_sample,
            }
        )

    result = {
        "audit": "material_plan_visible_note_audit",
        "status": "PASS" if not failures else "FAIL",
        "source_count": len(facts),
        "formal_count": len(plans),
        "source_note_count": source_note_count,
        "source_note_empty_count": source_note_empty_count,
        "source_note_projected_count": source_note_projected_count,
        "source_note_missing_count": source_note_missing_count,
        "source_note_line_missing_count": source_note_line_missing_count,
        "source_note_summary_missing_count": source_note_summary_missing_count,
        "covered_business_fields": ["legacy_visible_10", "line_ids.note", "line_note_summary"],
        "source_scope_notes": [
            {
                "field": "legacy_visible_10",
                "label": "备注",
                "decision": "source empty values remain empty; source non-empty notes must project to formal visible and line note fields",
            }
        ],
        "failures": failures,
    }
    OUTPUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    print("MATERIAL_PLAN_VISIBLE_NOTE_AUDIT: %s" % json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if not failures else 1


try:
    sys.exit(main())
except Exception as err:
    result = {
        "audit": "material_plan_visible_note_audit",
        "status": "FAIL",
        "error": str(err),
        "traceback": traceback.format_exc(),
    }
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    print("MATERIAL_PLAN_VISIBLE_NOTE_AUDIT: %s" % json.dumps(result, ensure_ascii=False, sort_keys=True))
    sys.exit(1)
