#!/usr/bin/env python3
"""Align income contract ledger visibility to the legacy construction contract surface."""

from __future__ import annotations

import csv
import json
import os
from collections import Counter
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path


def repo_root() -> Path:
    env_root = os.getenv("MIGRATION_REPO_ROOT")
    candidates = []
    if env_root:
        candidates.append(Path(env_root))
    candidates.extend([Path("/mnt"), Path.cwd()])
    for candidate in candidates:
        if (candidate / "tmp/raw/contract/contract.csv").exists():
            return candidate
    return Path.cwd()


def ensure_allowed_db() -> None:
    allowlist = {
        item.strip()
        for item in os.getenv(
            "MIGRATION_REPLAY_DB_ALLOWLIST",
            "sc_migration_fresh,sc_partner_acceptance",
        ).split(",")
        if item.strip()
    }
    if env.cr.dbname not in allowlist:  # noqa: F821
        raise RuntimeError({"db_name_not_allowed_for_replay": env.cr.dbname, "allowlist": sorted(allowlist)})  # noqa: F821


REPO_ROOT = repo_root()
ARTIFACT_ROOT = Path(os.getenv("MIGRATION_ARTIFACT_ROOT", str(REPO_ROOT / "artifacts/migration")))
RAW_CSV = Path(os.getenv("CONSTRUCTION_CONTRACT_RAW_CSV", str(REPO_ROOT / "tmp/raw/contract/contract.csv")))
OUTPUT_JSON = ARTIFACT_ROOT / "fresh_db_construction_contract_income_count_alignment_write_result_v1.json"
DETAIL_CSV = ARTIFACT_ROOT / "fresh_db_construction_contract_income_count_alignment_detail_v1.csv"
EXPECTED_TARGET_ROWS = int(os.getenv("CONSTRUCTION_CONTRACT_INCOME_VISIBLE_EXPECTED_ROWS", "1532"))
DETAIL_FIELDS = [
    "action",
    "legacy_contract_id",
    "legacy_document_no",
    "legacy_contract_no",
    "subject",
    "contract_amount",
    "contract_amount_source",
    "platform_contract_amount",
    "contract_amount_delta",
    "legacy_status",
    "project_id",
    "partner_id",
    "contract_id",
]
LEGACY_AMOUNT_LINE_NOTE = "legacy_contract_amount:T_ProjectContract_Out"


def clean(value: object) -> str:
    return "" if value is None else str(value).replace("\r\n", "\n").replace("\r", "\n").strip()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def is_legacy_income_visible(row: dict[str, str]) -> bool:
    return (
        clean(row.get("DEL")) != "1"
        and clean(row.get("DJZT")) in {"2", "1", ""}
        and bool(clean(row.get("HTBT")))
        and bool(clean(row.get("FBF")))
    )


def legacy_state(row: dict[str, str]) -> str:
    return "confirmed" if clean(row.get("DJZT")) == "2" else "draft"


def parse_date(value: object) -> str | None:
    text = clean(value)
    if not text:
        return None
    head = text[:10]
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(head, fmt).date().isoformat()
        except ValueError:
            continue
    return None


def parse_datetime(value: object) -> str | None:
    text = clean(value)
    if not text:
        return None
    normalized = text.replace("T", " ")
    for fmt in ("%Y-%m-%d %H:%M:%S", "%m/%d/%Y %H:%M:%S", "%Y/%m/%d %H:%M:%S"):
        try:
            return datetime.strptime(normalized[:19], fmt).strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            continue
    date_value = parse_date(text)
    return f"{date_value} 00:00:00" if date_value else None


def parse_amount(value: object) -> Decimal:
    text = clean(value).replace(",", "")
    if not text:
        return Decimal("0")
    try:
        return Decimal(text)
    except InvalidOperation:
        return Decimal("0")


def contract_amount_with_source(row: dict[str, str]) -> tuple[Decimal, str]:
    for field in ("GCYSZJ", "D_SCBSJS_QYHTJ", "D_SCBSJS_JSJE", "f_HTJK", "YFK", "ZLBZJ"):
        amount = parse_amount(row.get(field))
        if amount:
            return amount, field
    return Decimal("0"), ""


def contract_amount(row: dict[str, str]) -> Decimal:
    amount, _source = contract_amount_with_source(row)
    return amount


ensure_allowed_db()

Contract = env["construction.contract"].sudo()  # noqa: F821
ContractLine = env["construction.contract.line"].sudo()  # noqa: F821
ContractEvent = env["sc.contract.event"].sudo()  # noqa: F821
Project = env["project.project"].sudo()  # noqa: F821
Partner = env["res.partner"].sudo()  # noqa: F821

if "legacy_income_surface_visible" not in Contract._fields:
    raise RuntimeError({"missing_field": "construction.contract.legacy_income_surface_visible"})

raw_rows = read_csv(RAW_CSV)
raw_by_id = {clean(row.get("Id")): row for row in raw_rows if clean(row.get("Id"))}
target_rows = [row for row in raw_rows if is_legacy_income_visible(row)]
target_ids = {clean(row.get("Id")) for row in target_rows}
duplicate_target_ids = sorted(
    identity for identity, count in Counter(clean(row.get("Id")) for row in target_rows).items() if identity and count > 1
)

if len(target_ids) != EXPECTED_TARGET_ROWS:
    raise RuntimeError(
        {
            "unexpected_legacy_visible_count": len(target_ids),
            "expected": EXPECTED_TARGET_ROWS,
            "duplicate_target_ids": duplicate_target_ids[:20],
        }
    )


def resolve_project(row: dict[str, str]):
    legacy_project_id = clean(row.get("XMID"))
    if legacy_project_id:
        matches = Project.search([("legacy_project_id", "=", legacy_project_id)], limit=2)
        if len(matches) == 1:
            return matches[0]
        if len(matches) > 1:
            return matches.sorted(key=lambda item: item.id)[0]
    name = clean(row.get("f_XMMC")) or clean(row.get("HTBT")) or clean(row.get("DJBH")) or "历史施工合同项目"
    if legacy_project_id:
        existing = Project.search([("legacy_project_id", "=", legacy_project_id)], limit=1)
        if existing:
            return existing
    vals = {
        "name": name,
        "legacy_project_id": legacy_project_id,
    }
    if "company_id" in Project._fields:
        vals["company_id"] = env.company.id  # noqa: F821
    if "legacy_source_evidence" in Project._fields:
        vals["legacy_source_evidence"] = f"T_ProjectContract_Out.XMID:{legacy_project_id}"
    return Project.create(vals)


def resolve_partner(row: dict[str, str]):
    name = clean(row.get("FBF")) or clean(row.get("f_JSDW")) or "历史施工合同发包人"
    matches = Partner.search([("name", "=", name)], order="id")
    if matches:
        ranked = matches.filtered(lambda item: item.customer_rank > 0)
        return (ranked or matches)[0]
    vals = {
        "name": name,
        "company_type": "company",
        "legacy_partner_id": f"contract_income_counterparty:{clean(row.get('Id'))}",
        "legacy_partner_source": "contract_income_counterparty_runtime",
        "legacy_partner_name": name,
        "legacy_source_evidence": f"T_ProjectContract_Out.FBF:{clean(row.get('Id'))}",
    }
    if "is_company" in Partner._fields:
        vals["is_company"] = True
    if "customer_rank" in Partner._fields:
        vals["customer_rank"] = 1
    return Partner.create(vals)


def visible_vals(row: dict[str, str]) -> dict[str, object]:
    project = resolve_project(row)
    partner = resolve_partner(row)
    amount, amount_source = contract_amount_with_source(row)
    vals: dict[str, object] = {
        "legacy_contract_id": clean(row.get("Id")),
        "legacy_project_id": clean(row.get("XMID")),
        "legacy_contract_no": clean(row.get("HTBH")),
        "legacy_document_no": clean(row.get("DJBH")),
        "legacy_external_contract_no": clean(row.get("WBHTBH")),
        "legacy_status": clean(row.get("DJZT")),
        "legacy_deleted_flag": clean(row.get("DEL")),
        "legacy_counterparty_text": clean(row.get("FBF")),
        "legacy_income_surface_visible": True,
        "subject": clean(row.get("HTBT")),
        "type": "out",
        "state": legacy_state(row),
        "project_id": project.id,
        "partner_id": partner.id,
        "date_contract": parse_date(row.get("f_HTDLRQ")),
        "engineering_address": clean(row.get("f_GCDZ")),
        "engineering_category_text": clean(row.get("HTLX")),
        "engineering_content": clean(row.get("f_GCNR")),
        "entry_user_text": clean(row.get("LRR")) or clean(row.get("f_LRR")),
        "entry_time": parse_datetime(row.get("LRRQ")) or parse_datetime(row.get("f_LRSJ")),
        "legacy_contract_amount": float(amount),
        "legacy_contract_amount_source": amount_source,
    }
    if clean(row.get("D_SCBSJS_SFGD")):
        vals["archived"] = clean(row.get("D_SCBSJS_SFGD")) in {"是", "1", "true", "True"}
    return {key: value for key, value in vals.items() if value not in ("", None)}


existing = Contract.search([("legacy_document_no", "ilike", "WBHTGL%")], order="legacy_contract_id,id")
existing_by_legacy: dict[str, object] = {}
duplicate_existing: list[dict[str, object]] = []
for rec in existing:
    identity = rec.legacy_contract_id or ""
    if not identity:
        continue
    if identity in existing_by_legacy:
        duplicate_existing.append({"legacy_contract_id": identity, "ids": [existing_by_legacy[identity].id, rec.id]})
    else:
        existing_by_legacy[identity] = rec

if duplicate_existing:
    raise RuntimeError({"duplicate_existing_legacy_contract_id": duplicate_existing[:20]})

sale_tax = Contract._get_default_tax("out")
details: list[dict[str, object]] = []
created = updated_visible = hidden = type_corrected = amount_line_created = amount_line_updated = 0
amount_event_created = amount_event_updated = 0


def sync_contract_amount_line(contract, row: dict[str, str]) -> str:
    global amount_line_created, amount_line_updated
    amount = contract_amount(row)
    if not amount:
        return ""
    legacy_lines = contract.line_ids.filtered(lambda line: (line.note or "") == LEGACY_AMOUNT_LINE_NOTE)
    vals = {
        "contract_id": contract.id,
        "sequence": 1,
        "qty_contract": 1.0,
        "price_contract": float(amount),
        "note": LEGACY_AMOUNT_LINE_NOTE,
    }
    if legacy_lines:
        legacy_lines[:1].write(vals)
        amount_line_updated += 1
        return "amount_line_updated"
    if not contract.line_ids:
        ContractLine.create(vals)
        amount_line_created += 1
        return "amount_line_created"
    return ""


def sync_contract_amount_fields(contract, row: dict[str, str]) -> None:
    amount, source = contract_amount_with_source(row)
    updates = {
        "legacy_contract_amount": float(amount),
        "legacy_contract_amount_source": source,
    }
    contract.write(updates)


def sync_amount_difference_event(contract, row: dict[str, str]) -> str:
    global amount_event_created, amount_event_updated
    amount = contract_amount(row)
    if not amount:
        return ""
    delta = float(amount) - float(contract.amount_untaxed or 0.0)
    if round(delta, 2) == 0.0:
        return ""
    legacy_id = clean(row.get("Id"))
    fact_type = "construction_contract_amount_reconciliation"
    domain = [
        ("legacy_fact_model", "=", "T_ProjectContract_Out"),
        ("legacy_fact_key", "=", legacy_id),
        ("legacy_fact_type", "=", fact_type),
    ]
    existing = ContractEvent.search(domain, limit=1)
    subject = clean(row.get("HTBT")) or contract.subject or contract.legacy_document_no or legacy_id
    event_type = "settlement_audit" if ("结算" in subject or "审核" in subject) else "legacy_amount_difference"
    vals = {
        "name": f"{contract.legacy_document_no or legacy_id} 金额口径差异",
        "event_type": event_type,
        "project_id": contract.project_id.id,
        "contract_id": contract.id,
        "partner_id": contract.partner_id.id,
        "event_no": contract.legacy_document_no or legacy_id,
        "source_channel": "import",
        "event_date": contract.date_contract or False,
        "amount_impact": delta,
        "tax_excluded_amount": delta,
        "tax_amount": 0.0,
        "settlement_included": True,
        "state": "done",
        "legacy_fact_model": "T_ProjectContract_Out",
        "legacy_fact_key": legacy_id,
        "legacy_fact_type": fact_type,
        "description": (
            f"旧系统施工合同金额={amount}; 平台合同明细金额={contract.amount_untaxed or 0.0}; "
            f"差额={delta:.2f}。该事实用于承载历史金额口径差异，不覆盖已存在合同明细。"
        ),
        "basis": "T_ProjectContract_Out 金额字段与 construction.contract.line 汇总对比",
    }
    if existing:
        existing.write(vals)
        amount_event_updated += 1
        return "amount_event_updated"
    ContractEvent.create(vals)
    amount_event_created += 1
    return "amount_event_created"

try:
    for rec in existing:
        identity = rec.legacy_contract_id or ""
        should_show = identity in target_ids
        updates = {"legacy_income_surface_visible": should_show}
        if should_show and rec.type != "out":
            updates["type"] = "out"
            updates["tax_id"] = sale_tax.id
            type_corrected += 1
        rec.write(updates)
        if should_show:
            raw_row = raw_by_id.get(identity)
            amount_action = ""
            event_action = ""
            if raw_row:
                sync_contract_amount_fields(rec, raw_row)
                amount_action = sync_contract_amount_line(rec, raw_row)
                rec.flush_recordset()
                rec.invalidate_recordset()
                event_action = sync_amount_difference_event(rec, raw_row)
            updated_visible += 1
            suffix = "+".join(item for item in (amount_action, event_action) if item)
            action = "mark_visible" if not suffix else f"mark_visible+{suffix}"
        else:
            hidden += 1
            action = "mark_hidden"
        details.append(
            {
                "action": action,
                "legacy_contract_id": identity,
                "legacy_document_no": rec.legacy_document_no or "",
                "legacy_contract_no": rec.legacy_contract_no or "",
                "subject": rec.subject or "",
                "contract_amount": str(contract_amount(raw_by_id.get(identity, {}))) if identity in raw_by_id else "",
                "contract_amount_source": contract_amount_with_source(raw_by_id.get(identity, {}))[1] if identity in raw_by_id else "",
                "platform_contract_amount": rec.amount_untaxed or 0.0,
                "contract_amount_delta": rec.legacy_contract_amount_delta or 0.0,
                "legacy_status": rec.legacy_status or "",
                "project_id": rec.project_id.id or "",
                "partner_id": rec.partner_id.id or "",
                "contract_id": rec.id,
            }
        )

    for identity in sorted(target_ids - set(existing_by_legacy)):
        row = raw_by_id[identity]
        vals = visible_vals(row)
        vals["tax_id"] = sale_tax.id
        rec = Contract.create(vals)
        amount_action = sync_contract_amount_line(rec, row)
        rec.flush_recordset()
        rec.invalidate_recordset()
        event_action = sync_amount_difference_event(rec, row)
        created += 1
        suffix = "+".join(item for item in (amount_action, event_action) if item)
        details.append(
            {
                "action": "create_missing" if not suffix else f"create_missing+{suffix}",
                "legacy_contract_id": identity,
                "legacy_document_no": rec.legacy_document_no or "",
                "legacy_contract_no": rec.legacy_contract_no or "",
                "subject": rec.subject or "",
                "contract_amount": str(contract_amount(row)),
                "contract_amount_source": contract_amount_with_source(row)[1],
                "platform_contract_amount": rec.amount_untaxed or 0.0,
                "contract_amount_delta": rec.legacy_contract_amount_delta or 0.0,
                "legacy_status": rec.legacy_status or "",
                "project_id": rec.project_id.id or "",
                "partner_id": rec.partner_id.id or "",
                "contract_id": rec.id,
            }
        )
    env.cr.commit()  # noqa: F821
except Exception:
    env.cr.rollback()  # noqa: F821
    raise

visible_count = Contract.search_count(
    [
        ("type", "=", "out"),
        "|",
        ("legacy_contract_id", "=", False),
        ("legacy_income_surface_visible", "=", True),
    ]
)
legacy_visible_count = Contract.search_count(
    [
        ("type", "=", "out"),
        ("legacy_document_no", "ilike", "WBHTGL%"),
        ("legacy_income_surface_visible", "=", True),
    ]
)
legacy_all_count = Contract.search_count([("legacy_document_no", "ilike", "WBHTGL%")])
hidden_out_count = Contract.search_count(
    [
        ("type", "=", "out"),
        ("legacy_document_no", "ilike", "WBHTGL%"),
        ("legacy_income_surface_visible", "=", False),
    ]
)
legacy_visible_records = Contract.search(
    [
        ("type", "=", "out"),
        ("legacy_document_no", "ilike", "WBHTGL%"),
        ("legacy_income_surface_visible", "=", True),
    ]
)
legacy_visible_amount_sum = round(sum(legacy_visible_records.mapped("amount_untaxed")), 2)
legacy_raw_amount_sum = round(float(sum(contract_amount(row) for row in target_rows)), 2)
legacy_amount_field_sum = round(sum(legacy_visible_records.mapped("legacy_contract_amount")), 2)
user_visible_amount_sum = round(sum(legacy_visible_records.mapped("visible_contract_amount")), 2)
amount_difference_event_count = ContractEvent.search_count(
    [
        ("legacy_fact_model", "=", "T_ProjectContract_Out"),
        ("legacy_fact_type", "=", "construction_contract_amount_reconciliation"),
        ("contract_id", "in", legacy_visible_records.ids),
    ]
)
amount_delta_count = len(legacy_visible_records.filtered(lambda rec: round(rec.legacy_contract_amount_delta or 0.0, 2) != 0.0))
positive_amount_without_line_count = sum(
    1 for rec in legacy_visible_records if not rec.line_ids and contract_amount(raw_by_id.get(rec.legacy_contract_id or "", {})) > 0
)

post_errors = []
if legacy_visible_count != EXPECTED_TARGET_ROWS:
    post_errors.append({"error": "legacy_visible_count_not_expected", "actual": legacy_visible_count, "expected": EXPECTED_TARGET_ROWS})
if visible_count < legacy_visible_count:
    post_errors.append({"error": "income_action_visible_count_below_legacy_visible", "actual": visible_count})
if positive_amount_without_line_count:
    post_errors.append(
        {
            "error": "positive_legacy_amount_without_contract_line",
            "actual": positive_amount_without_line_count,
            "expected": 0,
        }
    )
if legacy_amount_field_sum != legacy_raw_amount_sum:
    post_errors.append(
        {
            "error": "legacy_contract_amount_field_sum_not_expected",
            "actual": legacy_amount_field_sum,
            "expected": legacy_raw_amount_sum,
        }
    )
if user_visible_amount_sum != legacy_raw_amount_sum:
    post_errors.append(
        {
            "error": "visible_contract_amount_sum_not_expected",
            "actual": user_visible_amount_sum,
            "expected": legacy_raw_amount_sum,
        }
    )
if amount_difference_event_count != amount_delta_count:
    post_errors.append(
        {
            "error": "amount_difference_event_count_not_expected",
            "actual": amount_difference_event_count,
            "expected": amount_delta_count,
        }
    )

status = "PASS" if not post_errors else "FAIL"
result = {
    "status": status,
    "mode": "fresh_db_construction_contract_income_count_alignment_write",
    "database": env.cr.dbname,  # noqa: F821
    "legacy_source_table": "T_ProjectContract_Out",
    "legacy_visible_filter": "DEL<>1 AND DJZT IN ('2','1','') AND HTBT<>'' AND FBF<>''",
    "legacy_visible_target_rows": len(target_ids),
    "existing_wbhtgl_rows_before": len(existing),
    "created_missing_rows": created,
    "updated_visible_rows": updated_visible,
    "hidden_non_visible_rows": hidden,
    "type_corrected_to_out_rows": type_corrected,
    "amount_line_created_rows": amount_line_created,
    "amount_line_updated_rows": amount_line_updated,
    "amount_difference_event_created_rows": amount_event_created,
    "amount_difference_event_updated_rows": amount_event_updated,
    "amount_difference_event_count": amount_difference_event_count,
    "amount_delta_contract_count": amount_delta_count,
    "legacy_wbhtgl_rows_after": legacy_all_count,
    "legacy_income_visible_rows_after": legacy_visible_count,
    "income_action_visible_rows_after": visible_count,
    "legacy_raw_amount_sum": legacy_raw_amount_sum,
    "legacy_contract_amount_field_sum_after": legacy_amount_field_sum,
    "user_visible_contract_amount_sum_after": user_visible_amount_sum,
    "legacy_income_visible_amount_sum_after": legacy_visible_amount_sum,
    "legacy_income_visible_amount_sum_delta": round(legacy_visible_amount_sum - legacy_raw_amount_sum, 2),
    "platform_contract_amount_sum_after": legacy_visible_amount_sum,
    "platform_contract_amount_sum_delta": round(legacy_visible_amount_sum - legacy_raw_amount_sum, 2),
    "positive_amount_without_line_count": positive_amount_without_line_count,
    "hidden_income_out_rows_after": hidden_out_count,
    "post_errors": post_errors,
    "artifacts": {"detail_csv": str(DETAIL_CSV)},
    "decision": "income_contract_ledger_count_aligned" if status == "PASS" else "STOP_REVIEW_REQUIRED",
}
write_csv(DETAIL_CSV, DETAIL_FIELDS, details)
write_json(OUTPUT_JSON, result)
print(
    "FRESH_DB_CONSTRUCTION_CONTRACT_INCOME_COUNT_ALIGNMENT_WRITE="
    + json.dumps(
        {
            "status": status,
            "legacy_visible_target_rows": len(target_ids),
            "created_missing_rows": created,
            "type_corrected_to_out_rows": type_corrected,
            "amount_line_created_rows": amount_line_created,
            "amount_line_updated_rows": amount_line_updated,
            "amount_difference_event_count": amount_difference_event_count,
            "legacy_income_visible_rows_after": legacy_visible_count,
            "income_action_visible_rows_after": visible_count,
            "legacy_income_visible_amount_sum_after": legacy_visible_amount_sum,
            "user_visible_contract_amount_sum_after": user_visible_amount_sum,
            "positive_amount_without_line_count": positive_amount_without_line_count,
        },
        ensure_ascii=False,
        sort_keys=True,
    )
)
if status != "PASS":
    raise RuntimeError({"income_count_alignment_failed": post_errors})
