"""Readonly responsibility candidate strength selection for project_member pairs."""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path


PAIRS_JSON = Path("/mnt/artifacts/migration/project_member_consolidated_pairs_v1.json")
CANDIDATES_JSON = Path("/mnt/artifacts/migration/project_member_responsibility_candidates_v1.json")
CANDIDATES_CSV = Path("/mnt/artifacts/migration/project_member_responsibility_candidates_v1.csv")
SUMMARY_JSON = Path("/mnt/artifacts/migration/project_member_responsibility_candidate_summary_v1.json")

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


def classify(row):
    evidence_count = int(row.get("evidence_count") or 0)
    batches = list(row.get("evidence_batches") or [])
    multi_batch = len(set(batches)) > 1
    reasons = ["all_consolidated_pairs"]
    level = "L0"

    if evidence_count >= 2:
        level = "L1"
        reasons.append("evidence_count>=2")
    if evidence_count >= 3 and multi_batch:
        level = "L2"
        reasons.append("evidence_count>=3")
        reasons.append("multi_batch")
    if evidence_count >= 4:
        level = "L3"
        reasons.append("evidence_count>=4")

    return level, reasons


def main():
    if env.cr.dbname != "sc_demo":  # noqa: F821
        raise RuntimeError({"db_name_not_sc_demo": env.cr.dbname})  # noqa: F821

    source = json.loads(PAIRS_JSON.read_text(encoding="utf-8"))
    if source.get("status") != "PASS":
        raise RuntimeError({"consolidated_pairs_not_pass": source.get("status")})
    pairs = list(source.get("pairs") or [])

    candidates = []
    csv_rows = []
    level_counter = Counter()
    for row in pairs:
        level, reasons = classify(row)
        promotion_ready = bool(row.get("promotion_candidate"))
        item = {
            "pair_key": row["pair_key"],
            "project_id": row["project_id"],
            "project_name": row["project_name"],
            "user_id": row["user_id"],
            "user_name": row["user_name"],
            "evidence_count": row["evidence_count"],
            "duplicate_flag": row["duplicate_flag"],
            "role_fact_status": row["role_fact_status"],
            "candidate_level": level,
            "candidate_reason": reasons,
            "promotion_ready": promotion_ready,
            "requires_role_source": not promotion_ready,
            "evidence_batches": row["evidence_batches"],
            "evidence_row_ids": row["evidence_row_ids"],
        }
        candidates.append(item)
        level_counter[level] += 1
        csv_rows.append({
            "pair_key": item["pair_key"],
            "project_id": item["project_id"],
            "project_name": item["project_name"],
            "user_id": item["user_id"],
            "user_name": item["user_name"],
            "evidence_count": item["evidence_count"],
            "duplicate_flag": "yes" if item["duplicate_flag"] else "no",
            "candidate_level": item["candidate_level"],
            "candidate_reason": ",".join(item["candidate_reason"]),
            "promotion_ready": "yes" if item["promotion_ready"] else "no",
            "requires_role_source": "yes" if item["requires_role_source"] else "no",
        })

    blocking_reasons = []
    if len(candidates) != EXPECTED_PAIR_COUNT:
        blocking_reasons.append({"error": "pair_count_not_362", "actual": len(candidates)})
    if any(not row["candidate_reason"] for row in candidates):
        blocking_reasons.append({"error": "candidate_reason_missing"})

    summary = {
        "status": "PASS" if not blocking_reasons else "BLOCKED",
        "mode": "project_member_responsibility_candidate_selection_summary",
        "database": env.cr.dbname,  # noqa: F821
        "db_writes": 0,
        "total_pairs": len(candidates),
        "L0_candidates": level_counter.get("L0", 0),
        "L1_candidates": level_counter.get("L1", 0),
        "L2_candidates": level_counter.get("L2", 0),
        "L3_candidates": level_counter.get("L3", 0),
        "promotion_ready_pairs": sum(1 for row in candidates if row["promotion_ready"]),
        "requires_role_source_pairs": sum(1 for row in candidates if row["requires_role_source"]),
        "blocking_reasons": blocking_reasons,
    }
    output = {
        "status": summary["status"],
        "mode": "project_member_responsibility_candidate_selection",
        "database": env.cr.dbname,  # noqa: F821
        "db_writes": 0,
        "selection_rule": {
            "L0": "all consolidated pairs",
            "L1": "evidence_count >= 2",
            "L2": "evidence_count >= 3 and multi_batch",
            "L3": "evidence_count >= 4",
        },
        "total_pairs": len(candidates),
        "candidates": candidates,
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
            "candidate_level",
            "candidate_reason",
            "promotion_ready",
            "requires_role_source",
        ],
        csv_rows,
    )
    write_json(SUMMARY_JSON, summary)
    env.cr.rollback()  # noqa: F821
    print("PROJECT_MEMBER_RESPONSIBILITY_CANDIDATE_SELECTION=" + json.dumps({
        "status": output["status"],
        "total_pairs": summary["total_pairs"],
        "L0_candidates": summary["L0_candidates"],
        "L1_candidates": summary["L1_candidates"],
        "L2_candidates": summary["L2_candidates"],
        "L3_candidates": summary["L3_candidates"],
        "promotion_ready_pairs": summary["promotion_ready_pairs"],
        "requires_role_source_pairs": summary["requires_role_source_pairs"],
        "db_writes": output["db_writes"],
    }, ensure_ascii=False, sort_keys=True))
    if blocking_reasons:
        raise RuntimeError({"project_member_responsibility_candidate_selection_blocked": blocking_reasons})


main()
