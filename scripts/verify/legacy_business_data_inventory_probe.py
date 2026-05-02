# -*- coding: utf-8 -*-
"""Inventory legacy migrated data and formal business model coverage.

Run with:
ENV=test ENV_FILE=.env.prod.sim DB_NAME=sc_prod_sim make odoo.shell.exec < scripts/verify/legacy_business_data_inventory_probe.py
"""

from collections import Counter, defaultdict
import json


LEGACY_PREFIX = "sc.legacy."
KNOWN_SOURCE_FIELDS = ("source_origin", "legacy_source_model", "legacy_source_table", "legacy_record_id")
LINKAGE_FIELDS = (
    "project_id",
    "partner_id",
    "company_id",
    "contract_id",
    "payment_request_id",
    "receipt_id",
    "invoice_id",
    "account_id",
    "material_id",
    "product_id",
    "employee_id",
    "user_id",
)
AMOUNT_HINTS = ("amount", "price", "cost", "total", "subtotal", "balance", "debit", "credit", "tax")
DATE_HINTS = ("date", "time", "deadline")
STATE_FIELDS = ("state", "status", "legacy_document_state", "document_state")


DOMAIN_RULES = (
    ("attachment_file", ("file", "attachment", "evidence", "资料", "附件")),
    ("material", ("material", "product", "inventory", "stock", "材料")),
    ("construction_diary", ("construction", "diary", "task", "attendance", "施工")),
    ("receipt_income", ("receipt", "income", "collection", "receivable")),
    ("payment_execution", ("payment", "outflow", "payable", "付款", "支出")),
    ("invoice_registration", ("invoice", "tax", "发票")),
    ("treasury_fund", ("fund", "treasury", "account", "cash", "资金", "账户")),
    ("contract", ("contract", "agreement", "合同")),
    ("partner", ("partner", "supplier", "customer", "vendor", "客户", "供应商")),
    ("expense", ("expense", "reimbursement", "deposit", "费用")),
    ("settlement", ("settlement", "adjustment", "结算")),
    ("workflow", ("workflow", "audit", "approval", "审批")),
    ("project", ("project", "项目")),
)


FORMAL_TARGET_HINTS = {
    "attachment_file": ("ir.attachment", "sc.legacy.file.index"),
    "receipt_income": ("sc.receipt.income", "receipt.invoice.line"),
    "payment_execution": ("sc.payment.execution", "payment.request", "payment.request.line"),
    "invoice_registration": ("sc.invoice.registration", "receipt.invoice.line"),
    "treasury_fund": ("sc.treasury.ledger", "sc.treasury.reconciliation"),
    "contract": ("construction.contract", "sc.general.contract", "purchase.order"),
    "project": ("project.project",),
    "partner": ("res.partner",),
    "material": ("product.product", "product.template", "sc.material.catalog"),
    "construction_diary": ("sc.construction.diary", "project.task"),
    "expense": ("sc.expense.claim",),
    "settlement": ("sc.settlement.adjustment",),
    "workflow": ("sc.history.todo",),
}


def _safe_count(model, domain=None):
    try:
        return int(model.search_count(domain or []))
    except Exception as exc:
        return {"error": "%s: %s" % (type(exc).__name__, str(exc)[:240])}


def _field_names(model):
    return set(model._fields)


def _stored(model, field_name):
    field = model._fields.get(field_name)
    return bool(field and getattr(field, "store", True))


def _read_group_distribution(model, field_name, limit=8):
    if field_name not in model._fields or not _stored(model, field_name):
        return []
    try:
        rows = model.read_group([], [field_name], [field_name], limit=limit, orderby="%s_count desc" % field_name)
    except Exception:
        try:
            rows = model.read_group([], [field_name], [field_name], limit=limit)
        except Exception as exc:
            return [{"error": "%s: %s" % (type(exc).__name__, str(exc)[:160])}]
    result = []
    for row in rows:
        raw_value = row.get(field_name)
        if isinstance(raw_value, (list, tuple)) and raw_value:
            value = raw_value[-1]
        else:
            value = raw_value
        result.append({"value": value, "count": row.get("%s_count" % field_name, row.get("__count", 0))})
    return result


def _sample_values(model, field_name, limit=8):
    if field_name not in model._fields:
        return []
    try:
        records = model.search([(field_name, "!=", False)], limit=limit, order="id desc")
        values = records.mapped(field_name)
    except Exception as exc:
        return [{"error": "%s: %s" % (type(exc).__name__, str(exc)[:160])}]
    result = []
    for value in values:
        if hasattr(value, "display_name"):
            result.append(value.display_name)
        else:
            result.append(value)
    return result[:limit]


def _legacy_fields(fields):
    return sorted(
        name
        for name in fields
        if name.startswith("legacy_") or "_legacy_" in name or name.endswith("_legacy_id")
    )


def _business_domain(model_name, fields):
    model_haystack = model_name.lower()
    for domain, hints in DOMAIN_RULES:
        if any(hint.lower() in model_haystack for hint in hints):
            return domain
    weak_fields = " ".join(
        name
        for name in fields
        if name.startswith("legacy_") or name in ("name", "display_name", "document_no", "fact_type")
    ).lower()
    for domain, hints in DOMAIN_RULES:
        if domain == "project":
            continue
        if any(hint.lower() in weak_fields for hint in hints):
            return domain
    return "unclassified"


def _classify(model_name, fields):
    if model_name.startswith(LEGACY_PREFIX):
        return "legacy_raw_fact"
    if any(field in fields for field in KNOWN_SOURCE_FIELDS) or _legacy_fields(fields):
        return "formal_legacy_backed"
    return "related_business_model"


def _numeric_fields(model, fields):
    result = []
    for name, field in model._fields.items():
        if name not in fields:
            continue
        field_type = getattr(field, "type", "")
        if field_type in ("float", "monetary", "integer") and any(hint in name.lower() for hint in AMOUNT_HINTS):
            result.append(name)
    return sorted(result)


def _date_fields(model, fields):
    result = []
    for name, field in model._fields.items():
        if name not in fields:
            continue
        field_type = getattr(field, "type", "")
        if field_type in ("date", "datetime") and any(hint in name.lower() for hint in DATE_HINTS):
            result.append(name)
    return sorted(result)


def _inventory_model(model_name, ir_model):
    model = env[model_name].sudo()
    fields = _field_names(model)
    legacy_fields = _legacy_fields(fields)
    source_fields = [field for field in KNOWN_SOURCE_FIELDS if field in fields]
    if not (model_name.startswith(LEGACY_PREFIX) or legacy_fields or source_fields):
        return None

    record_count = _safe_count(model)
    legacy_count = None
    if "source_origin" in fields:
        legacy_count = _safe_count(model, [("source_origin", "=", "legacy")])

    state_fields = [field for field in STATE_FIELDS if field in fields]
    source_distribution = {}
    for field in ("source_origin", "legacy_source_model", "legacy_source_table"):
        if field in fields:
            source_distribution[field] = _read_group_distribution(model, field)

    state_distribution = {}
    for field in state_fields:
        state_distribution[field] = _read_group_distribution(model, field)

    linkage_fields = [field for field in LINKAGE_FIELDS if field in fields]
    domain = _business_domain(model_name, fields)
    return {
        "model": model_name,
        "name": ir_model.name,
        "class": _classify(model_name, fields),
        "business_domain": domain,
        "formal_target_hints": [target for target in FORMAL_TARGET_HINTS.get(domain, ()) if target in env],
        "record_count": record_count,
        "legacy_record_count": legacy_count,
        "legacy_fields": legacy_fields,
        "source_fields": source_fields,
        "linkage_fields": linkage_fields,
        "amount_fields": _numeric_fields(model, fields),
        "date_fields": _date_fields(model, fields),
        "state_fields": state_fields,
        "source_distribution": source_distribution,
        "state_distribution": state_distribution,
        "samples": {
            field: _sample_values(model, field)
            for field in ("legacy_record_id", "legacy_source_table", "legacy_source_model")
            if field in fields
        },
    }


def main():
    rows = []
    failures = []
    ir_models = env["ir.model"].sudo().search([], order="model")
    for ir_model in ir_models:
        model_name = ir_model.model
        if not model_name or model_name not in env:
            continue
        try:
            row = _inventory_model(model_name, ir_model)
        except Exception as exc:
            failures.append({"model": model_name, "error": "%s: %s" % (type(exc).__name__, str(exc)[:300])})
            continue
        if row:
            rows.append(row)

    class_counts = Counter(row["class"] for row in rows)
    domain_counts = Counter(row["business_domain"] for row in rows)
    record_counts_by_domain = defaultdict(int)
    populated_rows = []
    for row in rows:
        count = row["record_count"]
        if isinstance(count, int):
            record_counts_by_domain[row["business_domain"]] += count
            if count:
                populated_rows.append(row)

    mapping_backlog = []
    for domain, total in sorted(record_counts_by_domain.items(), key=lambda item: item[1], reverse=True):
        source_models = [
            {
                "model": row["model"],
                "class": row["class"],
                "records": row["record_count"],
                "legacy_records": row["legacy_record_count"],
                "targets": row["formal_target_hints"],
            }
            for row in populated_rows
            if row["business_domain"] == domain
        ]
        if source_models:
            mapping_backlog.append(
                {
                    "business_domain": domain,
                    "record_count": total,
                    "source_models": source_models,
                    "recommended_targets": sorted(
                        {
                            target
                            for source in source_models
                            for target in source.get("targets", [])
                        }
                    ),
                }
            )

    result = {
        "ok": not failures,
        "database": env.cr.dbname,
        "model_count": len(rows),
        "populated_model_count": len(populated_rows),
        "class_counts": dict(sorted(class_counts.items())),
        "domain_counts": dict(sorted(domain_counts.items())),
        "record_counts_by_domain": dict(sorted(record_counts_by_domain.items())),
        "mapping_backlog": mapping_backlog,
        "models": rows,
        "failures": failures,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


main()
