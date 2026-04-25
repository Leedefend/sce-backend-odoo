#!/usr/bin/env python3
"""Restore approved historical projects into execution lifecycle."""

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
        if (candidate / "artifacts/migration/history_project_lifecycle_continuity_payload_v1.csv").exists():
            return candidate
    return Path.cwd()


REPO_ROOT = repo_root()
ARTIFACT_ROOT = REPO_ROOT / "artifacts/migration"
INPUT_CSV = REPO_ROOT / "artifacts/migration/history_project_lifecycle_continuity_payload_v1.csv"
OUTPUT_JSON = ARTIFACT_ROOT / "history_project_lifecycle_continuity_write_result_v1.json"


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_json(path: Path, payload: dict[str, object]) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    except OSError:
        # Result persistence is best-effort in shell-exec context; stdout remains the source of truth.
        pass


rows = read_rows(INPUT_CSV)
Project = env["project.project"].sudo()  # noqa: F821
target_stage = env.ref("smart_construction_core.project_stage_running")  # noqa: F821

legacy_ids = [row["legacy_project_id"] for row in rows if row.get("legacy_project_id")]
projects = Project.search([("legacy_project_id", "in", legacy_ids)])
project_map = {project.legacy_project_id: project for project in projects}

update_ids = []
already_synced = 0
conflict_rows = []
missing_rows = []

for row in rows:
    legacy_project_id = row.get("legacy_project_id") or ""
    project = project_map.get(legacy_project_id)
    if not project:
        missing_rows.append(legacy_project_id)
        continue
    if (
        project.lifecycle_state == "in_progress"
        and project.phase_key == "execution"
        and project.stage_id.id == target_stage.id
    ):
        already_synced += 1
        continue
    if project.lifecycle_state != "draft":
        conflict_rows.append(
            {
                "legacy_project_id": legacy_project_id,
                "project_id": project.id,
                "current_lifecycle_state": project.lifecycle_state,
            }
        )
        continue
    update_ids.append(project.id)

if update_ids:
    env.cr.execute(  # noqa: F821
        """
        UPDATE project_project
           SET lifecycle_state = %s,
               phase_key = %s,
               stage_id = %s,
               write_uid = %s,
               write_date = NOW()
         WHERE id = ANY(%s)
        """,
        ["in_progress", "execution", target_stage.id, env.user.id, update_ids],  # noqa: F821
    )
    env.cr.commit()  # noqa: F821
else:
    env.cr.rollback()  # noqa: F821

result = {
    "status": "PASS" if not missing_rows else "FAIL",
    "mode": "history_project_lifecycle_continuity_write",
    "database": env.cr.dbname,  # noqa: F821
    "input_rows": len(rows),
    "updated_rows": len(update_ids),
    "already_synced": already_synced,
    "conflict_rows": len(conflict_rows),
    "missing_rows": len(missing_rows),
    "db_writes": len(update_ids),
    "decision": "project_lifecycle_continuity_applied" if not missing_rows else "STOP_REVIEW_REQUIRED",
}
write_json(OUTPUT_JSON, result)
print("HISTORY_PROJECT_LIFECYCLE_CONTINUITY_WRITE=" + json.dumps(result, ensure_ascii=False, sort_keys=True))
