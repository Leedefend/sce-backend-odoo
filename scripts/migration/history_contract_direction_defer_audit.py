#!/usr/bin/env python3
"""Freeze remaining direction-defer contract headers against original blocker screens."""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
GAP_ROWS_CSV = REPO_ROOT / "artifacts/migration/history_contract_partner_gap_rows_v1.csv"
ANCHOR_SCREEN_CSV = REPO_ROOT / "artifacts/migration/contract_partner_anchor_recovery_screen_rows_v1.csv"
SOURCE_COVERAGE_CSV = REPO_ROOT / "artifacts/migration/contract_source_coverage_nodb_screen_rows_v1.csv"
OUTPUT_JSON = REPO_ROOT / "artifacts/migration/history_contract_direction_defer_audit_v1.json"
OUTPUT_CSV = REPO_ROOT / "artifacts/migration/history_contract_direction_defer_rows_v1.csv"


def clean(value: object) -> str:
    return "" if value is None else str(value).strip()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    gap_rows = [row for row in read_csv(GAP_ROWS_CSV) if "direction_defer" in clean(row.get("blockers"))]
    anchor_rows = {clean(row.get("legacy_contract_id")): row for row in read_csv(ANCHOR_SCREEN_CSV)}
    source_rows = {clean(row.get("legacy_contract_id")): row for row in read_csv(SOURCE_COVERAGE_CSV)}

    policy_counts = Counter()
    blocker_counts = Counter()
    rows_out: list[dict[str, object]] = []
    missing_anchor: list[str] = []
    missing_source: list[str] = []

    for row in gap_rows:
        legacy_contract_id = clean(row.get("legacy_contract_id"))
        anchor = anchor_rows.get(legacy_contract_id)
        source = source_rows.get(legacy_contract_id)
        if not anchor:
            missing_anchor.append(legacy_contract_id)
        if not source:
            missing_source.append(legacy_contract_id)
        policy = clean(anchor.get("reason_code")) if anchor else ""
        blocker = clean(source.get("blockers")) if source else clean(row.get("blockers"))
        if policy:
            policy_counts[policy] += 1
        if blocker:
            blocker_counts[blocker] += 1
        rows_out.append(
            {
                "legacy_contract_id": legacy_contract_id,
                "subject": clean(row.get("subject")),
                "legacy_contract_no": clean(row.get("legacy_contract_no")),
                "fbf": clean(row.get("fbf")),
                "cbf": clean(row.get("cbf")),
                "gap_blockers": clean(row.get("blockers")),
                "anchor_policy_bucket": clean(anchor.get("bucket")) if anchor else "",
                "anchor_reason_code": policy,
                "source_coverage_bucket": clean(source.get("bucket")) if source else "",
                "source_coverage_blockers": blocker,
            }
        )

    payload = {
        "status": "PASS",
        "mode": "history_contract_direction_defer_audit",
        "direction_defer_rows": len(gap_rows),
        "anchor_reason_code_counts": dict(sorted(policy_counts.items())),
        "source_coverage_blocker_counts": dict(sorted(blocker_counts.items())),
        "missing_anchor_rows": missing_anchor,
        "missing_source_rows": missing_source,
        "row_artifact": str(OUTPUT_CSV.relative_to(REPO_ROOT)),
        "sample_rows": rows_out[:20],
    }
    write_csv(
        OUTPUT_CSV,
        [
            "legacy_contract_id",
            "subject",
            "legacy_contract_no",
            "fbf",
            "cbf",
            "gap_blockers",
            "anchor_policy_bucket",
            "anchor_reason_code",
            "source_coverage_bucket",
            "source_coverage_blockers",
        ],
        rows_out,
    )
    write_json(OUTPUT_JSON, payload)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
