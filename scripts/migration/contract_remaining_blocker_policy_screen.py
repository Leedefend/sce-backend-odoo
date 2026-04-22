#!/usr/bin/env python3
"""No-DB policy screen for remaining blocked contract source rows."""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path


REPO_ROOT = Path.cwd()
INPUT_CSV = REPO_ROOT / "artifacts/migration/contract_source_coverage_nodb_screen_rows_v1.csv"
OUTPUT_JSON = REPO_ROOT / "artifacts/migration/contract_remaining_blocker_policy_screen_result_v1.json"
OUTPUT_CSV = REPO_ROOT / "artifacts/migration/contract_remaining_blocker_policy_screen_rows_v1.csv"
OUTPUT_REPORT = REPO_ROOT / "docs/migration_alignment/contract_remaining_blocker_policy_screen_report_v1.md"


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


def split_blockers(value: str) -> list[str]:
    return [item for item in (value or "").split("|") if item]


def policy_route(row: dict[str, str]) -> tuple[str, str]:
    blockers = set(split_blockers(row.get("blockers", "")))
    coverage_route = row.get("coverage_route", "")
    if coverage_route == "discard_deleted_source" or "deleted_flag" in blockers:
        return "discard_deleted_source", "deleted legacy source row; do not migrate unless business reversal evidence appears"
    if "project_unresolved" in blockers or "project_ambiguous" in blockers:
        return "project_anchor_recovery_screen", "contract row cannot migrate until project anchor is resolved"
    if "partner_unresolved" in blockers or "partner_ambiguous" in blockers:
        return "partner_anchor_recovery_screen", "contract row cannot migrate until counterparty anchor is resolved"
    if "direction_defer" in blockers:
        return "direction_policy_screen", "contract direction cannot be inferred from current own-company rule"
    return "manual_review_hold", "blocked row does not match a known automatic policy route"


def write_report(payload: dict[str, object]) -> None:
    text = f"""# Contract Remaining Blocker Policy Screen v1

Status: {payload["status"]}

Task: `ITER-2026-04-15-CONTRACT-REMAINING-BLOCKER-POLICY-SCREEN`

## Scope

Classify the remaining blocked contract source rows from the coverage artifact.
This batch performs no database reads or writes and does not authorize contract,
line, payment, settlement, or accounting writes.

## Result

- input source rows: `{payload["input_rows"]}`
- remaining blocked rows: `{payload["remaining_blocked_rows"]}`
- DB writes: `0`

## Policy Routes

```json
{json.dumps(payload["policy_route_counts"], ensure_ascii=False, indent=2)}
```

## Blocker Counts

```json
{json.dumps(payload["blocker_counts"], ensure_ascii=False, indent=2)}
```

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

    input_rows = read_csv(INPUT_CSV)
    blocked_rows = [row for row in input_rows if not row.get("target_contract_id")]
    policy_rows: list[dict[str, object]] = []
    route_counts: Counter[str] = Counter()
    blocker_counts: Counter[str] = Counter()

    for row in blocked_rows:
        route, note = policy_route(row)
        route_counts[route] += 1
        blockers = split_blockers(row.get("blockers", ""))
        for blocker in blockers:
            blocker_counts[blocker] += 1
        policy_rows.append(
            {
                "legacy_contract_id": row.get("legacy_contract_id", ""),
                "legacy_project_id": row.get("legacy_project_id", ""),
                "subject": row.get("subject", ""),
                "coverage_route": row.get("coverage_route", ""),
                "blockers": "|".join(blockers),
                "policy_route": route,
                "policy_note": note,
            }
        )

    status = "PASS" if len(blocked_rows) == 350 else "FAIL"
    payload = {
        "status": status,
        "mode": "contract_remaining_blocker_policy_screen",
        "db_writes": 0,
        "input_artifact": str(INPUT_CSV),
        "input_rows": len(input_rows),
        "remaining_blocked_rows": len(blocked_rows),
        "policy_route_counts": dict(sorted(route_counts.items())),
        "blocker_counts": dict(sorted(blocker_counts.items())),
        "row_artifact": str(OUTPUT_CSV),
        "decision": "remaining_blockers_policy_screened" if status == "PASS" else "STOP_REVIEW_REQUIRED",
        "write_authorization": "not_granted",
        "next_step": "open project-anchor recovery no-DB screen first; deleted rows remain discard candidates",
        "errors": [] if status == "PASS" else [{"expected_remaining_blocked_rows": 350, "actual": len(blocked_rows)}],
    }
    write_csv(
        OUTPUT_CSV,
        [
            "legacy_contract_id",
            "legacy_project_id",
            "subject",
            "coverage_route",
            "blockers",
            "policy_route",
            "policy_note",
        ],
        policy_rows,
    )
    write_json(OUTPUT_JSON, payload)
    write_report(payload)
    print(
        "CONTRACT_REMAINING_BLOCKER_POLICY_SCREEN="
        + json.dumps(
            {
                "status": status,
                "remaining_blocked_rows": len(blocked_rows),
                "policy_route_counts": payload["policy_route_counts"],
                "db_writes": 0,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
