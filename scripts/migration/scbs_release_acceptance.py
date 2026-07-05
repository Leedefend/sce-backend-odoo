"""SCBS migration release acceptance guard.

Modes:
- strict: accept the loaded SCBS simulation database and verify closure numbers.
- empty: accept a freshly installed database and verify the SCBS carriers are
  installed without imported SCBS facts.
"""

from __future__ import annotations

import json
import os
from pathlib import Path


SOURCE_MODEL = "sc.legacy.scbs.fact.staging"


def repo_root() -> Path:
    env_root = os.getenv("MIGRATION_REPO_ROOT")
    candidates = [Path(env_root)] if env_root else []
    candidates.extend([Path("/mnt/artifacts/migration/scbs_replay_asset_v1"), Path("/mnt"), Path.cwd()])
    for candidate in candidates:
        if (candidate / "artifacts/migration/scbs_replay_expected_baseline_v1.json").exists():
            return candidate
    return Path.cwd()


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
    names = [desc[0] for desc in env.cr.description]  # noqa: F821
    row = env.cr.fetchone()  # noqa: F821
    return dict(zip(names, row or []))


def fetch_rows(sql: str) -> list[dict[str, object]]:
    env.cr.execute(sql)  # noqa: F821
    names = [desc[0] for desc in env.cr.description]  # noqa: F821
    return [dict(zip(names, row)) for row in env.cr.fetchall()]  # noqa: F821


def count(model: str, domain) -> int:
    return env[model].sudo().with_context(active_test=False).search_count(domain)  # noqa: F821


def sum_field(model: str, domain, field_name: str) -> float:
    records = env[model].sudo().with_context(active_test=False).search(domain)  # noqa: F821
    return float(sum(records.mapped(field_name)) or 0.0)


def near(left: object, right: object) -> bool:
    return abs(float(left or 0) - float(right or 0)) < 0.01


def by_key(rows: list[dict[str, object]], key: str) -> dict[str, dict[str, object]]:
    return {str(row[key]): row for row in rows}


def expected_baseline() -> dict[str, object]:
    baseline_path = repo_root() / "artifacts/migration/scbs_replay_expected_baseline_v1.json"
    return json.loads(baseline_path.read_text(encoding="utf-8"))


def closure_result() -> dict[str, object]:
    path = artifact_root() / "scbs_migration_closure_reconciliation_result_v1.json"
    if not path.exists():
        return {"status": "MISSING", "path": str(path)}
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["path"] = str(path)
    return payload


def closure_acceptance_checks(closure: dict[str, object]) -> dict[str, bool]:
    non_direct = closure.get("non_direct") or {}
    duplicate_checks = closure.get("duplicate_checks") or {}
    return {
        "closure_status_pass": closure.get("status") == "PASS",
        "closure_amount_closed": bool(closure.get("amount_closure_ok")),
        "closure_stock_delta_ok": bool(closure.get("stock_delta_ok")),
        "closure_all_direct": all(int(value or 0) == 0 for value in non_direct.values()),
        "closure_no_duplicate_sources": all(int(value or 0) == 0 for value in duplicate_checks.values()),
        "closure_material_all_confirmed": int(closure.get("material_nonconfirmed") or 0) == 0,
        "closure_fund_daily_no_project": int(closure.get("fund_daily_project_bound") or 0) == 0,
        "closure_fund_daily_all_have_entity": int(closure.get("fund_daily_missing_entity") or 0) == 0,
    }


def duplicate_count(table: str, where: str, keys: str) -> int:
    sql = """
        SELECT COUNT(*)
          FROM (
            SELECT {keys}, COUNT(*)
              FROM {table}
             WHERE {where}
             GROUP BY {keys}
            HAVING COUNT(*) > 1
          ) d
    """.format(table=table, where=where, keys=keys)
    return int(fetch_one(sql)["count"] or 0)


def scbs_project_domain_sql(alias: str = "p") -> str:
    return (
        "(%s.other_system_code = 'SCBS' "
        "OR %s.other_system_id LIKE 'SCBS:%%' "
        "OR %s.legacy_project_id LIKE 'SCBS_BUCKET:%%' "
        "OR %s.project_environment = 'legacy_scbs_project_fact')"
    ) % (alias, alias, alias, alias)


def model_installed_checks() -> dict[str, bool]:
    models = [
        "sc.legacy.scbs.fact.staging",
        "sc.legacy.payment.adjustment.fact",
        "sc.legacy.enterprise.business.fact",
        "sc.legacy.fund.daily.snapshot.fact",
        "sc.material.catalog",
    ]
    return {"model:%s" % model: model in env for model in models}  # noqa: F821


def empty_acceptance() -> tuple[dict[str, bool], dict[str, object]]:
    checks = model_installed_checks()
    checks.update(
        {
            "no_scbs_staging": count("sc.legacy.scbs.fact.staging", [("import_batch", "=", "scbs_fact_staging_v1")]) == 0,
            "no_scbs_payment_adjustment": count(
                "sc.legacy.payment.adjustment.fact", [("legacy_source_model", "=", SOURCE_MODEL)]
            )
            == 0,
            "no_scbs_enterprise_fact": count(
                "sc.legacy.enterprise.business.fact", [("legacy_source_model", "=", SOURCE_MODEL)]
            )
            == 0,
            "no_scbs_fund_daily": count(
                "sc.legacy.fund.daily.snapshot.fact",
                [("legacy_source_table", "=", "D_SCBSJS_ZJGL_ZJSZ_ZJRBB")],
            )
            == 0,
        }
    )
    observations = {
        "mode": "empty",
        "scbs_staging_rows": count("sc.legacy.scbs.fact.staging", [("import_batch", "=", "scbs_fact_staging_v1")]),
        "scbs_payment_adjustment_rows": count(
            "sc.legacy.payment.adjustment.fact", [("legacy_source_model", "=", SOURCE_MODEL)]
        ),
        "scbs_enterprise_fact_rows": count(
            "sc.legacy.enterprise.business.fact", [("legacy_source_model", "=", SOURCE_MODEL)]
        ),
    }
    return checks, observations


def strict_acceptance() -> tuple[dict[str, bool], dict[str, object]]:
    checks = model_installed_checks()
    baseline = expected_baseline()
    closure = closure_result()
    staging = fetch_rows(
        """
        SELECT fact_family,
               COUNT(*) AS rows,
               ROUND(COALESCE(SUM(amount_total), 0)::numeric, 2) AS amount
          FROM sc_legacy_scbs_fact_staging
         WHERE import_batch = 'scbs_fact_staging_v1'
           AND active IS TRUE
           AND mapping_gate_state = 'projection_ready'
         GROUP BY fact_family
        """
    )
    staging_by_family = {row["fact_family"]: row for row in staging}
    staging_total = fetch_one(
        """
        SELECT COUNT(*) AS rows,
               ROUND(COALESCE(SUM(amount_total), 0)::numeric, 2) AS amount
          FROM sc_legacy_scbs_fact_staging
         WHERE import_batch = 'scbs_fact_staging_v1'
        """
    )
    payment_execution_rows = count("sc.payment.execution", [("legacy_source_model", "=", SOURCE_MODEL)])
    payment_execution_amount = sum_field("sc.payment.execution", [("legacy_source_model", "=", SOURCE_MODEL)], "paid_amount")
    payment_adjustment_rows = count(
        "sc.legacy.payment.adjustment.fact",
        [("legacy_source_model", "=", SOURCE_MODEL), ("legacy_source_table", "=", "T_FK_Supplier")],
    )
    payment_adjustment_amount = sum_field(
        "sc.legacy.payment.adjustment.fact",
        [("legacy_source_model", "=", SOURCE_MODEL), ("legacy_source_table", "=", "T_FK_Supplier")],
        "source_amount",
    )
    enterprise_payment_rows = count(
        "sc.legacy.enterprise.business.fact",
        [("legacy_source_model", "=", SOURCE_MODEL), ("fact_family", "=", "payment")],
    )
    enterprise_payment_amount = sum_field(
        "sc.legacy.enterprise.business.fact",
        [("legacy_source_model", "=", SOURCE_MODEL), ("fact_family", "=", "payment")],
        "amount_total",
    )
    contract_rows = count("sc.general.contract", [("legacy_source_model", "=", SOURCE_MODEL)])
    contract_amount = sum_field("sc.general.contract", [("legacy_source_model", "=", SOURCE_MODEL)], "amount_total")
    enterprise_contract_rows = count(
        "sc.legacy.enterprise.business.fact",
        [("legacy_source_model", "=", SOURCE_MODEL), ("fact_family", "=", "supplier_contract")],
    )
    enterprise_contract_amount = sum_field(
        "sc.legacy.enterprise.business.fact",
        [("legacy_source_model", "=", SOURCE_MODEL), ("fact_family", "=", "supplier_contract")],
        "amount_total",
    )
    stock_rows = count("sc.material.inbound", [("legacy_fact_model", "=", SOURCE_MODEL)])
    stock_amount = sum_field("sc.material.inbound", [("legacy_fact_model", "=", SOURCE_MODEL)], "amount_total")
    fund_rows = count(
        "sc.legacy.fund.daily.snapshot.fact",
        [
            ("legacy_source_table", "=", "D_SCBSJS_ZJGL_ZJSZ_ZJRBB"),
            ("import_batch", "=", "scbs_fund_daily_enterprise_v1"),
        ],
    )
    fund_amount = sum_field(
        "sc.legacy.fund.daily.snapshot.fact",
        [
            ("legacy_source_table", "=", "D_SCBSJS_ZJGL_ZJSZ_ZJRBB"),
            ("import_batch", "=", "scbs_fund_daily_enterprise_v1"),
        ],
        "source_account_balance_total",
    )
    project_strategy = {
        "scbs_direct": fetch_one(
            "SELECT COUNT(*) FROM project_project p WHERE %s AND p.operation_strategy = 'direct'"
            % scbs_project_domain_sql("p")
        )["count"],
        "scbs_non_direct": fetch_one(
            "SELECT COUNT(*) FROM project_project p WHERE %s AND p.operation_strategy IS DISTINCT FROM 'direct'"
            % scbs_project_domain_sql("p")
        )["count"],
        "non_scbs_joint": fetch_one(
            "SELECT COUNT(*) FROM project_project p WHERE NOT %s AND p.operation_strategy = 'joint'"
            % scbs_project_domain_sql("p")
        )["count"],
        "non_scbs_not_joint": fetch_one(
            "SELECT COUNT(*) FROM project_project p WHERE NOT %s AND p.operation_strategy IS DISTINCT FROM 'joint'"
            % scbs_project_domain_sql("p")
        )["count"],
    }

    checks.update(
        {
            "staging_total_expected": int(staging_total["rows"] or 0) == int(baseline["staging"]["total"]["rows"])
            and near(staging_total["amount"], baseline["staging"]["total"]["amount"]),
            "scbs_projects_are_direct": int(project_strategy["scbs_direct"] or 0) > 0
            and int(project_strategy["scbs_non_direct"] or 0) == 0,
            "existing_projects_are_joint": int(project_strategy["non_scbs_joint"] or 0) > 0
            and int(project_strategy["non_scbs_not_joint"] or 0) == 0,
            "no_non_direct_payment_execution": fetch_one(
                "SELECT COUNT(*) FROM sc_payment_execution WHERE legacy_source_model = '%s' AND operation_strategy <> 'direct'"
                % SOURCE_MODEL
            )["count"]
            == 0,
            "no_non_direct_payment_adjustment": fetch_one(
                "SELECT COUNT(*) FROM sc_legacy_payment_adjustment_fact WHERE legacy_source_model = '%s' AND operation_strategy <> 'direct'"
                % SOURCE_MODEL
            )["count"]
            == 0,
            "no_non_direct_enterprise_fact": fetch_one(
                "SELECT COUNT(*) FROM sc_legacy_enterprise_business_fact WHERE legacy_source_model = '%s' AND operation_strategy <> 'direct'"
                % SOURCE_MODEL
            )["count"]
            == 0,
            "no_non_direct_contract": fetch_one(
                "SELECT COUNT(*) FROM sc_general_contract WHERE legacy_source_model = '%s' AND operation_strategy <> 'direct'"
                % SOURCE_MODEL
            )["count"]
            == 0,
            "no_non_direct_stock": fetch_one(
                "SELECT COUNT(*) FROM sc_material_inbound WHERE legacy_fact_model = '%s' AND operation_strategy <> 'direct'"
                % SOURCE_MODEL
            )["count"]
            == 0,
            "fund_daily_no_project": count(
                "sc.legacy.fund.daily.snapshot.fact",
                [
                    ("legacy_source_table", "=", "D_SCBSJS_ZJGL_ZJSZ_ZJRBB"),
                    ("import_batch", "=", "scbs_fund_daily_enterprise_v1"),
                    ("project_id", "!=", False),
                ],
            )
            == 0,
            "fund_daily_all_have_entity": count(
                "sc.legacy.fund.daily.snapshot.fact",
                [
                    ("legacy_source_table", "=", "D_SCBSJS_ZJGL_ZJSZ_ZJRBB"),
                    ("import_batch", "=", "scbs_fund_daily_enterprise_v1"),
                    ("business_entity_id", "=", False),
                ],
            )
            == 0,
            "material_map_all_confirmed": count("sc.legacy.scbs.material.map", [("mapping_state", "!=", "confirmed")])
            == 0,
            "payment_source_unique": duplicate_count(
                "sc_payment_execution",
                "legacy_source_model = '%s'" % SOURCE_MODEL,
                "legacy_source_model, legacy_record_id",
            )
            == 0,
            "payment_adjustment_source_unique": duplicate_count(
                "sc_legacy_payment_adjustment_fact",
                "legacy_source_model = '%s'" % SOURCE_MODEL,
                "legacy_source_model, legacy_source_table, legacy_record_id",
            )
            == 0,
            "enterprise_fact_source_unique": duplicate_count(
                "sc_legacy_enterprise_business_fact",
                "legacy_source_model = '%s'" % SOURCE_MODEL,
                "legacy_source_model, legacy_source_table, legacy_record_id",
            )
            == 0,
            "contract_source_unique": duplicate_count(
                "sc_general_contract",
                "legacy_source_model = '%s'" % SOURCE_MODEL,
                "legacy_source_model, legacy_record_id",
            )
            == 0,
            "stock_source_unique": duplicate_count(
                "sc_material_inbound",
                "legacy_fact_model = '%s'" % SOURCE_MODEL,
                "legacy_fact_model, legacy_fact_id",
            )
            == 0,
            "fund_daily_source_unique": duplicate_count(
                "sc_legacy_fund_daily_snapshot_fact",
                "legacy_source_table = 'D_SCBSJS_ZJGL_ZJSZ_ZJRBB'",
                "legacy_source_table, legacy_record_id",
            )
            == 0,
        }
    )
    checks.update(closure_acceptance_checks(closure))
    observations = {
        "mode": "strict",
        "baseline": baseline,
        "closure": closure,
        "staging": staging_by_family,
        "staging_total": staging_total,
        "formal": {
            "payment_execution": {"rows": payment_execution_rows, "amount": payment_execution_amount},
            "payment_adjustment": {"rows": payment_adjustment_rows, "amount": payment_adjustment_amount},
            "enterprise_payment": {"rows": enterprise_payment_rows, "amount": enterprise_payment_amount},
            "contract": {"rows": contract_rows, "amount": contract_amount},
            "enterprise_contract": {"rows": enterprise_contract_rows, "amount": enterprise_contract_amount},
            "stock_in": {"rows": stock_rows, "amount": stock_amount},
            "fund_daily": {"rows": fund_rows, "amount": fund_amount},
        },
        "project_operation_strategy": project_strategy,
    }
    return checks, observations


def main() -> None:
    mode = os.getenv("SCBS_ACCEPTANCE_MODE", "strict").strip().lower()
    artifacts = artifact_root()
    output_json = artifacts / ("scbs_release_acceptance_%s_result_v1.json" % mode)
    output_md = artifacts / ("scbs_release_acceptance_%s_v1.md" % mode)

    if mode == "empty":
        checks, observations = empty_acceptance()
    elif mode == "strict":
        checks, observations = strict_acceptance()
    else:
        raise ValueError("Unsupported SCBS_ACCEPTANCE_MODE=%s" % mode)

    failed = [name for name, ok in checks.items() if not ok]
    status = "PASS" if not failed else "REVIEW_REQUIRED"
    payload = {
        "status": status,
        "database": env.cr.dbname,  # noqa: F821
        "mode": mode,
        "failed_checks": failed,
        "checks": checks,
        "observations": observations,
    }
    output_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = [
        "# SCBS Release Acceptance",
        "",
        "Status: `%s`" % status,
        "",
        "- database: `%s`" % env.cr.dbname,  # noqa: F821
        "- mode: `%s`" % mode,
        "- failed checks: `%s`" % (", ".join(failed) if failed else "none"),
        "",
        "## Checks",
        "",
        "| Check | Result |",
        "| --- | --- |",
    ]
    for name in sorted(checks):
        lines.append("| %s | %s |" % (name, "PASS" if checks[name] else "FAIL"))
    output_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("SCBS_RELEASE_ACCEPTANCE=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))


main()
