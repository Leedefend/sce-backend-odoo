#!/usr/bin/env python3
"""Audit whether user-facing ledgers can be reconciled by business dimensions."""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

from lxml import etree


def artifact_root() -> Path:
    env_root = os.getenv("MIGRATION_ARTIFACT_ROOT")
    candidates = [Path(env_root)] if env_root else []
    candidates.append(Path("/mnt/artifacts/verify"))
    candidates.append(Path(f"/tmp/history_continuity/{env.cr.dbname}/verify"))  # noqa: F821
    for candidate in candidates:
        try:
            candidate.mkdir(parents=True, exist_ok=True)
            probe = candidate / ".write_probe"
            probe.write_text("ok\n", encoding="utf-8")
            probe.unlink()
            return candidate
        except Exception:
            continue
    return Path(f"/tmp/history_continuity/{env.cr.dbname}/verify")  # noqa: F821


def scalar(sql: str, params: list[object] | None = None) -> object:
    env.cr.execute(sql, params or [])  # noqa: F821
    row = env.cr.fetchone()  # noqa: F821
    return row[0] if row else None


def resolve_view(xmlid: str):
    try:
        return env.ref(xmlid).sudo()  # noqa: F821
    except ValueError:
        return None


def parse_view(xmlid: str) -> dict[str, object]:
    view = resolve_view(xmlid)
    arch = view.arch_db if view else ""
    group_fields = set(re.findall(r"group_by'?\s*:\s*'([^']+)'", arch))
    try:
        root = etree.fromstring(arch.encode("utf-8")) if arch else None
    except Exception:
        root = None
    sum_fields = set()
    visible_fields = set()
    if root is not None:
        for node in root.xpath(".//field[@name]"):
            name = node.get("name")
            if name:
                visible_fields.add(name)
                if node.get("sum"):
                    sum_fields.add(name)
    return {
        "xmlid": xmlid,
        "exists": bool(view),
        "group_fields": sorted(group_fields),
        "sum_fields": sorted(sum_fields),
        "visible_fields": sorted(visible_fields),
    }


def read_group_sample(model_name: str, field_name: str, amount_field: str | None, domain: list[object]) -> list[dict[str, object]]:
    Model = env[model_name].sudo()  # noqa: F821
    fields = [f"{amount_field}:sum"] if amount_field else []
    rows = Model.read_group(domain, fields, [field_name], lazy=False)
    rows.sort(key=lambda row: row.get(amount_field or "__count") or row.get("__count") or 0, reverse=True)
    sample = []
    for row in rows[:8]:
        item = {
            "value": row.get(field_name),
            "count": int(row.get(f"{field_name}_count") or row.get("__count") or 0),
        }
        if amount_field:
            item["amount"] = float(row.get(amount_field) or 0)
        sample.append(item)
    return sample


def non_empty_count(model_name: str, field_name: str, domain: list[object]) -> int:
    Model = env[model_name].sudo()  # noqa: F821
    return Model.search_count(domain + [(field_name, "!=", False)])


def table_count(model_name: str, domain: list[object]) -> int:
    return env[model_name].sudo().search_count(domain)  # noqa: F821


CONFIGS = [
    {
        "key": "income_contract_ledger",
        "label": "收入合同台账",
        "model": "sc.income.contract.ledger",
        "search_view": "smart_construction_core.view_sc_income_contract_ledger_search",
        "tree_view": "smart_construction_core.view_sc_income_contract_ledger_tree",
        "domain": [],
        "amount": "amount_total",
        "required_group_fields": ["contract_family", "project_id", "partner_name_text", "operation_strategy", "state", "contract_date"],
        "required_sum_fields": ["amount_total", "invoice_amount", "received_amount", "unreceived_amount"],
        "required_visible_fields": ["contract_no", "contract_name", "project_id", "partner_name_text", "amount_total"],
        "coverage_fields": ["project_id", "partner_name_text", "contract_no", "contract_date"],
    },
    {
        "key": "expense_contract_ledger",
        "label": "支出合同台账",
        "model": "sc.expense.contract.ledger",
        "search_view": "smart_construction_core.view_sc_expense_contract_ledger_search",
        "tree_view": "smart_construction_core.view_sc_expense_contract_ledger_tree",
        "domain": [],
        "amount": "amount_total",
        "required_group_fields": ["contract_type", "project_id", "partner_name_text", "operation_strategy", "state", "contract_date"],
        "required_sum_fields": ["amount_total", "invoice_amount", "paid_amount", "unpaid_amount"],
        "required_visible_fields": ["contract_no", "contract_name", "contract_type", "project_id", "partner_name_text", "amount_total"],
        "coverage_fields": ["project_id", "partner_name_text", "contract_no", "contract_date", "contract_type"],
    },
    {
        "key": "receipt_income",
        "label": "收款收入",
        "model": "sc.receipt.income",
        "search_view": "smart_construction_core.view_sc_receipt_income_search",
        "tree_view": "smart_construction_core.view_sc_receipt_income_tree",
        "domain": [("source_origin", "=", "legacy")],
        "amount": "amount",
        "required_group_fields": ["project_id", "partner_id", "legacy_receipt_type", "legacy_receipt_subtype", "income_category", "receipt_type", "state", "date_receipt"],
        "required_sum_fields": ["amount", "deducted_invoice_amount", "deducted_tax_amount", "settlement_amount"],
        "required_visible_fields": ["document_no", "project_id", "partner_id", "income_category", "legacy_receipt_type", "amount"],
        "coverage_fields": ["project_id", "income_category", "date_receipt", "document_no"],
    },
    {
        "key": "payment_execution",
        "label": "付款执行",
        "model": "sc.payment.execution",
        "search_view": "smart_construction_core.view_sc_payment_execution_search",
        "tree_view": "smart_construction_core.view_sc_payment_execution_tree",
        "domain": [("source_origin", "=", "legacy")],
        "amount": "paid_amount",
        "required_group_fields": ["project_id", "partner_id", "payment_family", "payment_method", "source_kind", "state", "date_payment"],
        "required_sum_fields": ["planned_amount", "paid_amount", "invoice_amount"],
        "required_visible_fields": ["document_no", "project_id", "partner_id", "payment_family", "paid_amount"],
        "coverage_fields": ["project_id", "payment_family", "date_payment", "document_no"],
    },
    {
        "key": "expense_claim",
        "label": "费用/保证金",
        "model": "sc.expense.claim",
        "search_view": "smart_construction_core.view_sc_expense_claim_search",
        "tree_view": "smart_construction_core.view_sc_expense_claim_tree",
        "domain": [("source_origin", "=", "legacy")],
        "amount": "amount",
        "required_group_fields": ["project_id", "partner_id", "claim_type", "expense_type", "payment_method", "direction", "state", "date_claim"],
        "required_sum_fields": ["amount", "approved_amount"],
        "required_visible_fields": ["name", "project_id", "partner_id", "claim_type", "expense_type", "amount"],
        "coverage_fields": ["project_id", "claim_type", "expense_type", "date_claim"],
    },
    {
        "key": "invoice_registration",
        "label": "发票登记",
        "model": "sc.invoice.registration",
        "search_view": "smart_construction_core.view_sc_invoice_registration_search",
        "tree_view": "smart_construction_core.view_sc_invoice_registration_tree",
        "domain": [("source_origin", "=", "legacy")],
        "amount": "amount_total",
        "required_group_fields": ["project_id", "partner_id", "direction", "source_kind", "invoice_type", "tax_rate", "cost_category_name", "state", "invoice_date"],
        "required_sum_fields": ["amount_no_tax", "tax_amount", "amount_total"],
        "required_visible_fields": ["document_no", "project_id", "partner_id", "direction", "source_kind", "invoice_type", "amount_total"],
        "coverage_fields": ["project_id", "direction", "source_kind", "invoice_date", "invoice_no"],
    },
    {
        "key": "tax_deduction_registration",
        "label": "抵扣登记",
        "model": "sc.tax.deduction.registration",
        "search_view": "smart_construction_core.view_sc_tax_deduction_registration_search",
        "tree_view": "smart_construction_core.view_sc_tax_deduction_registration_tree",
        "domain": [("source_origin", "=", "legacy")],
        "amount": "deduction_amount",
        "required_group_fields": ["project_id", "partner_id", "operation_strategy", "state", "invoice_date", "deduction_confirm_date"],
        "required_sum_fields": ["invoice_amount_total", "deduction_amount", "deduction_tax_amount", "deduction_surcharge_amount"],
        "required_visible_fields": ["document_no", "project_id", "partner_id", "invoice_no", "deduction_amount"],
        "coverage_fields": ["project_id", "invoice_no", "invoice_date", "deduction_confirm_date"],
    },
    {
        "key": "fund_account_operation",
        "label": "资金账户操作",
        "model": "sc.fund.account.operation",
        "search_view": "smart_construction_core.view_sc_fund_account_operation_search",
        "tree_view": "smart_construction_core.view_sc_fund_account_operation_tree",
        "domain": [("legacy_record_id", "!=", False)],
        "amount": "amount",
        "required_group_fields": ["operation_type", "project_id", "operation_strategy", "operation_date"],
        "required_sum_fields": ["amount", "daily_income", "daily_expense"],
        "required_visible_fields": ["name", "project_id", "operation_type", "amount"],
        "coverage_fields": ["project_id", "operation_type", "operation_date"],
    },
]


results = []
errors = []
for config in CONFIGS:
    model_name = config["model"]
    if model_name not in env:  # noqa: F821
        errors.append({"key": config["key"], "reason": "model_missing"})
        continue

    search = parse_view(config["search_view"])
    tree = parse_view(config["tree_view"])
    domain = config["domain"]
    total = table_count(model_name, domain)
    amount_field = config.get("amount")
    amount_sum = 0.0
    if amount_field and amount_field in env[model_name]._fields:  # noqa: F821
        amount_sum = float(sum(env[model_name].sudo().search(domain).mapped(amount_field)) or 0.0)  # noqa: F821

    missing_groups = sorted(set(config["required_group_fields"]) - set(search["group_fields"]))
    missing_sums = sorted(set(config["required_sum_fields"]) - set(tree["sum_fields"]))
    missing_visible = sorted(set(config["required_visible_fields"]) - set(tree["visible_fields"]))

    coverage = {}
    for field_name in config["coverage_fields"]:
        if field_name not in env[model_name]._fields:  # noqa: F821
            coverage[field_name] = {"exists": False}
            continue
        filled = non_empty_count(model_name, field_name, domain)
        coverage[field_name] = {
            "exists": True,
            "filled": filled,
            "total": total,
            "ratio": round((filled / total), 4) if total else 1.0,
        }

    group_samples = {}
    for field_name in config["required_group_fields"]:
        if field_name in env[model_name]._fields:  # noqa: F821
            group_samples[field_name] = read_group_sample(model_name, field_name, amount_field, domain)

    row = {
        "key": config["key"],
        "label": config["label"],
        "model": model_name,
        "total": total,
        "amount_field": amount_field,
        "amount_sum": amount_sum,
        "missing_group_fields": missing_groups,
        "missing_sum_fields": missing_sums,
        "missing_visible_fields": missing_visible,
        "coverage": coverage,
        "group_samples": group_samples,
    }
    results.append(row)
    if missing_groups or missing_sums or missing_visible:
        errors.append(
            {
                "key": config["key"],
                "missing_group_fields": missing_groups,
                "missing_sum_fields": missing_sums,
                "missing_visible_fields": missing_visible,
            }
        )

payload = {
    "status": "FAIL" if errors else "PASS",
    "database": env.cr.dbname,  # noqa: F821
    "mode": "user_reconciliation_readiness_probe",
    "entry_count": len(results),
    "gap_count": len(errors),
    "gaps": errors,
    "results": results,
}
output = artifact_root() / "user_reconciliation_readiness_probe_result_v1.json"
output.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print("USER_RECONCILIATION_READINESS_PROBE=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))

if errors:
    raise SystemExit(1)
