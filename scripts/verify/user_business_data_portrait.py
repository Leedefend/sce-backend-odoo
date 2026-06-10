# -*- coding: utf-8 -*-
"""Profile real user business data for productized capability design.

Run with:
docker compose exec -T odoo odoo shell -d sc_demo -c /var/lib/odoo/odoo.conf < scripts/verify/user_business_data_portrait.py
"""

from collections import Counter
import json


AMOUNT_HINTS = ("amount", "balance", "price", "cost", "total", "tax", "paid", "income", "expense")
DATE_HINTS = ("date", "time", "deadline")
ANCHOR_FIELDS = (
    "project_id",
    "partner_id",
    "contract_id",
    "payment_request_id",
    "account_id",
    "source_account_id",
    "target_account_id",
    "fund_account_id",
    "employee_id",
    "user_id",
)
STATE_FIELDS = ("state", "status", "document_state", "legacy_document_state")
SOURCE_FIELDS = ("source_origin", "source_family", "legacy_source_model", "legacy_source_table")
GENERIC_ACTION_METHODS = {
    "action_archive",
    "action_unarchive",
    "action_open_business_doc",
}


CAPABILITY_FAMILIES = [
    {
        "key": "project_master_data",
        "name": "项目与主数据",
        "product_question": "项目、公司、客户、供应商、账户是否能作为所有业务单据的统一锚点。",
        "models": [
            "project.project",
            "res.partner",
            "sc.business.entity",
            "sc.fund.account",
            "sc.legacy.project.map",
            "sc.legacy.partner.map",
        ],
    },
    {
        "key": "contract_settlement",
        "name": "合同与结算",
        "product_question": "收入合同、支出合同、结算、台账是否能承接收付款和成本闭环。",
        "models": [
            "construction.contract",
            "construction.contract.line",
            "construction.contract.income",
            "construction.contract.expense",
            "sc.income.contract.ledger",
            "sc.expense.contract.ledger",
            "project.settlement",
            "project.settlement.line",
            "sc.settlement.order",
            "sc.settlement.order.line",
            "sc.contract.event",
            "sc.contract.recon.summary",
        ],
    },
    {
        "key": "income_receivable",
        "name": "收入与收款",
        "product_question": "工程进度收款、到款确认、自筹收入是否统一为项目收入/收款办理。",
        "models": [
            "sc.receipt.income",
            "sc.receipt.invoice.line",
            "sc.legacy.fund.confirmation.document",
            "sc.legacy.fund.confirmation.line",
            "sc.legacy.engineering.progress.receipt",
            "sc.legacy.receipt.income.fact",
            "sc.legacy.self.funding.fact",
        ],
    },
    {
        "key": "payment_expense",
        "name": "付款与费用",
        "product_question": "费用支出、扣款实缴/退回、保证金支付/退回是否统一为项目付款/费用办理。",
        "models": [
            "payment.request",
            "payment.request.line",
            "sc.payment.execution",
            "payment.ledger",
            "sc.expense.claim",
            "sc.legacy.expense.deposit.fact",
            "sc.legacy.expense.reimbursement.line",
            "sc.legacy.payment.residual.fact",
        ],
    },
    {
        "key": "tax_invoice",
        "name": "税务与发票",
        "product_question": "抵扣、销项、进项、发票成本进度是否统一到税务/发票办理。",
        "models": [
            "sc.tax.deduction.registration",
            "sc.invoice.registration",
            "sc.output.invoice.ledger",
            "sc.output.invoice.adjustment",
            "sc.legacy.tax.deduction.fact",
            "sc.legacy.invoice.tax.fact",
            "sc.legacy.invoice.registration.line",
            "sc.legacy.invoice_analysis_report_fact",
            "sc.legacy.invoice.cost.progress.report.fact",
        ],
    },
    {
        "key": "fund_interfund",
        "name": "账户与往来资金",
        "product_question": "公司与项目、项目与项目、项目与承包人之间的借还/调拨是否统一为资金往来办理。",
        "models": [
            "sc.fund.account.operation",
            "sc.financing.loan",
            "sc.finance.project.capital.position",
            "sc.finance.project.counterparty.position",
            "sc.finance.counterparty.position.summary",
            "sc.interfund.movement.fact",
            "sc.interfund.movement.project.summary",
            "sc.legacy.fund.daily.line",
            "sc.legacy.fund.daily.snapshot.fact",
            "sc.legacy.account.transaction.line",
            "sc.legacy.financing.loan.fact",
        ],
    },
    {
        "key": "procurement_material",
        "name": "材料与采购库存",
        "product_question": "材料计划、采购、验收、入库、出库、结算是否形成一条办理链。",
        "models": [
            "project.material.plan",
            "project.material.plan.line",
            "sc.material.purchase.request",
            "sc.material.purchase.request.line",
            "sc.material.rfq",
            "sc.material.rfq.line",
            "sc.material.acceptance",
            "sc.material.acceptance.line",
            "sc.material.inbound",
            "sc.material.inbound.line",
            "sc.material.outbound",
            "sc.material.outbound.line",
            "sc.material.settlement",
            "sc.material.settlement.line",
            "sc.material.catalog",
            "sc.material.price",
            "sc.legacy.material.stock.fact",
            "sc.legacy.purchase.contract.fact",
        ],
    },
    {
        "key": "subcontract_labor_equipment",
        "name": "分包劳务机械",
        "product_question": "分包、劳务、机械是否按计划/申请/使用/结算/价格形成统一办理链。",
        "models": [
            "sc.subcontract.plan",
            "sc.subcontract.request",
            "sc.subcontract.register",
            "sc.subcontract.settlement",
            "sc.labor.plan",
            "sc.labor.request",
            "sc.attendance.checkin",
            "sc.labor.usage",
            "sc.labor.settlement",
            "sc.equipment.plan",
            "sc.equipment.request",
            "sc.equipment.usage",
            "sc.equipment.settlement",
            "sc.legacy.labor.subcontract.fact",
            "sc.legacy.equipment.lease.fact",
        ],
    },
    {
        "key": "site_quality_safety_progress",
        "name": "现场进度质量安全",
        "product_question": "施工日志、进度、质量、安全是否支撑项目现场过程管控。",
        "models": [
            "sc.construction.diary",
            "project.progress.entry",
            "project.task",
            "sc.quality.issue",
            "sc.quality.rectification",
            "sc.quality.recheck",
            "sc.safety.plan",
            "sc.safety.issue",
            "sc.safety.rectification",
            "sc.safety.recheck",
            "sc.safety.patrol.task",
            "sc.legacy.construction.diary.line",
            "sc.legacy.task.evidence",
        ],
    },
    {
        "key": "cost_budget_control",
        "name": "预算成本管控",
        "product_question": "目标成本、清单、成本科目、成本台账是否能约束合同/采购/付款。",
        "models": [
            "project.budget",
            "project.budget.line",
            "project.boq.line",
            "project.budget.boq.line",
            "project.budget.cost.alloc",
            "project.cost.code",
            "project.cost.ledger",
            "project.cost.period",
            "project.funding.baseline",
            "sc.comprehensive.cost.summary",
        ],
    },
    {
        "key": "governance_workflow_evidence",
        "name": "审批附件与治理",
        "product_question": "审批、附件、历史轨迹是否能支撑正式办理追溯和审计。",
        "models": [
            "sc.approval.policy",
            "sc.approval.step",
            "sc.history.todo",
            "sc.workflow.instance",
            "sc.workflow.workitem",
            "sc.workflow.log",
            "sc.audit.log",
            "ir.attachment",
            "sc.legacy.file.index",
            "sc.legacy.workflow.audit",
            "sc.legacy.workflow.detail.fact",
        ],
    },
]


def _safe_count(model, domain=None):
    try:
        return int(model.search_count(domain or []))
    except Exception as exc:
        return {"error": "%s: %s" % (type(exc).__name__, str(exc)[:180])}


def _read_group_distribution(model, field_name, limit=12):
    field = model._fields.get(field_name)
    if not field or not getattr(field, "store", True):
        return []
    try:
        rows = model.read_group([], [field_name], [field_name], limit=limit, lazy=False)
    except Exception as exc:
        return [{"error": "%s: %s" % (type(exc).__name__, str(exc)[:160])}]
    result = []
    for row in rows:
        raw = row.get(field_name)
        value = raw[-1] if isinstance(raw, (list, tuple)) and raw else raw
        result.append({"value": value, "count": int(row.get("%s_count" % field_name, row.get("__count", 0)) or 0)})
    return sorted(result, key=lambda item: item["count"], reverse=True)


def _sum_field(model, field_name):
    field = model._fields.get(field_name)
    if not field or not getattr(field, "store", True):
        return None
    try:
        rows = model.read_group([], ["%s:sum" % field_name], [])
        if rows:
            return rows[0].get(field_name) or 0.0
    except Exception:
        return None
    return None


def _date_range(model, field_name):
    field = model._fields.get(field_name)
    table = getattr(model, "_table", None)
    if not field or not table or not getattr(field, "store", True):
        return None
    if getattr(field, "type", "") not in ("date", "datetime"):
        return None
    try:
        env.cr.execute(
            'SELECT MIN("%s"), MAX("%s") FROM "%s" WHERE "%s" IS NOT NULL'
            % (field_name, field_name, table, field_name)
        )
        row = env.cr.fetchone()
    except Exception:
        return None
    if not row or (row[0] is None and row[1] is None):
        return None
    return {"min": str(row[0]) if row[0] is not None else None, "max": str(row[1]) if row[1] is not None else None}


def _missing_anchor_count(model, field_name):
    field = model._fields.get(field_name)
    if not field or not getattr(field, "store", True):
        return None
    try:
        return int(model.search_count([(field_name, "=", False)]))
    except Exception:
        return None


def _action_methods(model):
    methods = []
    for name in dir(model):
        if not name.startswith("action_"):
            continue
        if name in GENERIC_ACTION_METHODS:
            continue
        attr = getattr(model, name, None)
        if callable(attr):
            methods.append(name)
    return sorted(methods)


def _candidate_fields(model, hints, field_types):
    result = []
    for name, field in model._fields.items():
        if getattr(field, "type", "") not in field_types:
            continue
        if not getattr(field, "store", True):
            continue
        lowered = name.lower()
        if any(hint in lowered for hint in hints):
            result.append(name)
    return sorted(result)


def _profile_model(model_name):
    if model_name not in env:
        return {"model": model_name, "installed": False}
    model = env[model_name].sudo()
    count = _safe_count(model)
    fields = model._fields
    amount_fields = _candidate_fields(model, AMOUNT_HINTS, ("float", "monetary", "integer"))[:10]
    date_fields = _candidate_fields(model, DATE_HINTS, ("date", "datetime"))[:8]
    anchors = [field for field in ANCHOR_FIELDS if field in fields]
    state_fields = [field for field in STATE_FIELDS if field in fields]
    source_fields = [field for field in SOURCE_FIELDS if field in fields]

    amount_totals = {}
    for field_name in amount_fields:
        total = _sum_field(model, field_name)
        if total is not None:
            amount_totals[field_name] = total

    date_ranges = {}
    for field_name in date_fields:
        rng = _date_range(model, field_name)
        if rng:
            date_ranges[field_name] = rng

    anchor_missing = {}
    if isinstance(count, int) and count:
        for field_name in anchors:
            missing = _missing_anchor_count(model, field_name)
            if missing is not None:
                anchor_missing[field_name] = missing

    distributions = {}
    for field_name in state_fields + source_fields:
        dist = _read_group_distribution(model, field_name)
        if dist:
            distributions[field_name] = dist

    actions = _action_methods(model)
    return {
        "model": model_name,
        "installed": True,
        "description": getattr(model, "_description", ""),
        "record_count": count,
        "has_legacy_source": bool(set(fields) & set(SOURCE_FIELDS)) or model_name.startswith("sc.legacy."),
        "state_fields": state_fields,
        "source_fields": source_fields,
        "anchor_fields": anchors,
        "anchor_missing": anchor_missing,
        "amount_fields": amount_fields,
        "amount_totals": amount_totals,
        "date_ranges": date_ranges,
        "actions": actions,
        "state_and_source_distribution": distributions,
    }


def _assess_family(family, model_rows):
    installed = [row for row in model_rows if row.get("installed")]
    populated = [row for row in installed if isinstance(row.get("record_count"), int) and row.get("record_count")]
    total_records = sum(row["record_count"] for row in populated)
    legacy_models = [row["model"] for row in installed if row.get("has_legacy_source")]
    handling_models = [row["model"] for row in installed if row.get("actions")]
    anchor_gap_models = []
    for row in populated:
        gaps = {k: v for k, v in row.get("anchor_missing", {}).items() if v}
        if gaps:
            anchor_gap_models.append({"model": row["model"], "missing": gaps})
    return {
        "model_count": len(installed),
        "populated_model_count": len(populated),
        "record_count": total_records,
        "legacy_backed_model_count": len(legacy_models),
        "handling_model_count": len(handling_models),
        "anchor_gap_model_count": len(anchor_gap_models),
        "legacy_backed_models": legacy_models,
        "handling_models": handling_models,
        "anchor_gap_models": anchor_gap_models[:12],
    }


def main():
    families = []
    all_model_rows = []
    for family in CAPABILITY_FAMILIES:
        model_rows = [_profile_model(model_name) for model_name in family["models"]]
        all_model_rows.extend([row for row in model_rows if row.get("installed")])
        families.append(
            {
                "key": family["key"],
                "name": family["name"],
                "product_question": family["product_question"],
                "assessment": _assess_family(family, model_rows),
                "models": model_rows,
            }
        )

    model_counter = Counter(row["model"] for row in all_model_rows)
    duplicated_models = sorted(model for model, count in model_counter.items() if count > 1)
    result = {
        "ok": True,
        "database": env.cr.dbname,
        "scope": "real_user_business_data_portrait",
        "family_count": len(families),
        "installed_model_count": len(set(model_counter)),
        "duplicated_models_across_families": duplicated_models,
        "summary": {
            "total_profiled_records": sum(
                family["assessment"]["record_count"]
                for family in families
                if isinstance(family["assessment"]["record_count"], int)
            ),
            "families_with_data": [
                family["name"] for family in families if family["assessment"]["record_count"] > 0
            ],
            "families_with_anchor_gaps": [
                family["name"] for family in families if family["assessment"]["anchor_gap_model_count"] > 0
            ],
        },
        "families": families,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True, default=str))
    return 0


main()
