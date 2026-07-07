# -*- coding: utf-8 -*-
import json
import sys
import traceback

from odoo import fields


def _token():
    return env["ir.sequence"].sudo().next_by_code("sc.business.fact") or str(fields.Datetime.now())  # noqa: F821


def _expect(condition, label, failures):
    if not condition:
        failures.append(label)
        return False
    return True


def _ensure_groups():
    user = env.user.sudo()  # noqa: F821
    for xmlid in (
        "smart_construction_core.group_sc_cap_business_initiator",
        "smart_construction_core.group_sc_cap_material_user",
        "smart_construction_core.group_sc_cap_material_manager",
    ):
        group = env.ref(xmlid, raise_if_not_found=False)  # noqa: F821
        if group and group.id not in user.groups_id.ids:
            user.write({"groups_id": [(4, group.id)]})
    env.invalidate_all()  # noqa: F821


def _project():
    return env["project.project"].sudo().create(  # noqa: F821
        {
            "name": "MDT Project %s" % _token(),
            "company_id": env.company.id,  # noqa: F821
            "manager_id": env.user.id,  # noqa: F821
        }
    )


def _supplier():
    return env["res.partner"].sudo().create(  # noqa: F821
        {
            "name": "MDT Supplier %s" % _token(),
            "supplier_rank": 1,
        }
    )


def _product():
    product = env["product.product"].sudo().search([("default_code", "=", "SC-SYSTEM-DEFAULT-MATERIAL")], limit=1)  # noqa: F821
    if product:
        return product
    return env["product.product"].sudo().create(  # noqa: F821
        {
            "name": "系统默认材料",
            "default_code": "SC-SYSTEM-DEFAULT-MATERIAL",
            "type": "product",
        }
    )


def _warehouse():
    warehouse = env["stock.warehouse"].sudo().search([("company_id", "in", [env.company.id, False])], limit=1)  # noqa: F821
    if warehouse:
        return warehouse
    return env["stock.warehouse"].sudo().create(  # noqa: F821
        {
            "name": "MDT Warehouse",
            "code": "MDT",
            "company_id": env.company.id,  # noqa: F821
        }
    )


def _material(project):
    token = _token()
    return env["sc.material.catalog"].sudo().create(  # noqa: F821
        {
            "name": "MDT Material %s" % token,
            "code": "MDT-%s" % token,
            "company_id": env.company.id,  # noqa: F821
            "project_id": project.id,
            "spec_model": "MDT-SPEC",
            "uom_text": "件",
        }
    )


def _line_vals(shared, qty, price=False):
    vals = {
        "product_id": shared["product"].id,
        "material_catalog_id": shared["material"].id,
        "product_uom_id": shared["product"].uom_id.id,
        "material_spec": "MDT-SPEC",
        "qty": qty,
    }
    if price is not False:
        vals["unit_price"] = price
    return vals


def _shared():
    project = _project()
    return {
        "project": project,
        "supplier": _supplier(),
        "product": _product(),
        "warehouse": _warehouse(),
        "material": _material(project),
    }


def _run_inbound(shared):
    inbound = env["sc.material.inbound"].sudo().create(  # noqa: F821
        {
            "project_id": shared["project"].id,
            "supplier_id": shared["supplier"].id,
            "warehouse_id": shared["warehouse"].id,
            "dest_location_id": shared["warehouse"].lot_stock_id.id,
            "line_ids": [(0, 0, _line_vals(shared, 5.0, price=12.0))],
        }
    )
    inbound.action_submit()
    inbound.action_receive()
    inbound.invalidate_recordset()
    return inbound


def _run_outbound(shared):
    outbound = env["sc.material.outbound"].sudo().create(  # noqa: F821
        {
            "project_id": shared["project"].id,
            "receiver_id": shared["supplier"].id,
            "warehouse_id": shared["warehouse"].id,
            "source_location_id": shared["warehouse"].lot_stock_id.id,
            "purpose": "MDT领用",
            "line_ids": [(0, 0, _line_vals(shared, 2.0, price=12.0))],
        }
    )
    outbound.action_submit()
    outbound.action_issue()
    outbound.invalidate_recordset()
    return outbound


def _run_settlement(shared):
    settlement = env["sc.material.settlement"].sudo().create(  # noqa: F821
        {
            "project_id": shared["project"].id,
            "supplier_id": shared["supplier"].id,
            "line_ids": [(0, 0, _line_vals(shared, 3.0, price=20.0))],
        }
    )
    settlement.action_submit()
    settlement.action_confirm()
    settlement.invalidate_recordset()
    return settlement


def _find_stock_summary(shared):
    return env["sc.material.stock.summary"].sudo().search(  # noqa: F821
        [
            ("project_id", "=", shared["project"].id),
            ("material_code", "=", shared["material"].code),
            ("material_name", "=", shared["material"].name),
            ("material_spec", "=", "MDT-SPEC"),
        ],
        limit=1,
    )


def _find_settlement_ledgers(settlement):
    return env["project.cost.ledger"].sudo().search(  # noqa: F821
        [
            ("source_model", "=", "sc.material.settlement"),
            ("source_id", "=", settlement.id),
        ]
    )


def _find_outbound_ledgers(outbound):
    return env["project.cost.ledger"].sudo().search(  # noqa: F821
        [
            ("source_model", "=", "sc.material.outbound"),
            ("source_id", "=", outbound.id),
        ]
    )


failures = []
evidence = {}

try:
    _ensure_groups()
    shared = _shared()
    inbound = _run_inbound(shared)
    outbound = _run_outbound(shared)
    settlement = _run_settlement(shared)
    env.flush_all()  # noqa: F821

    summary = _find_stock_summary(shared)
    _expect(bool(summary), "stock_summary: expected formal material summary row", failures)
    if summary:
        _expect(summary.in_qty >= 5.0, "stock_summary.in_qty: expected >= 5, got %s" % summary.in_qty, failures)
        _expect(summary.out_qty >= 2.0, "stock_summary.out_qty: expected >= 2, got %s" % summary.out_qty, failures)
        _expect(summary.stock_qty >= 3.0, "stock_summary.stock_qty: expected >= 3, got %s" % summary.stock_qty, failures)
        _expect(summary.in_amount >= 60.0, "stock_summary.in_amount: expected >= 60, got %s" % summary.in_amount, failures)
        _expect(
            "新办理" in (summary.coverage_note or ""),
            "stock_summary.coverage_note: expected formal handling coverage note",
            failures,
        )
    outbound_ledgers = _find_outbound_ledgers(outbound)
    outbound_ledger_amount = sum(outbound_ledgers.mapped("amount"))
    _expect(bool(outbound_ledgers), "outbound_cost_ledger: expected material outbound ledger rows", failures)
    _expect(
        outbound_ledger_amount >= 24.0,
        "outbound_cost_ledger.amount: expected >= 24, got %s" % outbound_ledger_amount,
        failures,
    )
    _expect(
        all(ledger.source_line_id in outbound.line_ids.ids for ledger in outbound_ledgers),
        "outbound_cost_ledger.source_line_id: expected outbound line traceability",
        failures,
    )
    ledgers = _find_settlement_ledgers(settlement)
    ledger_amount = sum(ledgers.mapped("amount"))
    _expect(bool(ledgers), "settlement_cost_ledger: expected material settlement ledger rows", failures)
    _expect(
        ledger_amount >= 60.0,
        "settlement_cost_ledger.amount: expected >= 60, got %s" % ledger_amount,
        failures,
    )
    payment_request = settlement.payment_request_id
    _expect(bool(payment_request), "settlement_payment_request: expected payment request", failures)
    if payment_request:
        _expect(
            payment_request.material_settlement_id == settlement,
            "settlement_payment_request.link: expected reverse link to settlement",
            failures,
        )
        _expect(payment_request.type == "pay", "settlement_payment_request.type: expected pay", failures)
        _expect(
            payment_request.project_id == shared["project"],
            "settlement_payment_request.project: expected settlement project",
            failures,
        )
        _expect(
            payment_request.partner_id == shared["supplier"],
            "settlement_payment_request.partner: expected settlement supplier",
            failures,
        )
        _expect(
            payment_request.amount >= 60.0,
            "settlement_payment_request.amount: expected >= 60, got %s" % payment_request.amount,
            failures,
        )
    evidence = {
        "project": shared["project"].id,
        "material": shared["material"].id,
        "inbound": inbound.id,
        "outbound": outbound.id,
        "settlement": settlement.id,
        "payment_request": payment_request.id if payment_request else False,
        "outbound_cost_ledger_count": len(outbound_ledgers),
        "outbound_cost_ledger_amount": outbound_ledger_amount,
        "cost_ledger_count": len(ledgers),
        "cost_ledger_amount": ledger_amount,
        "summary": summary.id if summary else False,
        "in_qty": summary.in_qty if summary else 0.0,
        "out_qty": summary.out_qty if summary else 0.0,
        "stock_qty": summary.stock_qty if summary else 0.0,
    }
except Exception as err:
    failures.append("unexpected error: %s" % err)
    failures.append(traceback.format_exc())

result = {
    "audit": "material_downstream_traceability_audit",
    "status": "PASS" if not failures else "FAIL",
    "evidence": evidence,
    "failures": failures,
}
print("MATERIAL_DOWNSTREAM_TRACEABILITY_AUDIT: %s" % json.dumps(result, ensure_ascii=False, sort_keys=True))
if failures:
    print("FAILURES:")
    for failure in failures:
        print("- %s" % failure)

sys.exit(0 if not failures else 1)
