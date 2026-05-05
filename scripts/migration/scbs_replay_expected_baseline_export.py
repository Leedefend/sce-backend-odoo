"""Export the expected SCBS replay baseline from the accepted rebuilt database.

This is the bridge between the previous successful rebuild and future
no-legacy replay. The exported JSON is copied into the replay asset package and
used to verify that a fresh database rebuild reproduces the accepted business
fact counts and amounts.
"""

from __future__ import annotations

import json
import os
from pathlib import Path


SOURCE_MODEL = "sc.legacy.scbs.fact.staging"


def artifact_root() -> Path:
    env_root = os.getenv("MIGRATION_ARTIFACT_ROOT")
    candidates = [Path(env_root)] if env_root else []
    candidates.extend([Path.cwd() / "artifacts/migration", Path("/mnt/artifacts/migration"), Path("/tmp")])
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


def fetch_one(sql: str) -> dict[str, object]:
    env.cr.execute(sql)  # noqa: F821
    columns = [desc[0] for desc in env.cr.description]  # noqa: F821
    row = env.cr.fetchone()  # noqa: F821
    return dict(zip(columns, row or []))


def fetch_rows(sql: str) -> list[dict[str, object]]:
    env.cr.execute(sql)  # noqa: F821
    columns = [desc[0] for desc in env.cr.description]  # noqa: F821
    return [dict(zip(columns, row)) for row in env.cr.fetchall()]  # noqa: F821


def count_amount(sql: str) -> dict[str, object]:
    row = fetch_one(sql)
    return {"rows": int(row.get("rows") or 0), "amount": float(row.get("amount") or 0.0)}


def main() -> None:
    artifacts = artifact_root()
    output = artifacts / "scbs_replay_expected_baseline_v1.json"
    baseline = {
        "source_database": env.cr.dbname,  # noqa: F821
        "policy": {
            "legacy_database_required_for_replay": False,
            "full_legacy_material_library_replay": False,
            "material_scope": "material catalog facts required by SCBS stock-in documents",
            "base_system_unspecified_project_links": True,
        },
        "staging": {
            "total": count_amount(
                """
                SELECT COUNT(*) AS rows, ROUND(COALESCE(SUM(amount_total), 0)::numeric, 2) AS amount
                  FROM sc_legacy_scbs_fact_staging
                 WHERE import_batch = 'scbs_fact_staging_v1'
                """
            ),
            "active_projection_ready_by_family": fetch_rows(
                """
                SELECT fact_family,
                       COUNT(*) AS rows,
                       ROUND(COALESCE(SUM(amount_total), 0)::numeric, 2) AS amount
                  FROM sc_legacy_scbs_fact_staging
                 WHERE import_batch = 'scbs_fact_staging_v1'
                   AND active IS TRUE
                   AND mapping_gate_state = 'projection_ready'
                 GROUP BY fact_family
                 ORDER BY fact_family
                """
            ),
            "inactive": count_amount(
                """
                SELECT COUNT(*) AS rows, ROUND(COALESCE(SUM(amount_total), 0)::numeric, 2) AS amount
                  FROM sc_legacy_scbs_fact_staging
                 WHERE import_batch = 'scbs_fact_staging_v1'
                   AND active IS FALSE
                """
            ),
            "base_system_project_bound": count_amount(
                """
                SELECT COUNT(*) AS rows, ROUND(COALESCE(SUM(amount_total), 0)::numeric, 2) AS amount
                  FROM sc_legacy_scbs_fact_staging
                 WHERE import_batch = 'scbs_fact_staging_v1'
                   AND active IS TRUE
                   AND project_id IS NOT NULL
                   AND project_map_id IS NULL
                """
            ),
        },
        "formal": {
            "payment_execution": count_amount(
                """
                SELECT COUNT(*) AS rows, ROUND(COALESCE(SUM(paid_amount), 0)::numeric, 2) AS amount
                  FROM sc_payment_execution
                 WHERE legacy_source_model = 'sc.legacy.scbs.fact.staging'
                """
            ),
            "payment_adjustment": count_amount(
                """
                SELECT COUNT(*) AS rows, ROUND(COALESCE(SUM(source_amount), 0)::numeric, 2) AS amount
                  FROM sc_legacy_payment_adjustment_fact
                 WHERE legacy_source_model = 'sc.legacy.scbs.fact.staging'
                """
            ),
            "enterprise_fact_by_family": fetch_rows(
                """
                SELECT fact_family,
                       COUNT(*) AS rows,
                       ROUND(COALESCE(SUM(amount_total), 0)::numeric, 2) AS amount
                  FROM sc_legacy_enterprise_business_fact
                 WHERE legacy_source_model = 'sc.legacy.scbs.fact.staging'
                 GROUP BY fact_family
                 ORDER BY fact_family
                """
            ),
            "supplier_contract": count_amount(
                """
                SELECT COUNT(*) AS rows, ROUND(COALESCE(SUM(amount_total), 0)::numeric, 2) AS amount
                  FROM sc_general_contract
                 WHERE legacy_source_model = 'sc.legacy.scbs.fact.staging'
                """
            ),
            "stock_in": count_amount(
                """
                SELECT COUNT(*) AS rows, ROUND(COALESCE(SUM(amount_total), 0)::numeric, 2) AS amount
                  FROM sc_material_inbound
                 WHERE legacy_fact_model = 'sc.legacy.scbs.fact.staging'
                """
            ),
            "fund_daily": count_amount(
                """
                SELECT COUNT(*) AS rows, ROUND(COALESCE(SUM(source_account_balance_total), 0)::numeric, 2) AS amount
                  FROM sc_legacy_fund_daily_snapshot_fact
                 WHERE legacy_source_table = 'D_SCBSJS_ZJGL_ZJSZ_ZJRBB'
                   AND import_batch = 'scbs_fund_daily_enterprise_v1'
                """
            ),
        },
        "dimensions": {
            "business_entities_scbs": int(
                fetch_one("SELECT COUNT(*) AS rows FROM sc_business_entity WHERE legacy_xmid IS NOT NULL")["rows"] or 0
            ),
            "projects_direct_scbs": int(
                fetch_one(
                    """
                    SELECT COUNT(*) AS rows
                      FROM project_project
                     WHERE operation_strategy = 'direct'
                       AND other_system_code = 'SCBS'
                    """
                )["rows"]
                or 0
            ),
            "base_system_unspecified_projects": int(
                fetch_one(
                    """
                    SELECT COUNT(*) AS rows
                      FROM project_project
                     WHERE other_system_id LIKE 'SCBS:BASE_SYSTEM_PROJECT:%'
                    """
                )["rows"]
                or 0
            ),
            "material_catalog_scbs": int(
                fetch_one(
                    """
                    SELECT COUNT(*) AS rows
                      FROM sc_material_catalog
                     WHERE source_origin = 'legacy'
                       AND (code LIKE 'SCBS-%' OR code LIKE 'SCBS-GROUP-%')
                    """
                )["rows"]
                or 0
            ),
            "material_maps_confirmed": int(
                fetch_one(
                    """
                    SELECT COUNT(*) AS rows
                      FROM sc_legacy_scbs_material_map
                     WHERE source_domain = 'SCBS'
                       AND mapping_state = 'confirmed'
                    """
                )["rows"]
                or 0
            ),
        },
    }
    output.write_text(json.dumps(baseline, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("SCBS_REPLAY_EXPECTED_BASELINE=" + json.dumps({"output": str(output), **baseline}, ensure_ascii=False, sort_keys=True))


main()
