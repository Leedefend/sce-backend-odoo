#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def read(rel_path: str) -> str:
    return (ROOT / rel_path).read_text(encoding="utf-8")


def assert_ok(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def main() -> int:
    errors: list[str] = []
    invoice_views = read("addons/smart_construction_core/views/core/invoice_registration_views.xml")
    taxonomy = read("addons/smart_construction_core/views/menu_business_taxonomy.xml")
    cleanup = read("addons/smart_construction_core/views/menu_user_acceptance_cleanup.xml")
    makefile = read("Makefile")

    assert_ok(
        '<field name="name">发票总台账</field>' in invoice_views
        and "'search_default_group_source_kind': 1" in invoice_views,
        "invoice total ledger action must be named 发票总台账 and default-group by business source kind",
        errors,
    )
    assert_ok(
        '<field name="source_kind"/>' in invoice_views
        and '<field name="direction"/>' in invoice_views
        and '<field name="legacy_source_model" optional="show"/>' in invoice_views
        and '<field name="legacy_source_table" optional="show"/>' in invoice_views,
        "invoice total ledger tree/search must expose source kind, direction, and fact source",
        errors,
    )
    assert_ok(
        'name="has_invoice_no"' in invoice_views
        and 'name="missing_invoice_no"' in invoice_views
        and 'name="source_origin_legacy"' in invoice_views,
        "invoice total ledger search must let users separate real invoice-number rows from tax facts",
        errors,
    )
    assert_ok(
        "<field name=\"name\">销项开票申请</field>" in taxonomy
        and "<field name=\"name\">进项发票登记</field>" in taxonomy
        and "<field name=\"name\">进项税额上报</field>" in taxonomy
        and 'name="销项开票申请"' in taxonomy
        and 'name="进项发票登记"' in taxonomy
        and 'name="进项税额上报"' in taxonomy,
        "invoice business entries must use precise output/input/prepaid labels",
        errors,
    )
    assert_ok(
        "<field name=\"name\">发票总台账</field>" in cleanup
        and "<field name=\"name\">发票台账</field>" in cleanup
        and "<field name=\"name\">开票与税务办理</field>" in cleanup,
        "invoice menu acceptance cleanup must keep ledger and handling groups separated",
        errors,
    )
    assert_ok(
        "verify.invoice_entry_fact.contract_guard" in makefile
        and "verify.invoice_entry_fact.runtime_smoke" in makefile,
        "invoice entry optimization must be wired into Makefile verification targets",
        errors,
    )

    if errors:
        print("[verify.invoice_entry_fact.contract_guard] FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("[verify.invoice_entry_fact.contract_guard] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
