"""Project skeleton rollback dry-run.

Run through Odoo shell only:

    ENV=dev DB_NAME=sc_demo make odoo.shell.exec
    exec(open('/mnt/scripts/migration/project_rollback_dry_run.py').read())

The script is intentionally read-only. It does not call create/write/unlink and
does not commit transactions. Rollback targets are selected only by
legacy_project_id from the 30-row sample.
"""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path


INPUT_CSV = Path("/mnt/artifacts/migration/project_sample_v1.csv")
OUTPUT_JSON = Path("/mnt/artifacts/migration/project_rollback_dry_run_result_v1.json")
EXPECTED_COUNT = 30


def read_target_ids(path):
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if "legacy_project_id" not in (reader.fieldnames or []):
            raise RuntimeError("legacy_project_id column is required")
        return [(row.get("legacy_project_id") or "").strip() for row in reader]


def stage_label(stage):
    if not stage:
        return ""
    parts = []
    if getattr(stage, "name", None):
        parts.append(stage.name)
    if getattr(stage, "fold", False):
        parts.append("folded")
    return " / ".join(parts)


def main():
    target_ids = read_target_ids(INPUT_CSV)
    non_empty_ids = [identity for identity in target_ids if identity]
    target_counts = Counter(non_empty_ids)
    duplicate_targets = sorted(identity for identity, count in target_counts.items() if count > 1)

    model = env["project.project"].sudo()  # noqa: F821 - provided by Odoo shell
    records = model.search([("legacy_project_id", "in", non_empty_ids)], order="legacy_project_id,id")

    grouped = {}
    for rec in records:
        grouped.setdefault(rec.legacy_project_id or "", []).append(rec)

    missing_ids = [identity for identity in non_empty_ids if identity not in grouped]
    duplicate_matches = [
        {"legacy_project_id": identity, "count": len(items), "ids": [item.id for item in items]}
        for identity, items in sorted(grouped.items())
        if len(items) > 1
    ]
    out_of_scope_matches = [
        {
            "id": rec.id,
            "legacy_project_id": rec.legacy_project_id or "",
            "name": rec.name or "",
        }
        for rec in records
        if (rec.legacy_project_id or "") not in target_counts
    ]

    rows = []
    stage_counter = Counter()
    for identity in non_empty_ids:
        recs = grouped.get(identity, [])
        if not recs:
            rows.append(
                {
                    "legacy_project_id": identity,
                    "matched": False,
                    "project_id": None,
                    "name": "",
                    "stage_id": None,
                    "stage_name": "",
                    "out_of_scope": False,
                    "match_count": 0,
                }
            )
            continue
        for rec in recs:
            stage = rec.stage_id
            stage_key = str(stage.id) if stage else ""
            stage_counter[stage_key] += 1
            rows.append(
                {
                    "legacy_project_id": identity,
                    "matched": True,
                    "project_id": rec.id,
                    "name": rec.name or "",
                    "stage_id": stage.id if stage else None,
                    "stage_name": stage_label(stage),
                    "out_of_scope": (rec.legacy_project_id or "") not in target_counts,
                    "match_count": len(recs),
                }
            )

    stage_ids = sorted({row["stage_id"] for row in rows if row["stage_id"] is not None})
    stage_summary = []
    for stage_id in stage_ids:
        stage_rows = [row for row in rows if row["stage_id"] == stage_id]
        stage_summary.append(
            {
                "stage_id": stage_id,
                "stage_name": stage_rows[0]["stage_name"],
                "count": len(stage_rows),
            }
        )

    blocking_reasons = []
    if len(non_empty_ids) != EXPECTED_COUNT:
        blocking_reasons.append(f"expected {EXPECTED_COUNT} target ids, got {len(non_empty_ids)}")
    if duplicate_targets:
        blocking_reasons.append("duplicate target legacy_project_id in input")
    if missing_ids:
        blocking_reasons.append("missing matched project records")
    if duplicate_matches:
        blocking_reasons.append("duplicate project matches")
    if out_of_scope_matches:
        blocking_reasons.append("out-of-scope matches")

    payload = {
        "status": "ROLLBACK_READY" if not blocking_reasons else "ROLLBACK_BLOCKED",
        "mode": "rollback_dry_run_no_delete",
        "db": env.cr.dbname,  # noqa: F821 - provided by Odoo shell
        "input": str(INPUT_CSV),
        "rollback_key": "legacy_project_id",
        "total_targets": len(non_empty_ids),
        "matched_rows": sum(1 for row in rows if row["matched"]),
        "missing_rows": len(missing_ids),
        "duplicate_matches": duplicate_matches,
        "out_of_scope_matches": out_of_scope_matches,
        "stage_id_summary": stage_summary,
        "stage_id_all_same": len(stage_summary) == 1,
        "target_input_duplicates": duplicate_targets,
        "missing_legacy_project_ids": missing_ids,
        "blocking_reasons": blocking_reasons,
        "rows": rows,
    }

    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "status": payload["status"],
                "total_targets": payload["total_targets"],
                "matched_rows": payload["matched_rows"],
                "missing_rows": payload["missing_rows"],
                "duplicate_matches": len(payload["duplicate_matches"]),
                "out_of_scope_matches": len(payload["out_of_scope_matches"]),
                "stage_id_summary": payload["stage_id_summary"],
            },
            ensure_ascii=False,
        )
    )


main()
