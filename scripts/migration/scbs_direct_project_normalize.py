"""Normalize provisional SCBS project buckets into direct-operation projects.

The previous bucket pass only proved that the target formal models needed a
project_id. Further source evidence shows the linked rows carry legacy_xmid /
legacy_xmmc values that match SCBS BASE_SYSTEM_PROJECT direct projects. This
script converts provisional bucket projects into source-tagged SCBS direct
projects without changing staging project links.

Dry-run by default. Set APPLY=1 to write.
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


def provisional_project_rows() -> list[dict[str, object]]:
    return fetch_dicts(
        """
        WITH linked AS (
            SELECT p.id AS project_id,
                   p.project_code AS old_project_code,
                   p.name AS old_project_name,
                   p.legacy_project_id AS old_legacy_project_id,
                   p.other_system_id AS old_other_system_id,
                   p.project_environment AS old_project_environment,
                   s.legacy_xmid,
                   s.legacy_xmmc,
                   COUNT(*) AS fact_rows,
                   ROUND(SUM(s.amount_total)::numeric, 2) AS amount_total,
                   ROW_NUMBER() OVER (
                       PARTITION BY p.id
                       ORDER BY SUM(s.amount_total) DESC NULLS LAST, COUNT(*) DESC, s.legacy_xmmc
                   ) AS name_rank
              FROM project_project p
              JOIN sc_legacy_scbs_fact_staging s ON s.project_id = p.id
             WHERE p.project_code LIKE 'SCBS-BUCKET-BE-%'
               AND s.import_batch = 'scbs_fact_staging_v1'
               AND s.active IS TRUE
               AND s.mapping_gate_state = 'projection_ready'
               AND COALESCE(s.legacy_xmid, '') <> ''
               AND COALESCE(s.legacy_xmmc, '') <> ''
             GROUP BY p.id, p.project_code, p.name, p.legacy_project_id,
                      p.other_system_id, p.project_environment, s.legacy_xmid, s.legacy_xmmc
        ),
        per_project AS (
            SELECT project_id,
                   COUNT(DISTINCT legacy_xmid) AS xmid_count,
                   COUNT(DISTINCT legacy_xmmc) AS xmmc_count,
                   SUM(fact_rows) AS fact_rows,
                   ROUND(SUM(amount_total)::numeric, 2) AS amount_total
              FROM linked
             GROUP BY project_id
        )
        SELECT l.project_id,
               l.old_project_code,
               l.old_project_name,
               l.old_legacy_project_id,
               l.old_other_system_id,
               l.old_project_environment,
               l.legacy_xmid,
               l.legacy_xmmc,
               p.xmid_count,
               p.xmmc_count,
               p.fact_rows,
               p.amount_total
          FROM linked l
          JOIN per_project p ON p.project_id = l.project_id
         WHERE l.name_rank = 1
         ORDER BY p.amount_total DESC NULLS LAST, l.legacy_xmmc
        """
    )


def main() -> None:
    apply = os.getenv("APPLY") == "1"
    artifacts = artifact_root()
    plan_csv = artifacts / "scbs_direct_project_normalize_plan_v1.csv"
    rollback_csv = artifacts / "scbs_direct_project_normalize_rollback_v1.csv"
    result_json = artifacts / "scbs_direct_project_normalize_result_v1.json"

    Project = env["project.project"].sudo().with_context(active_test=False)  # noqa: F821
    rows = provisional_project_rows()
    plan_rows: list[dict[str, object]] = []
    rollback_rows: list[dict[str, object]] = []
    updated = 0
    blocked = 0

    for row in rows:
        target_code = f"SCBS-DIRECT-{row['legacy_xmid']}"
        conflict = Project.search(
            [("project_code", "=", target_code), ("id", "!=", int(row["project_id"]))],
            limit=1,
        )
        action = "normalize_to_scbs_direct_project"
        if int(row["xmid_count"] or 0) != 1 or conflict:
            action = "blocked_conflict"
            blocked += 1

        plan_row = {
            **row,
            "target_project_code": target_code,
            "target_project_name": row["legacy_xmmc"],
            "target_operation_strategy": "direct",
            "action": action,
            "conflict_project_id": conflict.id if conflict else "",
        }
        plan_rows.append(plan_row)

        if not apply or action != "normalize_to_scbs_direct_project":
            continue

        project = Project.browse(int(row["project_id"]))
        rollback_rows.append(
            {
                "project_id": project.id,
                "old_project_code": project.project_code or "",
                "old_name": project.name or "",
                "old_legacy_project_id": project.legacy_project_id or "",
                "old_other_system_id": project.other_system_id or "",
                "old_project_environment": project.project_environment or "",
                "old_operation_strategy": project.operation_strategy or "",
            }
        )
        project.write(
            {
                "name": row["legacy_xmmc"],
                "project_code": target_code,
                "operation_strategy": "direct",
                "legacy_project_id": row["legacy_xmid"],
                "legacy_company_name": "SCBS",
                "other_system_id": f"SCBS:BASE_SYSTEM_PROJECT:{row['legacy_xmid']}",
                "other_system_code": "SCBS",
                "project_environment": "legacy_scbs_direct_project",
                "legacy_state": "scbs_direct_project_confirmed",
                "description": (
                    "SCBS历史直营正式项目承接。\n"
                    f"source_table=BASE_SYSTEM_PROJECT\n"
                    f"legacy_xmid={row['legacy_xmid']}\n"
                    f"legacy_xmmc={row['legacy_xmmc']}\n"
                    f"fact_rows={row['fact_rows']}\n"
                    f"amount_signal={row['amount_total']}"
                ),
            }
        )
        updated += 1

    write_csv(
        plan_csv,
        plan_rows,
        [
            "project_id",
            "old_project_code",
            "old_project_name",
            "old_legacy_project_id",
            "old_other_system_id",
            "old_project_environment",
            "legacy_xmid",
            "legacy_xmmc",
            "xmid_count",
            "xmmc_count",
            "fact_rows",
            "amount_total",
            "target_project_code",
            "target_project_name",
            "target_operation_strategy",
            "action",
            "conflict_project_id",
        ],
    )
    write_csv(
        rollback_csv,
        rollback_rows,
        [
            "project_id",
            "old_project_code",
            "old_name",
            "old_legacy_project_id",
            "old_other_system_id",
            "old_project_environment",
            "old_operation_strategy",
        ],
    )
    if apply:
        env.cr.commit()  # noqa: F821

    payload = {
        "status": "APPLIED" if apply else "DRY_RUN",
        "database": env.cr.dbname,  # noqa: F821
        "plan_csv": str(plan_csv),
        "rollback_csv": str(rollback_csv),
        "planned_projects": len(plan_rows),
        "updated_projects": updated,
        "blocked_projects": blocked,
        "fact_rows": sum(int(row["fact_rows"] or 0) for row in plan_rows if row["action"] != "blocked_conflict"),
        "amount_total": str(sum(float(row["amount_total"] or 0) for row in plan_rows if row["action"] != "blocked_conflict")),
    }
    write_json(result_json, payload)
    print("SCBS_DIRECT_PROJECT_NORMALIZE=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))


main()
