#!/usr/bin/env python3
"""No-DB design for 57 single-source contract partner-anchor recovery rows."""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path


REPO_ROOT = Path.cwd()
SCREEN_CSV = REPO_ROOT / "artifacts/migration/contract_partner_anchor_recovery_screen_rows_v1.csv"
OUTPUT_JSON = REPO_ROOT / "artifacts/migration/contract_partner_source_57_design_result_v1.json"
OUTPUT_CSV = REPO_ROOT / "artifacts/migration/contract_partner_source_57_design_rows_v1.csv"
OUTPUT_REPORT = REPO_ROOT / "docs/migration_alignment/contract_partner_source_57_design_report_v1.md"


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
    text = f"""# Contract Partner Source 57 Design v1

Status: {payload["status"]}

Task: `ITER-2026-04-15-CONTRACT-PARTNER-SOURCE-57-DESIGN`

## Scope

Create a no-DB recovery design for contract partner-anchor blockers that have
single-source legacy partner evidence. This batch performs no database reads or
writes.

## Result

- input rows from partner-anchor screen: `{payload["input_rows"]}`
- design rows: `{payload["design_rows"]}`
- distinct counterparties: `{payload["distinct_counterparties"]}`
- DB writes: `0`

## Source Type Counts

```json
{json.dumps(payload["source_type_counts"], ensure_ascii=False, indent=2)}
```

## Decision

`{payload["decision"]}`

## Next

{payload["next_step"]}
"""
    OUTPUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_REPORT.write_text(text, encoding="utf-8")


def main() -> int:
    if not SCREEN_CSV.exists():
        raise RuntimeError({"missing_screen_csv": str(SCREEN_CSV)})

    input_rows = read_csv(SCREEN_CSV)
    candidates = [
        row
        for row in input_rows
        if row.get("recovery_route") == "partner_source_recoverable_design_candidate"
    ]
    design_rows: list[dict[str, object]] = []
    source_type_counts: Counter[str] = Counter()
    counterparty_counts: Counter[str] = Counter()

    for row in candidates:
        source_type = row.get("source_types") or "unknown"
        counterparty = row.get("counterparty_text", "")
        source_type_counts[source_type] += 1
        counterparty_counts[counterparty] += 1
        design_rows.append(
            {
                "legacy_contract_id": row.get("legacy_contract_id", ""),
                "legacy_project_id": row.get("legacy_project_id", ""),
                "contract_subject": row.get("subject", ""),
                "direction": row.get("direction", ""),
                "counterparty_text": counterparty,
                "legacy_partner_source_type": source_type,
                "design_action": "prepare_partner_anchor_candidate",
                "contract_retry_after_partner_anchor": "yes",
                "db_write_authorized": "no",
                "rollback_key": row.get("legacy_contract_id", ""),
            }
        )

    status = "PASS" if len(candidates) == 57 else "FAIL"
    payload = {
        "status": status,
        "mode": "contract_partner_source_57_design",
        "db_writes": 0,
        "input_artifact": str(SCREEN_CSV),
        "input_rows": len(input_rows),
        "design_rows": len(design_rows),
        "distinct_counterparties": len(counterparty_counts),
        "source_type_counts": dict(sorted(source_type_counts.items())),
        "row_artifact": str(OUTPUT_CSV),
        "decision": "partner_source_57_design_ready" if status == "PASS" else "STOP_REVIEW_REQUIRED",
        "write_authorization": "not_granted",
        "next_step": "open migration acceleration analysis and bus plan before any DB write",
        "errors": [] if status == "PASS" else [{"expected_design_rows": 57, "actual": len(candidates)}],
    }

    write_csv(
        OUTPUT_CSV,
        [
            "legacy_contract_id",
            "legacy_project_id",
            "contract_subject",
            "direction",
            "counterparty_text",
            "legacy_partner_source_type",
            "design_action",
            "contract_retry_after_partner_anchor",
            "db_write_authorized",
            "rollback_key",
        ],
        design_rows,
    )
    write_json(OUTPUT_JSON, payload)
    write_report(payload)
    print(
        "CONTRACT_PARTNER_SOURCE_57_DESIGN="
        + json.dumps(
            {
                "status": status,
                "design_rows": len(design_rows),
                "distinct_counterparties": len(counterparty_counts),
                "source_type_counts": payload["source_type_counts"],
                "db_writes": 0,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
