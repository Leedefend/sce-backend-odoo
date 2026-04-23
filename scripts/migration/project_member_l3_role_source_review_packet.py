"""Generate a readonly review packet for L3 project_member role-source repair."""

from __future__ import annotations

import csv
import json
from pathlib import Path


SOURCE_JSON = Path("artifacts/migration/project_member_responsibility_candidates_v1.json")
OUTPUT_JSON = Path("artifacts/migration/project_member_l3_role_source_review_packet_v1.json")
OUTPUT_CSV = Path("artifacts/migration/project_member_l3_role_source_review_packet_v1.csv")
SUMMARY_JSON = Path("artifacts/migration/project_member_l3_role_source_review_summary_v1.json")
EXPECTED_L3_COUNT = 10


def write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_csv(path, fieldnames, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main():
    source = json.loads(SOURCE_JSON.read_text(encoding="utf-8"))
    if source.get("status") != "PASS":
        raise RuntimeError({"candidate_selection_not_pass": source.get("status")})

    candidates = list(source.get("candidates") or [])
    l3_candidates = [row for row in candidates if row.get("candidate_level") == "L3"]
    review_rows = []
    for index, row in enumerate(l3_candidates, start=1):
        item = {
            "review_rank": index,
            "pair_key": row["pair_key"],
            "project_id": row["project_id"],
            "project_name": row["project_name"],
            "user_id": row["user_id"],
            "user_name": row["user_name"],
            "evidence_count": row["evidence_count"],
            "candidate_level": row["candidate_level"],
            "candidate_reason": row["candidate_reason"],
            "role_fact_status": row["role_fact_status"],
            "promotion_ready": False,
            "requires_role_source": True,
            "proposed_role_key": "",
            "role_source_evidence": "",
            "business_reviewer": "",
            "business_decision": "pending",
            "approval_required": True,
            "write_allowed": False,
        }
        review_rows.append(item)

    blocking_reasons = []
    if len(l3_candidates) != EXPECTED_L3_COUNT:
        blocking_reasons.append({"error": "l3_count_not_10", "actual": len(l3_candidates)})

    summary = {
        "status": "PASS" if not blocking_reasons else "BLOCKED",
        "mode": "project_member_l3_role_source_review_packet_summary",
        "total_candidates": len(candidates),
        "l3_candidates": len(l3_candidates),
        "promotion_ready": 0,
        "requires_role_source": len(l3_candidates),
        "write_allowed": False,
        "db_writes": 0,
        "blocking_reasons": blocking_reasons,
    }
    output = {
        "status": summary["status"],
        "mode": "project_member_l3_role_source_review_packet",
        "db_writes": 0,
        "write_allowed": False,
        "review_packet": review_rows,
        "blocking_reasons": blocking_reasons,
    }
    write_json(OUTPUT_JSON, output)
    write_csv(
        OUTPUT_CSV,
        [
            "review_rank",
            "pair_key",
            "project_id",
            "project_name",
            "user_id",
            "user_name",
            "evidence_count",
            "candidate_level",
            "candidate_reason",
            "role_fact_status",
            "promotion_ready",
            "requires_role_source",
            "proposed_role_key",
            "role_source_evidence",
            "business_reviewer",
            "business_decision",
            "approval_required",
            "write_allowed",
        ],
        [
            {
                **row,
                "candidate_reason": ",".join(row["candidate_reason"]),
                "promotion_ready": "yes" if row["promotion_ready"] else "no",
                "requires_role_source": "yes" if row["requires_role_source"] else "no",
                "approval_required": "yes" if row["approval_required"] else "no",
                "write_allowed": "yes" if row["write_allowed"] else "no",
            }
            for row in review_rows
        ],
    )
    write_json(SUMMARY_JSON, summary)
    print("PROJECT_MEMBER_L3_ROLE_SOURCE_REVIEW_PACKET=" + json.dumps({
        "status": output["status"],
        "l3_candidates": summary["l3_candidates"],
        "requires_role_source": summary["requires_role_source"],
        "write_allowed": summary["write_allowed"],
        "db_writes": summary["db_writes"],
    }, ensure_ascii=False, sort_keys=True))
    if blocking_reasons:
        raise RuntimeError({"project_member_l3_role_source_review_packet_blocked": blocking_reasons})


if __name__ == "__main__":
    main()
