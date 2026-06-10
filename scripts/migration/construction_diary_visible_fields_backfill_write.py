# -*- coding: utf-8 -*-
"""Backfill source-proven construction diary visible fields.

Run inside Odoo shell:
    odoo shell -d sc_demo < scripts/migration/construction_diary_visible_fields_backfill_write.py
"""

from __future__ import annotations

import json
import sys
import traceback
from collections import Counter


SOURCE_MODEL = "online_old_scbsly:direct_acceptance"
SOURCE_TABLE = "direct_acceptance:施工日志（新）"


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
    counts = Counter()
    samples = []
    for record in records:
        vals = {}
        source_equipment = _text(record.legacy_visible_07)
        source_note = _text(record.legacy_visible_08)
        if source_equipment:
            vals["attendance_equipment"] = source_equipment
        if source_note:
            vals["note"] = source_note
        if vals:
            record.write(vals)
            counts["updated"] += 1
            if source_equipment:
                counts["equipment_updated"] += 1
            if source_note:
                counts["note_updated"] += 1
            if len(samples) < 20:
                samples.append({"id": record.id, "name": _text(record.name), "fields": sorted(vals)})
        else:
            counts["source_empty"] += 1

    result = {
        "script": "construction_diary_visible_fields_backfill_write",
        "status": "PASS",
        "records": len(records),
        "counts": dict(sorted(counts.items())),
        "sample": samples,
    }
    env.cr.commit()  # noqa: F821
    print("CONSTRUCTION_DIARY_VISIBLE_FIELDS_BACKFILL: %s" % json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


try:
    sys.exit(main())
except Exception as err:
    result = {
        "script": "construction_diary_visible_fields_backfill_write",
        "status": "FAIL",
        "error": str(err),
        "traceback": traceback.format_exc(),
    }
    print("CONSTRUCTION_DIARY_VISIBLE_FIELDS_BACKFILL: %s" % json.dumps(result, ensure_ascii=False, sort_keys=True))
    sys.exit(1)
