"""Replay SCBS BASE_SYSTEM project links without the legacy database.

Some SCBS rows have no source project name, but were confirmed as project-level
facts by carrying the BASE_SYSTEM business entity as an "unspecified project"
carrier. This script consumes the exported replay artifact and restores those
stored project links in a fresh Odoo database.

Dry-run by default. Set APPLY=1 to write.
"""

from __future__ import annotations

import csv
import json
import os
from pathlib import Path


SOURCE_CSV = "scbs_base_system_project_links_v1.csv"


def repo_root() -> Path:
    env_root = os.getenv("MIGRATION_REPO_ROOT")
    candidates = [Path(env_root)] if env_root else []
    candidates.extend([Path("/mnt"), Path.cwd()])
    for candidate in candidates:
        if (candidate / "artifacts/migration" / SOURCE_CSV).exists():
            return candidate
    return Path.cwd()


def artifact_root(root: Path) -> Path:
    env_root = os.getenv("MIGRATION_ARTIFACT_ROOT")
    candidates = [Path(env_root)] if env_root else []
    candidates.extend([root / "artifacts/migration", Path("/mnt/artifacts/migration"), Path("/tmp")])
    for candidate in candidates:
        try:
            candidate.mkdir(parents=True, exist_ok=True)
            probe = candidate / ".write_probe"
            probe.write_text("ok\n", encoding="utf-8")
            probe.unlink()
            return candidate
        except Exception:
            continue
    return Path("/tmp")


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def project_values(row: dict[str, str]) -> dict[str, object]:
    entity_name = (row.get("project_name") or "").strip()
    other_system_id = (row.get("other_system_id") or "").strip()
    return {
        "name": f"SCBS未指定项目 - {entity_name}",
        "company_id": env.company.id,  # noqa: F821
        "legacy_project_id": other_system_id,
        "legacy_company_name": "SCBS",
        "other_system_id": other_system_id,
        "other_system_code": "SCBS",
        "operation_strategy": "direct",
        "project_environment": "legacy_scbs_base_system_unspecified_project",
        "description": "\n".join(
            [
                "SCBS BASE_SYSTEM经营主体项目口径承接。",
                "源事实缺少工程名，但业务确认应进入项目级管控。",
                f"business_entity_name={entity_name}",
                "batch=scbs_base_system_project_link_import_v1",
            ]
        ),
    }


def main() -> None:
    apply = os.getenv("APPLY") == "1"
    root = repo_root()
    artifacts = artifact_root(root)
    source_csv = root / "artifacts/migration" / SOURCE_CSV
    result_json = artifacts / "scbs_base_system_project_link_import_result_v1.json"
    rows = read_rows(source_csv)

    Project = env["project.project"].sudo().with_context(active_test=False)  # noqa: F821
    Staging = env["sc.legacy.scbs.fact.staging"].sudo().with_context(active_test=False)  # noqa: F821
    project_by_key = {}
    created_projects = 0
    linked_existing_projects = 0
    updated_staging_rows = 0
    missing_staging_rows = 0

    for row in rows:
        other_system_id = (row.get("other_system_id") or "").strip()
        if not other_system_id:
            continue
        project = project_by_key.get(other_system_id)
        if project is None:
            project = Project.search([("other_system_id", "=", other_system_id)], limit=1)
            if project:
                linked_existing_projects += 1
            elif apply:
                project = Project.create(project_values(row))
                created_projects += 1
            else:
                project = Project.browse()
            project_by_key[other_system_id] = project
        facts = Staging.search(
            [
                ("import_batch", "=", "scbs_fact_staging_v1"),
                ("source_table", "=", (row.get("source_table") or "").strip()),
                ("legacy_record_id", "=", (row.get("legacy_record_id") or "").strip()),
            ]
        )
        if not facts:
            missing_staging_rows += 1
            continue
        if apply and project:
            env.cr.execute(  # noqa: F821
                "UPDATE sc_legacy_scbs_fact_staging SET project_id = %s WHERE id = ANY(%s)",
                [project.id, facts.ids],
            )
        updated_staging_rows += len(facts)

    if apply:
        env.cr.commit()  # noqa: F821

    payload = {
        "status": "APPLIED" if apply else "DRY_RUN",
        "database": env.cr.dbname,  # noqa: F821
        "source_csv": str(source_csv),
        "source_rows": len(rows),
        "project_keys": len(project_by_key),
        "created_projects": created_projects,
        "linked_existing_projects": linked_existing_projects,
        "updated_staging_rows": updated_staging_rows,
        "missing_staging_rows": missing_staging_rows,
        "business_policy": "replay_base_system_unspecified_project_links_without_legacy_database",
    }
    write_json(result_json, payload)
    print("SCBS_BASE_SYSTEM_PROJECT_LINK_IMPORT=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))


main()
