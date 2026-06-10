# -*- coding: utf-8 -*-
"""Audit source-proven construction diary visible field coverage.

Run inside Odoo shell:
    odoo shell -d sc_demo < scripts/verify/construction_diary_visible_fields_audit.py
"""

from __future__ import annotations

import json
import os
import sys
import traceback
from pathlib import Path


SOURCE_MODEL = "online_old_scbsly:direct_acceptance"
SOURCE_TABLE = "direct_acceptance:施工日志（新）"


def artifact_root() -> Path:
    root = Path(os.getenv("MIGRATION_ARTIFACT_ROOT", "artifacts/migration"))
    try:
        root.mkdir(parents=True, exist_ok=True)
    except PermissionError:
        root = Path("/tmp/sce-migration-artifacts")
        root.mkdir(parents=True, exist_ok=True)
    return root


OUTPUT_JSON = artifact_root() / "construction_diary_visible_fields_audit_result_v1.json"


def _text(value) -> str:
    value = "" if value in (None, False) else str(value)
    value = value.replace("\r\n", "\n").replace("\r", "\n").strip()
    if value.lower() in {"false", "none", "null"}:
        return ""
    return value


def main():
    Diary = env["sc.construction.diary"].sudo().with_context(active_test=False)  # noqa: F821
    if "attendance_equipment" not in Diary._fields:
        raise RuntimeError("missing sc.construction.diary.attendance_equipment; upgrade smart_construction_core first")

    records = Diary.search([("legacy_source_model", "=", SOURCE_MODEL), ("legacy_source_table", "=", SOURCE_TABLE)])
    failures = []
    source_equipment_count = 0
    source_equipment_empty_count = 0
    source_note_count = 0
    source_note_empty_count = 0
    equipment_projected_count = 0
    note_projected_count = 0
    equipment_missing = []
    note_missing = []

    for record in records:
        source_equipment = _text(record.legacy_visible_07)
        source_note = _text(record.legacy_visible_08)
        if source_equipment:
            source_equipment_count += 1
            if _text(record.attendance_equipment) == source_equipment:
                equipment_projected_count += 1
            elif len(equipment_missing) < 20:
                equipment_missing.append(
                    {
                        "id": record.id,
                        "name": _text(record.name),
                        "source": source_equipment,
                        "attendance_equipment": _text(record.attendance_equipment),
                    }
                )
        else:
            source_equipment_empty_count += 1

        if source_note:
            source_note_count += 1
            if _text(record.note) == source_note:
                note_projected_count += 1
            elif len(note_missing) < 20:
                note_missing.append(
                    {"id": record.id, "name": _text(record.name), "source": source_note, "note": _text(record.note)}
                )
        else:
            source_note_empty_count += 1

    source_equipment_missing_count = source_equipment_count - equipment_projected_count
    source_note_missing_count = source_note_count - note_projected_count
    if source_equipment_missing_count:
        failures.append(
            {
                "check": "legacy_visible_07_attendance_equipment_projected",
                "missing": source_equipment_missing_count,
                "sample": equipment_missing,
            }
        )
    if source_note_missing_count:
        failures.append(
            {
                "check": "legacy_visible_08_note_projected",
                "missing": source_note_missing_count,
                "sample": note_missing,
            }
        )

    result = {
        "audit": "construction_diary_visible_fields_audit",
        "status": "PASS" if not failures else "FAIL",
        "source_count": len(records),
        "source_equipment_count": source_equipment_count,
        "source_equipment_empty_count": source_equipment_empty_count,
        "source_equipment_projected_count": equipment_projected_count,
        "source_equipment_missing_count": source_equipment_missing_count,
        "source_note_count": source_note_count,
        "source_note_empty_count": source_note_empty_count,
        "source_note_projected_count": note_projected_count,
        "source_note_missing_count": source_note_missing_count,
        "covered_business_fields": ["legacy_visible_07", "legacy_visible_08", "attendance_equipment", "note"],
        "source_scope_notes": [
            {
                "field": "legacy_visible_07",
                "label": "出勤机械",
                "decision": "source non-empty values must project to attendance_equipment; source empty values remain empty",
            },
            {
                "field": "legacy_visible_08",
                "label": "备注",
                "decision": "source non-empty values must project to note; source empty values remain empty",
            },
        ],
        "failures": failures,
    }
    OUTPUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    print("CONSTRUCTION_DIARY_VISIBLE_FIELDS_AUDIT: %s" % json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if not failures else 1


try:
    sys.exit(main())
except Exception as err:
    result = {
        "audit": "construction_diary_visible_fields_audit",
        "status": "FAIL",
        "error": str(err),
        "traceback": traceback.format_exc(),
    }
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    print("CONSTRUCTION_DIARY_VISIBLE_FIELDS_AUDIT: %s" % json.dumps(result, ensure_ascii=False, sort_keys=True))
    sys.exit(1)
