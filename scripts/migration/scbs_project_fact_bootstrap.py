"""Create target projects from SCBS project-level business facts.

Policy:

- SCBS project names confirmed by the user are treated as real project facts.
- Normal project candidates without a target project are created directly in
  ``project.project`` and their legacy project maps are confirmed.
- Non-real/test/conflict rows are intentionally left untouched.
- No existing project is merged by fuzzy matching in this script.

Run through Odoo shell. Dry-run by default:

    odoo shell -c /path/to/odoo.conf -d DB < scripts/migration/scbs_project_fact_bootstrap.py

Set ``SCBS_PROJECT_FACT_BOOTSTRAP_APPLY=1`` to write.
"""

from __future__ import annotations

import csv
import json
import os
from pathlib import Path

from odoo import fields


BATCH = "scbs_project_fact_bootstrap_v1"
SOURCE_DOMAIN = "SCBS"
SOURCE_TABLE = "SCBS_GCMC_PROJECT_CANDIDATE"
REAL_PROJECT_STATES = {"project_candidate", "single_source_project_candidate"}


def artifact_root() -> Path:
    env_root = os.getenv("MIGRATION_ARTIFACT_ROOT")
    candidates = [Path(env_root)] if env_root else []
    candidates.extend([Path.cwd() / "artifacts/migration", Path("/mnt/artifacts/migration"), Path("/tmp")])
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return Path("artifacts/migration")


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


def excluded_names() -> set[str]:
    raw = os.getenv("SCBS_PROJECT_FACT_BOOTSTRAP_EXCLUDE_NAMES") or "公司综合平台"
    return {item.strip() for item in raw.split(",") if item.strip()}


def project_values(rec) -> dict[str, object]:
    description = "\n".join(
        [
            "SCBS历史项目业务事实承接。",
            f"source_domain={SOURCE_DOMAIN}",
            f"source_table={rec.source_table}",
            f"legacy_gcmc={rec.legacy_gcmc}",
            f"fact_rows={rec.rows_total or 0}",
            f"amount_signal={rec.amount_total or 0.0}",
            f"batch={BATCH}",
        ]
    )
    values = {
        "name": rec.legacy_gcmc,
        "company_id": rec.company_id.id,
        "legacy_project_id": rec.legacy_gcmc,
        "legacy_company_name": "SCBS",
        "other_system_id": f"SCBS:{rec.source_table}:{rec.legacy_gcmc}",
        "other_system_code": "SCBS",
        "operation_strategy": "direct",
        "project_environment": "legacy_scbs_project_fact",
        "description": description,
    }
    return values


def main() -> None:
    artifacts = artifact_root()
    apply = os.getenv("SCBS_PROJECT_FACT_BOOTSTRAP_APPLY") == "1"
    excludes = excluded_names()
    plan_csv = artifacts / "scbs_project_fact_bootstrap_plan_v1.csv"
    rollback_csv = artifacts / "scbs_project_fact_bootstrap_rollback_targets_v1.csv"
    result_json = artifacts / "scbs_project_fact_bootstrap_result_v1.json"

    ProjectMap = env["sc.legacy.project.map"].sudo()
    Project = env["project.project"].sudo()

    domain = [
        ("source_domain", "=", SOURCE_DOMAIN),
        ("source_table", "=", SOURCE_TABLE),
        ("mapping_state", "=", "candidate"),
        ("project_id", "=", False),
        ("suggested_state", "in", list(REAL_PROJECT_STATES)),
    ]
    maps = ProjectMap.search(domain, order="amount_total desc, legacy_gcmc")
    plan_rows: list[dict[str, object]] = []
    rollback_rows: list[dict[str, object]] = []
    created = 0
    skipped_excluded = 0
    skipped_existing_business_key = 0

    for rec in maps:
        if rec.legacy_gcmc in excludes:
            skipped_excluded += 1
            continue

        business_key = f"SCBS:{rec.source_table}:{rec.legacy_gcmc}"
        existing = Project.search([("other_system_id", "=", business_key)], limit=1)
        if existing:
            skipped_existing_business_key += 1
            target = existing
            proposal = "link_existing_by_business_key"
        else:
            target = False
            proposal = "create_project_from_scbs_fact"

        plan_rows.append(
            {
                "map_id": rec.id,
                "legacy_gcmc": rec.legacy_gcmc,
                "suggested_state": rec.suggested_state,
                "match_method": rec.match_method,
                "fact_rows": rec.rows_total,
                "amount_total": rec.amount_total,
                "company": rec.company_id.display_name,
                "proposal": proposal,
                "target_project_id": target.id if target else "",
                "target_project_name": target.display_name if target else "",
            }
        )

        if not apply:
            continue

        if not target:
            target = Project.create(project_values(rec))
            created += 1
            rollback_rows.append(
                {
                    "project_id": target.id,
                    "name": target.name,
                    "company": target.company_id.display_name,
                    "other_system_id": target.other_system_id,
                }
            )

        rec.write(
            {
                "project_id": target.id,
                "mapping_state": "confirmed",
                "match_method": "manual",
                "reviewer_id": env.user.id,
                "reviewed_at": fields.Datetime.now(),
                "note": ((rec.note or "") + f"\n{BATCH}: {proposal}").strip(),
            }
        )

    result = {
        "mode": "apply" if apply else "dry_run",
        "planned_rows": len(plan_rows),
        "created_projects": created,
        "skipped_excluded": skipped_excluded,
        "skipped_existing_business_key": skipped_existing_business_key,
        "remaining_candidate_real_project_maps": ProjectMap.search_count(domain),
        "excluded_names": sorted(excludes),
        "plan_csv": str(plan_csv),
        "rollback_csv": str(rollback_csv),
        "result_json": str(result_json),
    }
    write_csv(
        plan_csv,
        plan_rows,
        [
            "map_id",
            "legacy_gcmc",
            "suggested_state",
            "match_method",
            "fact_rows",
            "amount_total",
            "company",
            "proposal",
            "target_project_id",
            "target_project_name",
        ],
    )
    write_csv(
        rollback_csv,
        rollback_rows,
        ["project_id", "name", "company", "other_system_id"],
    )
    write_json(result_json, result)

    if apply:
        env.cr.commit()

    print("SCBS_PROJECT_FACT_BOOTSTRAP=" + json.dumps(result, ensure_ascii=False, sort_keys=True))


main()
