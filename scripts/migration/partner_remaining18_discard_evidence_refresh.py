#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path


INPUT_CSV = Path("artifacts/migration/partner_l4_nodb_refresh_rows_v1.csv")
OUTPUT_JSON = Path("artifacts/migration/partner_l4_remaining18_discard_evidence_result_v1.json")
TARGET_CSV = Path("artifacts/migration/partner_l4_remaining18_discard_targets_v1.csv")
EXPECTED_ROWS = 18


def clean(value: object) -> str:
    return "" if value is None else str(value).strip()


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), [dict(row) for row in reader]


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    columns, rows = read_csv(INPUT_CSV)
    required = {
        "row_no",
        "legacy_partner_source",
        "legacy_partner_id",
        "partner_name",
        "tax_number",
        "sources",
        "source_row_count",
        "merge_strategy",
        "dry_run_action",
        "blockers",
    }
    missing_columns = sorted(required - set(columns))
    blocked_rows = [row for row in rows if clean(row.get("dry_run_action")) == "blocked"]
    target_rows: list[dict[str, object]] = []
    blocker_counts: Counter[str] = Counter()
    source_counts: Counter[str] = Counter()
    seen_keys: set[tuple[str, str]] = set()
    duplicate_keys: list[tuple[str, str]] = []
    for index, row in enumerate(blocked_rows, start=1):
        source = clean(row.get("legacy_partner_source"))
        legacy_id = clean(row.get("legacy_partner_id"))
        key = (source, legacy_id)
        if key in seen_keys:
            duplicate_keys.append(key)
        seen_keys.add(key)
        blockers = clean(row.get("blockers"))
        blocker_counts[blockers] += 1
        source_counts[source] += 1
        target_rows.append({
            "discard_run_id": f"partner_l4_remaining18_discard_{index:04d}",
            "legacy_partner_source": source,
            "legacy_partner_id": legacy_id,
            "partner_name": clean(row.get("partner_name")),
            "tax_number": clean(row.get("tax_number")),
            "sources": clean(row.get("sources")),
            "source_row_count": clean(row.get("source_row_count")),
            "merge_strategy": clean(row.get("merge_strategy")),
            "policy_decision": "discard_remaining_blocked_by_user_decision",
            "policy_reason": "user_direct_discard_remaining_partner_l4_blocked_rows",
            "source_audit_row_no": clean(row.get("row_no")),
            "source_blockers": blockers,
            "discard_scope": "partner_l4_remaining18_blocked",
            "db_write": "false",
        })

    fieldnames = [
        "discard_run_id",
        "legacy_partner_source",
        "legacy_partner_id",
        "partner_name",
        "tax_number",
        "sources",
        "source_row_count",
        "merge_strategy",
        "policy_decision",
        "policy_reason",
        "source_audit_row_no",
        "source_blockers",
        "discard_scope",
        "db_write",
    ]
    write_csv(TARGET_CSV, fieldnames, target_rows)
    status = "PASS" if not missing_columns and len(target_rows) == EXPECTED_ROWS and not duplicate_keys else "FAIL"
    result = {
        "status": status,
        "mode": "partner_l4_remaining18_discard_evidence_refresh",
        "input": str(INPUT_CSV),
        "discard_rows": len(target_rows),
        "expected_rows": EXPECTED_ROWS,
        "missing_columns": missing_columns,
        "duplicate_identity_count": len(duplicate_keys),
        "blocker_counts": dict(sorted(blocker_counts.items())),
        "source_counts": dict(sorted(source_counts.items())),
        "outputs": {"discard_targets": str(TARGET_CSV)},
        "next_gate": "Run partner_rebuild_dry_run.py so these identities classify as discarded_validation.",
    }
    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("PARTNER_REMAINING18_DISCARD_EVIDENCE=" + json.dumps({
        "status": status,
        "discard_rows": len(target_rows),
        "duplicate_identity_count": len(duplicate_keys),
        "blocker_counts": result["blocker_counts"],
    }, ensure_ascii=False, sort_keys=True))
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
