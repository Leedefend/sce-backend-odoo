# -*- coding: utf-8 -*-
"""Runtime probe for customer/supplier business fact display surfaces.

Run through Odoo shell, for example:
  ENV=test ENV_FILE=.env.prod.sim DB_NAME=sc_prod_sim \
    bash scripts/ops/odoo_shell_exec.sh < scripts/migration/partner_display_surface_runtime_probe.py
"""

import json
import xml.etree.ElementTree as ET


REQUIRED_MODEL_FIELDS = {
    "res.partner": {
        "customer_rank",
        "supplier_rank",
        "sc_supplier_type",
        "sc_account_name",
        "sc_bank_name",
        "sc_bank_account",
        "sc_region",
        "sc_registered_capital",
        "sc_business_scope",
        "sc_default_tax_rate",
        "sc_default_tax_rate_text",
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
        "sc_business_role_label",
        "sc_business_fact_basis",
        "sc_legacy_source_label",
        "legacy_partner_id",
        "legacy_partner_source",
        "legacy_partner_name",
        "legacy_source_evidence",
        "bank_ids",
    },
    "res.partner.bank": {
        "acc_number",
        "sc_legacy_external_id",
        "sc_legacy_partner_id",
        "sc_legacy_partner_source",
        "sc_account_holder_name",
        "sc_bank_name",
        "sc_source_evidence",
        "sc_import_batch",
    },
    "sc.partner.import.review": {
        "review_state",
        "review_reason",
        "partner_name",
        "suggested_customer_rank",
        "suggested_supplier_rank",
        "confirmed_customer_rank",
        "confirmed_supplier_rank",
        "target_partner_id",
        "sc_supplier_type",
        "sc_region",
        "sc_registered_capital",
        "sc_business_scope",
        "sc_default_tax_rate",
        "sc_bank_name",
        "sc_bank_account",
        "gate_reason",
        "evidence",
    },
}

REQUIRED_VIEW_FIELDS = {
    "smart_construction_core.view_sc_customer_partner_tree": {
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
        "sc_legacy_source_label",
    },
    "smart_construction_core.view_sc_customer_partner_form": {
        "name",
        "vat",
        "sc_region",
        "sc_registered_capital",
        "sc_business_scope",
        "sc_default_tax_rate",
        "sc_business_role_label",
        "sc_business_fact_basis",
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
        "sc_account_name",
        "sc_bank_name",
        "sc_bank_account",
        "bank_ids",
        "legacy_source_evidence",
    },
    "smart_construction_core.view_sc_customer_partner_search": {
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
    "smart_construction_core.view_sc_supplier_partner_tree": {
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
        "sc_legacy_source_label",
    },
    "smart_construction_core.view_sc_supplier_partner_form": {
        "name",
        "sc_supplier_type",
        "vat",
        "sc_region",
        "sc_registered_capital",
        "sc_business_scope",
        "sc_default_tax_rate",
        "sc_business_role_label",
        "sc_business_fact_basis",
        "sc_legacy_source_label",
        "sc_source_partner_code",
        "sc_source_document_state",
        "sc_source_push_result",
        "sc_source_project_name",
        "sc_source_receipt_amount",
        "sc_source_payment_amount",
        "sc_source_created_by",
        "sc_source_created_at",
        "sc_account_name",
        "sc_bank_name",
        "sc_bank_account",
        "bank_ids",
        "legacy_source_evidence",
    },
    "smart_construction_core.view_sc_supplier_partner_search": {
        "name",
        "sc_supplier_type",
        "vat",
        "sc_region",
        "sc_default_tax_rate",
        "sc_bank_name",
        "sc_bank_account",
        "legacy_partner_id",
        "sc_source_partner_code",
        "sc_source_document_state",
        "sc_source_push_result",
        "sc_source_project_name",
        "sc_source_created_by",
        "sc_business_role_label",
        "sc_business_fact_basis",
        "sc_legacy_source_label",
    },
    "smart_construction_core.view_sc_partner_import_review_tree": {
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
    "smart_construction_core.view_sc_partner_import_review_form": {
        "partner_name",
        "review_reason",
        "gate_reason",
        "target_partner_id",
        "vat",
        "sc_supplier_type",
        "sc_region",
        "sc_registered_capital",
        "sc_business_scope",
        "sc_default_tax_rate",
        "sc_bank_name",
        "sc_bank_account",
        "evidence",
    },
}

REQUIRED_ACTION_DOMAINS = {
    "smart_construction_core.action_sc_customer_partner": "customer_rank",
    "smart_construction_core.action_sc_supplier_partner": "supplier_rank",
}


def _env():
    return globals()["env"]


def _xml_fields(arch):
    root = ET.fromstring(arch)
    return {node.attrib["name"] for node in root.findall(".//field[@name]")}


def _ref(xmlid):
    return _env().ref(xmlid, raise_if_not_found=False)


errors = []
model_field_status = {}
for model_name, required in REQUIRED_MODEL_FIELDS.items():
    model = _env()[model_name]
    missing = sorted(required - set(model._fields))
    model_field_status[model_name] = {
        "required": len(required),
        "missing": missing,
    }
    if missing:
        errors.append({"model": model_name, "missing_fields": missing})

view_status = {}
for xmlid, required in REQUIRED_VIEW_FIELDS.items():
    view = _ref(xmlid)
    if not view:
        errors.append({"view": xmlid, "missing_view": True})
        continue
    actual = _xml_fields(view.arch_db)
    missing = sorted(required - actual)
    view_status[xmlid] = {
        "view_id": view.id,
        "model": view.model,
        "type": view.type,
        "required": len(required),
        "missing": missing,
    }
    if missing:
        errors.append({"view": xmlid, "missing_fields": missing})

action_status = {}
for xmlid, required_token in REQUIRED_ACTION_DOMAINS.items():
    action = _ref(xmlid)
    domain = str(action.domain or "") if action else ""
    ok = bool(action) and required_token in domain
    action_status[xmlid] = {"exists": bool(action), "domain": domain, "required_token": required_token, "ok": ok}
    if not ok:
        errors.append({"action": xmlid, "missing_domain_token": required_token, "domain": domain})

Partner = _env()["res.partner"].sudo().with_context(active_test=False)
Bank = _env()["res.partner.bank"].sudo().with_context(active_test=False)
Review = _env()["sc.partner.import.review"].sudo().with_context(active_test=False)

data_counts = {
    "customers": Partner.search_count([("customer_rank", ">", 0)]),
    "suppliers": Partner.search_count([("supplier_rank", ">", 0)]),
    "customer_supplier_mixed": Partner.search_count([("customer_rank", ">", 0), ("supplier_rank", ">", 0)]),
    "partners_with_legacy_identity": Partner.search_count([("legacy_partner_id", "!=", False)]),
    "partners_with_bank_account_surface": Partner.search_count([("sc_bank_account", "!=", False)]),
    "partners_with_default_tax_rate": Partner.search_count([("sc_default_tax_rate", "!=", 0)]),
    "partners_with_source_document_state": Partner.search_count([("sc_source_document_state", "!=", False)]),
    "partners_with_source_project_name": Partner.search_count([("sc_source_project_name", "!=", False)]),
    "partners_with_source_cooperation_type": Partner.search_count([("sc_source_cooperation_type", "!=", False)]),
    "partners_with_source_fact_source": Partner.search_count([("sc_source_fact_source", "!=", False)]),
    "partners_with_source_created_by": Partner.search_count([("sc_source_created_by", "!=", False)]),
    "partners_with_business_role_label": Partner.search_count([("sc_business_role_label", "!=", False)]),
    "partners_with_business_fact_basis": Partner.search_count([("sc_business_fact_basis", "!=", False)]),
    "legacy_mssql_customer_fact_partners": Partner.search_count([("legacy_partner_source", "=", "legacy_mssql_customer_business_fact")]),
    "partner_bank_accounts": Bank.search_count([]),
    "partner_bank_accounts_with_legacy_key": Bank.search_count([("sc_legacy_external_id", "!=", False)]),
    "import_review_candidates": Review.search_count([("review_state", "=", "candidate")]),
}

payload = {
    "status": "FAIL" if errors else "PASS",
    "mode": "partner_display_surface_runtime_probe",
    "database": _env().cr.dbname,
    "model_field_status": model_field_status,
    "view_status": view_status,
    "action_status": action_status,
    "data_counts": data_counts,
    "errors": errors,
    "db_writes": 0,
}

print("PARTNER_DISPLAY_SURFACE_RUNTIME_PROBE=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))

if errors:
    raise AssertionError(json.dumps(errors, ensure_ascii=False, sort_keys=True))
