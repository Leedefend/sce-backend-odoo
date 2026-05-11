"""Project SCBS payment and supplier-contract facts into formal models.

Only rows with confirmed project_id are eligible. Negative payment rows are not
written to sc.payment.execution because that model enforces non-negative
amounts; they remain residual refund/reversal facts.

Dry-run by default. Set APPLY=1 to write.
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


def active_facts(domain_extra):
    domain = [
        ("import_batch", "=", "scbs_fact_staging_v1"),
        ("active", "=", True),
        ("mapping_gate_state", "=", "projection_ready"),
        ("project_id", "!=", False),
    ]
    domain.extend(domain_extra)
    return env["sc.legacy.scbs.fact.staging"].sudo().with_context(active_test=False).search(domain, order="document_date, id")  # noqa: F821


def existing_payment_keys():
    rows = env["sc.payment.execution"].sudo().with_context(active_test=False).search_read(  # noqa: F821
        [("legacy_source_model", "=", SOURCE_MODEL), ("legacy_source_table", "=", "T_FK_Supplier")],
        ["legacy_record_id"],
    )
    return {row["legacy_record_id"] for row in rows}


def existing_contract_keys():
    rows = env["sc.general.contract"].sudo().with_context(active_test=False).search_read(  # noqa: F821
        [("legacy_source_model", "=", SOURCE_MODEL), ("legacy_source_table", "=", "T_GYSHT_INFO")],
        ["legacy_record_id"],
    )
    return {row["legacy_record_id"] for row in rows}


def payment_values(fact):
    amount = fact.amount_total or 0.0
    return {
        "source_origin": "legacy",
        "source_kind": "actual_outflow",
        "state": "legacy_confirmed",
        "project_id": fact.project_id.id,
        "partner_id": fact.partner_id.id or False,
        "date_payment": fact.document_date,
        "document_no": fact.document_no,
        "payment_family": "SCBS供应商付款",
        "planned_amount": amount,
        "paid_amount": amount,
        "invoice_amount": 0.0,
        "legacy_source_model": SOURCE_MODEL,
        "legacy_source_table": fact.source_table,
        "legacy_record_id": fact.legacy_record_id,
        "legacy_document_state": fact.document_state,
        "legacy_residual_reason": "SCBS_PROJECT_FACT_IMPORT",
        "creator_legacy_user_id": fact.creator_legacy_user_id,
        "creator_name": fact.creator_name,
        "created_time": fact.created_time,
        "note": "\n".join(
            item
            for item in [
                "SCBS历史供应商付款事实迁入。",
                f"legacy_partner_name={fact.legacy_partner_name or ''}",
                f"legacy_xmid={fact.legacy_xmid or ''}",
                f"legacy_xmmc={fact.legacy_xmmc or ''}",
                f"legacy_gcmc={fact.legacy_gcmc or ''}",
            ]
            if item
        ),
    }


def contract_values(fact):
    return {
        "source_origin": "legacy",
        "state": "legacy_confirmed",
        "project_id": fact.project_id.id,
        "partner_id": fact.partner_id.id or False,
        "partner_name_text": fact.legacy_partner_name,
        "document_no": fact.document_no,
        "contract_no": fact.document_no,
        "contract_name": fact.document_no or fact.legacy_partner_name or f"SCBS供应商合同-{fact.legacy_record_id}",
        "contract_type": "SCBS供应商合同",
        "contract_date": fact.document_date,
        "amount_total": fact.amount_total or 0.0,
        "legacy_source_model": SOURCE_MODEL,
        "legacy_source_table": fact.source_table,
        "legacy_record_id": fact.legacy_record_id,
        "legacy_document_state": fact.document_state,
        "creator_legacy_user_id": fact.creator_legacy_user_id,
        "creator_name": fact.creator_name,
        "created_time": fact.created_time,
        "note": "\n".join(
            item
            for item in [
                "SCBS历史供应商合同事实迁入。",
                f"legacy_partner_name={fact.legacy_partner_name or ''}",
                f"legacy_xmid={fact.legacy_xmid or ''}",
                f"legacy_xmmc={fact.legacy_xmmc or ''}",
                f"legacy_gcmc={fact.legacy_gcmc or ''}",
            ]
            if item
        ),
    }


def supported_values(model, values: dict[str, object]) -> dict[str, object]:
    return {key: value for key, value in values.items() if key in model._fields}


def main() -> None:
    apply = os.getenv("APPLY") == "1"
    artifacts = artifact_root()
    plan_csv = artifacts / "scbs_payment_contract_projection_plan_v1.csv"
    residual_csv = artifacts / "scbs_payment_contract_projection_residual_v1.csv"
    result_json = artifacts / "scbs_payment_contract_projection_result_v1.json"

    Payment = env["sc.payment.execution"].sudo()  # noqa: F821
    Contract = env["sc.general.contract"].sudo()  # noqa: F821
    payment_existing = existing_payment_keys()
    contract_existing = existing_contract_keys()

    positive_payments = active_facts([("fact_family", "=", "payment"), ("amount_total", ">=", 0)])
    negative_payments = active_facts([("fact_family", "=", "payment"), ("amount_total", "<", 0)])
    contracts = active_facts([("fact_family", "=", "supplier_contract")])

    plan_rows: list[dict[str, object]] = []
    residual_rows: list[dict[str, object]] = []
    created_payments = 0
    created_contracts = 0
    skipped_existing = 0

    for fact in positive_payments:
        exists = fact.legacy_record_id in payment_existing
        action = "skip_existing" if exists else "create_payment_execution"
        if exists:
            skipped_existing += 1
        elif apply:
            Payment.create(supported_values(Payment, payment_values(fact)))
            created_payments += 1
        plan_rows.append(
            {
                "fact_family": "payment",
                "staging_id": fact.id,
                "legacy_record_id": fact.legacy_record_id,
                "document_no": fact.document_no,
                "project_id": fact.project_id.id,
                "project_name": fact.project_id.display_name,
                "amount_total": fact.amount_total,
                "target_model": "sc.payment.execution",
                "action": action,
            }
        )

    for fact in contracts:
        exists = fact.legacy_record_id in contract_existing
        action = "skip_existing" if exists else "create_general_contract"
        if exists:
            skipped_existing += 1
        elif apply:
            Contract.create(supported_values(Contract, contract_values(fact)))
            created_contracts += 1
        plan_rows.append(
            {
                "fact_family": "supplier_contract",
                "staging_id": fact.id,
                "legacy_record_id": fact.legacy_record_id,
                "document_no": fact.document_no,
                "project_id": fact.project_id.id,
                "project_name": fact.project_id.display_name,
                "amount_total": fact.amount_total,
                "target_model": "sc.general.contract",
                "action": action,
            }
        )

    for fact in negative_payments:
        residual_rows.append(
            {
                "fact_family": "payment_negative",
                "staging_id": fact.id,
                "legacy_record_id": fact.legacy_record_id,
                "document_no": fact.document_no,
                "project_id": fact.project_id.id,
                "project_name": fact.project_id.display_name,
                "amount_total": fact.amount_total,
                "reason": "negative_payment_requires_refund_or_reversal_target",
            }
        )

    write_csv(
        plan_csv,
        plan_rows,
        [
            "fact_family",
            "staging_id",
            "legacy_record_id",
            "document_no",
            "project_id",
            "project_name",
            "amount_total",
            "target_model",
            "action",
        ],
    )
    write_csv(
        residual_csv,
        residual_rows,
        [
            "fact_family",
            "staging_id",
            "legacy_record_id",
            "document_no",
            "project_id",
            "project_name",
            "amount_total",
            "reason",
        ],
    )

    if apply:
        env.cr.commit()  # noqa: F821

    payload = {
        "status": "APPLIED" if apply else "DRY_RUN",
        "database": env.cr.dbname,  # noqa: F821
        "plan_csv": str(plan_csv),
        "residual_csv": str(residual_csv),
        "planned_rows": len(plan_rows),
        "planned_payment_rows": len(positive_payments),
        "planned_contract_rows": len(contracts),
        "negative_payment_residual_rows": len(negative_payments),
        "created_payments": created_payments,
        "created_contracts": created_contracts,
        "skipped_existing": skipped_existing,
    }
    write_json(result_json, payload)
    print("SCBS_PAYMENT_CONTRACT_PROJECTION=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))


main()
