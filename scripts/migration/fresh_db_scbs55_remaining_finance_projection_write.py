#!/usr/bin/env python3
"""Project the remaining SCBS55 finance menus from verified legacy facts."""

from __future__ import annotations

import csv
import json
import os
from pathlib import Path


def repo_root() -> Path:
    env_root = os.getenv("MIGRATION_REPO_ROOT")
    candidates = [Path(env_root)] if env_root else []
    candidates.extend([Path("/mnt"), Path.cwd()])
    for candidate in candidates:
        if (candidate / "artifacts/migration/fresh_db_legacy_employee_loan_replay_payload_v1.csv").exists():
            return candidate
    return Path.cwd()


def artifact_root() -> Path:
    env_root = os.getenv("MIGRATION_ARTIFACT_ROOT")
    candidates = [Path(env_root)] if env_root else []
    candidates.append(REPO_ROOT / "artifacts" / "migration")
    candidates.append(Path("/mnt/artifacts/migration"))
    for candidate in candidates:
        try:
            candidate.mkdir(parents=True, exist_ok=True)
            probe = candidate / ".write_probe"
            probe.write_text("ok\n", encoding="utf-8")
            probe.unlink()
            return candidate
        except Exception:
            continue
    return Path(f"/tmp/scbs55_remaining_finance/{env.cr.dbname}")  # noqa: F821


def ensure_allowed_db() -> None:
    allowlist = {
        item.strip()
        for item in os.getenv("MIGRATION_REPLAY_DB_ALLOWLIST", "sc_migration_fresh,sc_demo").split(",")
        if item.strip()
    }
    if env.cr.dbname not in allowlist:  # noqa: F821
        raise RuntimeError({"db_name_not_allowed_for_replay": env.cr.dbname, "allowlist": sorted(allowlist)})  # noqa: F821


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def clean(value: object) -> str:
    return str(value or "").strip()


def as_float(value: object) -> float:
    text = clean(value)
    return float(text) if text else 0.0


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def project_id_for(legacy_project_id: str, project_name: str) -> int:
    Project = env["project.project"].sudo().with_context(active_test=False)  # noqa: F821
    project = Project.browse()
    if legacy_project_id:
        project = Project.search([("legacy_project_id", "=", legacy_project_id)], limit=1)
    if not project and project_name:
        project = Project.search([("name", "=", project_name)], limit=1)
    if project:
        return project.id
    fallback_name = project_name or "历史未归集资金项目"
    return Project.create({"name": fallback_name, "legacy_project_id": legacy_project_id or False}).id


def state_from_legacy(value: str) -> str:
    return "legacy_confirmed" if clean(value) in {"2", "已通过", "已确认", "已完成"} else "draft"


def loan_values_from_employee_row(row: dict[str, str]) -> dict[str, object]:
    source_table = clean(row.get("source_table"))
    legacy_record_id = clean(row.get("legacy_record_id"))
    document_date = clean(row.get("document_date")) or False
    amount = as_float(row.get("amount"))
    purpose = clean(row.get("purpose"))
    counterparty_name = clean(row.get("counterparty_name"))
    account_name = clean(row.get("account_name"))
    extra_parts = [
        clean(row.get("source_extra_ref")),
        clean(row.get("source_extra_label")),
        account_name,
    ]
    return {
        "name": clean(row.get("document_no")) or f"{source_table}-{legacy_record_id}",
        "source_origin": "legacy",
        "loan_type": clean(row.get("loan_type")) or "borrowing_request",
        "direction": clean(row.get("direction")) or "borrowed_fund",
        "state": state_from_legacy(clean(row.get("legacy_state"))),
        "project_id": project_id_for(clean(row.get("project_legacy_id")), clean(row.get("project_name"))),
        "document_no": clean(row.get("document_no")) or False,
        "document_date": document_date,
        "due_date": clean(row.get("due_date")) or False,
        "amount": max(amount, 0.0),
        "currency_id": env.company.currency_id.id,  # noqa: F821
        "purpose": purpose or clean(row.get("note")) or False,
        "rate_label": clean(row.get("source_type_label")) or False,
        "extra_ref": " / ".join(part for part in extra_parts if part) or False,
        "extra_label": "还款登记" if source_table == "BGGL_JHK_HKDJ" else "借款申请",
        "legacy_source_model": "sc.legacy.employee.loan",
        "legacy_source_table": source_table,
        "legacy_record_id": f"{source_table}:{legacy_record_id}",
        "legacy_document_state": clean(row.get("legacy_state")) or False,
        "legacy_counterparty_id": clean(row.get("counterparty_legacy_id")) or False,
        "legacy_counterparty_name": counterparty_name or False,
        "legacy_amount_field": clean(row.get("amount_field")) or False,
        "creator_legacy_user_id": clean(row.get("creator_legacy_user_id")) or False,
        "creator_name": clean(row.get("creator_name")) or False,
        "created_time": clean(row.get("created_time")) or False,
        "note": "\n".join(
            part
            for part in [
                "[migration:employee_loan]",
                f"source_table={source_table}",
                f"legacy_record_id={legacy_record_id}",
                f"counterparty={counterparty_name}",
                clean(row.get("note")),
            ]
            if part
        ),
        "active": True,
    }


def upsert_loan(values: dict[str, object]) -> str:
    Loan = env["sc.financing.loan"].sudo().with_context(active_test=False)  # noqa: F821
    existing = Loan.search(
        [
            ("legacy_source_model", "=", values["legacy_source_model"]),
            ("legacy_record_id", "=", values["legacy_record_id"]),
        ],
        limit=1,
    )
    if existing:
        env.cr.execute(  # noqa: F821
            """
            UPDATE sc_financing_loan
               SET loan_type = %s,
                   direction = %s,
                   state = %s,
                   project_id = %s,
                   document_no = %s,
                   document_date = %s,
                   due_date = %s,
                   amount = %s,
                   purpose = %s,
                   rate_label = %s,
                   extra_ref = %s,
                   extra_label = %s,
                   legacy_source_table = %s,
                   legacy_document_state = %s,
                   legacy_counterparty_id = %s,
                   legacy_counterparty_name = %s,
                   legacy_amount_field = %s,
                   creator_legacy_user_id = %s,
                   creator_name = %s,
                   created_time = %s,
                   note = %s,
                   active = TRUE,
                   write_uid = 1,
                   write_date = NOW()
             WHERE id = %s
            """,
            [
                values["loan_type"],
                values["direction"],
                values["state"],
                values["project_id"],
                values["document_no"],
                values["document_date"],
                values["due_date"],
                values["amount"],
                values["purpose"],
                values["rate_label"],
                values["extra_ref"],
                values["extra_label"],
                values["legacy_source_table"],
                values["legacy_document_state"],
                values["legacy_counterparty_id"],
                values["legacy_counterparty_name"],
                values["legacy_amount_field"],
                values["creator_legacy_user_id"],
                values["creator_name"],
                values["created_time"],
                values["note"],
                existing.id,
            ],
        )
        return "updated"
    Loan.create(values)
    return "created"


def project_employee_loans(input_csv: Path) -> dict[str, object]:
    rows = read_csv(input_csv)
    stats = {"rows": len(rows), "created": 0, "updated": 0, "skipped_no_amount": 0, "by_source": {}}
    for row in rows:
        values = loan_values_from_employee_row(row)
        if not values["amount"]:
            stats["skipped_no_amount"] += 1
            continue
        result = upsert_loan(values)
        stats[result] += 1
        source_table = values["legacy_source_table"]
        by_source = stats["by_source"]
        by_source[source_table] = by_source.get(source_table, 0) + 1
    return stats


def project_project_company_repayments() -> dict[str, object]:
    Line = env["sc.legacy.account.transaction.line"].sudo().with_context(active_test=False)  # noqa: F821
    domain = [("source_table", "=", "ZJGL_ZJSZ_DKGL_HKDJ"), ("amount", ">", 0), ("project_id", "!=", False)]
    stats = {"candidate_count": Line.search_count(domain), "created": 0, "updated": 0}
    for line in Line.search(domain, order="transaction_date desc, id desc"):
        values = {
            "name": clean(line.document_no) or f"ZJGL_ZJSZ_DKGL_HKDJ-{line.legacy_record_id}",
            "source_origin": "legacy",
            "loan_type": "borrowing_request",
            "direction": "borrowed_fund",
            "state": state_from_legacy(clean(line.document_state)),
            "project_id": line.project_id.id,
            "document_no": clean(line.document_no) or False,
            "document_date": line.transaction_date or False,
            "due_date": line.transaction_date or False,
            "amount": float(line.amount or 0.0),
            "currency_id": env.company.currency_id.id,  # noqa: F821
            "purpose": clean(line.source_summary) or "项目还公司款登记",
            "rate_label": clean(line.category) or False,
            "extra_ref": clean(line.account_name) or False,
            "extra_label": "项目还公司款登记",
            "legacy_source_model": "sc.legacy.account.transaction.line",
            "legacy_source_table": line.source_table,
            "legacy_record_id": clean(line.source_key) or f"{line.source_table}:{line.legacy_record_id}",
            "legacy_document_state": clean(line.document_state) or False,
            "legacy_counterparty_id": clean(line.counterparty_account_legacy_id) or False,
            "legacy_counterparty_name": clean(line.counterparty_account_name) or False,
            "legacy_amount_field": "HKJE",
            "note": clean(line.note) or False,
            "active": True,
        }
        result = upsert_loan(values)
        stats[result] += 1
    return stats


def project_deduction_bills() -> dict[str, object]:
    Residual = env["sc.legacy.payment.residual.fact"].sudo().with_context(active_test=False)  # noqa: F821
    Target = env["sc.tax.deduction.registration"].sudo().with_context(active_test=False)  # noqa: F821
    domain = [("source_table", "=", "C_ZFSQGL_KKD"), ("project_id", "!=", False), ("planned_amount", ">", 0)]
    stats = {"candidate_count": Residual.search_count(domain), "created": 0, "updated": 0}
    for item in Residual.search(domain, order="document_date desc, id desc"):
        amount = float(item.planned_amount or 0.0)
        values = {
            "name": clean(item.document_no) or f"KKD-{item.legacy_record_id}",
            "source_origin": "legacy",
            "state": state_from_legacy(clean(item.document_state)),
            "document_no": clean(item.document_no) or False,
            "document_date": item.document_date or False,
            "project_id": item.project_id.id,
            "partner_id": item.partner_id.id or False,
            "partner_name": clean(item.partner_name) or clean(item.taxpayer_name) or False,
            "deduction_amount": amount,
            "deduction_tax_amount": 0.0,
            "deduction_surcharge_amount": 0.0,
            "currency_id": env.company.currency_id.id,  # noqa: F821
            "legacy_source_model": "sc.legacy.payment.residual.fact",
            "legacy_source_table": item.source_table,
            "legacy_record_id": f"{item.source_table}:{item.legacy_record_id}",
            "legacy_document_state": clean(item.document_state) or False,
            "creator_legacy_user_id": clean(item.creator_legacy_user_id) or False,
            "creator_name": clean(item.creator_name) or False,
            "created_time": item.created_time or False,
            "note": "\n".join(
                part
                for part in [
                    clean(item.residual_reason),
                    clean(item.note),
                    f"[migration:deduction_bill] legacy_record_id={item.legacy_record_id}",
                ]
                if part
            ),
            "active": True,
        }
        existing = Target.search(
            [
                ("legacy_source_model", "=", values["legacy_source_model"]),
                ("legacy_record_id", "=", values["legacy_record_id"]),
            ],
            limit=1,
        )
        if existing:
            env.cr.execute(  # noqa: F821
                """
                UPDATE sc_tax_deduction_registration
                   SET state = %s,
                       document_no = %s,
                       document_date = %s,
                       project_id = %s,
                       partner_id = %s,
                       partner_name = %s,
                       deduction_amount = %s,
                       legacy_source_table = %s,
                       legacy_document_state = %s,
                       creator_legacy_user_id = %s,
                       creator_name = %s,
                       created_time = %s,
                       note = %s,
                       active = TRUE,
                       write_uid = 1,
                       write_date = NOW()
                 WHERE id = %s
                """,
                [
                    values["state"],
                    values["document_no"],
                    values["document_date"],
                    values["project_id"],
                    values["partner_id"],
                    values["partner_name"],
                    values["deduction_amount"],
                    values["legacy_source_table"],
                    values["legacy_document_state"],
                    values["creator_legacy_user_id"],
                    values["creator_name"],
                    values["created_time"],
                    values["note"],
                    existing.id,
                ],
            )
            stats["updated"] += 1
            continue
        Target.create(values)
        stats["created"] += 1
    return stats


REPO_ROOT = repo_root()
ARTIFACT_ROOT = artifact_root()
INPUT_CSV = REPO_ROOT / "artifacts" / "migration" / "fresh_db_legacy_employee_loan_replay_payload_v1.csv"
OUTPUT_JSON = ARTIFACT_ROOT / "fresh_db_scbs55_remaining_finance_projection_write_result_v1.json"

ensure_allowed_db()
employee = project_employee_loans(INPUT_CSV)
project_repay = project_project_company_repayments()
deduction = project_deduction_bills()

env.cr.commit()  # noqa: F821

payload = {
    "status": "PASS",
    "mode": "fresh_db_scbs55_remaining_finance_projection_write",
    "database": env.cr.dbname,  # noqa: F821
    "employee_loans": employee,
    "project_company_repayments": project_repay,
    "deduction_bills": deduction,
}
write_json(OUTPUT_JSON, payload)
print("SCBS55_REMAINING_FINANCE_PROJECTION_WRITE=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
