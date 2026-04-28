#!/usr/bin/env python3
"""Build project lifecycle continuity payload from frozen snapshot evidence."""

from __future__ import annotations

import csv
import json
import os
from pathlib import Path


def repo_root() -> Path:
    env_root = os.getenv("MIGRATION_REPO_ROOT")
    if env_root:
        return Path(env_root)
    for candidate in (Path("/mnt"), Path.cwd()):
        if (candidate / "artifacts/migration/project_continuity_downstream_fact_state_sync_snapshot_v1.csv").exists():
            return candidate
    return Path.cwd()


REPO_ROOT = repo_root()
SNAPSHOT_CSV = REPO_ROOT / "artifacts/migration/project_continuity_downstream_fact_state_sync_snapshot_v1.csv"
OUTPUT_JSON = REPO_ROOT / "artifacts/migration/history_project_lifecycle_continuity_adapter_result_v1.json"
OUTPUT_CSV = REPO_ROOT / "artifacts/migration/history_project_lifecycle_continuity_payload_v1.csv"
OUTPUT_REPORT = REPO_ROOT / "docs/migration_alignment/history_project_lifecycle_continuity_report_v1.md"


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_report(payload: dict[str, object]) -> None:
    text = f"""# History Project Lifecycle Continuity Report v1

Status: `{payload["status"]}`

## Source

- snapshot csv: `{payload["snapshot_csv"]}`
- approved legacy project rows: `{payload["payload_rows"]}`

## Target

- `lifecycle_state = in_progress`
- `phase_key = execution`
- `stage_xmlid = smart_construction_core.project_stage_running`

## Decision

`{payload["decision"]}`
"""
    OUTPUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_REPORT.write_text(text, encoding="utf-8")


def main() -> int:
    rows = read_rows(SNAPSHOT_CSV)
    payload_rows: list[dict[str, str]] = []
    seen: set[str] = set()
    for row in rows:
        legacy_project_id = (row.get("legacy_project_id") or "").strip()
        if not legacy_project_id or legacy_project_id in seen:
            continue
        seen.add(legacy_project_id)
        payload_rows.append(
            {
                "legacy_project_id": legacy_project_id,
                "target_lifecycle_state": "in_progress",
                "target_phase_key": "execution",
                "target_stage_xmlid": "smart_construction_core.project_stage_running",
            }
        )

    payload = {
        "status": "PASS",
        "mode": "history_project_lifecycle_continuity_adapter",
        "snapshot_csv": str(SNAPSHOT_CSV),
        "payload_csv": str(OUTPUT_CSV),
        "payload_rows": len(payload_rows),
        "db_writes": 0,
        "decision": "project_lifecycle_continuity_payload_ready",
    }
    write_csv(
        OUTPUT_CSV,
        ["legacy_project_id", "target_lifecycle_state", "target_phase_key", "target_stage_xmlid"],
        payload_rows,
    )
    write_json(OUTPUT_JSON, payload)
    write_report(payload)
    print("HISTORY_PROJECT_LIFECYCLE_CONTINUITY_ADAPTER=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
