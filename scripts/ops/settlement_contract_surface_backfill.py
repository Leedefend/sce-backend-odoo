# -*- coding: utf-8 -*-
"""Backfill settlement contract surface fields from auditable sources.

Run inside Odoo shell:
    odoo shell -d sc_demo < scripts/ops/settlement_contract_surface_backfill.py
"""

from __future__ import annotations

import json
import re
import sys
import traceback
from datetime import date


DIRECT_ENGINEERING_SOURCE = "sc.legacy.direct.acceptance.fact:direct_engineering_settlement_order"


def _text(value) -> str:
    value = "" if value in (None, False) else str(value)
    value = value.replace("\r\n", "\n").replace("\r", "\n").strip()
    if value in {"False", "false", "None", "none"}:
        return ""
    return value


def _contract_no(contract) -> str:
    for field_name in (
        "legacy_contract_no",
        "legacy_visible_contract_no",
        "legacy_document_no",
        "name",
    ):
        value = _text(getattr(contract, field_name, False))
        if value:
            return value
    return ""


def _contract_address(contract) -> str:
    for field_name in ("engineering_address", "legacy_visible_engineering_address"):
        value = _text(getattr(contract, field_name, False))
        if value:
            return value
    return ""


def _date_from_parts(year: int, month: int, day: int):
    try:
        return date(year, month, day)
    except ValueError:
        return None


def _parse_date_tokens(raw: str) -> list[date]:
    text = _text(raw)
    if not text:
        return []

    tokens: list[date] = []
    for match in re.finditer(r"(20\d{2})\s*[年./-]\s*(\d{1,2})\s*[月./-]\s*(\d{1,2})\s*日?", text):
        parsed = _date_from_parts(int(match.group(1)), int(match.group(2)), int(match.group(3)))
        if parsed:
            tokens.append(parsed)

    if tokens:
        return tokens

    month_range = re.search(
        r"(20\d{2})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日?\s*[~至到\\-—]+\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日?",
        text,
    )
    if month_range:
        year = int(month_range.group(1))
        start = _date_from_parts(year, int(month_range.group(2)), int(month_range.group(3)))
        end = _date_from_parts(year, int(month_range.group(4)), int(month_range.group(5)))
        return [item for item in (start, end) if item]

    return []


def _parse_period(record):
    candidates = [
        record.settlement_description,
        record.title,
        record.legacy_visible_06,
        record.legacy_visible_08,
        record.legacy_visible_13,
        record.note,
    ]
    for value in candidates:
        parsed = _parse_date_tokens(value)
        if len(parsed) >= 2:
            return min(parsed), max(parsed)
    return None, None


def _settlement_values(record) -> dict:
    vals = {}
    if record.contract_id:
        contract = record.contract_id
        contract_no = _contract_no(contract)
        if contract_no and _text(record.legacy_contract_no) != contract_no:
            vals["legacy_contract_no"] = contract_no
        subject = _text(contract.subject)
        if subject and _text(record.contract_subject) != subject:
            vals["contract_subject"] = subject
        address = _contract_address(contract)
        if address and _text(record.engineering_address) != address:
            vals["engineering_address"] = address

    if record.legacy_fact_model == DIRECT_ENGINEERING_SOURCE:
        subject = _text(record.legacy_visible_13)
        if subject and not _text(record.contract_subject):
            vals["contract_subject"] = subject
        address = _text(record.legacy_visible_15)
        if address and not _text(record.engineering_address):
            vals["engineering_address"] = address

    start, end = _parse_period(record)
    if start and not record.settlement_period_start:
        vals["settlement_period_start"] = start.isoformat()
    if end and not record.settlement_period_end:
        vals["settlement_period_end"] = end.isoformat()

    if vals:
        vals["write_uid"] = 1
    return vals


def main():
    Settlement = env["sc.settlement.order"].sudo().with_context(  # noqa: F821
        active_test=False,
        legacy_migration_allow_missing_contract=True,
    )
    records = Settlement.search([])
    updated = 0
    updated_fields = {}
    by_source = {}

    for record in records:
        vals = _settlement_values(record)
        if not vals:
            continue
        source = _text(record.legacy_fact_model) or "__manual__"
        by_source[source] = by_source.get(source, 0) + 1
        for field_name in vals:
            if field_name == "write_uid":
                continue
            updated_fields[field_name] = updated_fields.get(field_name, 0) + 1
        record.write(vals)
        updated += 1

    env.cr.commit()  # noqa: F821
    result = {
        "operation": "settlement_contract_surface_backfill",
        "status": "PASS",
        "settlement_count": len(records),
        "updated_rows": updated,
        "updated_fields": updated_fields,
        "updated_by_source": by_source,
    }
    print("SETTLEMENT_CONTRACT_SURFACE_BACKFILL: %s" % json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


try:
    sys.exit(main())
except Exception as err:
    result = {
        "operation": "settlement_contract_surface_backfill",
        "status": "FAIL",
        "error": str(err),
        "traceback": traceback.format_exc(),
    }
    print("SETTLEMENT_CONTRACT_SURFACE_BACKFILL: %s" % json.dumps(result, ensure_ascii=False, sort_keys=True))
    sys.exit(1)
