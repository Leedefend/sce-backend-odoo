# -*- coding: utf-8 -*-
import json
import sys
import traceback

from odoo.exceptions import UserError, ValidationError


def _token():
    return env["ir.sequence"].sudo().next_by_code("sc.business.fact") or "NEW"


def _expect_state(label, record, expected, failures):
    record.invalidate_recordset()
    if record.state != expected:
        failures.append("%s: expected state=%s, got %s" % (label, expected, record.state))
        return False
    return True


def _expect_exception(label, func, failures):
    try:
        with env.cr.savepoint():
            func()
    except (UserError, ValidationError):
        return True
    except Exception as err:
        failures.append("%s: expected business exception, got %s: %s" % (label, type(err).__name__, err))
        return False
    failures.append("%s: expected business exception, got success" % label)
    return False


def _partner(name):
    return env["res.partner"].create({"name": "%s %s" % (name, _token())})


def _project(name):
    return env["project.project"].create(
        {
            "name": "%s %s" % (name, _token()),
            "manager_id": env.user.id,
            "company_id": env.company.id,
        }
    )


def _tax(tax_use):
    return env["account.tax"].sudo().create(
        {
            "name": "FOA Audit Tax %s %s" % (tax_use, _token()),
            "amount": 0.0,
            "amount_type": "percent",
            "type_tax_use": tax_use,
            "price_include": False,
            "company_id": env.company.id,
        }
    )


def _contract(project, partner):
    return env["construction.contract"].create(
        {
            "subject": "FOA Audit Contract %s" % _token(),
            "type": "in",
            "project_id": project.id,
            "partner_id": partner.id,
            "company_id": env.company.id,
            "currency_id": env.company.currency_id.id,
            "tax_id": _tax("purchase").id,
        }
    )


def _run_labor(failures):
    project = _project("FOA Labor Project")
    contractor = _partner("FOA Labor Contractor")
    usage = env["sc.labor.usage"].create(
        {
            "project_id": project.id,
            "contractor_id": contractor.id,
            "labor_team": "FOA Team",
            "work_content": "masonry",
            "worker_qty": 3.0,
            "work_hours": 8.0,
        }
    )
    _expect_exception("labor.usage_confirm_before_submit", usage.action_confirm, failures)
    usage.action_submit()
    _expect_state("labor.usage_submit", usage, "submitted", failures)
    usage.action_confirm()
    _expect_state("labor.usage_confirm", usage, "confirmed", failures)

    settlement = env["sc.labor.settlement"].create(
        {
            "project_id": project.id,
            "contractor_id": contractor.id,
            "line_ids": [
                (
                    0,
                    0,
                    {
                        "labor_team": "FOA Team",
                        "work_content": "masonry",
                        "qty": 3.0,
                        "unit_name": "工日",
                        "unit_price": 100.0,
                        "tax_rate": 3.0,
                    },
                )
            ],
        }
    )
    _expect_exception("labor.settlement_confirm_before_submit", settlement.action_confirm, failures)
    settlement.action_submit()
    _expect_state("labor.settlement_submit", settlement, "submitted", failures)
    settlement.action_confirm()
    _expect_state("labor.settlement_confirm", settlement, "confirmed", failures)
    return {"usage": usage.id, "settlement": settlement.id}


def _run_equipment(failures):
    project = _project("FOA Equipment Project")
    supplier = _partner("FOA Equipment Supplier")
    usage = env["sc.equipment.usage"].create(
        {
            "project_id": project.id,
            "supplier_id": supplier.id,
            "equipment_name": "Tower Crane",
            "usage_location": "Zone A",
            "operator_name": "Operator",
            "usage_qty": 1.0,
            "usage_hours": 8.0,
        }
    )
    _expect_exception("equipment.usage_confirm_before_submit", usage.action_confirm, failures)
    usage.action_submit()
    _expect_state("equipment.usage_submit", usage, "submitted", failures)
    usage.action_confirm()
    _expect_state("equipment.usage_confirm", usage, "confirmed", failures)

    settlement = env["sc.equipment.settlement"].create(
        {
            "project_id": project.id,
            "supplier_id": supplier.id,
            "line_ids": [
                (
                    0,
                    0,
                    {
                        "usage_id": usage.id,
                        "equipment_name": "Tower Crane",
                        "qty": 8.0,
                        "unit_price": 100.0,
                        "tax_rate": 3.0,
                    },
                )
            ],
        }
    )
    _expect_exception("equipment.settlement_confirm_before_submit", settlement.action_confirm, failures)
    settlement.action_submit()
    _expect_state("equipment.settlement_submit", settlement, "submitted", failures)
    settlement.action_confirm()
    _expect_state("equipment.settlement_confirm", settlement, "confirmed", failures)
    return {"usage": usage.id, "settlement": settlement.id}


def _run_subcontract(failures):
    project = _project("FOA Subcontract Project")
    subcontractor = _partner("FOA Subcontractor")
    contract = _contract(project, subcontractor)
    plan = env["sc.subcontract.plan"].create(
        {
            "project_id": project.id,
            "contract_id": contract.id,
            "subcontract_scope": "concrete structure",
            "subcontractor_id": subcontractor.id,
            "line_ids": [
                (
                    0,
                    0,
                    {
                        "work_scope": "concrete structure",
                        "planned_qty": 1.0,
                        "unit_name": "项",
                        "estimated_amount": 1000.0,
                    },
                )
            ],
        }
    )
    _expect_exception("subcontract.plan_approve_before_submit", plan.action_approve, failures)
    plan.action_submit()
    _expect_state("subcontract.plan_submit", plan, "submitted", failures)
    plan.action_approve()
    _expect_state("subcontract.plan_approve", plan, "approved", failures)

    request = env["sc.subcontract.request"].create(
        {
            "project_id": project.id,
            "plan_id": plan.id,
            "contract_id": contract.id,
            "subcontract_scope": "concrete structure",
            "suggested_subcontractor_id": subcontractor.id,
            "line_ids": [
                (
                    0,
                    0,
                    {
                        "work_scope": "concrete structure",
                        "required_qty": 1.0,
                        "unit_name": "项",
                        "estimated_amount": 1000.0,
                    },
                )
            ],
        }
    )
    request.action_submit()
    _expect_state("subcontract.request_submit", request, "submitted", failures)
    request.action_approve()
    _expect_state("subcontract.request_approve", request, "approved", failures)

    register = env["sc.subcontract.register"].create(
        {
            "project_id": project.id,
            "request_id": request.id,
            "contract_id": contract.id,
            "subcontract_scope": "concrete structure",
            "subcontractor_id": subcontractor.id,
            "line_ids": [
                (
                    0,
                    0,
                    {
                        "work_scope": "concrete structure",
                        "contract_qty": 1.0,
                        "unit_name": "项",
                        "registered_amount": 1000.0,
                    },
                )
            ],
        }
    )
    register.action_register()
    _expect_state("subcontract.register_active", register, "active", failures)

    settlement = env["sc.subcontract.settlement"].create(
        {
            "project_id": project.id,
            "register_id": register.id,
            "contract_id": contract.id,
            "subcontractor_id": subcontractor.id,
            "line_ids": [
                (
                    0,
                    0,
                    {
                        "work_scope": "concrete structure",
                        "qty": 1.0,
                        "unit_name": "项",
                        "unit_price": 1000.0,
                        "tax_rate": 3.0,
                    },
                )
            ],
        }
    )
    _expect_exception("subcontract.settlement_confirm_before_submit", settlement.action_confirm, failures)
    settlement.action_submit()
    _expect_state("subcontract.settlement_submit", settlement, "submitted", failures)
    settlement.action_confirm()
    _expect_state("subcontract.settlement_confirm", settlement, "confirmed", failures)
    return {"plan": plan.id, "request": request.id, "register": register.id, "settlement": settlement.id}


def _run_rental(failures):
    project = _project("FOA Rental Project")
    supplier = _partner("FOA Rental Supplier")
    contract = _contract(project, supplier)
    plan = env["sc.material.rental.plan"].create(
        {
            "project_id": project.id,
            "supplier_id": supplier.id,
            "contract_id": contract.id,
            "line_ids": [
                (
                    0,
                    0,
                    {
                        "material_name": "Steel Pipe",
                        "planned_qty": 10.0,
                        "planned_days": 5.0,
                        "daily_price": 2.0,
                    },
                )
            ],
        }
    )
    _expect_exception("rental.plan_approve_before_submit", plan.action_approve, failures)
    plan.action_submit()
    _expect_state("rental.plan_submit", plan, "submitted", failures)
    plan.action_approve()
    _expect_state("rental.plan_approve", plan, "approved", failures)

    order = env["sc.material.rental.order"].create(
        {
            "project_id": project.id,
            "plan_id": plan.id,
            "supplier_id": supplier.id,
            "contract_id": contract.id,
            "line_ids": [
                (
                    0,
                    0,
                    {
                        "material_name": "Steel Pipe",
                        "qty": 10.0,
                        "rental_days": 5.0,
                        "daily_price": 2.0,
                    },
                )
            ],
        }
    )
    order.action_activate()
    _expect_state("rental.order_active", order, "active", failures)
    order.action_return()
    _expect_state("rental.order_returned", order, "returned", failures)

    settlement = env["sc.material.rental.settlement"].create(
        {
            "project_id": project.id,
            "rental_order_id": order.id,
            "supplier_id": supplier.id,
            "contract_id": contract.id,
            "line_ids": [
                (
                    0,
                    0,
                    {
                        "material_name": "Steel Pipe",
                        "qty": 10.0,
                        "rental_days": 5.0,
                        "daily_price": 2.0,
                        "damage_amount": 8.0,
                    },
                )
            ],
        }
    )
    _expect_exception("rental.settlement_confirm_before_submit", settlement.action_confirm, failures)
    settlement.action_submit()
    _expect_state("rental.settlement_submit", settlement, "submitted", failures)
    settlement.action_confirm()
    _expect_state("rental.settlement_confirm", settlement, "confirmed", failures)
    settlement.action_paid()
    _expect_state("rental.settlement_paid", settlement, "paid", failures)
    return {"plan": plan.id, "order": order.id, "settlement": settlement.id}


def _run_quality_safety(failures):
    project = _project("FOA Quality Safety Project")
    quality = env["sc.quality.issue"].create(
        {
            "name": "FOA Quality Issue %s" % _token(),
            "project_id": project.id,
            "location": "A1",
            "description": "Concrete surface defect",
        }
    )
    quality.action_submit()
    _expect_state("quality.issue_submit", quality, "submitted", failures)
    env["sc.quality.rectification"].create({"issue_id": quality.id, "result": "Repaired"})
    _expect_state("quality.rectifying", quality, "rectifying", failures)
    quality.action_request_recheck()
    _expect_state("quality.rechecking", quality, "rechecking", failures)
    env["sc.quality.recheck"].create({"issue_id": quality.id, "result": "passed", "comment": "Accepted"})
    _expect_state("quality.closed", quality, "closed", failures)

    safety = env["sc.safety.issue"].create(
        {
            "name": "FOA Safety Issue %s" % _token(),
            "project_id": project.id,
            "location": "B2",
            "description": "Missing edge protection",
        }
    )
    safety.action_submit()
    _expect_state("safety.issue_submit", safety, "submitted", failures)
    env["sc.safety.rectification"].create({"issue_id": safety.id, "result": "Installed guardrail"})
    _expect_state("safety.rectifying", safety, "rectifying", failures)
    safety.action_request_recheck()
    _expect_state("safety.rechecking", safety, "rechecking", failures)
    env["sc.safety.recheck"].create({"issue_id": safety.id, "result": "passed", "comment": "Accepted"})
    _expect_state("safety.closed", safety, "closed", failures)

    plan = env["sc.safety.plan"].create(
        {
            "name": "FOA Safety Plan %s" % _token(),
            "project_id": project.id,
            "description": "Safety plan content",
        }
    )
    plan.action_submit()
    _expect_state("safety.plan_submit", plan, "submitted", failures)
    plan.action_approve()
    _expect_state("safety.plan_approve", plan, "approved", failures)
    disclosure = env["sc.safety.disclosure"].create(
        {
            "name": "FOA Safety Disclosure %s" % _token(),
            "project_id": project.id,
            "safety_plan_id": plan.id,
            "participant_note": "Foreman and crew",
            "content": "Edge protection and daily inspection",
        }
    )
    disclosure.action_submit()
    _expect_state("safety.disclosure_submit", disclosure, "submitted", failures)
    disclosure.action_approve()
    _expect_state("safety.disclosure_approve", disclosure, "approved", failures)
    return {"quality_issue": quality.id, "safety_issue": safety.id, "safety_plan": plan.id, "safety_disclosure": disclosure.id}


failures = []
coverage = {}

try:
    coverage["labor"] = _run_labor(failures)
    coverage["equipment"] = _run_equipment(failures)
    coverage["subcontract"] = _run_subcontract(failures)
    coverage["material_rental"] = _run_rental(failures)
    coverage["quality_safety"] = _run_quality_safety(failures)
except Exception as err:
    failures.append("unexpected error: %s" % err)
    failures.append(traceback.format_exc())

result = {
    "audit": "field_operation_action_audit",
    "status": "PASS" if not failures else "FAIL",
    "coverage": coverage,
    "failures": failures,
}
print("FIELD_OPERATION_ACTION_AUDIT: %s" % json.dumps(result, ensure_ascii=False, sort_keys=True))
if failures:
    print("FAILURES:")
    for failure in failures:
        print("- %s" % failure)

sys.exit(0 if not failures else 1)
