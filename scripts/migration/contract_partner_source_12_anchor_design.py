#!/usr/bin/env python3
"""Collapse 57 contract partner-source design rows into 12 anchor candidates."""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path


REPO_ROOT = Path.cwd()
INPUT_CSV = REPO_ROOT / "artifacts/migration/contract_partner_source_57_design_rows_v1.csv"
OUTPUT_JSON = REPO_ROOT / "artifacts/migration/contract_partner_source_12_anchor_design_result_v1.json"
OUTPUT_CSV = REPO_ROOT / "artifacts/migration/contract_partner_source_12_anchor_design_rows_v1.csv"
OUTPUT_REPORT = REPO_ROOT / "docs/migration_alignment/contract_partner_source_12_anchor_design_report_v1.md"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_report(payload: dict[str, object]) -> None:
    text = f"""# Contract Partner Source 12 Anchor Design v1

Status: {payload["status"]}

Task: `ITER-2026-04-15-CONTRACT-PARTNER-SOURCE-12-ANCHOR-DESIGN`

## Scope

Collapse the 57 contract partner-source design rows into distinct partner
anchors. This batch performs no database reads or writes.

## Result

- input design rows: `{payload["input_rows"]}`
- anchor rows: `{payload["anchor_rows"]}`
- dependent contract rows: `{payload["dependent_contract_rows"]}`
- DB writes: `0`

## Decision

`{payload["decision"]}`

## Next

{payload["next_step"]}
"""
    OUTPUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_REPORT.write_text(text, encoding="utf-8")


def main() -> int:
    if not INPUT_CSV.exists():
        raise RuntimeError({"missing_input_csv": str(INPUT_CSV)})
    rows = read_csv(INPUT_CSV)
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[row.get("counterparty_text", "")].append(row)

    output_rows: list[dict[str, object]] = []
    for counterparty, items in sorted(grouped.items()):
        output_rows.append(
            {
                "counterparty_text": counterparty,
                "legacy_partner_source_type": items[0].get("legacy_partner_source_type", ""),
                "dependent_contract_rows": len(items),
                "sample_legacy_contract_id": items[0].get("legacy_contract_id", ""),
                "sample_contract_subject": items[0].get("contract_subject", ""),
                "design_action": "prepare_single_partner_anchor",
                "idempotency_key": f"company::{counterparty}",
                "db_write_authorized": "no",
            }
        )

    status = "PASS" if len(rows) == 57 and len(output_rows) == 12 else "FAIL"
    payload = {
        "status": status,
        "mode": "contract_partner_source_12_anchor_design",
        "db_writes": 0,
        "input_artifact": str(INPUT_CSV),
        "input_rows": len(rows),
        "anchor_rows": len(output_rows),
        "dependent_contract_rows": sum(int(row["dependent_contract_rows"]) for row in output_rows),
        "row_artifact": str(OUTPUT_CSV),
        "decision": "partner_source_12_anchor_design_ready" if status == "PASS" else "STOP_REVIEW_REQUIRED",
        "write_authorization": "not_granted",
        "next_step": "open bounded DB write task for 12 partner anchors, then retry dependent 57 contract rows",
        "errors": [] if status == "PASS" else [{"expected_input_rows": 57, "actual_input_rows": len(rows), "expected_anchor_rows": 12, "actual_anchor_rows": len(output_rows)}],
    }
    write_csv(
        OUTPUT_CSV,
        [
            "counterparty_text",
            "legacy_partner_source_type",
            "dependent_contract_rows",
            "sample_legacy_contract_id",
            "sample_contract_subject",
            "design_action",
            "idempotency_key",
            "db_write_authorized",
        ],
        output_rows,
    )
    write_json(OUTPUT_JSON, payload)
    write_report(payload)
    print(
        "CONTRACT_PARTNER_SOURCE_12_ANCHOR_DESIGN="
        + json.dumps(
            {
                "status": status,
                "input_rows": len(rows),
                "anchor_rows": len(output_rows),
                "dependent_contract_rows": payload["dependent_contract_rows"],
                "db_writes": 0,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
