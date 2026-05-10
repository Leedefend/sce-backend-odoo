#!/usr/bin/env python3
"""Classify remaining business fact backfill gaps without mutating data.

Run through ``scripts/ops/odoo_shell_exec.sh`` so the global ``env`` is
available. The classifier is deliberately evidence-only: if old-system creator,
time, amount, or balance fields are absent, it records that as a residual gap
instead of falling back to Odoo import metadata.
"""

from __future__ import annotations

import csv
import json
import os
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


DB_NAME = env.cr.dbname  # noqa: F821
ROOT = Path(os.getenv("BUSINESS_FACT_RESIDUAL_ROOT") or f"/mnt/artifacts/business-fact-audit/{DB_NAME}_residual_gap_classifier")


def clean(value) -> str:
    if value in (None, False):
        return ""
    text = str(value).strip()
    return "" if text.lower() in {"false", "none", "null"} else text


def rows(sql: str, params: list[object] | None = None) -> list[dict[str, object]]:
    env.cr.execute(sql, params or [])  # noqa: F821
    columns = [desc[0] for desc in env.cr.description]  # noqa: F821
    return [dict(zip(columns, row)) for row in env.cr.fetchall()]  # noqa: F821


def write_csv(path: Path, csv_rows: list[dict[str, object]]) -> None:
    if not csv_rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(csv_rows[0]), extrasaction="ignore")
        writer.writeheader()
        writer.writerows(csv_rows)


def model_exists(model_name: str) -> bool:
    return model_name in env.registry  # noqa: F821


def fact_field_values(record, field_names: tuple[str, ...]) -> list[str]:
    values: list[str] = []
    for field_name in field_names:
        if field_name not in record._fields:
            continue
        value = getattr(record, field_name)
        if hasattr(value, "display_name"):
            value = value.display_name
        text = clean(value)
        if text:
            values.append(text)
    return values


def classify_partner_residuals() -> tuple[dict[str, object], list[dict[str, object]]]:
    Partner = env["res.partner"].sudo().with_context(active_test=False)  # noqa: F821
    partners = Partner.search(
        [
            ("sc_source_fact_count", ">", 0),
            "|",
            ("customer_rank", ">", 0),
            ("supplier_rank", ">", 0),
            "|",
            ("sc_source_created_by", "=", False),
            ("sc_source_created_at", "=", False),
        ]
    )
    fact_models = (
        "construction.contract",
        "sc.receipt.income",
        "payment.request",
        "sc.legacy.receipt.residual.fact",
        "sc.payment.execution",
        "sc.legacy.payment.residual.fact",
        "sc.settlement.order",
        "sc.legacy.enterprise.business.fact",
        "sc.legacy.expense.deposit.fact",
        "sc.legacy.supplier.contract.pricing.fact",
        "sc.legacy.invoice.registration.line",
    )
    source_counter: Counter[str] = Counter()
    missing_shape_counter: Counter[str] = Counter()
    objective_field_counter: Counter[str] = Counter()
    detail_rows: list[dict[str, object]] = []
    for partner in partners:
        source_text = clean(partner.sc_source_fact_source)
        for source in [part for part in source_text.split("；") if part]:
            source_counter[source] += 1
        if not partner.sc_source_created_by and not partner.sc_source_created_at:
            missing_shape_counter["missing_creator_and_time"] += 1
        elif not partner.sc_source_created_by:
            missing_shape_counter["missing_creator_only"] += 1
        elif not partner.sc_source_created_at:
            missing_shape_counter["missing_time_only"] += 1
        if "示例" in clean(partner.name):
            missing_shape_counter["example_named_partner"] += 1

        fact_summary: Counter[str] = Counter()
        for model_name in fact_models:
            if not model_exists(model_name):
                continue
            Model = env[model_name].sudo().with_context(active_test=False)  # noqa: F821
            if "partner_id" not in Model._fields:
                continue
            for record in Model.search([("partner_id", "=", partner.id)], limit=200):
                creator_values = fact_field_values(
                    record,
                    ("creator_name", "created_by_name", "source_operator", "entry_user_text"),
                )
                time_values = fact_field_values(record, ("created_time", "source_time", "legacy_created_at", "entry_time"))
                if creator_values:
                    fact_summary[f"{model_name}:creator_present"] += 1
                else:
                    fact_summary[f"{model_name}:creator_blank"] += 1
                if time_values:
                    fact_summary[f"{model_name}:time_present"] += 1
                else:
                    fact_summary[f"{model_name}:time_blank"] += 1
        for key, count in fact_summary.items():
            objective_field_counter[key] += count
        detail_rows.append(
            {
                "partner_id": partner.id,
                "name": partner.name,
                "customer_rank": partner.customer_rank,
                "supplier_rank": partner.supplier_rank,
                "source_fact_count": partner.sc_source_fact_count,
                "source_fact_source": partner.sc_source_fact_source,
                "source_created_by": partner.sc_source_created_by,
                "source_created_at": partner.sc_source_created_at,
                "fact_field_summary": json.dumps(dict(sorted(fact_summary.items())), ensure_ascii=False, sort_keys=True),
            }
        )
    return (
        {
            "partner_residual_total": len(partners),
            "missing_shape_counts": dict(sorted(missing_shape_counter.items())),
            "source_label_counts": dict(sorted(source_counter.items())),
            "objective_fact_field_counts": dict(sorted(objective_field_counter.items())),
            "decision": "do_not_use_odoo_import_metadata_as_business_fact",
        },
        detail_rows,
    )


def classify_contract_residuals() -> tuple[dict[str, object], list[dict[str, object]], list[dict[str, object]]]:
    amount_rows = rows(
        """
        SELECT id AS contract_id,
               type,
               legacy_contract_id,
               legacy_document_no,
               legacy_contract_no,
               subject,
               legacy_contract_amount,
               amount_untaxed,
               visible_contract_amount,
               entry_user_text,
               entry_time,
               note
          FROM construction_contract
         WHERE legacy_contract_id IS NOT NULL
           AND COALESCE(visible_contract_amount, 0) = 0
         ORDER BY type, legacy_document_no, id
        """
    )
    balance_rows = rows(
        """
        SELECT id AS contract_id,
               legacy_contract_id,
               legacy_document_no,
               legacy_contract_no,
               subject,
               visible_contract_amount,
               visible_received_amount,
               visible_unreceived_amount
          FROM construction_contract
         WHERE type = 'out'
           AND COALESCE(visible_contract_amount, 0) <> 0
           AND (visible_received_amount IS NULL OR visible_unreceived_amount IS NULL)
         ORDER BY legacy_document_no, id
        """
    )
    supplier_entry_rows = rows(
        """
        SELECT id AS contract_id,
               type,
               legacy_contract_id,
               legacy_document_no,
               legacy_contract_no,
               subject,
               entry_user_text,
               entry_time,
               note
          FROM construction_contract
         WHERE legacy_contract_id IS NOT NULL
           AND type = 'in'
           AND (COALESCE(entry_user_text, '') = '' OR entry_time IS NULL)
         ORDER BY legacy_document_no, id
        """
    )
    amount_type_counts = Counter(clean(row["type"]) or "unknown" for row in amount_rows)
    return (
        {
            "contract_amount_missing_total": len(amount_rows),
            "contract_amount_missing_by_type": dict(sorted(amount_type_counts.items())),
            "contract_receivable_balance_missing_total": len(balance_rows),
            "supplier_contract_entry_source_missing_total": len(supplier_entry_rows),
            "decision": "amount_and_balance_residuals_require_old_system_fields_or_business_confirmation",
        },
        amount_rows,
        balance_rows + supplier_entry_rows,
    )


ROOT.mkdir(parents=True, exist_ok=True)
partner_summary, partner_rows = classify_partner_residuals()
contract_summary, contract_amount_rows, contract_other_rows = classify_contract_residuals()
write_csv(ROOT / "partner_residual_gap_classification_rows_v1.csv", partner_rows)
write_csv(ROOT / "contract_amount_residual_gap_rows_v1.csv", contract_amount_rows)
write_csv(ROOT / "contract_balance_entry_residual_gap_rows_v1.csv", contract_other_rows)
payload = {
    "status": "WARN",
    "database": DB_NAME,
    "generated_at": datetime.now(timezone.utc).isoformat(),
    "mode": "business_fact_residual_gap_classifier",
    "partner": partner_summary,
    "contract": contract_summary,
    "artifact_root": str(ROOT),
    "objective_fact_policy": (
        "Only legacy creator/time/amount/balance fields are acceptable backfill evidence; "
        "Odoo create_uid/create_date and import timestamps are technical metadata."
    ),
}
(ROOT / "business_fact_residual_gap_classifier_v1.json").write_text(
    json.dumps(payload, ensure_ascii=False, indent=2, default=str) + "\n",
    encoding="utf-8",
)
print("BUSINESS_FACT_RESIDUAL_GAP_CLASSIFIER=" + json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str))
