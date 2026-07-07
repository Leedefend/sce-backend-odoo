#!/usr/bin/env python3
"""Classify source-field coverage for migrated business facts.

Run through ``scripts/ops/odoo_shell_exec.sh`` so the global ``env`` is
available. The classifier is deliberately evidence-only: if historical-source creator,
time, amount, or balance fields are absent, it records source-field coverage
instead of forcing historical data to satisfy new-system customer/supplier rules or
falling back to Odoo import metadata.
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
RAW_CONTRACT_CSV = Path(os.getenv("CONSTRUCTION_CONTRACT_RAW_CSV", "/mnt/tmp/raw/contract/contract.csv"))
RAW_AMOUNT_FIELDS = ("GCYSZJ", "D_SCBSJS_QYHTJ", "D_SCBSJS_JSJE", "f_HTJK", "YFK", "ZLBZJ")
RAW_BALANCE_FIELDS = ("GCLJYSK_1", "GCLJYSK_2", "GCQK", "GCLJKPJE")
SOURCE_CREATOR_CSVS = [
    Path(item.strip())
    for item in os.getenv(
        "BUSINESS_FACT_SOURCE_CREATOR_CSVS",
        os.getenv("PARTNER_SOURCE_CREATOR_CSVS", ""),
    ).split(",")
    if item.strip()
]
TECHNICAL_CREATED_BY_VALUES = {"odoobot", "administrator", "admin", "system", "系统", "系统导入"}


def clean(value) -> str:
    if value in (None, False):
        return ""
    text = str(value).strip()
    return "" if text.lower() in {"false", "none", "null"} else text


def business_creator_present(value) -> bool:
    text = clean(value)
    return bool(text and text.lower() not in TECHNICAL_CREATED_BY_VALUES and text not in TECHNICAL_CREATED_BY_VALUES)


def rows(sql: str, params: list[object] | None = None) -> list[dict[str, object]]:
    env.cr.execute(sql, params or [])  # noqa: F821
    columns = [desc[0] for desc in env.cr.description]  # noqa: F821
    return [dict(zip(columns, row)) for row in env.cr.fetchall()]  # noqa: F821


def money_present(value) -> bool:
    text = clean(value).replace(",", "")
    if not text:
        return False
    try:
        return abs(float(text)) > 0.000001
    except ValueError:
        return False


def read_raw_contract_rows() -> dict[str, dict[str, str]]:
    if not RAW_CONTRACT_CSV.is_file():
        return {}
    raw_rows: dict[str, dict[str, str]] = {}
    with RAW_CONTRACT_CSV.open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            legacy_id = clean(row.get("Id"))
            if legacy_id:
                raw_rows[legacy_id] = row
    return raw_rows


def write_csv(path: Path, csv_rows: list[dict[str, object]]) -> None:
    if not csv_rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(csv_rows[0]), extrasaction="ignore")
        writer.writeheader()
        writer.writerows(csv_rows)


def read_source_creator_evidence() -> dict[tuple[str, str], dict[str, str]]:
    evidence: dict[tuple[str, str], dict[str, str]] = {}
    for path in SOURCE_CREATOR_CSVS:
        if not path.is_file():
            continue
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            for row in csv.DictReader(handle):
                source_table = clean(row.get("source_table"))
                legacy_record_id = clean(row.get("legacy_record_id"))
                if not source_table or not legacy_record_id:
                    continue
                evidence[(source_table, legacy_record_id)] = {
                    "source_table": source_table,
                    "legacy_record_id": legacy_record_id,
                    "creator_legacy_user_id": clean(row.get("creator_legacy_user_id")),
                    "creator_name": clean(row.get("creator_name")),
                    "created_time": clean(row.get("created_time")),
                }
    return evidence


def model_exists(model_name: str) -> bool:
    return model_name in env.registry  # noqa: F821


def fact_field_values(record, field_names: tuple[str, ...], *, creator: bool = False) -> list[str]:
    values: list[str] = []
    for field_name in field_names:
        if field_name not in record._fields:
            continue
        value = getattr(record, field_name)
        if hasattr(value, "display_name"):
            value = value.display_name
        text = clean(value)
        if creator and not business_creator_present(text):
            continue
        if text:
            values.append(text)
    return values


def source_identity(record) -> tuple[str, str]:
    for table_field, record_field in (
        ("legacy_source_table", "legacy_record_id"),
        ("legacy_source_table", "legacy_contract_id"),
        ("source_table", "legacy_record_id"),
        ("source_table", "legacy_line_id"),
    ):
        if table_field in record._fields and record_field in record._fields:
            source_table = clean(getattr(record, table_field))
            legacy_record_id = clean(getattr(record, record_field))
            if source_table and legacy_record_id:
                return source_table, legacy_record_id
    if record._name == "construction.contract" and "legacy_contract_id" in record._fields:
        legacy_contract_id = clean(getattr(record, "legacy_contract_id"))
        note = clean(getattr(record, "note")) if "note" in record._fields else ""
        if legacy_contract_id and "supplier_contract_pricing" in note:
            return "T_GYSHT_INFO", legacy_contract_id
    return "", ""


def source_gap_status(
    evidence: dict[tuple[str, str], dict[str, str]],
    key: tuple[str, str],
    *,
    missing_creator: bool,
    missing_time: bool,
) -> tuple[str, str]:
    if not key[0] or not key[1]:
        return "runtime_source_key_missing", "runtime_source_key_missing"
    row = evidence.get(key)
    if not row:
        return "source_evidence_absent_or_all_blank", "source_evidence_absent_or_all_blank"
    creator_status = "not_missing"
    time_status = "not_missing"
    if missing_creator:
        creator_status = "source_creator_present" if business_creator_present(row.get("creator_name")) else "source_creator_blank"
    if missing_time:
        time_status = "source_time_present" if clean(row.get("created_time")) else "source_time_blank"
    return creator_status, time_status


def classify_business_fact_source_fields() -> tuple[dict[str, object], list[dict[str, object]], list[dict[str, object]]]:
    Partner = env["res.partner"].sudo().with_context(active_test=False)  # noqa: F821
    source_evidence = read_source_creator_evidence()
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
    residual_evidence_counter: Counter[str] = Counter()
    residual_source_counter: Counter[str] = Counter()
    excluded_counter: Counter[str] = Counter()
    detail_rows: list[dict[str, object]] = []
    residual_record_rows: list[dict[str, object]] = []
    included_partner_count = 0
    for partner in partners:
        if "示例" in clean(partner.name):
            excluded_counter["example_named_partner"] += 1
            continue
        included_partner_count += 1
        source_text = clean(partner.sc_source_fact_source)
        for source in [part for part in source_text.split("；") if part]:
            source_counter[source] += 1
        if not partner.sc_source_created_by and not partner.sc_source_created_at:
            missing_shape_counter["missing_creator_and_time"] += 1
        elif not partner.sc_source_created_by:
            missing_shape_counter["missing_creator_only"] += 1
        elif not partner.sc_source_created_at:
            missing_shape_counter["missing_time_only"] += 1
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
                    creator=True,
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
                if not creator_values or not time_values:
                    key = source_identity(record)
                    residual_source_counter[f"{model_name}:{key[0] or 'no_source_table'}"] += 1
                    creator_status, time_status = source_gap_status(
                        source_evidence,
                        key,
                        missing_creator=not bool(creator_values),
                        missing_time=not bool(time_values),
                    )
                    if not creator_values:
                        residual_evidence_counter[f"{model_name}:creator:{creator_status}"] += 1
                    if not time_values:
                        residual_evidence_counter[f"{model_name}:time:{time_status}"] += 1
                    residual_record_rows.append(
                        {
                            "partner_id": partner.id,
                            "partner_name": clean(partner.name),
                            "model": model_name,
                            "record_id": record.id,
                            "source_table": key[0],
                            "legacy_record_id": key[1],
                            "missing_creator": int(not bool(creator_values)),
                            "missing_time": int(not bool(time_values)),
                            "source_creator_status": creator_status,
                            "source_time_status": time_status,
                        }
                    )
        for key, count in fact_summary.items():
            objective_field_counter[key] += count
        detail_rows.append(
            {
                "partner_id": partner.id,
                "name": clean(partner.name),
                "customer_rank": partner.customer_rank,
                "supplier_rank": partner.supplier_rank,
                "source_fact_count": partner.sc_source_fact_count,
                "source_fact_source": clean(partner.sc_source_fact_source),
                "source_created_by": clean(partner.sc_source_created_by),
                "source_created_at": clean(partner.sc_source_created_at),
                "fact_field_summary": json.dumps(dict(sorted(fact_summary.items())), ensure_ascii=False, sort_keys=True),
            }
        )
    return (
        {
            "affected_business_subject_count": included_partner_count,
            "affected_subject_missing_shape_counts": dict(sorted(missing_shape_counter.items())),
            "business_fact_source_label_counts": dict(sorted(source_counter.items())),
            "fact_field_presence_counts": dict(sorted(objective_field_counter.items())),
            "fact_source_counts": dict(sorted(residual_source_counter.items())),
            "source_field_coverage_counts": dict(sorted(residual_evidence_counter.items())),
            "source_creator_evidence_csvs": [str(path) for path in SOURCE_CREATOR_CSVS],
            "source_creator_evidence_keys": len(source_evidence),
            "excluded_counts": dict(sorted(excluded_counter.items())),
            "decision": "old_data_is_not_forced_to_satisfy_new_customer_supplier_rules",
        },
        detail_rows,
        residual_record_rows,
    )


def classify_contract_residuals() -> tuple[dict[str, object], list[dict[str, object]], list[dict[str, object]]]:
    raw_contract_rows = read_raw_contract_rows()
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
           AND COALESCE(legacy_contract_amount_source, '') = ''
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
           AND legacy_contract_id IS NOT NULL
           AND COALESCE(visible_contract_amount, 0) <> 0
           AND (visible_received_amount IS NULL OR visible_unreceived_amount IS NULL)
           AND (COALESCE(visible_received_amount_source, '') = '' OR COALESCE(visible_unreceived_amount_source, '') = '')
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
    amount_source_counts: Counter[str] = Counter()
    amount_source_by_type_counts: Counter[str] = Counter()
    amount_detail_rows: list[dict[str, object]] = []
    for row in amount_rows:
        contract_type = clean(row.get("type")) or "unknown"
        raw_row = raw_contract_rows.get(clean(row.get("legacy_contract_id")))
        if not raw_row:
            source_status = "raw_contract_row_missing"
            source_field = ""
            source_amount = ""
        else:
            source_field = ""
            source_amount = ""
            for field_name in RAW_AMOUNT_FIELDS:
                if money_present(raw_row.get(field_name)):
                    source_field = field_name
                    source_amount = clean(raw_row.get(field_name))
                    break
            source_status = "raw_amount_present" if source_field else "raw_amount_zero_or_blank"
        amount_source_counts[source_status] += 1
        amount_source_by_type_counts[f"{contract_type}:{source_status}"] += 1
        amount_detail_rows.append(
            {
                **row,
                "raw_source_status": source_status,
                "raw_source_field": source_field,
                "raw_source_amount": source_amount,
            }
        )

    balance_source_counts: Counter[str] = Counter()
    balance_detail_rows: list[dict[str, object]] = []
    for row in balance_rows:
        raw_row = raw_contract_rows.get(clean(row.get("legacy_contract_id")))
        if not raw_row:
            source_status = "raw_contract_row_missing"
            populated_fields: list[str] = []
        else:
            populated_fields = [field_name for field_name in RAW_BALANCE_FIELDS if clean(raw_row.get(field_name))]
            source_status = "raw_balance_field_present" if populated_fields else "raw_balance_fields_blank"
        balance_source_counts[source_status] += 1
        balance_detail_rows.append(
            {
                **row,
                "raw_source_status": source_status,
                "raw_balance_fields": ",".join(populated_fields),
            }
        )
    return (
        {
            "contract_amount_missing_total": len(amount_rows),
            "contract_amount_missing_by_type": dict(sorted(amount_type_counts.items())),
            "contract_amount_source_status_counts": dict(sorted(amount_source_counts.items())),
            "contract_amount_source_status_by_type": dict(sorted(amount_source_by_type_counts.items())),
            "contract_receivable_balance_missing_total": len(balance_rows),
            "contract_receivable_balance_source_status_counts": dict(sorted(balance_source_counts.items())),
            "supplier_contract_entry_source_missing_total": len(supplier_entry_rows),
            "decision": "amount_and_balance_residuals_require_old_system_fields_or_business_confirmation",
        },
        amount_detail_rows,
        balance_detail_rows + supplier_entry_rows,
    )


ROOT.mkdir(parents=True, exist_ok=True)
source_field_summary, subject_rows, source_field_record_rows = classify_business_fact_source_fields()
contract_summary, contract_amount_rows, contract_other_rows = classify_contract_residuals()
write_csv(ROOT / "business_subject_source_field_impact_rows_v1.csv", subject_rows)
write_csv(ROOT / "business_fact_source_field_coverage_rows_v1.csv", source_field_record_rows)
# Compatibility outputs for earlier audit tooling; do not use these names as acceptance terminology.
write_csv(ROOT / "partner_residual_gap_classification_rows_v1.csv", subject_rows)
write_csv(ROOT / "partner_residual_fact_rows_v1.csv", source_field_record_rows)
write_csv(ROOT / "contract_amount_residual_gap_rows_v1.csv", contract_amount_rows)
write_csv(ROOT / "contract_balance_entry_residual_gap_rows_v1.csv", contract_other_rows)
blocking_source_keys = {
    key: count
    for key, count in source_field_summary["source_field_coverage_counts"].items()
    if "runtime_source_key_missing" in key
}
status = "PASS" if not blocking_source_keys and not contract_amount_rows and not contract_other_rows else "WARN"
payload = {
    "status": status,
    "database": DB_NAME,
    "generated_at": datetime.now(timezone.utc).isoformat(),
    "mode": "business_fact_source_field_coverage_classifier",
    "business_fact_source_field_coverage": source_field_summary,
    "legacy_source_blank_fields_are_acceptance_blockers": False,
    "blocking_source_key_counts": blocking_source_keys,
    "contract": contract_summary,
    "artifact_root": str(ROOT),
    "raw_contract_csv": str(RAW_CONTRACT_CSV),
    "objective_fact_policy": (
        "Business fact acceptance is based on carrying historical facts into the new system. "
        "Old data is not forced to satisfy new customer/supplier classification rules. "
        "Only legacy creator/time/amount/balance fields are acceptable evidence; "
        "Odoo create_uid/create_date and import timestamps are technical metadata. "
        "Blank creator/time fields in the old source are documented coverage observations, not acceptance blockers."
    ),
}
(ROOT / "business_fact_residual_gap_classifier_v1.json").write_text(
    json.dumps(payload, ensure_ascii=False, indent=2, default=str) + "\n",
    encoding="utf-8",
)
print("BUSINESS_FACT_RESIDUAL_GAP_CLASSIFIER=" + json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str))
