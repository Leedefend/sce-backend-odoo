#!/usr/bin/env python3
"""No-DB screen for contract rows blocked by missing project anchors."""

from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path


REPO_ROOT = Path.cwd()
BLOCKER_CSV = REPO_ROOT / "artifacts/migration/contract_remaining_blocker_policy_screen_rows_v1.csv"
PROJECT_CSV = REPO_ROOT / "tmp/raw/project/project.csv"
OUTPUT_JSON = REPO_ROOT / "artifacts/migration/contract_project_anchor_recovery_screen_result_v1.json"
OUTPUT_CSV = REPO_ROOT / "artifacts/migration/contract_project_anchor_recovery_screen_rows_v1.csv"
OUTPUT_REPORT = REPO_ROOT / "docs/migration_alignment/contract_project_anchor_recovery_screen_report_v1.md"


def clean(value: object) -> str:
    return "" if value is None else str(value).strip()


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


def route_for_project(project_rows: list[dict[str, str]]) -> tuple[str, str]:
    if not project_rows:
        return "legacy_project_source_missing", "legacy project id is not present in project.csv"
    active_rows = [row for row in project_rows if clean(row.get("DEL")) != "1"]
    if not active_rows:
        return "legacy_project_deleted_source", "legacy project source rows are deleted; keep contract blocked or discard"
    if len(active_rows) == 1:
        return "project_anchor_recoverable_design_candidate", "one active legacy project source row can enter no-DB project write design"
    return "project_anchor_duplicate_source_screen", "multiple active legacy project source rows require source dedupe screen"


def write_report(payload: dict[str, object]) -> None:
    text = f"""# Contract Project Anchor Recovery Screen v1

Status: {payload["status"]}

Task: `ITER-2026-04-15-CONTRACT-PROJECT-ANCHOR-RECOVERY-SCREEN`

## Scope

Screen contract rows blocked by missing project anchors against the legacy
project source export. This batch performs no database reads or writes.

## Result

- project-anchor blocked contract rows: `{payload["project_anchor_blocked_rows"]}`
- distinct missing legacy project ids: `{payload["distinct_legacy_project_ids"]}`
- DB writes: `0`

## Recovery Routes

```json
{json.dumps(payload["recovery_route_counts"], ensure_ascii=False, indent=2)}
```

## Decision

`{payload["decision"]}`

## Next

{payload["next_step"]}
"""
    OUTPUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_REPORT.write_text(text, encoding="utf-8")


def main() -> int:
    if not BLOCKER_CSV.exists():
        raise RuntimeError({"missing_blocker_csv": str(BLOCKER_CSV)})
    if not PROJECT_CSV.exists():
        raise RuntimeError({"missing_project_csv": str(PROJECT_CSV)})

    blocker_rows = read_csv(BLOCKER_CSV)
    project_rows = read_csv(PROJECT_CSV)
    by_project_id: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in project_rows:
        legacy_project_id = clean(row.get("ID"))
        if legacy_project_id:
            by_project_id[legacy_project_id].append(row)

    target_rows = [row for row in blocker_rows if row.get("policy_route") == "project_anchor_recovery_screen"]
    contracts_by_project: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in target_rows:
        contracts_by_project[clean(row.get("legacy_project_id"))].append(row)

    output_rows: list[dict[str, object]] = []
    route_counts: Counter[str] = Counter()
    contract_route_counts: Counter[str] = Counter()

    for legacy_project_id, contract_rows in sorted(contracts_by_project.items()):
        source_rows = by_project_id.get(legacy_project_id, [])
        route, note = route_for_project(source_rows)
        route_counts[route] += 1
        contract_route_counts[route] += len(contract_rows)
        first_source = source_rows[0] if source_rows else {}
        output_rows.append(
            {
                "legacy_project_id": legacy_project_id,
                "contract_rows": len(contract_rows),
                "source_project_rows": len(source_rows),
                "active_source_project_rows": sum(1 for row in source_rows if clean(row.get("DEL")) != "1"),
                "source_project_name": clean(first_source.get("XMMC")),
                "source_project_deleted": clean(first_source.get("DEL")),
                "source_project_state": clean(first_source.get("STATE")),
                "sample_contract_id": contract_rows[0].get("legacy_contract_id", ""),
                "sample_contract_subject": contract_rows[0].get("subject", ""),
                "recovery_route": route,
                "recovery_note": note,
            }
        )

    status = "PASS" if len(target_rows) == 88 else "FAIL"
    payload = {
        "status": status,
        "mode": "contract_project_anchor_recovery_screen",
        "db_writes": 0,
        "blocker_artifact": str(BLOCKER_CSV),
        "project_source_file": str(PROJECT_CSV),
        "project_anchor_blocked_rows": len(target_rows),
        "distinct_legacy_project_ids": len(contracts_by_project),
        "recovery_route_counts": dict(sorted(route_counts.items())),
        "contract_row_route_counts": dict(sorted(contract_route_counts.items())),
        "row_artifact": str(OUTPUT_CSV),
        "decision": "project_anchor_recovery_screened" if status == "PASS" else "STOP_REVIEW_REQUIRED",
        "write_authorization": "not_granted",
        "next_step": "open no-DB project anchor recoverable write-design screen for active single-source project ids",
        "errors": [] if status == "PASS" else [{"expected_project_anchor_blocked_rows": 88, "actual": len(target_rows)}],
    }

    write_csv(
        OUTPUT_CSV,
        [
            "legacy_project_id",
            "contract_rows",
            "source_project_rows",
            "active_source_project_rows",
            "source_project_name",
            "source_project_deleted",
            "source_project_state",
            "sample_contract_id",
            "sample_contract_subject",
            "recovery_route",
            "recovery_note",
        ],
        output_rows,
    )
    write_json(OUTPUT_JSON, payload)
    write_report(payload)
    print(
        "CONTRACT_PROJECT_ANCHOR_RECOVERY_SCREEN="
        + json.dumps(
            {
                "status": status,
                "project_anchor_blocked_rows": len(target_rows),
                "distinct_legacy_project_ids": len(contracts_by_project),
                "recovery_route_counts": payload["recovery_route_counts"],
                "db_writes": 0,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
