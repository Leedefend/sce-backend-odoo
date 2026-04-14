"""Readonly responsibility promotion candidate screen for project_member pairs."""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path


PAIRS_JSON = Path("/mnt/artifacts/migration/project_member_consolidated_pairs_v1.json")
CANDIDATES_JSON = Path("/mnt/artifacts/migration/project_member_responsibility_promotion_candidates_v1.json")
CANDIDATES_CSV = Path("/mnt/artifacts/migration/project_member_responsibility_promotion_candidates_v1.csv")
SUMMARY_JSON = Path("/mnt/artifacts/migration/project_member_responsibility_promotion_screen_summary_v1.json")

EXPECTED_PAIR_COUNT = 362


def write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_csv(path, fieldnames, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def classify_pair(row, existing_pairs):
    blockers = []
    if not row.get("project_id"):
        blockers.append("missing_project_id")
    if not row.get("user_id"):
        blockers.append("missing_user_id")
    if row.get("role_fact_status") == "missing":
        blockers.append("missing_verified_role_fact")
    if not row.get("role_fact_status") or row.get("role_fact_status") == "missing":
        blockers.append("missing_target_role_key")
    if (row.get("project_id"), row.get("user_id")) in existing_pairs:
        blockers.append("existing_project_responsibility_pair_requires_role_collision_review")
    return sorted(set(blockers))


def main():
    if env.cr.dbname != "sc_demo":  # noqa: F821
        raise RuntimeError({"db_name_not_sc_demo": env.cr.dbname})  # noqa: F821

    source = json.loads(PAIRS_JSON.read_text(encoding="utf-8"))
    if source.get("status") != "PASS":
        raise RuntimeError({"consolidated_pairs_not_pass": source.get("status")})
    pairs = list(source.get("pairs") or [])

    responsibility = env["project.responsibility"].sudo()  # noqa: F821
    existing_records = responsibility.search([("project_id", "in", [row["project_id"] for row in pairs]), ("user_id", "in", [row["user_id"] for row in pairs])])
    existing_pairs = {(record.project_id.id, record.user_id.id) for record in existing_records}

    rows = []
    csv_rows = []
    blocker_counter = Counter()
    candidate_count = 0
    for row in pairs:
        blockers = classify_pair(row, existing_pairs)
        if not blockers:
            candidate_count += 1
        for blocker in blockers:
            blocker_counter[blocker] += 1
        item = {
            "pair_key": row["pair_key"],
            "project_id": row["project_id"],
            "project_name": row["project_name"],
            "user_id": row["user_id"],
            "user_name": row["user_name"],
            "evidence_count": row["evidence_count"],
            "duplicate_flag": row["duplicate_flag"],
            "role_fact_status": row["role_fact_status"],
            "promotion_candidate": not blockers,
            "promotion_blockers": blockers,
            "evidence_row_ids": row["evidence_row_ids"],
        }
        rows.append(item)
        csv_rows.append({
            "pair_key": item["pair_key"],
            "project_id": item["project_id"],
            "project_name": item["project_name"],
            "user_id": item["user_id"],
            "user_name": item["user_name"],
            "evidence_count": item["evidence_count"],
            "duplicate_flag": "yes" if item["duplicate_flag"] else "no",
            "role_fact_status": item["role_fact_status"],
            "promotion_candidate": "yes" if item["promotion_candidate"] else "no",
            "promotion_blockers": ",".join(item["promotion_blockers"]),
            "evidence_row_ids": ",".join(str(value) for value in item["evidence_row_ids"]),
        })

    blocking_reasons = []
    if len(pairs) != EXPECTED_PAIR_COUNT:
        blocking_reasons.append({"error": "pair_count_not_362", "actual": len(pairs)})
    if candidate_count:
        unexpected = [row for row in rows if row["promotion_candidate"] and row["role_fact_status"] == "missing"]
        if unexpected:
            blocking_reasons.append({"error": "promotion_candidate_without_role_fact", "count": len(unexpected)})

    output = {
        "status": "PASS" if not blocking_reasons else "BLOCKED",
        "mode": "project_member_responsibility_promotion_candidate_screen",
        "database": env.cr.dbname,  # noqa: F821
        "db_writes": 0,
        "source": str(PAIRS_JSON),
        "total_pairs": len(rows),
        "promotion_candidate_pairs": candidate_count,
        "blocked_pairs": len(rows) - candidate_count,
        "blocker_distribution": dict(sorted(blocker_counter.items())),
        "candidates": rows,
        "blocking_reasons": blocking_reasons,
    }
    summary = {
        "status": output["status"],
        "mode": "project_member_responsibility_promotion_screen_summary",
        "database": env.cr.dbname,  # noqa: F821
        "db_writes": 0,
        "total_pairs": output["total_pairs"],
        "promotion_candidate_pairs": output["promotion_candidate_pairs"],
        "blocked_pairs": output["blocked_pairs"],
        "missing_role_fact_pairs": blocker_counter.get("missing_verified_role_fact", 0),
        "missing_target_role_key_pairs": blocker_counter.get("missing_target_role_key", 0),
        "existing_project_responsibility_pair_review_pairs": blocker_counter.get("existing_project_responsibility_pair_requires_role_collision_review", 0),
        "blocker_distribution": output["blocker_distribution"],
        "blocking_reasons": blocking_reasons,
    }
    write_json(CANDIDATES_JSON, output)
    write_csv(
        CANDIDATES_CSV,
        [
            "pair_key",
            "project_id",
            "project_name",
            "user_id",
            "user_name",
            "evidence_count",
            "duplicate_flag",
            "role_fact_status",
            "promotion_candidate",
            "promotion_blockers",
            "evidence_row_ids",
        ],
        csv_rows,
    )
    write_json(SUMMARY_JSON, summary)
    env.cr.rollback()  # noqa: F821
    print("PROJECT_MEMBER_RESPONSIBILITY_PROMOTION_CANDIDATE_SCREEN=" + json.dumps({
        "status": output["status"],
        "total_pairs": output["total_pairs"],
        "promotion_candidate_pairs": output["promotion_candidate_pairs"],
        "blocked_pairs": output["blocked_pairs"],
        "missing_role_fact_pairs": summary["missing_role_fact_pairs"],
        "db_writes": output["db_writes"],
    }, ensure_ascii=False, sort_keys=True))
    if blocking_reasons:
        raise RuntimeError({"project_member_responsibility_promotion_screen_blocked": blocking_reasons})


main()
