"""Compare a no-legacy replay database with the accepted rebuild baseline."""

from __future__ import annotations

import json
import os
from pathlib import Path


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
    columns = [desc[0] for desc in env.cr.description]  # noqa: F821
    row = env.cr.fetchone()  # noqa: F821
    return dict(zip(columns, row or []))


def fetch_rows(sql: str) -> list[dict[str, object]]:
    env.cr.execute(sql)  # noqa: F821
    columns = [desc[0] for desc in env.cr.description]  # noqa: F821
    return [dict(zip(columns, row)) for row in env.cr.fetchall()]  # noqa: F821


def count_amount(sql: str) -> dict[str, object]:
    row = fetch_one(sql)
    return {"rows": int(row.get("rows") or 0), "amount": round(float(row.get("amount") or 0.0), 2)}


def by_key(rows: list[dict[str, object]], key: str) -> dict[str, dict[str, object]]:
    return {str(row[key]): row for row in rows}


def near(left: object, right: object) -> bool:
    return abs(float(left or 0) - float(right or 0)) < 0.01


def load_closure(artifacts: Path) -> dict[str, object]:
    path = artifacts / "scbs_migration_closure_reconciliation_result_v1.json"
    if not path.exists():
        return {"status": "MISSING", "path": str(path)}
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["path"] = str(path)
    return payload


def closure_checks(closure: dict[str, object]) -> dict[str, bool]:
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


def main() -> None:
    root = repo_root()
    artifacts = artifact_root()
    baseline_path = root / "artifacts/migration/scbs_replay_expected_baseline_v1.json"
    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
    closure = load_closure(artifacts)

    actual = {
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
                "SELECT COUNT(*) AS rows, ROUND(COALESCE(SUM(paid_amount), 0)::numeric, 2) AS amount FROM sc_payment_execution WHERE legacy_source_model = 'sc.legacy.scbs.fact.staging'"
            ),
            "payment_adjustment": count_amount(
                "SELECT COUNT(*) AS rows, ROUND(COALESCE(SUM(source_amount), 0)::numeric, 2) AS amount FROM sc_legacy_payment_adjustment_fact WHERE legacy_source_model = 'sc.legacy.scbs.fact.staging'"
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
                "SELECT COUNT(*) AS rows, ROUND(COALESCE(SUM(amount_total), 0)::numeric, 2) AS amount FROM sc_general_contract WHERE legacy_source_model = 'sc.legacy.scbs.fact.staging'"
            ),
            "stock_in": count_amount(
                "SELECT COUNT(*) AS rows, ROUND(COALESCE(SUM(amount_total), 0)::numeric, 2) AS amount FROM sc_material_inbound WHERE legacy_fact_model = 'sc.legacy.scbs.fact.staging'"
            ),
            "fund_daily": count_amount(
                "SELECT COUNT(*) AS rows, ROUND(COALESCE(SUM(source_account_balance_total), 0)::numeric, 2) AS amount FROM sc_legacy_fund_daily_snapshot_fact WHERE legacy_source_table = 'D_SCBSJS_ZJGL_ZJSZ_ZJRBB' AND import_batch = 'scbs_fund_daily_enterprise_v1'"
            ),
        },
    }

    checks: dict[str, bool] = {
        "staging_total_baseline": int(actual["staging"]["total"]["rows"]) == int(baseline["staging"]["total"]["rows"])
        and near(actual["staging"]["total"]["amount"], baseline["staging"]["total"]["amount"]),
    }
    checks.update(closure_checks(closure))

    payload = {
        "status": "PASS" if all(checks.values()) else "FAIL",
        "database": env.cr.dbname,  # noqa: F821
        "baseline": str(baseline_path),
        "closure": closure,
        "checks": checks,
        "actual": actual,
        "expected": {
            "staging_total": baseline["staging"]["total"],
        },
    }
    output = artifacts / "scbs_no_legacy_replay_acceptance_result_v1.json"
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("SCBS_NO_LEGACY_REPLAY_ACCEPTANCE=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
    if payload["status"] != "PASS":
        raise RuntimeError(payload)


main()
