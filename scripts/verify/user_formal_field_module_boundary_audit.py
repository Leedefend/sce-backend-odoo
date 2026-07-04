#!/usr/bin/env python3
"""Guard formal visible field ownership across core and custom modules.

Business operation model fields and released business list views belong to
smart_construction_core. User-specific preferences, history, and customer-only
acceptance surfaces belong to smart_construction_custom. Each audited surface
declares its owner explicitly so boundary changes are intentional.
"""

from __future__ import annotations

import json
from pathlib import Path


ADDON_ROOT_CANDIDATES = [Path("/mnt/extra-addons"), Path.cwd() / "addons"]
REPO_ROOT_CANDIDATES = [Path.cwd()]
CORE_ADDON = Path("smart_construction_core")
CUSTOM_ADDON = Path("smart_construction_custom")

BOUNDARY_CASES = [
    {
        "name": "付款还保证金",
        "model": "tender.guarantee",
        "owner": "core",
        "action_xmlid": "smart_construction_core.action_tender_guarantee_formal_payment_deposit_return",
        "expected_view_xmlid": "smart_construction_core.view_tender_guarantee_formal_payment_deposit_return_tree",
        "fields": [
            "deposit_status_display",
            "deposit_push_result",
            "deposit_kingdee_document_no",
            "deposit_document_no",
            "deposit_bid_project_name",
            "deposit_engineering_project_name",
            "deposit_type_display",
            "deposit_company_name",
            "deposit_amount_display",
            "deposit_returned_amount_display",
            "deposit_unreturned_amount_display",
            "deposit_need_return_text",
            "deposit_payee_unit",
            "deposit_payment_account",
            "deposit_note_display",
            "deposit_attachment_text",
            "deposit_source_created_by",
            "deposit_source_created_at",
        ],
    },
    {
        "name": "报价单",
        "model": "sc.material.rfq",
        "owner": "core",
        "action_xmlid": "smart_construction_core.action_sc_material_quote_user_confirmed",
        "expected_view_xmlid": "smart_construction_core.view_sc_material_rfq_quote_formal_tree",
        "fields": [
            "quote_status_display",
            "quote_document_no",
            "quote_supplier_name",
            "quote_inquiry_time",
            "quote_material_name",
            "quote_material_spec",
            "quote_quantity_display",
            "quote_tax_price_display",
            "quote_tax_amount_display",
            "quote_total_quantity_display",
            "quote_total_amount_display",
            "quote_note_display",
            "quote_contact_name",
            "quote_contact_phone",
            "quote_attachment_text",
            "quote_selected_text",
            "quote_project_name",
            "quote_source_created_by",
            "quote_source_created_at",
        ],
    },
    {
        "name": "往来单位付款",
        "model": "sc.payment.execution",
        "owner": "core",
        "action_xmlid": "smart_construction_core.action_sc_payment_execution_partner_payment",
        "expected_view_xmlid": "smart_construction_core.view_sc_payment_execution_partner_formal_tree",
        "fields": [
            "partner_payment_status_display",
            "partner_payment_date_display",
            "partner_payment_payee_unit",
            "partner_payment_actual_payee_unit",
            "partner_payment_amount_display",
            "partner_payment_category_display",
            "partner_payment_content_display",
            "partner_payment_method_display",
            "partner_payment_cost_type_display",
            "partner_payment_account_name_display",
            "partner_payment_attachment_text",
            "partner_payment_voucher_no",
            "partner_payment_writer",
            "partner_payment_source_created_by",
            "partner_payment_project_name",
            "partner_payment_source_text",
            "partner_payment_document_no",
        ],
    },
    {
        "name": "公司财务支出",
        "model": "sc.payment.execution",
        "owner": "core",
        "action_xmlid": "smart_construction_core.action_sc_payment_execution_company_finance_expense",
        "expected_view_xmlid": "smart_construction_core.view_sc_payment_execution_formal_company_finance_expense_tree",
        "fields": [
            "company_finance_status_display",
            "company_finance_push_result",
            "company_finance_document_no",
            "company_finance_amount_display",
            "company_finance_cost_type_display",
            "company_finance_payee_unit",
            "company_finance_payment_account_name",
            "company_finance_note_display",
            "company_finance_source_created_by",
            "company_finance_source_created_at",
            "company_finance_attachment_text",
        ],
    },
    {
        "name": "扣款单",
        "model": "sc.tax.deduction.registration",
        "owner": "core",
        "action_xmlid": "smart_construction_core.action_sc_tax_deduction_registration_deduction_bill_acceptance",
        "expected_view_xmlid": "smart_construction_core.view_sc_tax_deduction_registration_formal_deduction_bill_tree",
        "fields": [
            "deduction_bill_status_display",
            "deduction_bill_document_no",
            "deduction_bill_project_name",
            "deduction_bill_unit_name",
            "deduction_bill_amount_display",
            "deduction_bill_reason_display",
            "deduction_bill_date_display",
            "deduction_bill_attachment_text",
            "deduction_bill_source_created_by",
            "deduction_bill_source_created_at",
        ],
    },
]


def _addon_root() -> Path:
    for candidate in ADDON_ROOT_CANDIDATES:
        if (candidate / CORE_ADDON).exists() and (candidate / CUSTOM_ADDON).exists():
            return candidate
    raise FileNotFoundError("Cannot locate smart construction addons root")


def _display_path(path: Path) -> str:
    for candidate in [*_repo_root_candidates(), _addon_root()]:
        try:
            return str(path.relative_to(candidate))
        except ValueError:
            continue
    return str(path)


def _repo_root_candidates() -> list[Path]:
    roots = []
    for candidate in REPO_ROOT_CANDIDATES:
        if (candidate / "addons" / CORE_ADDON).exists():
            roots.append(candidate)
    return roots


def _iter_source_files(base: Path):
    for suffix in ("*.py", "*.xml"):
        yield from base.rglob(suffix)


def _scan_static(addon_root: Path) -> list[dict]:
    failures = []
    core = addon_root / CORE_ADDON
    custom = addon_root / CUSTOM_ADDON
    custom_blob = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore")
        for path in _iter_source_files(custom)
    )
    core_files = list(_iter_source_files(core))
    core_blob = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore")
        for path in core_files
    )
    custom_files = list(_iter_source_files(custom))

    for case in BOUNDARY_CASES:
        owner = case.get("owner")
        for field_name in case["fields"]:
            if owner == "custom":
                if field_name not in custom_blob:
                    failures.append({
                        "type": "missing_custom_owner",
                        "case": case["name"],
                        "field": field_name,
                    })
                for path in core_files:
                    text = path.read_text(encoding="utf-8", errors="ignore")
                    if field_name in text:
                        failures.append({
                            "type": "core_user_field_leak",
                            "case": case["name"],
                            "field": field_name,
                            "path": _display_path(path),
                        })
            elif owner == "core":
                if field_name not in core_blob:
                    failures.append({
                        "type": "missing_core_owner",
                        "case": case["name"],
                        "field": field_name,
                    })
                for path in custom_files:
                    text = path.read_text(encoding="utf-8", errors="ignore")
                    if field_name in text:
                        failures.append({
                            "type": "custom_business_field_leak",
                            "case": case["name"],
                            "field": field_name,
                            "path": _display_path(path),
                        })
            else:
                failures.append({
                    "type": "unknown_owner",
                    "case": case["name"],
                    "owner": owner,
                })
    return failures


def _runtime_rows() -> tuple[list[dict], list[dict]]:
    if "env" not in globals():
        return [], []

    rows = []
    failures = []
    for case in BOUNDARY_CASES:
        action = env.ref(case["action_xmlid"])  # noqa: F821
        view_xmlid = action.view_id.get_external_id().get(action.view_id.id, "") if action.view_id else ""
        model = env[case["model"]]  # noqa: F821
        missing_fields = [field for field in case["fields"] if field not in model._fields]
        rows.append({
            "case": case["name"],
            "action_xmlid": case["action_xmlid"],
            "runtime_view_xmlid": view_xmlid,
            "expected_view_xmlid": case["expected_view_xmlid"],
            "missing_fields": missing_fields,
            "owner": case["owner"],
        })
        if view_xmlid != case["expected_view_xmlid"]:
            failures.append({
                "type": "runtime_action_view_owner_mismatch",
                "case": case["name"],
                "actual": view_xmlid,
                "expected": case["expected_view_xmlid"],
            })
        for field_name in missing_fields:
            failures.append({
                "type": "runtime_missing_custom_field",
                "case": case["name"],
                "field": field_name,
            })
    return rows, failures


addon_root = _addon_root()
failures = _scan_static(addon_root)
runtime_rows, runtime_failures = _runtime_rows()
failures.extend(runtime_failures)

payload = {
    "audit": "user_formal_field_module_boundary_audit",
    "status": "PASS" if not failures else "FAIL",
    "failure_count": len(failures),
    "failures": failures,
    "runtime_rows": runtime_rows,
}
print("USER_FORMAL_FIELD_MODULE_BOUNDARY_AUDIT=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
if failures:
    raise RuntimeError(payload)
