#!/usr/bin/env python3
"""Build a no-DB fresh-db replay payload for completed project anchor writes."""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path


REPO_ROOT = Path.cwd()
PROJECT_CSV = REPO_ROOT / "tmp/raw/project/project.csv"
OUTPUT_JSON = REPO_ROOT / "artifacts/migration/fresh_db_project_anchor_replay_adapter_result_v1.json"
OUTPUT_CSV = REPO_ROOT / "artifacts/migration/fresh_db_project_anchor_replay_payload_v1.csv"
OUTPUT_REPORT = REPO_ROOT / "docs/migration_alignment/fresh_db_project_anchor_replay_adapter_report_v1.md"

WRITE_RESULTS = [
    "artifacts/migration/project_create_only_write_result_v1.json",
    "artifacts/migration/project_create_only_expand_write_result_v1.json",
    "artifacts/migration/project_v2_100_write_result.json",
    "artifacts/migration/project_v3_100_write_result.json",
    "artifacts/migration/project_v4_200_write_result.json",
    "artifacts/migration/project_v5_200_write_result.json",
    "artifacts/migration/project_remaining_25_write_result.json",
]

PAYLOAD_FIELDS = [
    "legacy_project_id",
    "legacy_parent_id",
    "name",
    "short_name",
    "project_environment",
    "legacy_company_id",
    "legacy_company_name",
    "legacy_specialty_type_id",
    "specialty_type_name",
    "legacy_price_method",
    "business_nature",
    "detail_address",
    "project_profile",
    "project_area",
    "legacy_is_shared_base",
    "legacy_sort",
    "legacy_attachment_ref",
    "project_overview",
    "legacy_project_nature",
    "legacy_is_material_library",
    "other_system_id",
    "other_system_code",
    "legacy_stage_id",
    "legacy_stage_name",
    "legacy_region_id",
    "legacy_region_name",
    "legacy_state",
    "legacy_deleted_flag",
    "legacy_project_manager_name",
    "legacy_technical_responsibility_name",
    "current_db_project_id",
    "evidence_file",
    "idempotency_key",
    "replay_action",
]


def clean(value: object) -> str:
    return "" if value is None else str(value).strip()


def is_deleted_flag(value: object) -> bool:
    normalized = clean(value).lower()
    return bool(normalized) and normalized not in {"0", "false", "no", "n"}


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


def project_source_index() -> dict[str, dict[str, str]]:
    index: dict[str, dict[str, str]] = {}
    for row in read_csv(PROJECT_CSV):
        legacy_project_id = clean(row.get("ID"))
        if not legacy_project_id:
            continue
        index[legacy_project_id] = {
            "legacy_project_id": legacy_project_id,
            "legacy_parent_id": clean(row.get("PID")),
            "name": clean(row.get("XMMC")),
            "short_name": clean(row.get("SHORT_NAME")),
            "project_environment": clean(row.get("PROJECT_ENV")),
            "legacy_company_id": clean(row.get("COMPANYID")),
            "legacy_company_name": clean(row.get("COMPANYNAME")),
            "legacy_specialty_type_id": clean(row.get("SPECIALTY_TYPE_ID")),
            "specialty_type_name": clean(row.get("SPECIALTY_TYPE_NAME")),
            "legacy_price_method": clean(row.get("PRICE_METHOD")),
            "business_nature": clean(row.get("NATURE")),
            "detail_address": clean(row.get("DETAIL_ADDRESS")),
            "project_profile": clean(row.get("PROFILE")),
            "project_area": clean(row.get("AREA")),
            "legacy_is_shared_base": clean(row.get("IS_SHARED_BASE")),
            "legacy_sort": clean(row.get("SORT")),
            "legacy_attachment_ref": clean(row.get("FJ")),
            "project_overview": clean(row.get("PROJECTOVERVIEW")),
            "legacy_project_nature": clean(row.get("PROJECT_NATURE")),
            "legacy_is_material_library": clean(row.get("IS_MACHINTERIAL_LIBRARY")),
            "other_system_id": clean(row.get("OTHER_SYSTEM_ID")),
            "other_system_code": clean(row.get("OTHER_SYSTEM_CODE")),
            "legacy_stage_id": clean(row.get("XMJDID")),
            "legacy_stage_name": clean(row.get("XMJD")),
            "legacy_region_id": clean(row.get("SSDQID")),
            "legacy_region_name": clean(row.get("SSDQ")),
            "legacy_state": clean(row.get("STATE")),
            "legacy_deleted_flag": clean(row.get("DEL")),
            "legacy_project_manager_name": clean(row.get("PROJECTMANAGER")),
            "legacy_technical_responsibility_name": clean(row.get("TECHNICALRESPONSIBILITY")),
        }
    return index


def load_created_rows() -> tuple[list[dict[str, object]], list[str]]:
    rows: list[dict[str, object]] = []
    missing_files: list[str] = []
    for rel_path in WRITE_RESULTS:
        path = REPO_ROOT / rel_path
        if not path.exists():
            missing_files.append(rel_path)
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        for row in payload.get("created", []):
            rows.append(
                {
                    "source_file": rel_path,
                    "legacy_project_id": clean(row.get("legacy_project_id")),
                    "name": clean(row.get("name")),
                    "current_db_project_id": clean(row.get("id")),
                }
            )
    return rows, missing_files


def write_report(payload: dict[str, object]) -> None:
    text = f"""# Fresh DB Project Anchor Replay Adapter Report v1

Status: {payload["status"]}

Task: `ITER-2026-04-15-FRESH-DB-REPLAY-PROJECT-ANCHOR-ADAPTER`

## Scope

Build a no-DB consolidated replay payload for completed project anchor
create-only writes. This batch does not execute project write scripts and does
not touch a database.

## Result

- source write result files: `{payload["write_result_files"]}`
- created evidence rows: `{payload["created_evidence_rows"]}`
- replay payload rows: `{payload["replay_payload_rows"]}`
- duplicate replay identities: `{payload["duplicate_replay_identities"]}`
- raw source misses: `{payload["raw_source_misses"]}`
- deleted source rows in payload: `{payload["deleted_source_rows"]}`
- DB writes: `0`

## Stage Counts

```json
{json.dumps(payload["stage_counts"], ensure_ascii=False, indent=2)}
```

## Decision

`{payload["decision"]}`

## Next

{payload["next_step"]}
"""
    OUTPUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_REPORT.write_text(text, encoding="utf-8")


def main() -> int:
    source_index = project_source_index()
    created_rows, missing_files = load_created_rows()
    seen: dict[str, dict[str, object]] = {}
    duplicates: list[dict[str, object]] = []
    raw_misses: list[dict[str, str]] = []
    stage_counts: Counter[str] = Counter()
    deleted_source_rows = 0

    for row in created_rows:
        legacy_project_id = clean(row["legacy_project_id"])
        if not legacy_project_id:
            raw_misses.append({"legacy_project_id": legacy_project_id, "reason": "missing_identity"})
            continue
        if legacy_project_id in seen:
            duplicates.append({"legacy_project_id": legacy_project_id})
            continue
        source = source_index.get(legacy_project_id)
        if not source:
            raw_misses.append({"legacy_project_id": legacy_project_id, "reason": "missing_raw_source"})
            source = {
                field: ""
                for field in PAYLOAD_FIELDS
                if field
                not in {
                    "current_db_project_id",
                    "evidence_file",
                    "idempotency_key",
                    "replay_action",
                }
            }
            source["legacy_project_id"] = legacy_project_id
            source["name"] = clean(row["name"])
        stage_counts[source.get("legacy_stage_name", "") or "unknown"] += 1
        if is_deleted_flag(source.get("legacy_deleted_flag")):
            deleted_source_rows += 1
        payload_row = dict(source)
        payload_row.update(
            {
                "current_db_project_id": clean(row["current_db_project_id"]),
                "evidence_file": row["source_file"],
                "idempotency_key": f"project::{legacy_project_id}",
                "replay_action": "create_if_missing",
            }
        )
        seen[legacy_project_id] = payload_row

    payload_rows = sorted(seen.values(), key=lambda item: clean(item["legacy_project_id"]))
    status = "PASS" if not missing_files and not duplicates and not raw_misses else "FAIL"
    payload = {
        "status": status,
        "mode": "fresh_db_project_anchor_replay_adapter",
        "db_writes": 0,
        "database_operations": 0,
        "write_scripts_executed": 0,
        "write_result_files": len(WRITE_RESULTS),
        "missing_write_result_files": missing_files,
        "created_evidence_rows": len(created_rows),
        "replay_payload_rows": len(payload_rows),
        "duplicate_replay_identities": len(duplicates),
        "duplicate_samples": duplicates[:20],
        "raw_source_misses": len(raw_misses),
        "raw_source_miss_samples": raw_misses[:20],
        "deleted_source_rows": deleted_source_rows,
        "stage_counts": dict(sorted(stage_counts.items())),
        "row_artifact": str(OUTPUT_CSV),
        "decision": "project_anchor_replay_payload_ready" if status == "PASS" else "STOP_REVIEW_REQUIRED",
        "next_step": "implement contract partner 12 anchor replay adapter before fresh database operation",
    }
    write_csv(OUTPUT_CSV, PAYLOAD_FIELDS, payload_rows)
    write_json(OUTPUT_JSON, payload)
    write_report(payload)
    print(
        "FRESH_DB_PROJECT_ANCHOR_REPLAY_ADAPTER="
        + json.dumps(
            {
                "status": status,
                "created_evidence_rows": len(created_rows),
                "replay_payload_rows": len(payload_rows),
                "duplicates": len(duplicates),
                "raw_source_misses": len(raw_misses),
                "db_writes": 0,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
