# -*- coding: utf-8 -*-
"""Runtime probe for formal business fact operability.

Run with:
ENV=test ... DB_NAME=sc_prod_sim make odoo.shell.exec < scripts/verify/business_menu_fact_operability_probe.py
"""

import json

from odoo.exceptions import ValidationError


FORMAL_MODELS = [
    "sc.dashboard.cockpit.fact",
    "sc.workbench.item",
    "sc.project.budget.fact",
    "sc.project.document.fact",
    "sc.material.document",
    "sc.labor.document",
    "sc.equipment.document",
    "sc.subcontract.document",
    "sc.construction.inspection",
    "sc.construction.report",
    "sc.finance.expense.document",
    "sc.fund.operation",
    "sc.analysis.report.fact",
]


def _first(model, domain=None):
    return env[model].sudo().search(domain or [], limit=1)


def _valid_cases():
    partner = _first("res.partner")
    location = _first("stock.location", [("usage", "in", ["internal", "transit"])])
    return [
        ("sc.dashboard.cockpit.fact", "fund_cockpit", {"cockpit_scope": "project", "metric_period": "month", "metric_value": 1.5}),
        ("sc.workbench.item", "my_approval", {"priority": "normal", "todo_deadline": "2026-05-01"}),
        ("sc.project.budget.fact", "material_budget", {"budget_basis": "验收依据", "original_budget_amount": 10, "adjusted_budget_amount": 12}),
        ("sc.project.document.fact", "archive_document", {"archive_no": "ARCH-1", "owner_name": "验收责任人"}),
        ("sc.material.document", "inbound", {"quantity": 1, "dest_location_id": location.id if location else False}),
        ("sc.labor.document", "attendance_record", {"labor_team": "验收班组", "work_content": "验收作业", "worker_count": 2, "attendance_date": "2026-05-01"}),
        ("sc.equipment.document", "equipment_usage", {"equipment_name": "验收设备", "usage_location": "验收地点", "operator_name": "验收人员", "usage_hours": 2}),
        ("sc.subcontract.document", "subcontract_register", {"subcontract_scope": "验收范围", "subcontractor_id": partner.id if partner else False}),
        (
            "sc.construction.inspection",
            "quality_rectification",
            {
                "inspection_location": "验收部位",
                "responsible_party_id": partner.id if partner else False,
                "rectification_deadline": "2026-05-01",
                "rectification_result": "已整改",
            },
        ),
        ("sc.construction.report", "daily_report", {"period_start": "2026-05-01", "period_end": "2026-05-01", "completed_work": "已完成"}),
        ("sc.finance.expense.document", "borrowing_form", {"expense_category": "验收费用", "payee_id": partner.id if partner else False, "amount": 10, "repayment_due_date": "2026-05-01"}),
        ("sc.fund.operation", "fund_transfer_between", {"operation_reason": "验收调拨", "source_account": "A", "target_account": "B", "amount": 10}),
        ("sc.fund.operation", "fund_daily_report", {"operation_reason": "验收日报", "source_account": "现金账户", "target_account": "银行账户", "amount": 10}),
        ("sc.analysis.report.fact", "project_profit_statistics", {"report_period_start": "2026-05-01", "report_period_end": "2026-05-01", "metric_name": "利润"}),
    ]


def _create_valid_record(model, fact_type, vals):
    model_obj = env[model].sudo()
    return model_obj.with_context(default_fact_type=fact_type).create(dict({"name": "业务事实验收"}, **vals))


def _check_views(failures):
    results = []
    for model in FORMAL_MODELS:
        model_obj = env[model].sudo()
        specific = [name for name in model_obj._business_specific_fields() if name in model_obj._fields]
        form_view = env["ir.ui.view"].sudo().search([("name", "=", "%s.form" % model), ("model", "=", model)], limit=1)
        tree_view = env["ir.ui.view"].sudo().search([("name", "=", "%s.tree" % model), ("model", "=", model)], limit=1)
        search_view = env["ir.ui.view"].sudo().search([("name", "=", "%s.search" % model), ("model", "=", model)], limit=1)
        missing_form = [name for name in specific if ('name="%s"' % name) not in (form_view.arch_db or "")]
        if not form_view or not tree_view or not search_view or missing_form:
            failures.append(
                {
                    "check": "formal_view_specific_fields",
                    "model": model,
                    "form_view_id": form_view.id,
                    "tree_view_id": tree_view.id,
                    "search_view_id": search_view.id,
                    "missing_form": missing_form,
                }
            )
        results.append({"model": model, "specific_fields": specific, "form_view_id": form_view.id})
    return results


def _check_valid_flows(failures):
    created = []
    results = []
    for model, fact_type, vals in _valid_cases():
        if any(value is False for value in vals.values()):
            failures.append({"check": "fixture_missing", "model": model, "fact_type": fact_type, "vals": vals})
            continue
        rec = _create_valid_record(model, fact_type, vals)
        created.append(rec)
        initial_state = rec.state
        rec.action_submit()
        after_submit = rec.state
        rec.action_done()
        after_done = rec.state
        if not rec.document_no or rec.document_no.endswith("NEW"):
            failures.append({"check": "document_no", "model": model, "actual": rec.document_no})
        if (initial_state, after_submit, after_done) != ("draft", "in_progress", "done"):
            failures.append({"check": "state_flow", "model": model, "actual": [initial_state, after_submit, after_done]})
        results.append({"model": model, "fact_type": fact_type, "document_no": rec.document_no, "state": rec.state})
    return results, created


def _expect_blocked(model, fact_type, vals, action_name):
    rec = _create_valid_record(model, fact_type, vals)
    try:
        getattr(rec, action_name)()
    except ValidationError as exc:
        reason = str(exc)
        rec.unlink()
        return {"model": model, "fact_type": fact_type, "action": action_name, "blocked": True, "reason": reason}
    rec.unlink()
    return {"model": model, "fact_type": fact_type, "action": action_name, "blocked": False, "reason": ""}


def _check_blocking_rules(failures):
    blocked = [
        _expect_blocked("sc.material.document", "inbound", {"name": "缺目标库位阻断", "quantity": 1}, "action_submit"),
        _expect_blocked(
            "sc.fund.operation",
            "balance_adjustment",
            {"name": "余额未变化阻断", "operation_reason": "验收", "before_balance": 10, "after_balance": 10},
            "action_done",
        ),
    ]
    for item in blocked:
        if not item["blocked"]:
            failures.append({"check": "expected_rule_block", **item})
    return blocked


def main():
    failures = []
    created = []
    try:
        view_results = _check_views(failures)
        flow_results, flow_created = _check_valid_flows(failures)
        created.extend(flow_created)
        blocked_results = _check_blocking_rules(failures)
    finally:
        for rec in created:
            if rec.exists():
                rec.unlink()

    result = {
        "ok": not failures,
        "checked_models": len(FORMAL_MODELS),
        "views": view_results,
        "valid_flows": flow_results,
        "blocked_rules": blocked_results,
        "failures": failures,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
    return 0 if not failures else 1


raise SystemExit(main())
