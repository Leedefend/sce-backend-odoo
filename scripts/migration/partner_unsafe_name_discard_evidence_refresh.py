#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path


INPUT_CSV = Path("artifacts/migration/partner_l4_unsafe_name_policy_screen_rows_v1.csv")
OUTPUT_JSON = Path("artifacts/migration/partner_l4_unsafe_name_discard_evidence_result_v1.json")
TARGET_CSV = Path("artifacts/migration/partner_l4_unsafe_name_discard_targets_v1.csv")
SAMPLE_CSV = Path("artifacts/migration/partner_l4_unsafe_name_discard_samples_v1.csv")
EXPECTED_DISCARD_ROWS = 1110


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
    required_columns = {
        "row_no",
        "policy_decision",
        "policy_reason",
        "normalized_partner_name",
        "original_partner_name",
        "legacy_partner_source",
        "legacy_partner_id",
        "tax_number",
        "sources",
        "source_row_count",
        "blockers",
    }
    missing_columns = sorted(required_columns - set(columns))
    discard_rows = [
        row for row in rows
        if clean(row.get("policy_decision")) == "discard_non_enterprise_garbage"
    ]

    target_rows: list[dict[str, object]] = []
    reason_counts: Counter[str] = Counter()
    source_counts: Counter[str] = Counter()
    samples: dict[str, list[dict[str, object]]] = defaultdict(list)
    seen_keys: set[tuple[str, str]] = set()
    duplicate_keys: list[tuple[str, str]] = []
    for index, row in enumerate(discard_rows, start=1):
        source = clean(row.get("legacy_partner_source"))
        legacy_id = clean(row.get("legacy_partner_id"))
        key = (source, legacy_id)
        if key in seen_keys:
            duplicate_keys.append(key)
        seen_keys.add(key)
        reason = clean(row.get("policy_reason"))
        reason_counts[reason] += 1
        source_counts[clean(row.get("sources"))] += 1
        target_row = {
            "discard_run_id": f"partner_l4_unsafe_name_discard_{index:04d}",
            "legacy_partner_source": source,
            "legacy_partner_id": legacy_id,
            "original_partner_name": clean(row.get("original_partner_name")),
            "normalized_partner_name": clean(row.get("normalized_partner_name")),
            "tax_number": clean(row.get("tax_number")),
            "sources": clean(row.get("sources")),
            "source_row_count": clean(row.get("source_row_count")),
            "policy_decision": clean(row.get("policy_decision")),
            "policy_reason": reason,
            "source_policy_row_no": clean(row.get("row_no")),
            "source_blockers": clean(row.get("blockers")),
            "discard_scope": "partner_l4_unsafe_name_non_enterprise_garbage",
            "db_write": "false",
        }
        target_rows.append(target_row)
        if len(samples[reason]) < 20:
            samples[reason].append(target_row)

    fieldnames = [
        "discard_run_id",
        "legacy_partner_source",
        "legacy_partner_id",
        "original_partner_name",
        "normalized_partner_name",
        "tax_number",
        "sources",
        "source_row_count",
        "policy_decision",
        "policy_reason",
        "source_policy_row_no",
        "source_blockers",
        "discard_scope",
        "db_write",
    ]
    write_csv(TARGET_CSV, fieldnames, target_rows)
    write_csv(SAMPLE_CSV, fieldnames, [sample for reason in sorted(samples) for sample in samples[reason]])

    status = "PASS"
    if missing_columns or len(target_rows) != EXPECTED_DISCARD_ROWS or duplicate_keys:
        status = "FAIL"
    result = {
        "status": status,
        "mode": "partner_l4_unsafe_name_discard_evidence_refresh",
        "input": str(INPUT_CSV),
        "discard_rows": len(target_rows),
        "expected_discard_rows": EXPECTED_DISCARD_ROWS,
        "missing_columns": missing_columns,
        "duplicate_identity_count": len(duplicate_keys),
        "reason_counts": dict(sorted(reason_counts.items())),
        "source_counts": dict(sorted(source_counts.items())),
        "outputs": {
            "discard_targets": str(TARGET_CSV),
            "discard_samples": str(SAMPLE_CSV),
        },
        "next_gate": "Run partner_rebuild_dry_run.py so discard targets are classified as discarded_validation; no DB write is authorized.",
    }
    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("PARTNER_UNSAFE_NAME_DISCARD_EVIDENCE=" + json.dumps({
        "status": result["status"],
        "discard_rows": result["discard_rows"],
        "duplicate_identity_count": result["duplicate_identity_count"],
        "reason_counts": result["reason_counts"],
    }, ensure_ascii=False, sort_keys=True))
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
