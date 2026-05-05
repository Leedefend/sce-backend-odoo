"""Project SCBS fund daily rows as enterprise business documents.

Policy:
- fund daily is an enterprise/business-entity document, not a project document;
- business_entity_id is required by this projection;
- project_id stays empty unless a future source row has explicit project
  evidence.

Dry-run by default. Set APPLY=1 to write.
"""

from __future__ import annotations

import csv
import json
import os
from pathlib import Path


SOURCE_TABLE = "D_SCBSJS_ZJGL_ZJSZ_ZJRBB"


def artifact_root() -> Path:
    env_root = os.getenv("MIGRATION_ARTIFACT_ROOT")
    candidates = [Path(env_root)] if env_root else []
    candidates.extend([Path.cwd() / "artifacts/migration", Path("/mnt/artifacts/migration"), Path("/tmp")])
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return Path("artifacts/migration")


def repo_root() -> Path:
    env_root = os.getenv("MIGRATION_REPO_ROOT")
    candidates = [Path(env_root)] if env_root else []
    candidates.extend([Path("/mnt"), Path.cwd()])
    for candidate in candidates:
        if (candidate / "addons/smart_construction_core/__manifest__.py").exists():
            return candidate
    return Path.cwd()


def to_float(value: str | None) -> float:
    try:
        return float(value or 0)
    except ValueError:
        return 0.0


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


def read_source(path: Path) -> dict[str, dict[str, str]]:
    if not path.exists():
        raise RuntimeError({"missing_fund_daily_source_csv": str(path)})
    with path.open(encoding="utf-8-sig") as handle:
        return {row["legacy_record_id"]: row for row in csv.DictReader(handle)}


def main() -> None:
    apply = os.getenv("APPLY") == "1"
    artifacts = artifact_root()
    source_csv = Path(os.getenv("SCBS_FUND_DAILY_SOURCE_CSV") or (repo_root() / "artifacts/migration/scbs_fund_daily_source_v1.csv"))
    plan_csv = artifacts / "scbs_fund_daily_enterprise_projection_plan_v1.csv"
    residual_csv = artifacts / "scbs_fund_daily_enterprise_projection_residual_v1.csv"
    result_json = artifacts / "scbs_fund_daily_enterprise_projection_result_v1.json"

    source_by_id = read_source(source_csv)
    Fact = env["sc.legacy.scbs.fact.staging"].sudo().with_context(active_test=False)  # noqa: F821
    Target = env["sc.legacy.fund.daily.snapshot.fact"].sudo().with_context(active_test=False)  # noqa: F821
    facts = Fact.search(
        [
            ("import_batch", "=", "scbs_fact_staging_v1"),
            ("active", "=", True),
            ("mapping_gate_state", "=", "projection_ready"),
            ("fact_family", "=", "fund_daily"),
        ],
        order="document_date, id",
    )
    existing = Target.search_read([("legacy_source_table", "=", SOURCE_TABLE)], ["legacy_record_id"])
    existing_ids = {row["legacy_record_id"] for row in existing}

    plan_rows: list[dict[str, object]] = []
    residual_rows: list[dict[str, object]] = []
    created = 0
    skipped_existing = 0
    blocked = 0
    account_balance_total = 0.0
    bank_balance_total = 0.0
    bank_system_difference_total = 0.0

    for fact in facts:
        source = source_by_id.get(fact.legacy_record_id, {})
        reason = ""
        action = "create_enterprise_fund_daily"
        if fact.legacy_record_id in existing_ids:
            action = "skip_existing"
            skipped_existing += 1
        elif not fact.business_entity_id:
            action = "blocked"
            reason = "missing_business_entity"
            blocked += 1
        elif not source:
            action = "blocked"
            reason = "missing_source_detail"
            blocked += 1

        account_balance = to_float(source.get("source_account_balance_total")) if source else fact.amount_total or 0.0
        bank_balance = to_float(source.get("source_bank_balance_total")) if source else 0.0
        bank_system_difference = to_float(source.get("source_bank_system_difference")) if source else 0.0

        if action == "create_enterprise_fund_daily":
            account_balance_total += account_balance
            bank_balance_total += bank_balance
            bank_system_difference_total += bank_system_difference
            if apply:
                Target.create(
                    {
                        "legacy_source_table": SOURCE_TABLE,
                        "legacy_record_id": fact.legacy_record_id,
                        "legacy_pid": source.get("legacy_pid") or fact.legacy_pid or False,
                        "source_family": "SCBS企业资金日报",
                        "document_no": source.get("document_no") or fact.document_no,
                        "snapshot_date": fact.document_date,
                        "legacy_state": source.get("document_state") or fact.document_state,
                        "subject": source.get("subject") or fact.document_no or "SCBS企业资金日报",
                        "company_id": fact.business_entity_id.company_id.id,
                        "business_entity_id": fact.business_entity_id.id,
                        "project_id": False,
                        "legacy_project_id": False,
                        "legacy_project_name": False,
                        "legacy_business_entity_id": fact.legacy_xmid,
                        "legacy_business_entity_name": fact.legacy_xmmc,
                        "document_scope": "enterprise",
                        "source_account_balance_total": account_balance,
                        "source_bank_balance_total": bank_balance,
                        "source_bank_system_difference": bank_system_difference,
                        "note": "\n".join(
                            [
                                "SCBS企业资金日报正式迁入。",
                                "资金日报按业务核算主体承接，不绑定项目。",
                                "legacy_xmid=%s" % (fact.legacy_xmid or ""),
                                "legacy_xmmc=%s" % (fact.legacy_xmmc or ""),
                                "source_note=%s" % (source.get("note") or ""),
                            ]
                        ),
                        "import_batch": "scbs_fund_daily_enterprise_v1",
                    }
                )
                created += 1

        row = {
            "staging_id": fact.id,
            "legacy_record_id": fact.legacy_record_id,
            "document_no": fact.document_no,
            "document_date": fact.document_date,
            "business_entity_id": fact.business_entity_id.id if fact.business_entity_id else "",
            "business_entity_name": fact.business_entity_id.display_name if fact.business_entity_id else "",
            "source_account_balance_total": account_balance,
            "source_bank_balance_total": bank_balance,
            "source_bank_system_difference": bank_system_difference,
            "action": action,
            "reason": reason,
        }
        plan_rows.append(row)
        if action == "blocked":
            residual_rows.append(row)

    if apply:
        env.cr.commit()  # noqa: F821

    fields = [
        "staging_id",
        "legacy_record_id",
        "document_no",
        "document_date",
        "business_entity_id",
        "business_entity_name",
        "source_account_balance_total",
        "source_bank_balance_total",
        "source_bank_system_difference",
        "action",
        "reason",
    ]
    write_csv(plan_csv, plan_rows, fields)
    write_csv(residual_csv, residual_rows, fields)
    payload = {
        "status": "APPLIED" if apply else "DRY_RUN",
        "database": env.cr.dbname,  # noqa: F821
        "source_csv": str(source_csv),
        "eligible_rows": len(facts),
        "planned_rows": len([row for row in plan_rows if row["action"] == "create_enterprise_fund_daily"]),
        "created_rows": created,
        "skipped_existing": skipped_existing,
        "blocked_rows": blocked,
        "source_account_balance_total": account_balance_total,
        "source_bank_balance_total": bank_balance_total,
        "source_bank_system_difference_total": bank_system_difference_total,
        "plan_csv": str(plan_csv),
        "residual_csv": str(residual_csv),
    }
    write_json(result_json, payload)
    print("SCBS_FUND_DAILY_ENTERPRISE_PROJECTION=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))


main()
