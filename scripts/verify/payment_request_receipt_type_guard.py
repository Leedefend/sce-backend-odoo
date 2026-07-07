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
    model = _read("addons/smart_construction_core/models/core/payment_request.py")
    views = _read("addons/smart_construction_core/views/core/payment_request_views.xml")
    asset_generator = _read("scripts/migration/receipt_core_asset_generator.py")
    replay_adapter = _read("scripts/migration/fresh_db_receipt_core_replay_adapter.py")
    receipt_write = _read("scripts/migration/fresh_db_receipt_core_write.py")
    contract_generator = _read("scripts/migration/contract_header_asset_generator.py")
    contract_remaining_screen = _read("scripts/migration/contract_remaining214_strict_screen.py")
    normalize = _read("scripts/migration/visible_surface_receipt_core_creator_normalize_write.py")
    search_config = _read("addons/smart_core/app_config_engine/models/app_search_config.py")
    browser_smoke = _read("scripts/verify/payment_request_receipt_type_browser_group_smoke.js")
    makefile = _read("Makefile")

    _assert(
        'receipt_type = fields.Char(' in model and 'string="登记类型"' in model,
        "payment.request must carry receipt_type as 收款申请登记类型",
        errors,
    )
    _assert(
        '<field name="receipt_type" optional="show"/>' in views
        and '<field name="receipt_type" invisible="type != \'receive\'"/>' in views,
        "payment.request tree/form views must show receipt_type for receipt requests",
        errors,
    )
    _assert(
        "receipt_type_normal" in views
        and "receipt_type_other" in views
        and "group_by_receipt_type" in views
        and "search_default_group_by_receipt_type" in views,
        "receipt request action/search must support receipt_type filtering and grouping",
        errors,
    )
    _assert(
        "add_group(fname, meta, explicit=True)" in search_config
        and "allowed_group_types = allowed_group_types + ('char',)" in search_config,
        "explicit search-view char group_by fields must appear in browser custom group categories",
        errors,
    )
    _assert(
        "group_by=receipt_type" in browser_smoke
        and "分组结果" in browser_smoke
        and "正常类型收款" in browser_smoke
        and "其他类型收款" in browser_smoke
        and "verify.payment_request_receipt_type.browser_group_smoke" in makefile,
        "receipt type grouping must have a browser-level grouped-list smoke target",
        errors,
    )
    _assert(
        'add_text_field(record, "receipt_type", row["receipt_type"])' in asset_generator
        and 'receipt_type = clean(row.get("type"))' in asset_generator,
        "receipt core asset must preserve C_JFHKLR.type as payment.request.receipt_type",
        errors,
    )
    _assert(
        "LEGACY_DELETE_FIELDS" in asset_generator
        and "def is_deleted_row" in asset_generator
        and "old_system_deleted_rows_discarded" in asset_generator,
        "receipt core asset generation must directly discard historical-source deleted rows",
        errors,
    )
    _assert(
        "def receipt_source_lane" in asset_generator
        and "route_sales_receipt_or_pushed_income" in asset_generator
        and "route_other_receipt_income" in asset_generator
        and "sales_receipt_or_pushed_income_routed_out" in asset_generator,
        "receipt core asset generation must route sales/pushed income out of payment.request",
        errors,
    )
    _assert(
        'direction = "out"' in contract_generator
        and 'direction_source = "receipt_contract_reference"' in contract_generator
        and 'direction = "out"' in contract_remaining_screen,
        "receipt contract reference evidence must infer income contracts, not payment contracts",
        errors,
    )
    _assert(
        '"receipt_type",' in replay_adapter
        and '"receipt_type": clean(values.get("receipt_type"))' in replay_adapter,
        "receipt core replay adapter must emit receipt_type in the payload",
        errors,
    )
    _assert(
        "def raw_receipt_type_map" in replay_adapter
        and "receipt_types.get(legacy_receipt_id" in replay_adapter
        and "def raw_receipt_type_map" in receipt_write
        and "receipt_types.get(legacy_receipt_id" in receipt_write,
        "receipt core replay/write must backfill receipt_type from raw CSV when packaged XML lacks the field",
        errors,
    )
    _assert(
        "def raw_deleted_receipt_ids" in receipt_write
        and "discarded_old_system_deleted_rows" in receipt_write
        and "is_deleted_source_row" in receipt_write,
        "receipt core write must filter stale payload/XML rows deleted in the historical source",
        errors,
    )
    _assert(
        "discarded_existing_old_system_deleted_rows" in receipt_write
        and "C_JFHKLR_DELETED" in receipt_write
        and "old_system_deleted" in receipt_write,
        "receipt core write must quarantine already-written migration rows deleted in the historical source",
        errors,
    )
    _assert(
        "discarded_existing_stale_payload_rows" in receipt_write
        and "C_JFHKLR_ROUTED_OUT" in receipt_write
        and "legacy_receipt_id not in payload_receipt_ids" in receipt_write,
        "receipt core write must quarantine already-written migration rows routed out of the current receipt payload",
        errors,
    )
    _assert(
        "C_JFHKLR_DELETED" in views and "C_JFHKLR_ROUTED_OUT" in views,
        "receipt request action must hide quarantined legacy receipt carriers",
        errors,
    )
    _assert(
        '"receipt_type"' in receipt_write
        and '"receipt_type": clean(row.get("receipt_type")) or False' in receipt_write,
        "receipt core write must create payment.request rows with receipt_type",
        errors,
    )
    _assert(
        '"receipt_type": clean(row.get("type"))' in normalize
        and 'vals["receipt_type"] = fact["receipt_type"]' in normalize
        and '"receipt_requests_with_receipt_type"' in normalize,
        "visible surface normalize must backfill existing receipt requests with receipt_type",
        errors,
    )
    if errors:
        print("[verify.payment_request_receipt_type.guard] FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("[verify.payment_request_receipt_type.guard] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
