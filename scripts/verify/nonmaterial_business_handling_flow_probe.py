# -*- coding: utf-8 -*-
"""Non-material business handling flow proof.

This probe creates representative non-material business records, executes the
normal submit/done lifecycle, then rolls the transaction back so the simulated
production database is not polluted by proof records.

Run with:
ENV=test ENV_FILE=.env.prod.sim DB_NAME=sc_prod_sim make odoo.shell.exec < scripts/verify/nonmaterial_business_handling_flow_probe.py
"""

import json


def _first(model, domain=None):
    return env[model].sudo().search(domain or [], limit=1)


def _fixture_ids():
    return {
        "project_id": _first("project.project").id,
        "partner_id": _first("res.partner").id,
        "department_id": _first("hr.department").id,
        "cost_code_id": _first("project.cost.code").id,
        "uom_id": _first("uom.uom").id,
    }


def _base_vals(label, fixtures):
    vals = {
        "name": "%s办理验收" % label,
        "business_date": "2026-05-02",
        "project_id": fixtures["project_id"],
        "partner_id": fixtures["partner_id"],
        "department_id": fixtures["department_id"],
        "handler_id": env.user.id,
        "description": "非材料业务办理闭环验收",
    }
    if fixtures["uom_id"]:
        vals["uom_id"] = fixtures["uom_id"]
    return vals


def _cases(fixtures):
    partner = fixtures["partner_id"]
    cost_code = fixtures["cost_code_id"]
    return [
        (
            "项目预算/人工预算",
            "sc.project.budget.fact",
            "labor_budget",
            {
                "cost_code_id": cost_code,
                "budget_basis": "人工预算验收依据",
                "original_budget_amount": 1000,
                "adjusted_budget_amount": 1200,
                "amount": 1200,
            },
        ),
        (
            "施工资料/归档备案",
            "sc.project.document.fact",
            "archive_document",
            {"document_category": "竣工资料", "document_version": "V1", "archive_no": "ARCH-PROOF-001", "owner_name": "验收责任人"},
        ),
        (
            "劳务管理/考勤记录",
            "sc.labor.document",
            "attendance_record",
            {
                "labor_team": "验收班组",
                "work_content": "现场作业",
                "worker_count": 3,
                "work_hours": 24,
                "attendance_date": "2026-05-02",
                "quantity": 3,
            },
        ),
        (
            "机械设备/设备使用登记",
            "sc.equipment.document",
            "equipment_usage",
            {
                "equipment_name": "验收设备",
                "equipment_code": "EQ-PROOF-001",
                "usage_location": "一标段",
                "usage_hours": 8,
                "operator_name": "验收操作员",
                "quantity": 1,
            },
        ),
        (
            "专业分包/分包登记",
            "sc.subcontract.document",
            "subcontract_register",
            {
                "subcontract_scope": "主体结构劳务",
                "subcontractor_id": partner,
                "start_date": "2026-05-02",
                "end_date": "2026-05-10",
            },
        ),
        (
            "施工管理/质量整改",
            "sc.construction.inspection",
            "quality_rectification",
            {
                "inspection_location": "二层梁板",
                "responsible_party_id": partner,
                "rectification_deadline": "2026-05-10",
                "rectification_result": "复查合格",
            },
        ),
        (
            "施工管理/日报表",
            "sc.construction.report",
            "daily_report",
            {
                "period_start": "2026-05-02",
                "period_end": "2026-05-02",
                "weather": "晴",
                "manpower_count": 12,
                "completed_work": "完成钢筋绑扎",
                "next_plan": "模板安装",
            },
        ),
        (
            "费用报销/借款单",
            "sc.finance.expense.document",
            "borrowing_form",
            {
                "expense_category": "项目周转借款",
                "payee_id": partner,
                "bank_account": "6222000000000000000",
                "amount": 3000,
                "repayment_due_date": "2026-06-02",
            },
        ),
        (
            "资金账户/资金调拨",
            "sc.fund.operation",
            "fund_transfer_between",
            {
                "operation_reason": "项目资金调拨",
                "source_account": "公司基本户",
                "target_account": "项目专户",
                "amount": 5000,
            },
        ),
    ]


def _missing_fixtures(fixtures):
    required = ("project_id", "partner_id")
    return [name for name in required if not fixtures.get(name)]


def main():
    fixtures = _fixture_ids()
    failures = []
    flows = []
    missing = _missing_fixtures(fixtures)
    if missing:
        result = {
            "ok": False,
            "database": env.cr.dbname,
            "reason": "fixture_missing",
            "missing": missing,
            "fixtures": fixtures,
        }
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
        return 1

    try:
        for label, model_name, fact_type, extra_vals in _cases(fixtures):
            vals = _base_vals(label, fixtures)
            vals.update({key: value for key, value in extra_vals.items() if value})
            rec = env[model_name].sudo().with_context(default_fact_type=fact_type, default_name=label).create(vals)
            initial_state = rec.state
            rec.action_submit()
            submit_state = rec.state
            rec.action_done()
            done_state = rec.state
            flow = {
                "label": label,
                "model": model_name,
                "fact_type": fact_type,
                "record_id": rec.id,
                "document_no": rec.document_no,
                "states": [initial_state, submit_state, done_state],
            }
            if flow["states"] != ["draft", "in_progress", "done"]:
                failures.append({"check": "state_flow", **flow})
            if not rec.document_no or rec.document_no.endswith("NEW"):
                failures.append({"check": "document_no", **flow})
            flows.append(flow)
    except Exception as exc:
        failures.append({"check": "exception", "error": "%s: %s" % (type(exc).__name__, str(exc))})
    finally:
        env.cr.rollback()

    result = {
        "ok": not failures,
        "database": env.cr.dbname,
        "rollback": True,
        "scope": "non_material_business_handling",
        "checked": len(flows),
        "flows": flows,
        "failures": failures,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if not failures else 1


raise SystemExit(main())
