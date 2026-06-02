#!/usr/bin/env python3
"""Patch SCBS55 施工合同 surface from a live old-system row dump."""

from __future__ import annotations

import gzip
import json
import re
import csv
from datetime import datetime
from decimal import Decimal


SOURCE_PATH = "/tmp/scbs_55_old_live_full_rows_seq003_contract.json.gz"
AMOUNT_BACKFILL_PATHS = (
    "/tmp/contract_business_amount_backfill_from_mssql_v1.csv",
    "artifacts/migration/scbs_55_old_live_full_rows_current/contract_business_amount_backfill_from_mssql_v1.csv",
)
FINANCIAL_VISIBLE_FIELDS = {
    "legacy_visible_settlement_amount",
    "legacy_visible_invoice_amount",
    "legacy_visible_received_amount",
    "legacy_visible_unreceived_amount",
    "legacy_visible_unreceived_rate",
}


def clean(value):
    if value is None or value is False:
        return ""
    return re.sub(r"\s+", " ", str(value).replace("\u3000", " ").strip())


def money(value):
    try:
        return float(Decimal(str(value or 0)))
    except Exception:
        return 0.0


def amount_text(value):
    text = clean(value)
    if not text:
        return ""
    try:
        return f"{Decimal(text):.2f}"
    except Exception:
        return text


def rate_text(numerator, denominator):
    total = Decimal(str(money(denominator)))
    if not total:
        return ""
    rate = Decimal(str(money(numerator))) / total * Decimal("100")
    if rate == 0:
        rate = Decimal("0")
    return f"{rate:.2f}%"


def date(value):
    return clean(value)[:10] or False


def dt(value):
    text = clean(value)
    if not text:
        return False
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(text[:19], fmt).strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            pass
    return False


rows = json.load(gzip.open(SOURCE_PATH, "rt", encoding="utf-8"))["rows"]
amount_backfill = {}
for amount_path in AMOUNT_BACKFILL_PATHS:
    try:
        with open(amount_path, "r", encoding="utf-8-sig", newline="") as handle:
            for row in csv.DictReader(handle):
                legacy_id = clean(row.get("Id"))
                if not legacy_id:
                    continue
                amount_backfill[legacy_id] = {
                    "legacy_visible_settlement_amount": amount_text(row.get("settlement_amount")),
                    "legacy_visible_invoice_amount": amount_text(row.get("invoice_amount")),
                    "legacy_visible_received_amount": amount_text(row.get("received_amount")),
                    "legacy_visible_unreceived_amount": amount_text(row.get("unreceived_amount")),
                    "legacy_visible_unreceived_rate": rate_text(row.get("unreceived_amount"), row.get("contract_amount")),
                }
        break
    except FileNotFoundError:
        continue

Contract = env["construction.contract"].sudo().with_context(active_test=False)  # noqa: F821
Project = env["project.project"].sudo().with_context(active_test=False)  # noqa: F821
Partner = env["res.partner"].sudo().with_context(active_test=False)  # noqa: F821
Company = env.company  # noqa: F821
Tax = env["account.tax"].sudo().search([("type_tax_use", "in", ["sale", "purchase"]), ("company_id", "in", [False, Company.id])], limit=1)  # noqa: F821
if not Tax:
    Tax = env["account.tax"].sudo().search([], limit=1)  # noqa: F821


def resolve_project(row):
    legacy_id = clean(row.get("f_XMID"))
    name = clean(row.get("f_XMMC")) or legacy_id or "历史项目"
    project = Project.search(["|", ("legacy_project_id", "=", legacy_id), ("legacy_parent_id", "=", legacy_id)], limit=1) if legacy_id else Project.browse()
    if not project:
        project = Project.search([("name", "=", name)], limit=1)
    if not project:
        vals = {
            "name": name,
            "legacy_project_id": legacy_id or False,
            "short_name": name[:64],
            "project_environment": "legacy_contract_online_patch",
            "legacy_state": "online_old_system_anchor",
            "legacy_note": "线上老系统施工合同补齐; source=T_ProjectContract_Out",
        }
        if "company_id" in Project._fields:
            vals["company_id"] = Company.id
        project = Project.create(vals)
    return project


def resolve_partner(row):
    name = clean(row.get("FBF")) or "历史发包人"
    partner = Partner.search([("name", "=", name)], limit=1)
    if not partner:
        partner = Partner.create({"name": name, "company_type": "company", "is_company": True, "customer_rank": 1})
    return partner


def values_for(row):
    legacy_id = clean(row.get("Id"))
    amount = money(row.get("GCYSZJ"))
    vals = {
        "subject": clean(row.get("HTBT")) or clean(row.get("HTBH")) or clean(row.get("DJBH")) or legacy_id,
        "type": "out",
        "project_id": resolve_project(row).id,
        "partner_id": resolve_partner(row).id,
        "company_id": Company.id,
        "currency_id": Company.currency_id.id,
        "tax_id": Tax.id,
        "amount_untaxed": amount,
        "legacy_contract_id": legacy_id,
        "legacy_project_id": clean(row.get("f_XMID")) or False,
        "legacy_contract_no": clean(row.get("HTBH")) or False,
        "legacy_document_no": clean(row.get("DJBH")) or False,
        "legacy_status": clean(row.get("DJZT")) or False,
        "legacy_counterparty_text": clean(row.get("FBF")) or False,
        "legacy_income_surface_visible": True,
        "legacy_contract_amount": amount,
        "legacy_contract_amount_source": "online_old_scbs:T_ProjectContract_Out:list855",
        "legacy_visible_document_state": clean(row.get("DJZTText")) or clean(row.get("DJZT")) or False,
        "legacy_visible_document_no": clean(row.get("DJBH")) or False,
        "legacy_visible_contract_date": date(row.get("f_HTDLRQ")) or False,
        "legacy_visible_archived": clean(row.get("D_SCBSJS_SFGD")) or False,
        "legacy_visible_counterparty": clean(row.get("FBF")) or False,
        "legacy_visible_project_name": clean(row.get("f_XMMC")) or False,
        "legacy_visible_title": clean(row.get("HTBT")) or False,
        "legacy_visible_category": clean(row.get("HTLX")) or False,
        "legacy_visible_contract_no": clean(row.get("HTBH")) or False,
        "legacy_visible_amount": clean(row.get("GCYSZJ")) or False,
        "legacy_visible_settlement_amount": clean(row.get("D_SCBSJS_JSJE")) or False,
        "legacy_visible_invoice_amount": clean(row.get("LJKP")) or False,
        "legacy_visible_received_amount": clean(row.get("LJSK")) or False,
        "legacy_visible_unreceived_amount": clean(row.get("WSK")) or False,
        "legacy_visible_unreceived_rate": clean(row.get("WSKBL")) or False,
        "legacy_visible_affiliated_person": clean(row.get("GKR") or row.get("f_GKR")) or False,
        "legacy_visible_engineering_address": clean(row.get("f_GCDZ")) or False,
        "legacy_visible_engineering_content": clean(row.get("f_GCNR")) or False,
        "legacy_visible_creator_name": clean(row.get("LRR")) or False,
        "legacy_visible_created_time": dt(row.get("f_LRSJ")) or False,
        "entry_user_text": clean(row.get("LRR")) or False,
        "entry_time": dt(row.get("f_LRSJ")) or False,
        "engineering_category_text": clean(row.get("HTLX")) or False,
        "affiliated_person": clean(row.get("GKR") or row.get("f_GKR")) or False,
        "engineering_content": clean(row.get("f_GCNR")) or False,
        "attachment_text": clean(row.get("f_FJ") or row.get("FJ")) or False,
    }
    for field, value in amount_backfill.get(legacy_id, {}).items():
        if field in {
            "legacy_visible_invoice_amount",
            "legacy_visible_received_amount",
            "legacy_visible_unreceived_amount",
            "legacy_visible_unreceived_rate",
        }:
            continue
        if value and vals.get(field) in (False, ""):
            vals[field] = value
    return vals


old_ids = {clean(row.get("Id")) for row in rows if clean(row.get("Id"))}
existing = Contract.search([("legacy_contract_id", "!=", False)])
by_id = {record.legacy_contract_id: record for record in existing if record.legacy_contract_id}
created = 0
updated = 0
for row in rows:
    legacy_id = clean(row.get("Id"))
    vals = values_for(row)
    record = by_id.get(legacy_id)
    if record:
        # The live list endpoint may omit SQL-derived financial columns even
        # when the legacy page/business evidence has values. Never let a blank
        # list payload erase an already reconciled visible amount.
        datafetch_present = any(field in row for field in ("LJKP", "LJSK", "WSK", "WSKBL", "ZJE"))
        if not datafetch_present:
            for field in FINANCIAL_VISIBLE_FIELDS:
                if vals.get(field) in (False, "") and getattr(record, field):
                    vals.pop(field, None)
        record.write(vals)
        updated += 1
    else:
        Contract.create(vals)
        created += 1

Contract.search([("legacy_contract_id", "!=", False), ("legacy_contract_id", "not in", list(old_ids))]).write({"legacy_income_surface_visible": False})
action = env["ir.actions.act_window"].sudo().browse(855)  # noqa: F821
domain = [("legacy_contract_id", "!=", False), ("legacy_income_surface_visible", "=", True)]
action.write({"domain": repr(domain)})
env.cr.commit()  # noqa: F821
print({"old": len(old_ids), "created": created, "updated": updated, "final_count": Contract.search_count(domain), "action_domain": action.domain})
