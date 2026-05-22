#!/usr/bin/env python3
"""Backfill formal project fields from migration continuity carriers.

Default mode is dry-run. Set MIGRATION_WRITE_MODE=write to commit.

Policy:
- Never overwrite user-maintained formal fields.
- Char fields are copied only when the formal field is empty.
- Relation fields are filled only when the migration text resolves to one
  unique formal record; unresolved or ambiguous values are reported, not
  guessed.
"""

from __future__ import annotations

import csv
import json
import os
import re
from collections import Counter
from pathlib import Path


def repo_root() -> Path:
    env_root = os.getenv("MIGRATION_REPO_ROOT")
    if env_root:
        return Path(env_root)
    for candidate in (Path("/mnt"), Path.cwd()):
        if (candidate / "addons/smart_construction_core").exists():
            return candidate
    return Path.cwd()


REPO_ROOT = repo_root()


def artifact_root() -> Path:
    candidates = []
    env_root = os.getenv("MIGRATION_ARTIFACT_ROOT")
    if env_root:
        candidates.append(Path(env_root))
    candidates.extend(
        [
            REPO_ROOT / "artifacts/migration/project_migration_field_continuity_backfill_v1",
            Path("/mnt/artifacts/migration/project_migration_field_continuity_backfill_v1"),
            Path(f"/tmp/history_continuity/{env.cr.dbname}/project_migration_field_continuity_backfill_v1"),  # noqa: F821
        ]
    )
    for candidate in candidates:
        try:
            candidate.mkdir(parents=True, exist_ok=True)
            return candidate
        except Exception:
            continue
    raise RuntimeError("no writable artifact root for project migration field continuity backfill")


ARTIFACT_ROOT = artifact_root()
MODE = os.getenv("MIGRATION_WRITE_MODE", os.getenv("APPLY") == "1" and "write" or "dry-run")
ALLOWLIST = {
    item.strip()
    for item in os.getenv("MIGRATION_REPLAY_DB_ALLOWLIST", "sc_demo,sc_prod_sim,sc_migration_fresh").split(",")
    if item.strip()
}

CHAR_BACKFILLS = (
    ("owner_contact", ("legacy_owner_contact",), "project_owner_contact_from_migration_text"),
    ("location", ("detail_address", "legacy_region_name"), "project_location_from_address_or_region"),
)
RELATION_BACKFILLS = (
    ("owner_id", "res.partner", "legacy_owner_unit", ("name",), "project_owner_from_migration_unit"),
    ("manager_id", "res.users", "legacy_project_manager_name", ("name", "login"), "project_manager_from_migration_name"),
)


def clean(value: object) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    return "" if text in {"False", "false", "None", "none", "NULL", "null"} else text


def norm(value: object) -> str:
    return re.sub(r"\s+", "", clean(value)).lower()


def artifact_path(name: str) -> Path:
    return ARTIFACT_ROOT / name


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


def candidates_by_text(model: str, fields: tuple[str, ...]) -> dict[str, list[int]]:
    Model = env[model].sudo().with_context(active_test=False)  # noqa: F821
    mapping: dict[str, list[int]] = {}
    for record in Model.search([]):
        for field in fields:
            value = norm(record[field])
            if not value:
                continue
            mapping.setdefault(value, [])
            if record.id not in mapping[value]:
                mapping[value].append(record.id)
    return mapping


def first_source_value(record, source_fields: tuple[str, ...]) -> tuple[str, str]:
    for field in source_fields:
        value = clean(record[field])
        if value:
            return field, value
    return "", ""


def main() -> None:
    db_name = env.cr.dbname  # noqa: F821
    if db_name not in ALLOWLIST:
        raise RuntimeError({"db_name_not_allowed": db_name, "allowlist": sorted(ALLOWLIST)})
    if MODE not in {"dry-run", "write"}:
        raise RuntimeError({"invalid_migration_write_mode": MODE})

    Project = env["project.project"].sudo().with_context(active_test=False)  # noqa: F821
    projects = Project.search([], order="id")
    relation_indexes = {
        (model, fields): candidates_by_text(model, fields)
        for _, model, _, fields, _ in RELATION_BACKFILLS
    }

    plan_rows: list[dict[str, object]] = []
    unresolved_rows: list[dict[str, object]] = []
    updates_by_project: dict[int, dict[str, object]] = {}
    counters: Counter[str] = Counter()

    for project in projects:
        for target, sources, reason in CHAR_BACKFILLS:
            if clean(project[target]):
                counters[f"{target}.kept_formal_nonempty"] += 1
                continue
            source_field, source_value = first_source_value(project, sources)
            if not source_value:
                counters[f"{target}.no_source"] += 1
                continue
            updates_by_project.setdefault(project.id, {})[target] = source_value
            counters[f"{target}.planned"] += 1
            plan_rows.append(
                {
                    "project_id": project.id,
                    "project_name": project.display_name,
                    "target_field": target,
                    "source_field": source_field,
                    "source_value": source_value,
                    "target_value": source_value,
                    "action": "set",
                    "reason": reason,
                }
            )

        for target, relation_model, source, match_fields, reason in RELATION_BACKFILLS:
            if project[target]:
                counters[f"{target}.kept_formal_nonempty"] += 1
                continue
            source_value = clean(project[source])
            if not source_value:
                counters[f"{target}.no_source"] += 1
                continue
            matches = relation_indexes[(relation_model, match_fields)].get(norm(source_value), [])
            if len(matches) != 1:
                issue = "no_match" if not matches else "ambiguous_match"
                counters[f"{target}.{issue}"] += 1
                unresolved_rows.append(
                    {
                        "project_id": project.id,
                        "project_name": project.display_name,
                        "target_field": target,
                        "source_field": source,
                        "source_value": source_value,
                        "issue": issue,
                        "candidate_ids": ",".join(str(item) for item in matches),
                    }
                )
                continue
            updates_by_project.setdefault(project.id, {})[target] = matches[0]
            counters[f"{target}.planned"] += 1
            plan_rows.append(
                {
                    "project_id": project.id,
                    "project_name": project.display_name,
                    "target_field": target,
                    "source_field": source,
                    "source_value": source_value,
                    "target_value": matches[0],
                    "action": "set",
                    "reason": reason,
                }
            )

    updated_projects = 0
    updated_fields = 0
    if MODE == "write":
        for project_id, values in updates_by_project.items():
            Project.browse(project_id).write(values)
            updated_projects += 1
            updated_fields += len(values)
        env.cr.commit()  # noqa: F821

    plan_csv = artifact_path("project_migration_field_continuity_backfill_plan_v1.csv")
    unresolved_csv = artifact_path("project_migration_field_continuity_backfill_unresolved_v1.csv")
    result_json = artifact_path("project_migration_field_continuity_backfill_result_v1.json")
    write_csv(
        plan_csv,
        plan_rows,
        ["project_id", "project_name", "target_field", "source_field", "source_value", "target_value", "action", "reason"],
    )
    write_csv(
        unresolved_csv,
        unresolved_rows,
        ["project_id", "project_name", "target_field", "source_field", "source_value", "issue", "candidate_ids"],
    )

    payload = {
        "status": "APPLIED" if MODE == "write" else "DRY_RUN",
        "database": db_name,
        "project_count": len(projects),
        "planned_projects": len(updates_by_project),
        "planned_fields": sum(len(values) for values in updates_by_project.values()),
        "updated_projects": updated_projects,
        "updated_fields": updated_fields,
        "unresolved_count": len(unresolved_rows),
        "counters": dict(sorted(counters.items())),
        "plan_csv": str(plan_csv),
        "unresolved_csv": str(unresolved_csv),
    }
    write_json(result_json, payload)
    print("PROJECT_MIGRATION_FIELD_CONTINUITY_BACKFILL=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))


main()
