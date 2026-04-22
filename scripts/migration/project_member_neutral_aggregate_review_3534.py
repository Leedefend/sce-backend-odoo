"""Readonly aggregate review for 3534 project_member neutral carrier rows."""

from __future__ import annotations

import json
from pathlib import Path


OUTPUT_JSON = Path("/mnt/artifacts/migration/project_member_neutral_aggregate_review_3534_v1.json")
TARGET_MODEL = "sc.project.member.staging"
EXPECTED_BATCH_COUNTS = {
    "ITER-2026-04-14-0030N": 34,
    "ITER-2026-04-14-0030NZ": 500,
    "ITER-2026-04-14-1973N": 500,
    "ITER-2026-04-14-1975N": 500,
    "ITER-2026-04-14-1980N": 500,
    "ITER-2026-04-15-1982N": 500,
    "ITER-2026-04-15-1984N": 500,
    "ITER-2026-04-15-1986N": 500,
}


def write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main():
    if env.cr.dbname != "sc_demo":  # noqa: F821
        raise RuntimeError({"db_name_not_sc_demo": env.cr.dbname})  # noqa: F821

    model = env[TARGET_MODEL].sudo()  # noqa: F821
    blocking_reasons = []
    batch_counts = {}
    for batch, expected in EXPECTED_BATCH_COUNTS.items():
        count = model.search_count([("import_batch", "=", batch)])
        batch_counts[batch] = count
        if count != expected:
            blocking_reasons.append({"error": "unexpected_batch_count", "batch": batch, "expected": expected, "actual": count})

    total_expected = sum(EXPECTED_BATCH_COUNTS.values())
    batch_keys = list(EXPECTED_BATCH_COUNTS)
    records = model.search([("import_batch", "in", batch_keys)])
    missing_status_count = model.search_count([
        ("import_batch", "in", batch_keys),
        ("role_fact_status", "=", "missing"),
    ])
    if len(records) != total_expected:
        blocking_reasons.append({"error": "unexpected_total_count", "expected": total_expected, "actual": len(records)})
    if missing_status_count != total_expected:
        blocking_reasons.append({"error": "role_fact_status_not_all_missing", "expected": total_expected, "actual": missing_status_count})

    pair_counts = {}
    for rec in records:
        key = f"{rec.project_id.id}:{rec.user_id.id}"
        pair_counts[key] = pair_counts.get(key, 0) + 1
    duplicate_pair_count = sum(1 for count in pair_counts.values() if count > 1)
    max_rows_per_pair = max(pair_counts.values()) if pair_counts else 0

    payload = {
        "status": "PASS" if not blocking_reasons else "FAIL",
        "mode": "project_member_neutral_aggregate_review_3534",
        "database": env.cr.dbname,  # noqa: F821
        "target_model": TARGET_MODEL,
        "db_writes": 0,
        "batch_counts": batch_counts,
        "total_expected": total_expected,
        "total_records": len(records),
        "role_fact_status_missing_count": missing_status_count,
        "distinct_project_user_pairs": len(pair_counts),
        "duplicate_project_user_pair_count": duplicate_pair_count,
        "max_rows_per_project_user_pair": max_rows_per_pair,
        "project_responsibility_writes": 0,
        "blocking_reasons": blocking_reasons,
    }
    write_json(OUTPUT_JSON, payload)
    env.cr.rollback()  # noqa: F821
    print("PROJECT_MEMBER_NEUTRAL_AGGREGATE_REVIEW_3534=" + json.dumps({
        "status": payload["status"],
        "total_records": payload["total_records"],
        "role_fact_status_missing_count": payload["role_fact_status_missing_count"],
        "distinct_project_user_pairs": payload["distinct_project_user_pairs"],
        "duplicate_project_user_pair_count": payload["duplicate_project_user_pair_count"],
        "db_writes": payload["db_writes"],
    }, ensure_ascii=False, sort_keys=True))
    if blocking_reasons:
        raise RuntimeError({"project_member_neutral_aggregate_review_3534_failed": blocking_reasons})


main()
