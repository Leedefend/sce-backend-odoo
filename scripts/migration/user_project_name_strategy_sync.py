# -*- coding: utf-8 -*-
"""Apply the user-confirmed project name and operation strategy baseline.

The source CSV is a user-confirmed naming/classification list. It is not a
business-fact linkage source: this script never rewrites project_id,
legacy_project_id, or downstream contract/payment/SCBS relationships.

Default mode is dry-run. Set APPLY=1 to write exact name matches only.
"""

from __future__ import annotations

import csv
import json
import os
import re
from collections import Counter, defaultdict
from pathlib import Path


DEFAULT_SOURCE = "migration_assets/10_master/project/user_project_name_strategy_20260520.csv"
EXPECTED_COUNTS = {"direct": 41, "joint": 693}
SOURCE_TAG = "user_project_name_strategy_20260520"


def repo_root() -> Path:
    candidates = [
        Path.cwd(),
        Path("/mnt/extra-addons"),
        Path("/home/odoo/workspace/sce-backend-odoo"),
    ]
    for candidate in candidates:
        if (candidate / "addons").exists() and (candidate / "migration_assets").exists():
            return candidate
    return Path.cwd()


def artifact_root() -> Path:
    root = Path(
        os.getenv("MIGRATION_ARTIFACT_ROOT")
        or os.getenv("ARTIFACT_ROOT")
        or "/tmp/project_master_stabilization"
    )
    root.mkdir(parents=True, exist_ok=True)
    return root


def source_path() -> Path:
    raw = os.getenv("MIGRATION_USER_PROJECT_STRATEGY_CSV") or DEFAULT_SOURCE
    path = Path(raw)
    if path.is_absolute():
        return path
    if raw.startswith("migration_assets/") and Path("/mnt/migration_assets").exists():
        return Path("/mnt/migration_assets") / raw[len("migration_assets/") :]
    return repo_root() / path


def normalize_name(value: object) -> str:
    text = str(value or "").strip()
    text = re.sub(r"\s+", "", text)
    text = text.replace("（", "(").replace("）", ")")
    text = text.replace("－", "-").replace("—", "-").replace("–", "-")
    return text.rstrip(".")


def project_name(project) -> str:
    name = project.name
    if isinstance(name, dict):
        return name.get("zh_CN") or name.get("en_US") or next(iter(name.values()), "") or ""
    return str(name or "")


def load_source(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise RuntimeError(f"source csv missing: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = [dict(row) for row in csv.DictReader(handle)]

    required = {"project_name", "normalized_project_name", "operation_strategy"}
    missing = required - set(rows[0].keys() if rows else [])
    if missing:
        raise RuntimeError(f"source csv missing headers: {sorted(missing)}")
    if not rows:
        raise RuntimeError("source csv is empty")

    blank_names = [row for row in rows if not row.get("project_name")]
    if blank_names:
        raise RuntimeError(f"source csv has blank project names: {len(blank_names)}")

    duplicate_keys = [
        name for name, count in Counter(normalize_name(row["project_name"]) for row in rows).items() if count > 1
    ]
    if duplicate_keys:
        raise RuntimeError(f"source csv has duplicate normalized project names: {duplicate_keys[:20]}")

    strategy_counts = Counter(row.get("operation_strategy") for row in rows)
    if dict(strategy_counts) != EXPECTED_COUNTS:
        raise RuntimeError(f"source strategy counts mismatch: {dict(strategy_counts)} != {EXPECTED_COUNTS}")

    invalid = sorted(set(strategy_counts) - {"direct", "joint"})
    if invalid:
        raise RuntimeError(f"source csv has invalid operation_strategy values: {invalid}")

    return rows


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


def build_project_index():
    Project = env["project.project"].sudo().with_context(active_test=False)  # noqa: F821
    projects = Project.search([], order="id")
    by_name = defaultdict(lambda: Project.browse())
    for project in projects:
        by_name[normalize_name(project_name(project))] |= project
    return Project, projects, by_name


def main() -> None:
    apply = os.getenv("APPLY") == "1"
    source = source_path()
    source_rows = load_source(source)
    Project, all_projects, projects_by_name = build_project_index()

    plan_rows: list[dict[str, object]] = []
    matched_project_ids: set[int] = set()

    for row in source_rows:
        standard_name = row["project_name"].strip()
        key = row.get("normalized_project_name") or normalize_name(standard_name)
        target_strategy = row["operation_strategy"].strip()
        projects = projects_by_name.get(key, Project.browse())

        if not projects:
            plan_rows.append(
                {
                    "match_status": "missing_in_project_project",
                    "action": "manual_review",
                    "source_project_name": standard_name,
                    "source_operation_strategy": target_strategy,
                    "source_operation_mode": row.get("source_operation_mode", ""),
                    "project_id": "",
                    "current_project_name": "",
                    "current_operation_strategy": "",
                    "active": "",
                    "legacy_project_id": "",
                    "reason": "source_name_has_no_exact_project_match_no_business_relink",
                }
            )
            continue

        if len(projects) > 1:
            for project in projects:
                plan_rows.append(
                    {
                        "match_status": "duplicate_project_name",
                        "action": "manual_review",
                        "source_project_name": standard_name,
                        "source_operation_strategy": target_strategy,
                        "source_operation_mode": row.get("source_operation_mode", ""),
                        "project_id": project.id,
                        "current_project_name": project_name(project),
                        "current_operation_strategy": project.operation_strategy or "",
                        "active": bool(project.active),
                        "legacy_project_id": project.legacy_project_id or "",
                        "reason": "multiple_projects_share_the_same_normalized_name_no_automatic_write",
                    }
                )
            continue

        project = projects[0]
        matched_project_ids.add(project.id)
        vals = {}
        if project_name(project) != standard_name:
            vals["name"] = standard_name
        if (project.operation_strategy or "") != target_strategy:
            vals["operation_strategy"] = target_strategy

        action = "write" if vals else "keep"
        plan_rows.append(
            {
                "match_status": "exact_name",
                "action": action,
                "source_project_name": standard_name,
                "source_operation_strategy": target_strategy,
                "source_operation_mode": row.get("source_operation_mode", ""),
                "project_id": project.id,
                "current_project_name": project_name(project),
                "current_operation_strategy": project.operation_strategy or "",
                "active": bool(project.active),
                "legacy_project_id": project.legacy_project_id or "",
                "reason": SOURCE_TAG if vals else "already_matches_user_confirmed_name_strategy",
            }
        )
        if apply and vals:
            project.with_context(tracking_disable=True).write(vals)

    for project in all_projects:
        if project.id in matched_project_ids:
            continue
        plan_rows.append(
            {
                "match_status": "not_in_user_confirmed_source",
                "action": "keep",
                "source_project_name": "",
                "source_operation_strategy": "",
                "source_operation_mode": "",
                "project_id": project.id,
                "current_project_name": project_name(project),
                "current_operation_strategy": project.operation_strategy or "",
                "active": bool(project.active),
                "legacy_project_id": project.legacy_project_id or "",
                "reason": "existing_project_not_removed_business_facts_preserved",
            }
        )

    if apply:
        env.cr.commit()  # noqa: F821

    status_counts = Counter(row["match_status"] for row in plan_rows)
    action_counts = Counter(row["action"] for row in plan_rows)
    root = artifact_root()
    plan_csv = root / "user_project_name_strategy_sync_plan_20260520.csv"
    result_json = root / "user_project_name_strategy_sync_result_20260520.json"
    fieldnames = [
        "match_status",
        "action",
        "source_project_name",
        "source_operation_strategy",
        "source_operation_mode",
        "project_id",
        "current_project_name",
        "current_operation_strategy",
        "active",
        "legacy_project_id",
        "reason",
    ]
    write_csv(plan_csv, plan_rows, fieldnames)

    payload = {
        "status": "APPLIED" if apply else "DRY_RUN",
        "database": env.cr.dbname,  # noqa: F821
        "source_csv": str(source),
        "source_rows": len(source_rows),
        "source_counts": dict(Counter(row["operation_strategy"] for row in source_rows)),
        "project_count": len(all_projects),
        "match_status_counts": dict(status_counts),
        "action_counts": dict(action_counts),
        "writes": action_counts.get("write", 0) if apply else 0,
        "would_write": action_counts.get("write", 0) if not apply else 0,
        "plan_csv": str(plan_csv),
        "boundary": "exact project name only; no project_id, legacy_project_id, or business fact relink",
    }
    write_json(result_json, payload)
    print("USER_PROJECT_NAME_STRATEGY_SYNC=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))


main()
