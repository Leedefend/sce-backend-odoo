"""Bootstrap optional SCBS unassigned-project buckets for formal projection.

Default mode is dry-run. Set APPLY=1 to create bucket projects and attach active
SCBS staging facts that lack a project but have a confirmed business entity.
"""

from __future__ import annotations

import csv
import json
import os
from pathlib import Path


SOURCE_MODEL = "sc.legacy.scbs.fact.staging"


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


def bucket_candidates() -> list[dict[str, object]]:
    return fetch_dicts(
        """
        SELECT s.business_entity_id,
               be.name AS business_entity_name,
               COUNT(*) AS rows,
               ROUND(SUM(s.amount_total)::numeric, 2) AS amount_total,
               COUNT(*) FILTER (WHERE s.fact_family = 'payment') AS payment_rows,
               ROUND(COALESCE(SUM(s.amount_total) FILTER (WHERE s.fact_family = 'payment'), 0)::numeric, 2) AS payment_amount,
               COUNT(*) FILTER (WHERE s.fact_family = 'supplier_contract') AS supplier_contract_rows,
               ROUND(COALESCE(SUM(s.amount_total) FILTER (WHERE s.fact_family = 'supplier_contract'), 0)::numeric, 2) AS supplier_contract_amount,
               COUNT(*) FILTER (WHERE s.fact_family = 'stock_in') AS stock_in_rows,
               ROUND(COALESCE(SUM(s.amount_total) FILTER (WHERE s.fact_family = 'stock_in'), 0)::numeric, 2) AS stock_in_amount
          FROM sc_legacy_scbs_fact_staging s
          JOIN sc_business_entity be ON be.id = s.business_entity_id
         WHERE s.import_batch = 'scbs_fact_staging_v1'
           AND s.active IS TRUE
           AND s.mapping_gate_state = 'projection_ready'
           AND s.project_id IS NULL
           AND s.business_entity_id IS NOT NULL
           AND s.fact_family IN ('payment', 'supplier_contract', 'stock_in')
         GROUP BY s.business_entity_id, be.name
         ORDER BY SUM(s.amount_total) DESC NULLS LAST
        """
    )


def entityless_summary() -> dict[str, object]:
    rows = fetch_dicts(
        """
        SELECT COUNT(*) AS rows,
               ROUND(COALESCE(SUM(amount_total), 0)::numeric, 2) AS amount_total
          FROM sc_legacy_scbs_fact_staging
         WHERE import_batch = 'scbs_fact_staging_v1'
           AND active IS TRUE
           AND mapping_gate_state = 'projection_ready'
           AND project_id IS NULL
           AND business_entity_id IS NULL
           AND fact_family IN ('payment', 'supplier_contract', 'stock_in')
        """
    )
    return rows[0] if rows else {"rows": 0, "amount_total": 0}


def existing_bucket_by_code(project_code: str):
    return env["project.project"].sudo().with_context(active_test=False).search([("project_code", "=", project_code)], limit=1)  # noqa: F821


def main() -> None:
    apply = os.getenv("APPLY") == "1"
    artifacts = artifact_root()
    plan_csv = artifacts / "scbs_project_bucket_bootstrap_plan_v1.csv"
    result_json = artifacts / "scbs_project_bucket_bootstrap_result_v1.json"
    rollback_csv = artifacts / "scbs_project_bucket_bootstrap_rollback_targets_v1.csv"

    Project = env["project.project"].sudo()  # noqa: F821
    Staging = env["sc.legacy.scbs.fact.staging"].sudo().with_context(active_test=False)  # noqa: F821
    candidates = bucket_candidates()
    plan_rows: list[dict[str, object]] = []
    rollback_rows: list[dict[str, object]] = []
    created = 0
    linked = 0
    would_create = 0
    would_link_rows = 0

    for row in candidates:
        entity_id = int(row["business_entity_id"])
        entity_name = str(row["business_entity_name"])
        code = f"SCBS-BUCKET-BE-{entity_id}"
        bucket_name = f"SCBS未指定项目 - {entity_name}"
        existing = existing_bucket_by_code(code)
        action = "link_existing_bucket" if existing else "create_bucket"
        target_id = existing.id if existing else ""
        affected_domain = [
            ("import_batch", "=", "scbs_fact_staging_v1"),
            ("active", "=", True),
            ("mapping_gate_state", "=", "projection_ready"),
            ("project_id", "=", False),
            ("business_entity_id", "=", entity_id),
            ("fact_family", "in", ["payment", "supplier_contract", "stock_in"]),
        ]
        affected_count = int(row["rows"] or 0)

        if apply:
            if not existing:
                existing = Project.create(
                    {
                        "name": bucket_name,
                        "project_code": code,
                        "operation_strategy": "direct",
                        "legacy_project_id": f"SCBS_BUCKET:{entity_id}",
                        "legacy_company_name": entity_name,
                        "legacy_state": "historical_unassigned_project_bucket",
                        "description": (
                            "SCBS历史迁移未指定项目桶。仅用于承接源数据无项目但正式模型要求project_id的历史事实，"
                            "不代表真实用户创建项目。"
                        ),
                    }
                )
                created += 1
                rollback_rows.append({"project_id": existing.id, "project_code": code, "name": bucket_name})
            target_id = existing.id
            records = Staging.search(affected_domain)
            records.write({"project_id": target_id})
            linked += len(records)
            action = "created_and_linked" if code in {r["project_code"] for r in rollback_rows} else "linked_existing"
        else:
            if not existing:
                would_create += 1
            would_link_rows += affected_count

        plan_rows.append(
            {
                "business_entity_id": entity_id,
                "business_entity_name": entity_name,
                "project_code": code,
                "project_name": bucket_name,
                "target_project_id": target_id,
                "rows": row["rows"],
                "amount_total": row["amount_total"],
                "payment_rows": row["payment_rows"],
                "payment_amount": row["payment_amount"],
                "supplier_contract_rows": row["supplier_contract_rows"],
                "supplier_contract_amount": row["supplier_contract_amount"],
                "stock_in_rows": row["stock_in_rows"],
                "stock_in_amount": row["stock_in_amount"],
                "action": action,
            }
        )

    write_csv(
        plan_csv,
        plan_rows,
        [
            "business_entity_id",
            "business_entity_name",
            "project_code",
            "project_name",
            "target_project_id",
            "rows",
            "amount_total",
            "payment_rows",
            "payment_amount",
            "supplier_contract_rows",
            "supplier_contract_amount",
            "stock_in_rows",
            "stock_in_amount",
            "action",
        ],
    )
    if rollback_rows:
        write_csv(rollback_csv, rollback_rows, ["project_id", "project_code", "name"])

    if apply:
        env.cr.commit()  # noqa: F821

    entityless = entityless_summary()
    payload = {
        "status": "APPLIED" if apply else "DRY_RUN",
        "database": env.cr.dbname,  # noqa: F821
        "plan_csv": str(plan_csv),
        "rollback_csv": str(rollback_csv) if rollback_rows else "",
        "candidate_buckets": len(candidates),
        "would_create_buckets": would_create,
        "would_link_rows": would_link_rows,
        "created_buckets": created,
        "linked_rows": linked,
        "entityless_projectless_rows": entityless["rows"],
        "entityless_projectless_amount": entityless["amount_total"],
    }
    write_json(result_json, payload)
    print("SCBS_PROJECT_BUCKET_BOOTSTRAP=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))


main()
