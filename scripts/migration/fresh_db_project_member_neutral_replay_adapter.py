#!/usr/bin/env python3
"""Build fresh DB replay payload for project-member neutral staging rows."""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path


REPO_ROOT = Path.cwd()
PROJECT_ANCHOR_CSV = REPO_ROOT / "artifacts/migration/fresh_db_project_anchor_replay_rollback_targets_v1.csv"
RAW_PROJECT_MEMBER_CSV = REPO_ROOT / "tmp/raw/project_member/project_member.csv"
FIRST34_JSON = REPO_ROOT / "artifacts/migration/project_member_neutral_34_write_result_v1.json"
ROLLBACK_GLOB = "artifacts/migration/project_member_duplicate_relation_*_rollback_targets_v1.csv"
OUTPUT_JSON = REPO_ROOT / "artifacts/migration/fresh_db_project_member_neutral_replay_adapter_result_v1.json"
OUTPUT_CSV = REPO_ROOT / "artifacts/migration/fresh_db_project_member_neutral_replay_payload_v1.csv"
OUTPUT_REPORT = REPO_ROOT / "docs/migration_alignment/fresh_db_project_member_neutral_replay_adapter_report_v1.md"
EXPECTED_ROWS = 7389
PAYLOAD_FIELDS = [
    "legacy_member_id",
    "legacy_project_id",
    "legacy_user_ref",
    "fresh_project_id",
    "target_user_id",
    "role_fact_status",
    "import_batch",
    "evidence",
    "notes",
    "active",
    "idempotency_key",
    "replay_action",
]


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


def project_anchor_index() -> dict[str, dict[str, str]]:
    rows = read_csv(PROJECT_ANCHOR_CSV)
    return {
        clean(row.get("legacy_project_id")): {
            "fresh_project_id": clean(row.get("id")),
            "project_name": clean(row.get("name")),
        }
        for row in rows
        if clean(row.get("legacy_project_id"))
    }


def raw_member_index() -> dict[str, dict[str, str]]:
    rows = read_csv(RAW_PROJECT_MEMBER_CSV)
    return {
        clean(row.get("ID")): {
            "legacy_project_id": clean(row.get("XMID")),
            "legacy_user_ref": clean(row.get("USERID")),
        }
        for row in rows
        if clean(row.get("ID"))
    }


def completed_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    first = json.loads(FIRST34_JSON.read_text(encoding="utf-8"))
    for row in first.get("created_rows", []):
        rows.append(
            {
                "run_id": clean(row.get("import_batch")),
                "legacy_member_id": clean(row.get("legacy_member_id")),
                "old_project_id": clean(row.get("project_id")),
                "target_user_id": clean(row.get("user_id")),
                "role_fact_status": clean(row.get("role_fact_status")),
                "evidence": str(FIRST34_JSON.relative_to(REPO_ROOT)),
            }
        )
    for path in sorted(REPO_ROOT.glob(ROLLBACK_GLOB)):
        for row in read_csv(path):
            rows.append(
                {
                    "run_id": clean(row.get("run_id")),
                    "legacy_member_id": clean(row.get("legacy_member_id")),
                    "old_project_id": clean(row.get("project_id")),
                    "target_user_id": clean(row.get("user_id")),
                    "role_fact_status": clean(row.get("role_fact_status")),
                    "evidence": str(path.relative_to(REPO_ROOT)),
                }
            )
    return rows


def write_report(payload: dict[str, object]) -> None:
    text = f"""# Fresh DB Project Member Neutral Replay Adapter Report V1

Status: {payload["status"]}

Task: `ITER-2026-04-15-FRESH-DB-PROJECT-MEMBER-NEUTRAL-ADAPTER`

## Scope

Build a no-DB replay payload for completed `sc.project.member.staging` neutral
carrier rows. This batch does not create database records and does not promote
project responsibility or permission facts.

## Result

- completed source rows: `{payload["completed_source_rows"]}`
- replay payload rows: `{payload["replay_payload_rows"]}`
- duplicate replay identities: `{payload["duplicate_replay_identities"]}`
- missing raw member rows: `{payload["missing_raw_member_rows"]}`
- missing fresh project anchors: `{payload["missing_fresh_project_anchors"]}`
- DB writes: `0`

## Decision

`{payload["decision"]}`

## Next

{payload["next_step"]}
"""
    OUTPUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_REPORT.write_text(text, encoding="utf-8")


def main() -> int:
    project_index = project_anchor_index()
    member_index = raw_member_index()
    source_rows = completed_rows()
    payload_rows: list[dict[str, object]] = []
    missing_raw: list[str] = []
    missing_project: list[dict[str, str]] = []
    for row in source_rows:
        legacy_member_id = clean(row.get("legacy_member_id"))
        raw = member_index.get(legacy_member_id)
        if not raw:
            missing_raw.append(legacy_member_id)
            continue
        legacy_project_id = clean(raw.get("legacy_project_id"))
        project = project_index.get(legacy_project_id)
        if not project:
            missing_project.append({"legacy_member_id": legacy_member_id, "legacy_project_id": legacy_project_id})
            continue
        payload_rows.append(
            {
                "legacy_member_id": legacy_member_id,
                "legacy_project_id": legacy_project_id,
                "legacy_user_ref": clean(raw.get("legacy_user_ref")),
                "fresh_project_id": clean(project.get("fresh_project_id")),
                "target_user_id": clean(row.get("target_user_id")),
                "role_fact_status": clean(row.get("role_fact_status")) or "missing",
                "import_batch": clean(row.get("run_id")),
                "evidence": clean(row.get("evidence")),
                "notes": "Fresh replay of neutral carrier only; not responsibility, permission, or workflow truth.",
                "active": "1",
                "idempotency_key": f"{legacy_member_id}::{clean(row.get('run_id'))}",
                "replay_action": "create_if_missing",
            }
        )

    keys = [clean(row["idempotency_key"]) for row in payload_rows]
    duplicate_keys = [key for key, count in Counter(keys).items() if key and count > 1]
    status = (
        "PASS"
        if len(source_rows) == EXPECTED_ROWS
        and len(payload_rows) == EXPECTED_ROWS
        and not duplicate_keys
        and not missing_raw
        and not missing_project
        else "FAIL"
    )
    result = {
        "status": status,
        "mode": "fresh_db_project_member_neutral_replay_adapter",
        "db_writes": 0,
        "database_operations": 0,
        "completed_source_rows": len(source_rows),
        "replay_payload_rows": len(payload_rows),
        "duplicate_replay_identities": len(duplicate_keys),
        "duplicate_samples": duplicate_keys[:20],
        "missing_raw_member_rows": len(missing_raw),
        "missing_raw_member_samples": missing_raw[:20],
        "missing_fresh_project_anchors": len(missing_project),
        "missing_fresh_project_samples": missing_project[:20],
        "row_artifact": str(OUTPUT_CSV),
        "decision": "project_member_neutral_replay_payload_ready" if status == "PASS" else "STOP_REVIEW_REQUIRED",
        "next_step": "precheck and write project-member neutral payload into sc_migration_fresh",
    }
    write_csv(OUTPUT_CSV, PAYLOAD_FIELDS, sorted(payload_rows, key=lambda item: clean(item["idempotency_key"])))
    write_json(OUTPUT_JSON, result)
    write_report(result)
    print(
        "FRESH_DB_PROJECT_MEMBER_NEUTRAL_REPLAY_ADAPTER="
        + json.dumps(
            {
                "status": status,
                "completed_source_rows": len(source_rows),
                "replay_payload_rows": len(payload_rows),
                "duplicate_replay_identities": len(duplicate_keys),
                "missing_fresh_project_anchors": len(missing_project),
                "db_writes": 0,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
