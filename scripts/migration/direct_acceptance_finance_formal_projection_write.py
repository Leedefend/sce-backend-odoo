# -*- coding: utf-8 -*-
"""Project accepted finance-side direct acceptance rows into formal carriers."""

from __future__ import annotations

import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from odoo import fields


SOURCE_SYSTEM = "online_old_scbsly"
ENGINEERING_RECEIPT_SOURCE_MODEL = "online_old_scbsly:direct_acceptance:engineering_progress_receipt"
ENGINEERING_RECEIPT_SOURCE_TABLE = "direct_acceptance:工程进度收款"
INPUT_TAX_SOURCE_MODEL = "online_old_scbsly:direct_acceptance:input_tax_report:action932"
GENERAL_INPUT_TAX_SOURCE_MODEL = "online_old_scbsly:direct_acceptance:general_contract_input_tax_report:action933"
REFUEL_SOURCE_MODEL = "online_old_scbsly:D_LYXM_BG_BX_JYDJ:list"


def artifact_root() -> Path:
    root = Path(os.getenv("MIGRATION_ARTIFACT_ROOT", "artifacts/migration"))
    try:
        root.mkdir(parents=True, exist_ok=True)
    except PermissionError:
        root = Path("/tmp/sce-migration-artifacts")
        root.mkdir(parents=True, exist_ok=True)
    return root


def ensure_allowed_db() -> None:
    allowlist = {item.strip() for item in os.getenv("MIGRATION_REPLAY_DB_ALLOWLIST", "sc_demo").split(",") if item.strip()}
    if env.cr.dbname not in allowlist:  # noqa: F821
        raise RuntimeError({"db_name_not_allowed_for_replay": env.cr.dbname, "allowlist": sorted(allowlist)})  # noqa: F821


def text(value: Any) -> str:
    value = str(value or "").replace("\r\n", "\n").replace("\r", "\n").strip()
    return "" if value.lower() in {"false", "none", "null"} else value


def amount(value: Any) -> float:
    raw = text(value).replace(",", "").replace("￥", "").replace("¥", "")
    if not raw:
        return 0.0
    try:
        return float(raw)
    except ValueError:
        match = re.search(r"-?\d+(?:\.\d+)?", raw)
        return float(match.group(0)) if match else 0.0


def date_value(value: Any):
    raw = text(value).replace("/", "-")
    if not raw:
        return False
    for fmt, size in (("%Y-%m-%d", 10), ("%Y-%m-%d %H:%M:%S", 19), ("%Y-%m-%d %H:%M", 16)):
        try:
            return datetime.strptime(raw[:size], fmt).date().isoformat()
        except ValueError:
            continue
    return False


def datetime_value(value: Any):
    raw = text(value).replace("T", " ").replace("/", "-")
    if not raw:
        return False
    raw = re.sub(r"\.\d+$", "", raw)
    for fmt, size in (("%Y-%m-%d %H:%M:%S", 19), ("%Y-%m-%d %H:%M", 16), ("%Y-%m-%d", 10)):
        try:
            parsed = datetime.strptime(raw[:size], fmt)
            return parsed.strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            continue
    return False


def copy_visible(fact) -> dict[str, str]:
    vals = {"legacy_acceptance_label": fact.acceptance_label}
    for index in range(1, 61):
        vals[f"legacy_visible_{index:02d}"] = text(getattr(fact, f"legacy_visible_{index:02d}", ""))
    return vals


def sql_update_record(record, vals: dict[str, Any]) -> None:
    if not vals:
        return
    fields = record._fields
    allowed = {key: value for key, value in vals.items() if key in fields}
    if not allowed:
        return
    assignments = ", ".join(f"{key} = %s" for key in allowed)
    params = list(allowed.values()) + [record.id]
    env.cr.execute(f"UPDATE {record._table} SET {assignments} WHERE id = %s", params)  # noqa: F821
    record.invalidate_recordset(list(allowed))


def first_project(fact):
    Project = env["project.project"].sudo().with_context(active_test=False)  # noqa: F821
    if fact.project_id:
        return fact.project_id
    legacy_id = text(fact.project_legacy_id)
    if legacy_id and "legacy_project_id" in Project._fields:
        project = Project.search([("legacy_project_id", "=", legacy_id)], limit=1)
        if project:
            return project
    name = text(fact.project_name) or text(fact.legacy_visible_10) or text(fact.legacy_visible_03)
    if name:
        project = Project.search([("name", "=", name)], limit=1)
        if project:
            return project
    return Project.search([], order="id", limit=1)


def partner_id(name: str):
    name = text(name)
    if not name:
        return False
    Partner = env["res.partner"].sudo().with_context(active_test=False)  # noqa: F821
    partner = Partner.search([("name", "=", name)], limit=1)
    if partner:
        return partner.id
    return Partner.create({"name": name, "company_type": "company", "supplier_rank": 1}).id


def project_engineering_receipts() -> dict[str, int]:
    Fact = env["sc.legacy.direct.acceptance.fact"].sudo()  # noqa: F821
    Receipt = env["sc.receipt.income"].sudo().with_context(active_test=False)  # noqa: F821
    facts = Fact.search(
        [("source_system", "=", SOURCE_SYSTEM), ("acceptance_label", "=", "工程进度收款"), ("active", "=", True)],
        order="legacy_record_id,id",
    )
    created = updated = skipped = 0
    for fact in facts:
        key = text(fact.legacy_record_id) or str(fact.id)
        project = first_project(fact)
        if not project:
            skipped += 1
            continue
        vals = {
            "source_origin": "legacy",
            "source_kind": "receipt_income",
            "source_family": "direct_acceptance_engineering_progress_receipt",
            "state": "legacy_confirmed",
            "project_id": project.id,
            "legacy_project_name": text(fact.legacy_visible_10) or text(fact.project_name),
            "legacy_company_name": text(fact.legacy_visible_05),
            "partner_id": partner_id(fact.legacy_visible_04),
            "legacy_partner_name": text(fact.legacy_visible_04),
            "legacy_contract_no": text(fact.legacy_visible_09),
            "date_receipt": date_value(fact.legacy_visible_03) or fields.Date.today(),  # noqa: F821
            "document_no": text(fact.legacy_visible_02) or text(fact.document_no) or key,
            "receipt_type": text(fact.legacy_visible_06),
            "income_category": text(fact.legacy_visible_06) or "工程进度收款",
            "amount": amount(fact.legacy_visible_07),
            "legacy_source_model": ENGINEERING_RECEIPT_SOURCE_MODEL,
            "legacy_source_table": ENGINEERING_RECEIPT_SOURCE_TABLE,
            "legacy_record_id": key,
            "legacy_document_state": text(fact.document_state),
            "legacy_document_state_label": text(fact.legacy_visible_01),
            "legacy_attachment_ref": text(fact.legacy_visible_11),
            "legacy_note": text(fact.legacy_visible_08),
            "creator_name": text(fact.legacy_visible_12),
            "created_time": datetime_value(fact.legacy_visible_13),
            "note": text(fact.legacy_visible_08),
        }
        vals.update(copy_visible(fact))
        existing = Receipt.search([("legacy_source_model", "=", ENGINEERING_RECEIPT_SOURCE_MODEL), ("legacy_record_id", "=", key)], limit=1)
        if existing:
            sql_update_record(existing, vals)
            updated += 1
        else:
            Receipt.create(vals)
            created += 1
    return {"source_count": len(facts), "created": created, "updated": updated, "skipped": skipped}


def backfill_invoice_visible() -> dict[str, Any]:
    Fact = env["sc.legacy.direct.acceptance.fact"].sudo()  # noqa: F821
    Invoice = env["sc.invoice.registration"].sudo().with_context(active_test=False)  # noqa: F821
    specs = [
        ("进项上报", INPUT_TAX_SOURCE_MODEL, "SCBSLY_DIRECT_INPUT_TAX_REPORT"),
        ("总包进项上报", GENERAL_INPUT_TAX_SOURCE_MODEL, "SCBSLY_DIRECT_GENERAL_CONTRACT_INPUT_TAX_REPORT"),
    ]
    results = []
    for label, source_model, source_table in specs:
        facts = Fact.search([("source_system", "=", SOURCE_SYSTEM), ("acceptance_label", "=", label), ("active", "=", True)])
        updated = missing = 0
        for fact in facts:
            key = text(fact.legacy_record_id) or str(fact.id)
            invoice = Invoice.search([("legacy_source_model", "=", source_model), ("legacy_record_id", "=", key)], limit=1)
            if not invoice and text(fact.document_no):
                invoice = Invoice.search([("legacy_source_model", "=", source_model), ("document_no", "=", text(fact.document_no))], limit=1)
            if not invoice:
                missing += 1
                continue
            vals = {"legacy_source_table": source_table}
            vals.update(copy_visible(fact))
            sql_update_record(invoice, vals)
            updated += 1
        results.append({"label": label, "source_count": len(facts), "updated": updated, "missing": missing})
    return {"results": results}


def backfill_missing_refuel_fact() -> dict[str, int]:
    Fact = env["sc.legacy.direct.acceptance.fact"].sudo()  # noqa: F821
    Refuel = env["sc.legacy.fuel.card.refuel.fact"].sudo().with_context(active_test=False)  # noqa: F821
    facts = Fact.search([("source_system", "=", SOURCE_SYSTEM), ("acceptance_label", "=", "加油登记"), ("active", "=", True)])
    created = updated = 0
    for fact in facts:
        key = text(fact.legacy_record_id) or text(fact.document_no) or str(fact.id)
        existing = Refuel.search([("legacy_source_model", "=", REFUEL_SOURCE_MODEL), ("legacy_record_id", "=", key)], limit=1)
        if existing:
            updated += 1
            continue
        project = first_project(fact)
        vals = {
            "legacy_source_model": REFUEL_SOURCE_MODEL,
            "legacy_record_id": key,
            "document_no": text(fact.legacy_visible_02) or text(fact.document_no) or key,
            "document_date": datetime_value(fact.legacy_visible_03),
            "document_state": text(fact.document_state),
            "project_id": project.id if project else False,
            "project_legacy_id": text(fact.project_legacy_id),
            "project_name": text(fact.legacy_visible_04) or text(fact.project_name),
            "card_no": text(fact.legacy_visible_08),
            "fuel_date": datetime_value(fact.legacy_visible_03),
            "fuel_amount": amount(fact.legacy_visible_05),
            "total_fuel_amount": amount(fact.legacy_visible_06),
            "balance_amount": amount(fact.legacy_visible_07),
            "total_recharge_amount": amount(fact.legacy_visible_09),
            "handler_name": text(fact.legacy_visible_12),
            "creator_name": text(fact.legacy_visible_12),
            "created_time": datetime_value(fact.legacy_visible_13),
            "attachment_ref": text(fact.legacy_visible_11),
            "note": text(fact.legacy_visible_10),
            "active": True,
        }
        Refuel.create(vals)
        created += 1
    return {"source_count": len(facts), "created": created, "already_present": updated}


ensure_allowed_db()
payload = {
    "database": env.cr.dbname,  # noqa: F821
    "mode": "direct_acceptance_finance_formal_projection_write",
    "engineering_receipts": project_engineering_receipts(),
    "invoices": backfill_invoice_visible(),
    "refuel": backfill_missing_refuel_fact(),
}
payload["status"] = "PASS" if payload["engineering_receipts"]["skipped"] == 0 and all(not row["missing"] for row in payload["invoices"]["results"]) else "REVIEW"
env.cr.commit()  # noqa: F821
out = artifact_root() / "direct_acceptance_finance_formal_projection_write_result_v1.json"
out.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print("DIRECT_ACCEPTANCE_FINANCE_FORMAL_PROJECTION_WRITE=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
