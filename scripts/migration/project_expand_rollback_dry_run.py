"""100-row project expansion rollback dry-run for Odoo shell.

Read-only: no create/write/unlink/delete and no commit.
"""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path


INPUT_CSV = Path("/mnt/artifacts/migration/project_create_only_expand_post_write_snapshot_v1.csv")
OUTPUT_JSON = Path("/mnt/artifacts/migration/project_expand_rollback_dry_run_result_v1.json")
EXPECTED_COUNT = 100


def read_target_ids(path):
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if "legacy_project_id" not in (reader.fieldnames or []):
            raise RuntimeError("legacy_project_id column is required")
        return [(row.get("legacy_project_id") or "").strip() for row in reader]


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
    lifecycle_counter = Counter()
    projection_mismatches = []
    for identity in non_empty_ids:
        recs = grouped.get(identity, [])
        if not recs:
            rows.append(
                {
                    "legacy_project_id": identity,
                    "matched": False,
                    "project_id": None,
                    "name": "",
                    "lifecycle_state": "",
                    "stage_id": None,
                    "stage_name": "",
                    "match_count": 0,
                }
            )
            continue
        for rec in recs:
            stage = rec.stage_id
            stage_counter[(stage.id if stage else None, stage.display_name if stage else "")] += 1
            lifecycle_counter[rec.lifecycle_state or ""] += 1
            expected_stage = rec._get_stage_for_lifecycle(rec.lifecycle_state)
            if expected_stage and rec.stage_id != expected_stage:
                projection_mismatches.append(
                    {
                        "id": rec.id,
                        "legacy_project_id": rec.legacy_project_id or "",
                        "lifecycle_state": rec.lifecycle_state or "",
                        "stage_id": rec.stage_id.id or False,
                        "expected_stage_id": expected_stage.id,
                    }
                )
            rows.append(
                {
                    "legacy_project_id": identity,
                    "matched": True,
                    "project_id": rec.id,
                    "name": rec.name or "",
                    "lifecycle_state": rec.lifecycle_state or "",
                    "stage_id": stage.id if stage else None,
                    "stage_name": stage.display_name if stage else "",
                    "match_count": len(recs),
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
    if projection_mismatches:
        blocking_reasons.append("stage projection mismatches")

    payload = {
        "status": "ROLLBACK_READY" if not blocking_reasons else "ROLLBACK_BLOCKED",
        "mode": "rollback_dry_run_no_delete",
        "db": env.cr.dbname,  # noqa: F821
        "input": str(INPUT_CSV),
        "rollback_key": "legacy_project_id",
        "total_targets": len(non_empty_ids),
        "matched_rows": sum(1 for row in rows if row["matched"]),
        "missing_rows": len(missing_ids),
        "duplicate_matches": duplicate_matches,
        "out_of_scope_matches": out_of_scope_matches,
        "projection_mismatches": projection_mismatches,
        "stage_id_summary": [
            {"stage_id": stage_id, "stage_name": stage_name, "count": count}
            for (stage_id, stage_name), count in sorted(stage_counter.items(), key=lambda item: (item[0][0] or 0, item[0][1]))
        ],
        "lifecycle_state_summary": [
            {"lifecycle_state": state, "count": count}
            for state, count in sorted(lifecycle_counter.items())
        ],
        "target_input_duplicates": duplicate_targets,
        "missing_legacy_project_ids": missing_ids,
        "blocking_reasons": blocking_reasons,
        "rows": rows,
    }

    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        "ITER_1836_ROLLBACK_DRY_RUN="
        + json.dumps(
            {
                "status": payload["status"],
                "total_targets": payload["total_targets"],
                "matched_rows": payload["matched_rows"],
                "missing_rows": payload["missing_rows"],
                "duplicate_matches": len(payload["duplicate_matches"]),
                "out_of_scope_matches": len(payload["out_of_scope_matches"]),
                "projection_mismatches": len(payload["projection_mismatches"]),
                "stage_id_summary": payload["stage_id_summary"],
                "lifecycle_state_summary": payload["lifecycle_state_summary"],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )


main()
