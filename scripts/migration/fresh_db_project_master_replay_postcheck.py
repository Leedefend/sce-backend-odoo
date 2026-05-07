#!/usr/bin/env python3
"""Read-only postcheck for the project master upgrade replay flow."""

from __future__ import annotations

import csv
import json
import os
from collections import Counter
from pathlib import Path


def repo_root() -> Path:
    env_root = os.getenv("MIGRATION_REPO_ROOT")
    candidates = []
    if env_root:
        candidates.append(Path(env_root))
    candidates.extend([Path("/mnt"), Path.cwd()])
    for candidate in candidates:
        if (candidate / "artifacts/migration/fresh_db_project_anchor_replay_payload_v1.csv").exists():
            return candidate
    return Path.cwd()


REPO_ROOT = repo_root()
ARTIFACT_ROOT = Path(os.getenv("MIGRATION_ARTIFACT_ROOT", str(REPO_ROOT / "artifacts/migration")))
PAYLOAD_CSV = REPO_ROOT / "artifacts/migration/fresh_db_project_anchor_replay_payload_v1.csv"
ADAPTER_JSON = REPO_ROOT / "artifacts/migration/fresh_db_project_anchor_replay_adapter_result_v1.json"
WRITE_JSON = ARTIFACT_ROOT / "fresh_db_project_anchor_replay_write_result_v1.json"
OUTPUT_JSON = ARTIFACT_ROOT / "fresh_db_project_master_replay_postcheck_result_v1.json"
OUTPUT_REPORT = ARTIFACT_ROOT / "fresh_db_project_master_replay_postcheck_report_v1.md"


def clean(value: object) -> str:
    return "" if value is None else str(value).strip()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def read_json(path: Path) -> dict[str, object]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def expected_rows_from_sources(rows: list[dict[str, str]]) -> int:
    explicit = clean(os.getenv("PROJECT_ANCHOR_EXPECTED_ROWS"))
    if explicit:
        return int(explicit)
    adapter_payload = read_json(ADAPTER_JSON)
    adapter_rows = adapter_payload.get("replay_payload_rows")
    if adapter_rows:
        return int(adapter_rows)
    write_payload = read_json(WRITE_JSON)
    write_rows = write_payload.get("expected_rows") or write_payload.get("input_rows")
    if write_rows:
        return int(write_rows)
    return len(rows)


def write_report(payload: dict[str, object]) -> None:
    text = f"""# Project Master Replay Postcheck Report v1

Status: {payload["status"]}

Task: `ITER-2026-05-07-PROJECT-MASTER-UPGRADE-REPLAY`

## Scope

Read-only acceptance check after the project master replay flow.

## Replay Facts

- database: `{payload["database"]}`
- payload rows: `{payload["payload_rows"]}`
- expected rows: `{payload["expected_rows"]}`
- matched project rows: `{payload["matched_project_rows"]}`
- duplicate payload identities: `{len(payload["duplicate_payload_identities"])}`
- duplicate target identities: `{len(payload["duplicate_target_identities"])}`
- missing target identities: `{len(payload["missing_target_identities"])}`

## Source Lanes

```json
{json.dumps(payload["source_lane_counts"], ensure_ascii=False, indent=2)}
```

## Operation Strategy

```json
{json.dumps(payload["operation_strategy_counts"], ensure_ascii=False, indent=2)}
```

## Contract Linkage

```json
{json.dumps(payload["contract_visible_project_anchor_linkage"], ensure_ascii=False, indent=2)}
```

## Decision

`{payload["decision"]}`
"""
    OUTPUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_REPORT.write_text(text, encoding="utf-8")


rows = read_csv(PAYLOAD_CSV)
expected_rows = expected_rows_from_sources(rows)
payload_keys = [clean(row.get("legacy_project_id")) for row in rows]
payload_key_counts = Counter(payload_keys)
duplicate_payload = sorted(key for key, count in payload_key_counts.items() if key and count > 1)
missing_payload_key_rows = [index for index, key in enumerate(payload_keys, start=2) if not key]
source_lane_counts = Counter(clean(row.get("replay_source_lane")) or "unknown" for row in rows)
operation_strategy_counts = Counter(clean(row.get("operation_strategy")) or "unspecified" for row in rows)
operation_strategy_default = clean(os.getenv("PROJECT_ANCHOR_UNSPECIFIED_OPERATION_STRATEGY_DEFAULT")) or "direct"
model_operation_strategy_counts = Counter(clean(row.get("operation_strategy")) or operation_strategy_default for row in rows)

Project = env["project.project"].sudo()  # noqa: F821
project_fields = set(Project._fields)
missing_project_fields = [
    field
    for field in ["legacy_project_id", "name", "operation_strategy"]
    if field not in project_fields
]

missing_target: list[str] = []
duplicate_target: list[dict[str, object]] = []
matched_project_rows = 0
db_operation_strategy_counts: Counter[str] = Counter()
if not missing_project_fields:
    for key in payload_keys:
        if not key:
            continue
        records = Project.search([("legacy_project_id", "=", key)])
        if not records:
            missing_target.append(key)
        elif len(records) > 1:
            duplicate_target.append({"legacy_project_id": key, "ids": records[:20].mapped("id")})
        else:
            matched_project_rows += 1
            db_operation_strategy_counts[clean(records.operation_strategy) or "unspecified"] += 1

contract_linkage: dict[str, object] = {"model_present": "construction.contract" in env}  # noqa: F821
if "construction.contract" in env:  # noqa: F821
    Contract = env["construction.contract"].sudo()  # noqa: F821
    contract_fields = set(Contract._fields)
    required_contract_fields = {"legacy_project_id", "project_id", "legacy_income_surface_visible"}
    missing_contract_fields = sorted(required_contract_fields - contract_fields)
    contract_linkage["missing_fields"] = missing_contract_fields
    if not missing_contract_fields:
        visible_keys = sorted(
            clean(row.get("legacy_project_id"))
            for row in rows
            if clean(row.get("replay_source_lane")) == "contract_visible_project_anchor"
        )
        visible_contracts = Contract.search(
            [
                ("legacy_project_id", "in", visible_keys),
                ("legacy_income_surface_visible", "=", True),
            ]
        )
        linked_visible_contracts = visible_contracts.filtered(lambda rec: bool(rec.project_id))
        unresolved_contracts = visible_contracts.filtered(lambda rec: not rec.project_id)
        contract_linkage.update(
            {
                "contract_visible_project_anchor_keys": len(visible_keys),
                "visible_contract_rows": len(visible_contracts),
                "linked_visible_contract_rows": len(linked_visible_contracts),
                "unlinked_visible_contract_rows": len(unresolved_contracts),
                "unlinked_samples": [
                    {"id": rec.id, "legacy_contract_id": rec.legacy_contract_id or "", "legacy_project_id": rec.legacy_project_id or ""}
                    for rec in unresolved_contracts[:20]
                ],
            }
        )

errors: list[dict[str, object]] = []
if len(rows) != expected_rows:
    errors.append({"error": "unexpected_payload_row_count", "actual": len(rows), "expected": expected_rows})
if missing_payload_key_rows:
    errors.append({"error": "missing_payload_legacy_project_id", "lines": missing_payload_key_rows[:20]})
if duplicate_payload:
    errors.append({"error": "duplicate_payload_identity", "samples": duplicate_payload[:20]})
if missing_project_fields:
    errors.append({"error": "missing_project_fields", "fields": missing_project_fields})
if missing_target:
    errors.append({"error": "missing_target_identity", "samples": missing_target[:20]})
if duplicate_target:
    errors.append({"error": "duplicate_target_identity", "samples": duplicate_target[:20]})
if matched_project_rows != expected_rows:
    errors.append({"error": "unexpected_matched_project_rows", "actual": matched_project_rows, "expected": expected_rows})
if dict(sorted(db_operation_strategy_counts.items())) != dict(sorted(model_operation_strategy_counts.items())):
    errors.append(
        {
            "error": "operation_strategy_model_distribution_mismatch",
            "actual": dict(sorted(db_operation_strategy_counts.items())),
            "expected": dict(sorted(model_operation_strategy_counts.items())),
        }
    )
if contract_linkage.get("unlinked_visible_contract_rows", 0):
    errors.append(
        {
            "error": "visible_contract_project_link_missing",
            "unlinked_visible_contract_rows": contract_linkage["unlinked_visible_contract_rows"],
        }
    )

status = "PASS" if not errors else "FAIL"
result = {
    "status": status,
    "mode": "fresh_db_project_master_replay_postcheck",
    "database": env.cr.dbname,  # noqa: F821
    "db_writes": 0,
    "payload_rows": len(rows),
    "expected_rows": expected_rows,
    "matched_project_rows": matched_project_rows,
    "duplicate_payload_identities": duplicate_payload,
    "duplicate_target_identities": duplicate_target,
    "missing_target_identities": missing_target,
    "missing_payload_key_rows": missing_payload_key_rows,
    "source_lane_counts": dict(sorted(source_lane_counts.items())),
    "operation_strategy_counts": {
        "payload_raw": dict(sorted(operation_strategy_counts.items())),
        "payload_model_normalized": dict(sorted(model_operation_strategy_counts.items())),
        "database": dict(sorted(db_operation_strategy_counts.items())),
        "unspecified_default": operation_strategy_default,
    },
    "contract_visible_project_anchor_linkage": contract_linkage,
    "errors": errors,
    "payload_csv": str(PAYLOAD_CSV),
    "write_result_json": str(WRITE_JSON),
    "decision": "project_master_replay_acceptance_passed" if status == "PASS" else "STOP_REVIEW_REQUIRED",
}
write_json(OUTPUT_JSON, result)
write_report(result)
print(
    "FRESH_DB_PROJECT_MASTER_REPLAY_POSTCHECK="
    + json.dumps(
        {
            "status": status,
            "database": env.cr.dbname,  # noqa: F821
            "payload_rows": len(rows),
            "expected_rows": expected_rows,
            "matched_project_rows": matched_project_rows,
            "visible_contract_unlinked": contract_linkage.get("unlinked_visible_contract_rows"),
            "db_writes": 0,
        },
        ensure_ascii=False,
        sort_keys=True,
    )
)
