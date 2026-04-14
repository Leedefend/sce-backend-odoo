"""Readonly post-write review for the project v4 200-row write batch."""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path


POST_WRITE_SNAPSHOT_CSV = Path("/mnt/artifacts/migration/project_v4_200_post_write_snapshot.csv")
WRITE_RESULT_JSON = Path("/mnt/artifacts/migration/project_v4_200_write_result.json")
OUTPUT_JSON = Path("/mnt/artifacts/migration/project_v4_200_post_write_review_result.json")
ROLLBACK_TARGET_CSV = Path("/mnt/artifacts/migration/project_v4_200_rollback_target_list.csv")
EXPECTED_COUNT = 200


def clean(value):
    return ("" if value is None else str(value)).strip()


def read_csv(path):
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), [dict(row) for row in reader]


def write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_csv(path, fieldnames, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main():
    if env.cr.dbname != "sc_demo":  # noqa: F821
        raise RuntimeError({"db_name_not_sc_demo": env.cr.dbname})  # noqa: F821

    write_result = json.loads(WRITE_RESULT_JSON.read_text(encoding="utf-8"))
    _snapshot_fields, snapshot_rows = read_csv(POST_WRITE_SNAPSHOT_CSV)
    legacy_ids = [clean(row.get("legacy_project_id")) for row in snapshot_rows]
    project_ids = [int(clean(row.get("id"))) for row in snapshot_rows if clean(row.get("id"))]

    model = env["project.project"].sudo()  # noqa: F821
    records = model.search([("id", "in", project_ids)], order="id")
    by_id = {rec.id: rec for rec in records}
    by_legacy = {}
    for rec in records:
        by_legacy.setdefault(rec.legacy_project_id or "", []).append(rec)

    target_input_duplicates = sorted(identity for identity, count in Counter(legacy_ids).items() if identity and count > 1)
    missing_project_ids = [project_id for project_id in project_ids if project_id not in by_id]
    missing_legacy_matches = []
    duplicate_legacy_matches = []
    projection_mismatches = []
    stage_counter = Counter()
    lifecycle_counter = Counter()
    rows = []

    for target in snapshot_rows:
        project_id = int(clean(target.get("id"))) if clean(target.get("id")) else 0
        legacy_project_id = clean(target.get("legacy_project_id"))
        rec = by_id.get(project_id)
        matches = by_legacy.get(legacy_project_id, [])
        if not matches:
            missing_legacy_matches.append({"legacy_project_id": legacy_project_id})
        if len(matches) > 1:
            duplicate_legacy_matches.append({"legacy_project_id": legacy_project_id, "ids": [item.id for item in matches]})

        stage = rec.stage_id if rec else None
        lifecycle_state = rec.lifecycle_state if rec else ""
        if rec:
            stage_counter[(stage.id if stage else None, stage.display_name if stage else "")] += 1
            lifecycle_counter[lifecycle_state or ""] += 1
            expected_stage = rec._get_stage_for_lifecycle(lifecycle_state)
            projection_ok = not expected_stage or rec.stage_id == expected_stage
            if not projection_ok:
                projection_mismatches.append(
                    {
                        "id": rec.id,
                        "legacy_project_id": rec.legacy_project_id or "",
                        "lifecycle_state": lifecycle_state or "",
                        "stage_id": rec.stage_id.id or False,
                        "expected_stage_id": expected_stage.id,
                    }
                )
        else:
            projection_ok = False

        rollback_eligible = bool(rec) and len(matches) == 1 and projection_ok
        rows.append(
            {
                "project_id": project_id,
                "matched": bool(rec),
                "legacy_project_id": legacy_project_id,
                "name": rec.name if rec else "",
                "lifecycle_state": lifecycle_state,
                "stage_id": stage.id if stage else None,
                "stage_name": stage.display_name if stage else "",
                "match_count": len(matches),
                "rollback_eligible": rollback_eligible,
            }
        )

    blocking_reasons = []
    if write_result.get("status") != "PASS":
        blocking_reasons.append("write_result_not_pass")
    if write_result.get("summary", {}).get("created") != EXPECTED_COUNT:
        blocking_reasons.append("write_result_created_not_200")
    if len(snapshot_rows) != EXPECTED_COUNT:
        blocking_reasons.append("post_write_snapshot_not_200_rows")
    if len(records) != EXPECTED_COUNT:
        blocking_reasons.append("matched_project_rows_not_200")
    if target_input_duplicates:
        blocking_reasons.append("post_write_snapshot_duplicate_legacy_project_id")
    if missing_project_ids:
        blocking_reasons.append("post_write_snapshot_project_id_missing")
    if missing_legacy_matches:
        blocking_reasons.append("post_write_snapshot_legacy_identity_missing")
    if duplicate_legacy_matches:
        blocking_reasons.append("duplicate_legacy_identity_matches")
    if projection_mismatches:
        blocking_reasons.append("stage_projection_mismatches")
    if any(not row["rollback_eligible"] for row in rows):
        blocking_reasons.append("not_all_rows_rollback_eligible")

    rollback_rows = [
        {
            "project_id": row["project_id"],
            "legacy_project_id": row["legacy_project_id"],
            "name": row["name"],
            "lifecycle_state": row["lifecycle_state"],
            "stage_id": row["stage_id"],
            "stage_name": row["stage_name"],
            "rollback_eligible": row["rollback_eligible"],
        }
        for row in rows
    ]
    write_csv(
        ROLLBACK_TARGET_CSV,
        ["project_id", "legacy_project_id", "name", "lifecycle_state", "stage_id", "stage_name", "rollback_eligible"],
        rollback_rows,
    )

    payload = {
        "status": "ROLLBACK_READY" if not blocking_reasons else "ROLLBACK_BLOCKED",
        "mode": "project_v4_200_post_write_readonly_review",
        "database": env.cr.dbname,  # noqa: F821
        "rollback_key": "legacy_project_id",
        "target_rows": len(snapshot_rows),
        "matched_project_rows": len(records),
        "rollback_eligible_rows": sum(1 for row in rows if row["rollback_eligible"]),
        "stage_id_summary": [
            {"stage_id": stage_id, "stage_name": stage_name, "count": count}
            for (stage_id, stage_name), count in sorted(stage_counter.items(), key=lambda item: (item[0][0] or 0, item[0][1]))
        ],
        "lifecycle_state_summary": [
            {"lifecycle_state": state, "count": count}
            for state, count in sorted(lifecycle_counter.items())
        ],
        "missing_project_ids": missing_project_ids,
        "target_input_duplicates": target_input_duplicates,
        "missing_legacy_matches": missing_legacy_matches,
        "duplicate_legacy_matches": duplicate_legacy_matches,
        "projection_mismatches": projection_mismatches,
        "blocking_reasons": blocking_reasons,
        "rows": rows,
        "artifacts": {"rollback_target_list": str(ROLLBACK_TARGET_CSV)},
    }
    write_json(OUTPUT_JSON, payload)
    env.cr.rollback()  # noqa: F821 - keep Odoo shell transaction read-only
    print(
        "PROJECT_V4_200_POST_WRITE_REVIEW="
        + json.dumps(
            {
                "status": payload["status"],
                "target_rows": payload["target_rows"],
                "matched_project_rows": payload["matched_project_rows"],
                "rollback_eligible_rows": payload["rollback_eligible_rows"],
                "blocking_reasons": payload["blocking_reasons"],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    if blocking_reasons:
        raise RuntimeError({"project_v4_post_write_review_failed": blocking_reasons})


main()
