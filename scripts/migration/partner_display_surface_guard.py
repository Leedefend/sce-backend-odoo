#!/usr/bin/env python3
"""No-DB guard for customer/supplier business fact display surfaces."""

from __future__ import annotations

import argparse
import json
import xml.etree.ElementTree as ET
from pathlib import Path


ACCOUNT_VIEWS = Path("addons/smart_construction_core/views/support/account_extend_views.xml")
REVIEW_VIEWS = Path("addons/smart_construction_core/views/support/partner_import_review_views.xml")
MENU_VIEWS = Path("addons/smart_construction_core/views/menu_business_taxonomy.xml")


REQUIRED_VIEW_FIELDS: dict[str, set[str]] = {
    "view_sc_customer_partner_tree": {
        "name",
        "sc_business_role_label",
        "sc_business_fact_basis",
        "customer_rank",
        "supplier_rank",
        "vat",
        "sc_region",
        "sc_registered_capital",
        "sc_default_tax_rate",
        "sc_account_name",
        "sc_bank_name",
        "sc_bank_account",
        "sc_source_partner_code",
        "sc_source_document_state",
        "sc_source_push_result",
        "sc_source_project_name",
        "sc_source_cooperation_type",
        "sc_source_fact_count",
        "sc_source_fact_source",
        "sc_source_receipt_amount",
        "sc_source_payment_amount",
        "sc_source_created_by",
        "sc_source_created_at",
        "legacy_partner_id",
        "legacy_partner_source",
        "legacy_partner_name",
        "sc_legacy_source_label",
        "sc_source_partner_code",
        "sc_source_document_state",
        "sc_source_push_result",
        "sc_source_project_name",
        "sc_source_cooperation_type",
        "sc_source_fact_count",
        "sc_source_fact_source",
        "sc_source_receipt_amount",
        "sc_source_payment_amount",
        "sc_source_created_by",
        "sc_source_created_at",
    },
    "view_sc_customer_partner_form": {
        "name",
        "is_company",
        "vat",
        "sc_region",
        "sc_registered_capital",
        "sc_business_scope",
        "sc_default_tax_rate",
        "sc_default_tax_rate_text",
        "sc_business_role_label",
        "sc_business_fact_basis",
        "sc_legacy_source_label",
        "sc_account_name",
        "sc_bank_name",
        "sc_bank_account",
        "bank_ids",
        "legacy_partner_id",
        "legacy_partner_source",
        "sc_source_partner_code",
        "sc_source_document_state",
        "sc_source_push_result",
        "sc_source_project_name",
        "sc_source_created_by",
        "legacy_partner_name",
        "legacy_source_evidence",
    },
    "view_sc_customer_partner_search": {
        "name",
        "vat",
        "sc_region",
        "sc_default_tax_rate",
        "sc_bank_name",
        "sc_bank_account",
        "phone",
        "mobile",
        "email",
    },
    "view_sc_supplier_partner_tree": {
        "name",
        "sc_business_role_label",
        "sc_business_fact_basis",
        "supplier_rank",
        "customer_rank",
        "sc_supplier_type",
        "vat",
        "sc_region",
        "sc_registered_capital",
        "sc_default_tax_rate",
        "sc_account_name",
        "sc_bank_name",
        "sc_bank_account",
        "sc_source_partner_code",
        "sc_source_document_state",
        "sc_source_push_result",
        "sc_source_project_name",
        "sc_source_cooperation_type",
        "sc_source_receipt_amount",
        "sc_source_payment_amount",
        "sc_source_created_by",
        "sc_source_created_at",
        "legacy_partner_id",
        "legacy_partner_source",
        "legacy_partner_name",
        "sc_legacy_source_label",
        "sc_source_partner_code",
        "sc_source_document_state",
        "sc_source_push_result",
        "sc_source_project_name",
        "sc_source_cooperation_type",
        "sc_source_receipt_amount",
        "sc_source_payment_amount",
        "sc_source_created_by",
        "sc_source_created_at",
    },
    "view_sc_supplier_partner_form": {
        "name",
        "is_company",
        "sc_supplier_type",
        "vat",
        "sc_region",
        "sc_registered_capital",
        "sc_business_scope",
        "sc_default_tax_rate",
        "sc_default_tax_rate_text",
        "sc_business_role_label",
        "sc_business_fact_basis",
        "sc_legacy_source_label",
        "sc_account_name",
        "sc_bank_name",
        "sc_bank_account",
        "bank_ids",
        "legacy_partner_id",
        "legacy_partner_source",
        "sc_source_partner_code",
        "sc_source_document_state",
        "sc_source_push_result",
        "sc_source_project_name",
        "sc_source_created_by",
        "legacy_partner_name",
        "legacy_source_evidence",
    },
    "view_sc_supplier_partner_search": {
        "name",
        "sc_supplier_type",
        "vat",
        "sc_region",
        "sc_default_tax_rate",
        "sc_bank_name",
        "sc_bank_account",
        "legacy_partner_id",
        "legacy_partner_name",
        "legacy_partner_source",
        "sc_business_role_label",
        "sc_business_fact_basis",
        "sc_legacy_source_label",
    },
    "view_sc_partner_import_review_tree": {
        "review_state",
        "review_reason",
        "partner_name",
        "suggested_customer_rank",
        "suggested_supplier_rank",
        "sc_supplier_type",
        "vat",
        "sc_bank_name",
        "sc_bank_account",
        "gate_reason",
        "target_partner_id",
    },
    "view_sc_partner_import_review_form": {
        "partner_name",
        "review_reason",
        "gate_reason",
        "suggested_customer_rank",
        "suggested_supplier_rank",
        "confirmed_customer_rank",
        "confirmed_supplier_rank",
        "target_partner_id",
        "vat",
        "sc_supplier_type",
        "sc_region",
        "sc_registered_capital",
        "sc_business_scope",
        "sc_default_tax_rate",
        "sc_default_tax_rate_text",
        "sc_account_name",
        "sc_bank_name",
        "sc_bank_account",
        "legacy_partner_source",
        "legacy_partner_id",
        "evidence",
    },
    "view_sc_partner_import_review_search": {
        "partner_name",
        "legacy_partner_id",
        "vat",
        "gate_reason",
    },
}

REQUIRED_FILTERS: dict[str, set[str]] = {
    "view_sc_customer_partner_search": {
        "customer_supplier_mixed",
        "customer_with_bank_account",
        "group_default_tax_rate",
        "group_region",
        "group_is_company",
    },
    "view_sc_supplier_partner_search": {
        "supplier_customer_mixed",
        "supplier_with_bank_account",
        "group_business_role",
        "group_business_fact_basis",
        "group_default_tax_rate",
        "group_supplier_type",
        "group_region",
        "group_legacy_source",
    },
    "view_sc_partner_import_review_search": {
        "state_candidate",
        "state_resolved",
        "state_ignored",
        "reason_background_only",
        "reason_unknown_role",
        "reason_personal",
    },
}

REQUIRED_BUTTONS = {
    "view_sc_partner_import_review_form": {
        "action_resolve_customer",
        "action_resolve_supplier",
        "action_resolve_customer_supplier",
        "action_ignore",
    }
}


def parse_xml(path: Path) -> ET.Element:
    if not path.exists():
        raise RuntimeError({"missing_xml": str(path)})
    return ET.parse(path).getroot()


def view_records(paths: list[Path]) -> dict[str, ET.Element]:
    records: dict[str, ET.Element] = {}
    for path in paths:
        root = parse_xml(path)
        for record in root.findall(".//record"):
            record_id = record.attrib.get("id")
            if record_id:
                records[record_id] = record
    return records


def names(record: ET.Element, tag: str) -> set[str]:
    return {item.attrib["name"] for item in record.findall(f".//{tag}[@name]")}


def text_for_field(record: ET.Element, name: str) -> str:
    for field in record.findall("field"):
        if field.attrib.get("name") == name:
            return "".join(field.itertext())
    return ""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    errors: list[dict[str, object]] = []
    records = view_records([ACCOUNT_VIEWS, REVIEW_VIEWS, MENU_VIEWS])

    for view_id, required_fields in REQUIRED_VIEW_FIELDS.items():
        record = records.get(view_id)
        if record is None:
            errors.append({"view": view_id, "missing_record": True})
            continue
        actual_fields = names(record, "field")
        missing = sorted(required_fields - actual_fields)
        if missing:
            errors.append({"view": view_id, "missing_fields": missing})

    for view_id, required_filters in REQUIRED_FILTERS.items():
        record = records.get(view_id)
        if record is None:
            continue
        actual_filters = names(record, "filter")
        missing = sorted(required_filters - actual_filters)
        if missing:
            errors.append({"view": view_id, "missing_filters": missing})

    for view_id, required_buttons in REQUIRED_BUTTONS.items():
        record = records.get(view_id)
        if record is None:
            continue
        actual_buttons = names(record, "button")
        missing = sorted(required_buttons - actual_buttons)
        if missing:
            errors.append({"view": view_id, "missing_buttons": missing})

    customer_action = records.get("action_sc_customer_partner")
    supplier_action = records.get("action_sc_supplier_partner")
    if customer_action is None or "customer_rank" not in text_for_field(customer_action, "domain"):
        errors.append({"action": "action_sc_customer_partner", "missing_customer_rank_domain": True})
    if supplier_action is None or "supplier_rank" not in text_for_field(supplier_action, "domain"):
        errors.append({"action": "action_sc_supplier_partner", "missing_supplier_rank_domain": True})

    result = {
        "status": "FAIL" if errors else "PASS",
        "mode": "partner_display_surface_guard",
        "checked_views": len(REQUIRED_VIEW_FIELDS),
        "checked_search_views": len(REQUIRED_FILTERS),
        "checked_action_domains": 2,
        "errors": errors,
        "db_writes": 0,
    }
    print("PARTNER_DISPLAY_SURFACE_GUARD=" + json.dumps(result, ensure_ascii=False, sort_keys=True))
    if errors and args.check:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
