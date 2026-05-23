#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _read(rel_path: str) -> str:
    return (ROOT / rel_path).read_text(encoding="utf-8")


def _assert(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def main() -> int:
    errors: list[str] = []
    script = _read("scripts/migration/fresh_db_receipt_income_from_payment_request_projection_write.py")
    model = _read("addons/smart_construction_core/models/core/receipt_income.py")
    menu = _read("addons/smart_construction_core/views/menu_business_taxonomy.xml")

    _assert(
        'receipt_type = fields.Char(string="登记类型"' in model,
        "sc.receipt.income must keep receipt_type as the business registration type field",
        errors,
    )
    _assert(
        "raw.legacy_receipt_type" in script
        and 'COALESCE(NULLIF(source.legacy_receipt_type, \'\'), \'收款申请\')' in script,
        "receipt income projection must map C_JFHKLR.type into sc_receipt_income.receipt_type",
        errors,
    )
    _assert(
        "'收款申请',\n      NULLIF(source.legacy_receipt_type" not in script,
        "receipt income projection must not hard-code receipt_type to 收款申请 while moving legacy type only to audit fields",
        errors,
    )
    _assert(
        "legacy_receipt_type = EXCLUDED.legacy_receipt_type" in script
        and "legacy_receipt_subtype = EXCLUDED.legacy_receipt_subtype" in script,
        "receipt income projection must preserve legacy type/subtype audit fields",
        errors,
    )
    _assert(
        "('receipt_type', '=', '到款确认表')" in menu,
        "arrival confirmation menu must continue to route by runtime receipt_type",
        errors,
    )
    if errors:
        print("[verify.receipt_income_type_mapping.guard] FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("[verify.receipt_income_type_mapping.guard] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
