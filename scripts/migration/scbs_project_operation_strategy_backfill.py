"""Backfill project operation strategy for SCBS integration.

Business policy:

- Existing new-system projects are joint-operation projects.
- SCBS imported project facts and SCBS project buckets are direct-operation
  projects.

Default mode is dry-run. Set APPLY=1 to write values.
"""

from __future__ import annotations

import csv
import json
import os
from pathlib import Path


def artifact_root() -> Path:
    env_root = os.getenv("MIGRATION_ARTIFACT_ROOT")
    candidates = [Path(env_root)] if env_root else []
    candidates.extend([Path.cwd() / "artifacts/migration", Path("/mnt/artifacts/migration"), Path("/tmp")])
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return Path("artifacts/migration")


def fetch_dicts(query: str, params: tuple = ()) -> list[dict[str, object]]:
    env.cr.execute(query, params)  # noqa: F821
    names = [desc[0] for desc in env.cr.description]  # noqa: F821
    return [dict(zip(names, row)) for row in env.cr.fetchall()]  # noqa: F821


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def scbs_domain() -> list:
    return [
        "|",
        "|",
        "|",
        ("other_system_code", "=", "SCBS"),
        ("other_system_id", "=like", "SCBS:%"),
        ("legacy_project_id", "=like", "SCBS_BUCKET:%"),
        ("project_environment", "=", "legacy_scbs_project_fact"),
    ]


def main() -> None:
    apply = os.getenv("APPLY") == "1"
    artifacts = artifact_root()
    plan_csv = artifacts / "scbs_project_operation_strategy_backfill_plan_v1.csv"
    result_json = artifacts / "scbs_project_operation_strategy_backfill_result_v1.json"

    Project = env["project.project"].sudo().with_context(active_test=False)  # noqa: F821
    scbs_projects = Project.search(scbs_domain(), order="id")
    existing_projects = Project.search([("id", "not in", scbs_projects.ids)], order="id")

    plan_rows: list[dict[str, object]] = []
    for strategy, records, reason in [
        ("direct", scbs_projects, "scbs_imported_project_or_bucket"),
        ("joint", existing_projects, "existing_new_system_project"),
    ]:
        for project in records:
            current = project.operation_strategy or ""
            action = "keep" if current == strategy else "set"
            plan_rows.append(
                {
                    "project_id": project.id,
                    "name": project.display_name,
                    "project_code": project.project_code or "",
                    "current_operation_strategy": current,
                    "target_operation_strategy": strategy,
                    "action": action,
                    "reason": reason,
                    "other_system_id": project.other_system_id or "",
                    "legacy_project_id": project.legacy_project_id or "",
                    "project_environment": project.project_environment or "",
                }
            )
            if apply and action == "set":
                project.operation_strategy = strategy

    if apply:
        env.cr.commit()  # noqa: F821

    write_csv(
        plan_csv,
        plan_rows,
        [
            "project_id",
            "name",
            "project_code",
            "current_operation_strategy",
            "target_operation_strategy",
            "action",
            "reason",
            "other_system_id",
            "legacy_project_id",
            "project_environment",
        ],
    )
    payload = {
        "status": "APPLIED" if apply else "DRY_RUN",
        "database": env.cr.dbname,  # noqa: F821
        "plan_csv": str(plan_csv),
        "scbs_direct_projects": len(scbs_projects),
        "existing_joint_projects": len(existing_projects),
        "would_update": sum(1 for row in plan_rows if row["action"] == "set") if not apply else 0,
        "updated": sum(1 for row in plan_rows if row["action"] == "set") if apply else 0,
    }
    write_json(result_json, payload)
    print("SCBS_PROJECT_OPERATION_STRATEGY_BACKFILL=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))


main()
