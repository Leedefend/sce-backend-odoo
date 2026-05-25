#!/usr/bin/env python3
"""Backfill payment request line facts needed by the visible payment surface.

This uses the frozen migration asset for C_ZFSQGL_CB. It does not use the
user-supplied Excel row values.
"""

from __future__ import annotations

import json
import os
from decimal import Decimal, InvalidOperation
from pathlib import Path
from xml.etree import ElementTree as ET


DEFAULT_XML = Path("migration_assets/20_business/outflow_request_line/outflow_request_line_v1.xml")
CONTAINER_XML = Path("/tmp/outflow_request_line_v1.xml")


def clean(value: object) -> str:
    if value is None or value is False:
        return ""
    text = str(value).replace("\u3000", " ").strip()
    return "" if text in {"False", "false", "None", "NULL"} else text


def money(value: object) -> float:
    try:
        return float(Decimal(clean(value) or "0"))
    except InvalidOperation:
        return 0.0


def source_xml() -> Path:
    candidates = [os.getenv("OUTFLOW_REQUEST_LINE_XML"), str(DEFAULT_XML), str(CONTAINER_XML)]
    for candidate in candidates:
        if candidate and Path(candidate).exists():
            return Path(candidate)
    raise RuntimeError({"outflow_request_line_xml_missing": [item for item in candidates if item]})


def ensure_allowed_db() -> None:
    allowlist = {
        item.strip()
        for item in os.getenv("MIGRATION_REPLAY_DB_ALLOWLIST", "sc_demo").split(",")
        if item.strip()
    }
    if env.cr.dbname not in allowlist:  # noqa: F821
        raise RuntimeError({"db_name_not_allowed_for_replay": env.cr.dbname, "allowlist": sorted(allowlist)})  # noqa: F821


def fields_from_record(record: ET.Element) -> dict[str, str]:
    values: dict[str, str] = {}
    for field in record.findall("field"):
        name = clean(field.attrib.get("name"))
        if not name:
            continue
        if field.attrib.get("ref"):
            values[f"{name}__ref"] = clean(field.attrib.get("ref"))
        values[name] = clean(field.text)
    return values


ensure_allowed_db()

Request = env["payment.request"].sudo().with_context(active_test=False)  # noqa: F821
Line = env["payment.request.line"].sudo().with_context(active_test=False)  # noqa: F821
Contract = env["construction.contract"].sudo().with_context(active_test=False)  # noqa: F821

xml_path = source_xml()
parent_rows = Request.search_read(
    [("legacy_source_table", "=", "C_ZFSQGL"), ("legacy_record_id", "!=", False)],
    ["legacy_record_id"],
)
parent_by_legacy = {clean(row["legacy_record_id"]): int(row["id"]) for row in parent_rows}
existing_line_ids = {
    clean(row["legacy_line_id"])
    for row in Line.search_read([("legacy_line_id", "!=", False)], ["legacy_line_id"])
}
contract_by_legacy = {
    clean(row["legacy_contract_id"]): int(row["id"])
    for row in Contract.search_read([("legacy_contract_id", "!=", False)], ["legacy_contract_id"])
}

created = 0
skipped_existing = 0
skipped_missing_parent = 0
skipped_non_line = 0
resolved_contracts = 0
batch: list[dict[str, object]] = []
line_type_counts: dict[str, int] = {}

for _, record in ET.iterparse(xml_path, events=("end",)):
    if record.tag != "record":
        continue
    if clean(record.attrib.get("model")) != "payment.request.line":
        skipped_non_line += 1
        record.clear()
        continue
    values = fields_from_record(record)
    legacy_line_id = clean(values.get("legacy_line_id"))
    legacy_parent_id = clean(values.get("legacy_parent_id"))
    if not legacy_line_id or legacy_line_id in existing_line_ids:
        skipped_existing += 1
        record.clear()
        continue
    request_id = parent_by_legacy.get(legacy_parent_id)
    if not request_id:
        skipped_missing_parent += 1
        record.clear()
        continue
    legacy_contract_id = clean(values.get("legacy_supplier_contract_id"))
    contract_id = contract_by_legacy.get(legacy_contract_id)
    if contract_id:
        resolved_contracts += 1
    line_type = clean(values.get("source_line_type"))
    if line_type:
        line_type_counts[line_type] = line_type_counts.get(line_type, 0) + 1
    vals: dict[str, object] = {
        "request_id": request_id,
        "sequence": int(clean(values.get("sequence")) or "10"),
        "legacy_line_id": legacy_line_id,
        "legacy_parent_id": legacy_parent_id,
        "legacy_supplier_contract_id": legacy_contract_id or False,
        "source_document_no": clean(values.get("source_document_no")) or False,
        "source_line_type": line_type or False,
        "source_counterparty_text": clean(values.get("source_counterparty_text")) or False,
        "source_contract_no": clean(values.get("source_contract_no")) or False,
        "amount": money(values.get("amount")),
        "paid_before_amount": money(values.get("paid_before_amount")),
        "remaining_amount": money(values.get("remaining_amount")),
        "current_pay_amount": money(values.get("current_pay_amount")),
        "note": clean(values.get("note")) or False,
        "import_batch": "payment_request_visible_gap_backfill_v1",
    }
    if contract_id:
        vals["contract_id"] = contract_id
    batch.append(vals)
    existing_line_ids.add(legacy_line_id)
    if len(batch) >= 500:
        Line.create(batch)
        created += len(batch)
        batch = []
    record.clear()

if batch:
    Line.create(batch)
    created += len(batch)

env.cr.commit()  # noqa: F821

payload = {
    "status": "PASS",
    "mode": "payment_request_line_visible_gap_backfill_write",
    "database": env.cr.dbname,  # noqa: F821
    "source_xml": str(xml_path),
    "created_lines": created,
    "skipped_existing": skipped_existing,
    "skipped_missing_parent": skipped_missing_parent,
    "resolved_contracts": resolved_contracts,
    "line_type_counts": dict(sorted(line_type_counts.items())),
    "decision": "used_migration_line_asset_not_excel_rows",
}
print("PAYMENT_REQUEST_LINE_VISIBLE_GAP_BACKFILL=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
