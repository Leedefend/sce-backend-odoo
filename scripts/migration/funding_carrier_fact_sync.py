"""Replay funding carrier facts for imported contract-backed projects.

Run through Odoo shell:
SYNC_MODE=check odoo shell -d sc_demo -c /var/lib/odoo/odoo.conf < /mnt/scripts/migration/funding_carrier_fact_sync.py
SYNC_MODE=write odoo shell -d sc_demo -c /var/lib/odoo/odoo.conf < /mnt/scripts/migration/funding_carrier_fact_sync.py
"""

from __future__ import annotations

import csv
import json
import os
from pathlib import Path


RUN_ID = "ITER-2026-04-17-FUNDING-CARRIER-FACT-SYNC"
TARGET_DB = "sc_demo"
EXPECTED_ELIGIBLE_TOTAL = 642

OUTPUT_JSON = Path("/mnt/artifacts/migration/funding_carrier_fact_sync_result_v1.json")
SNAPSHOT_CSV = Path("/mnt/artifacts/migration/funding_carrier_fact_sync_snapshot_v1.csv")
ROLLBACK_CSV = Path("/mnt/artifacts/migration/funding_carrier_fact_sync_rollback_v1.csv")


def clean(value):
    return "" if value is None else str(value).strip()


def fetchall_dict(query, params=None):
    env.cr.execute(query, params or ())  # noqa: F821
    columns = [item[0] for item in env.cr.description]  # noqa: F821
    return [dict(zip(columns, row)) for row in env.cr.fetchall()]  # noqa: F821


def write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_csv(path, fieldnames, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def candidate_rows():
    return fetchall_dict(
        """
        WITH contract_sums AS (
            SELECT cc.project_id,
                   COUNT(cc.id) AS contract_count,
                   SUM(COALESCE(cc.amount_final, 0.0)) AS contract_amount_final_sum,
                   SUM(COALESCE(cc.amount_total, 0.0)) AS contract_amount_total_sum
              FROM construction_contract cc
             WHERE cc.project_id IS NOT NULL
               AND cc.state <> 'cancel'
             GROUP BY cc.project_id
        ),
        active_baselines AS (
            SELECT pfb.project_id,
                   COUNT(pfb.id) AS active_baseline_count,
                   SUM(COALESCE(pfb.total_amount, 0.0)) AS active_baseline_total
              FROM project_funding_baseline pfb
             WHERE pfb.state = 'active'
             GROUP BY pfb.project_id
        )
        SELECT pp.id AS project_id,
               pp.name::text AS project_name,
               pp.legacy_project_id,
               pp.project_code,
               pp.funding_enabled AS old_funding_enabled,
               cs.contract_count,
               cs.contract_amount_final_sum,
               cs.contract_amount_total_sum,
               COALESCE(ab.active_baseline_count, 0) AS active_baseline_count,
               COALESCE(ab.active_baseline_total, 0.0) AS active_baseline_total
          FROM project_project pp
          JOIN contract_sums cs ON cs.project_id = pp.id
          LEFT JOIN active_baselines ab ON ab.project_id = pp.id
         WHERE COALESCE(pp.legacy_project_id, '') <> ''
           AND COALESCE(pp.project_code, '') <> ''
           AND cs.contract_amount_final_sum > 0.0
         ORDER BY pp.id
        """
    )


def main():
    mode = clean(os.environ.get("SYNC_MODE") or "check")
    if mode not in {"check", "write"}:
        raise RuntimeError({"invalid_sync_mode": mode})
    if env.cr.dbname != TARGET_DB:  # noqa: F821
        raise RuntimeError({"database_not_sc_demo": env.cr.dbname})  # noqa: F821

    rows = candidate_rows()
    if len(rows) != EXPECTED_ELIGIBLE_TOTAL:
        raise RuntimeError({"target_count_drift": len(rows), "expected": EXPECTED_ELIGIBLE_TOTAL})

    target_rows = [row for row in rows if int(row["active_baseline_count"] or 0) == 0]
    already_active_rows = [row for row in rows if int(row["active_baseline_count"] or 0) > 0]
    if any(float(row["contract_amount_final_sum"] or 0.0) <= 0.0 for row in target_rows):
        raise RuntimeError({"zero_amount_project_included": True})

    snapshot_rows = []
    rollback_rows = []
    for row in rows:
        planned_amount = float(row["contract_amount_final_sum"] or 0.0)
        action = "skip_existing_active_baseline" if int(row["active_baseline_count"] or 0) > 0 else "create_active_baseline"
        snapshot_rows.append(
            {
                "project_id": row["project_id"],
                "legacy_project_id": clean(row["legacy_project_id"]),
                "project_code": clean(row["project_code"]),
                "project_name": clean(row["project_name"]),
                "old_funding_enabled": clean(row["old_funding_enabled"]),
                "contract_count": row["contract_count"],
                "contract_amount_final_sum": planned_amount,
                "contract_amount_total_sum": float(row["contract_amount_total_sum"] or 0.0),
                "active_baseline_count": row["active_baseline_count"],
                "active_baseline_total": float(row["active_baseline_total"] or 0.0),
                "planned_action": action,
            }
        )
        rollback_rows.append(
            {
                "project_id": row["project_id"],
                "legacy_project_id": clean(row["legacy_project_id"]),
                "restore_funding_enabled": "1" if row["old_funding_enabled"] else "0",
                "created_baseline_ids": "",
            }
        )

    write_csv(
        SNAPSHOT_CSV,
        [
            "project_id",
            "legacy_project_id",
            "project_code",
            "project_name",
            "old_funding_enabled",
            "contract_count",
            "contract_amount_final_sum",
            "contract_amount_total_sum",
            "active_baseline_count",
            "active_baseline_total",
            "planned_action",
        ],
        snapshot_rows,
    )

    created_baseline_ids_by_project = {}
    enabled_project_count = 0
    if mode == "write" and target_rows:
        Project = env["project.project"].sudo()  # noqa: F821
        Baseline = env["project.funding.baseline"].sudo()  # noqa: F821
        target_ids = [int(row["project_id"]) for row in target_rows]
        projects = Project.browse(target_ids)
        to_enable = projects.filtered(lambda project: not project.funding_enabled)
        enabled_project_count = len(to_enable)
        if to_enable:
            to_enable.write({"funding_enabled": True})
        for row in target_rows:
            baseline = Baseline.create(
                {
                    "project_id": int(row["project_id"]),
                    "total_amount": float(row["contract_amount_final_sum"] or 0.0),
                    "state": "active",
                }
            )
            created_baseline_ids_by_project[int(row["project_id"])] = baseline.id
        env.cr.commit()  # noqa: F821

    for item in rollback_rows:
        project_id = int(item["project_id"])
        if project_id in created_baseline_ids_by_project:
            item["created_baseline_ids"] = str(created_baseline_ids_by_project[project_id])
    write_csv(
        ROLLBACK_CSV,
        ["project_id", "legacy_project_id", "restore_funding_enabled", "created_baseline_ids"],
        rollback_rows,
    )

    result = {
        "run_id": RUN_ID,
        "mode": mode,
        "database": env.cr.dbname,  # noqa: F821
        "eligible_total": len(rows),
        "target_without_active_baseline_count": len(target_rows),
        "already_active_baseline_count": len(already_active_rows),
        "enabled_project_count": enabled_project_count if mode == "write" else 0,
        "created_baseline_count": len(created_baseline_ids_by_project) if mode == "write" else 0,
        "snapshot_csv": str(SNAPSHOT_CSV),
        "rollback_csv": str(ROLLBACK_CSV),
        "sample_project_ids": [int(row["project_id"]) for row in target_rows[:20]],
    }
    write_json(OUTPUT_JSON, result)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))


main()
