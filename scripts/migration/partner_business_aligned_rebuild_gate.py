#!/usr/bin/env python3
"""Gate the business-aligned partner rebuild payload before any DB write."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

from partner_import_source_audit import clean, write_csv, write_json


DEFAULT_PAYLOAD = (
    "artifacts/migration/partner_business_aligned_rebuild_v1/"
    "fact_based_partner_rebuild_payload_business_aligned_v1.csv"
)
BLOCKING_FLAGS = {
    "background_only_no_user_requested_business_fact",
    "invalid_bank_account_review",
    "invalid_or_placeholder_credit",
    "multiple_current_payload_matches",
    "personal_fragment_review",
    "unknown_business_role",
}
CREATE_BLOCK_FLAGS = {
    "duplicate_credit_in_xlsx",
    "duplicate_name_in_xlsx",
    "has_not_approved_source_row",
    "missing_credit_code",
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def flags(row: dict[str, str]) -> set[str]:
    return {clean(item) for item in clean(row.get("review_flags")).split(";") if clean(item)}


def classify_row(row: dict[str, str]) -> tuple[str, str]:
    row_flags = flags(row)
    blocking = sorted(row_flags & BLOCKING_FLAGS)
    if blocking:
        return "blocked_review", ";".join(blocking)
    create_blocking = sorted(row_flags & CREATE_BLOCK_FLAGS)
    if create_blocking:
        return "update_only_candidate", ";".join(create_blocking)
    if clean(row.get("supplier_rank")) == "0" and clean(row.get("customer_rank")) == "0":
        return "blocked_review", "no_business_role"
    if not clean(row.get("name")):
        return "blocked_review", "missing_name"
    return "write_candidate", ""


def build_gate(rows: list[dict[str, str]]) -> tuple[list[dict[str, object]], dict[str, object]]:
    gate_rows: list[dict[str, object]] = []
    action_counts: Counter[str] = Counter()
    flag_counts: Counter[str] = Counter()
    for row in rows:
        action, reason = classify_row(row)
        action_counts[action] += 1
        for flag in flags(row):
            flag_counts[flag] += 1
        gate_rows.append(
            {
                **row,
                "gate_action": action,
                "gate_reason": reason,
            }
        )
    summary = {
        "generated_at": datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "payload_rows": len(rows),
        "gate_action_counts": dict(sorted(action_counts.items())),
        "review_flag_counts": dict(sorted(flag_counts.items())),
        "write_rows_without_review_flags": action_counts.get("write_candidate", 0),
        "update_only_rows": action_counts.get("update_only_candidate", 0),
        "blocked_review_rows": action_counts.get("blocked_review", 0),
        "db_write": False,
        "decision": "partner_business_aligned_write_gate_ready",
    }
    return gate_rows, summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--payload", default=DEFAULT_PAYLOAD)
    parser.add_argument("--out-dir", default="artifacts/migration/partner_business_aligned_rebuild_v1")
    args = parser.parse_args()

    rows = read_csv(Path(args.payload))
    gate_rows, summary = build_gate(rows)
    out_dir = Path(args.out_dir)
    fieldnames = list(gate_rows[0].keys()) if gate_rows else []
    write_csv(out_dir / "fact_based_partner_rebuild_business_aligned_gate_v1.csv", fieldnames, gate_rows)
    write_csv(
        out_dir / "fact_based_partner_rebuild_business_aligned_write_candidates_v1.csv",
        fieldnames,
        [row for row in gate_rows if row["gate_action"] == "write_candidate"],
    )
    write_csv(
        out_dir / "fact_based_partner_rebuild_business_aligned_update_only_v1.csv",
        fieldnames,
        [row for row in gate_rows if row["gate_action"] == "update_only_candidate"],
    )
    write_csv(
        out_dir / "fact_based_partner_rebuild_business_aligned_blocked_review_v1.csv",
        fieldnames,
        [row for row in gate_rows if row["gate_action"] == "blocked_review"],
    )
    write_json(out_dir / "fact_based_partner_rebuild_business_aligned_gate_result_v1.json", summary)
    print("PARTNER_BUSINESS_ALIGNED_GATE=" + json.dumps(summary, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
