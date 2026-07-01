# -*- coding: utf-8 -*-
"""Guard locked historical facts carried by formal business models.

This check proves the product direction:
- locked user-accepted historical facts are present in formal business models;
- immutable historical fact fields cannot be edited after legacy confirmation;
- later business continuity must be built by new documents, derived views, or
  non-invasive mapping layers, not by rewriting locked facts.

Run with:
docker compose exec -T odoo odoo shell -d sc_demo -c /var/lib/odoo/odoo.conf < scripts/verify/locked_fact_formal_model_continuity_guard.py
"""

import json
import os
from pathlib import Path


LOCKED_FORMAL_MODELS = [
    {
        "model": "sc.receipt.income",
        "label": "收入与收款",
        "domain": [("source_origin", "=", "legacy"), ("state", "=", "legacy_confirmed")],
        "forbidden_candidates": ["amount", "document_no", "name", "date_receipt", "state"],
        "allowed_continuity_fields": ["partner_id", "contract_id", "payment_request_id", "treasury_ledger_id", "note"],
    },
    {
        "model": "sc.expense.claim",
        "label": "付款与费用",
        "domain": [("source_origin", "=", "legacy"), ("state", "=", "legacy_confirmed")],
        "forbidden_candidates": ["amount", "approved_amount", "legacy_document_no", "name", "date_claim", "state"],
        "allowed_continuity_fields": ["partner_id", "payment_request_id", "paid_amount", "payment_state", "note"],
    },
    {
        "model": "sc.invoice.registration",
        "label": "税务与发票",
        "domain": [("source_origin", "=", "legacy"), ("state", "=", "legacy_confirmed")],
        "forbidden_candidates": ["amount_total", "actual_invoice_amount", "invoice_no", "document_no", "name", "state"],
        "allowed_continuity_fields": ["partner_id", "contract_id", "settlement_id", "note"],
    },
    {
        "model": "sc.tax.deduction.registration",
        "label": "抵扣登记",
        "domain": [("source_origin", "=", "legacy"), ("state", "=", "legacy_confirmed")],
        "forbidden_candidates": ["invoice_amount_total", "deduction_amount", "invoice_no", "document_no", "name", "state"],
        "allowed_continuity_fields": ["partner_id", "deduction_unit_name", "withholding_amount", "deduction_reason", "note"],
    },
    {
        "model": "sc.payment.execution",
        "label": "付款执行",
        "domain": [("source_origin", "=", "legacy"), ("state", "=", "legacy_confirmed")],
        "forbidden_candidates": ["planned_amount", "paid_amount", "document_no", "name", "date_payment", "state"],
        "allowed_continuity_fields": ["partner_id", "contract_id", "payment_request_id", "note"],
    },
    {
        "model": "sc.financing.loan",
        "label": "融资与借款",
        "domain": [("source_origin", "=", "legacy"), ("state", "=", "legacy_confirmed")],
        "forbidden_candidates": ["state", "document_no", "name"],
        "allowed_continuity_fields": [
            "partner_id",
            "business_category_id",
            "amount",
            "purpose",
            "due_date",
            "document_date",
            "loan_type",
            "loan_bank_name",
            "loan_account",
            "financing_loan_request_department",
            "financing_loan_request_time",
            "financing_loan_budget_included",
            "financing_loan_actual_loan_amount",
            "financing_loan_fund_usage_plan",
            "financing_loan_bank_name",
            "financing_loan_borrow_account",
            "financing_loan_approved_amount",
            "financing_loan_request_amount",
            "financing_loan_expected_return_time",
            "financing_loan_loan_type_display",
            "note",
        ],
    },
]

FORMAL_SOURCE_MODELS = [
    {
        "model": "payment.request",
        "label": "付款申请",
        "domain": [("legacy_visible_document_no", "!=", False)],
        "continuity_note": "formal payment request carrier; historical visible fields are read-only evidence",
    },
    {
        "model": "sc.settlement.order",
        "label": "结算单",
        "domain": ["|", ("legacy_fact_model", "!=", False), ("legacy_acceptance_label", "!=", False)],
        "continuity_note": "formal settlement carrier; relationship changes must use explicit binding flow",
    },
    {
        "model": "sc.fund.account.operation",
        "label": "账户与往来资金",
        "domain": [("legacy_source_model", "!=", False)],
        "continuity_note": "formal fund operation carrier; account relationship gaps require mapping/new operation flow",
    },
]


def artifact_root() -> Path:
    raw = os.getenv("MIGRATION_ARTIFACT_ROOT")
    candidates = [Path(raw)] if raw else []
    candidates.extend([Path("/mnt/artifacts/backend"), Path.cwd() / "artifacts"])
    for candidate in candidates:
        try:
            candidate.mkdir(parents=True, exist_ok=True)
            probe = candidate / ".write_probe"
            probe.write_text("ok\n", encoding="utf-8")
            probe.unlink()
            return candidate
        except OSError:
            continue
    return Path("/tmp")


def _value_for_field(record, field_name):
    field = record._fields[field_name]
    field_type = field.type
    current = record[field_name]
    if field_type in ("float", "monetary"):
        return (current or 0.0) + 1.23
    if field_type == "integer":
        return (current or 0) + 1
    if field_type == "char":
        return "%s-LOCK-GUARD" % (current or "LOCK")
    if field_type == "text":
        return "%s\nLOCK-GUARD" % (current or "")
    if field_type == "date":
        return "2026-06-10"
    if field_type == "datetime":
        return "2026-06-10 00:00:00"
    if field_type == "selection":
        selection = field.selection or []
        current_key = current or False
        for key, _label in selection:
            if key != current_key:
                return key
        return current_key
    return None


def _first_forbidden_field(record, candidates):
    for field_name in candidates:
        if field_name in record._fields:
            value = _value_for_field(record, field_name)
            if value is not None:
                return field_name, value
    return None, None


def _probe_locked_write(model_name, domain, forbidden_candidates):
    model = env[model_name].sudo()
    rec = model.search(domain, limit=1)
    if not rec:
        return {"tested": False, "reason": "no_locked_sample"}
    field_name, value = _first_forbidden_field(rec, forbidden_candidates)
    if not field_name:
        return {"tested": False, "record_id": rec.id, "reason": "no_forbidden_field_candidate"}
    try:
        rec.write({field_name: value})
        env.cr.rollback()
        return {
            "tested": True,
            "record_id": rec.id,
            "field": field_name,
            "blocked": False,
            "error": "forbidden write unexpectedly succeeded",
        }
    except Exception as exc:
        env.cr.rollback()
        return {
            "tested": True,
            "record_id": rec.id,
            "field": field_name,
            "blocked": True,
            "exception": type(exc).__name__,
            "message": str(exc)[:240],
        }


def _count(model_name, domain):
    if model_name not in env:
        return {"error": "model_not_installed"}
    try:
        return int(env[model_name].sudo().search_count(domain))
    except Exception as exc:
        return {"error": "%s: %s" % (type(exc).__name__, str(exc)[:240])}


def main():
    locked_checks = []
    errors = []
    for spec in LOCKED_FORMAL_MODELS:
        model_name = spec["model"]
        if model_name not in env:
            locked_checks.append({**spec, "installed": False, "locked_count": 0})
            errors.append("%s not installed" % model_name)
            continue
        locked_count = _count(model_name, spec["domain"])
        write_probe = _probe_locked_write(model_name, spec["domain"], spec["forbidden_candidates"])
        row = {
            "model": model_name,
            "label": spec["label"],
            "installed": True,
            "locked_count": locked_count,
            "allowed_continuity_fields": spec["allowed_continuity_fields"],
            "write_probe": write_probe,
        }
        locked_checks.append(row)
        if isinstance(locked_count, int) and locked_count <= 0:
            errors.append("%s has no locked formal fact records" % model_name)
        if write_probe.get("tested") and not write_probe.get("blocked"):
            errors.append("%s forbidden write was not blocked" % model_name)

    source_checks = []
    for spec in FORMAL_SOURCE_MODELS:
        model_name = spec["model"]
        source_count = _count(model_name, spec["domain"]) if model_name in env else {"error": "model_not_installed"}
        source_checks.append(
            {
                "model": model_name,
                "label": spec["label"],
                "source_count": source_count,
                "continuity_note": spec["continuity_note"],
            }
        )
        if isinstance(source_count, int) and source_count <= 0:
            errors.append("%s has no formal source carrier records" % model_name)
        elif not isinstance(source_count, int):
            errors.append("%s source carrier count failed: %s" % (model_name, source_count))

    result = {
        "ok": not errors,
        "database": env.cr.dbname,
        "scope": "locked_fact_formal_model_continuity_guard",
        "policy": {
            "locked_user_fact_data": "must_remain_immutable",
            "continuity_carrier": "formal_models_new_documents_derived_views_or_non_invasive_mapping",
            "forbidden": "rewrite_locked_user_accepted_fact_values",
        },
        "summary": {
            "locked_model_count": len(locked_checks),
            "source_carrier_model_count": len(source_checks),
            "error_count": len(errors),
        },
        "locked_checks": locked_checks,
        "source_checks": source_checks,
        "errors": errors,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True, default=str))
    target = artifact_root() / f"locked_fact_formal_model_continuity_guard.{env.cr.dbname}.json"
    target.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True, default=str), encoding="utf-8")
    return 0 if result["ok"] else 1


raise SystemExit(main())
