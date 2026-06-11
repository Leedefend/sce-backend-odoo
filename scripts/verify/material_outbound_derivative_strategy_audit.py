# -*- coding: utf-8 -*-
import json
import sys
import traceback

from odoo import fields


DERIVATIVES = [
    {
        "code": "material.return",
        "action_xmlid": "smart_construction_core.action_sc_material_return",
        "outbound_type": "return",
        "expect_cost_ledger": False,
    },
    {
        "code": "material.transfer",
        "action_xmlid": "smart_construction_core.action_sc_material_transfer",
        "outbound_type": "transfer",
        "expect_cost_ledger": False,
    },
    {
        "code": "material.loss",
        "action_xmlid": "smart_construction_core.action_sc_material_loss",
        "outbound_type": "loss",
        "expect_cost_ledger": True,
    },
]


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
        "smart_construction_core.group_sc_cap_material_user",
        "smart_construction_core.group_sc_cap_material_manager",
    ):
        group = env.ref(xmlid, raise_if_not_found=False)  # noqa: F821
        if group and group.id not in user.groups_id.ids:
            user.write({"groups_id": [(4, group.id)]})
    env.invalidate_all()  # noqa: F821


def _material_outbound_policy():
    policy = env.ref("smart_construction_core.approval_policy_material_outbound", raise_if_not_found=False)  # noqa: F821
    if not policy:
        policy = env["sc.approval.policy"].sudo().search([("target_model", "=", "sc.material.outbound")], limit=1)  # noqa: F821
    return policy.sudo()


def _project():
    return env["project.project"].sudo().create(  # noqa: F821
        {
            "name": "MODS Project %s" % _token(),
            "manager_id": env.user.id,  # noqa: F821
            "company_id": env.company.id,  # noqa: F821
        }
    )


def _supplier():
    return env["res.partner"].sudo().create(  # noqa: F821
        {
            "name": "MODS Partner %s" % _token(),
            "supplier_rank": 1,
        }
    )


def _warehouse():
    warehouse = env["stock.warehouse"].sudo().search([("company_id", "in", [env.company.id, False])], limit=1)  # noqa: F821
    if not warehouse:
        raise AssertionError("missing warehouse")
    return warehouse


def _product_and_catalog(project, outbound_type):
    uom = env.ref("uom.product_uom_unit", raise_if_not_found=False) or env["uom.uom"].sudo().search([], limit=1)  # noqa: F821
    token = _token()
    product = env["product.product"].sudo().create(  # noqa: F821
        {
            "name": "MODS %s Material %s" % (outbound_type, token),
            "default_code": "MODS-%s-%s" % (outbound_type, token),
            "type": "product",
            "uom_id": uom.id,
            "uom_po_id": uom.id,
        }
    )
    catalog = env["sc.material.catalog"].sudo().create(  # noqa: F821
        {
            "name": "MODS %s Catalog %s" % (outbound_type, token),
            "code": "MODS-CAT-%s-%s" % (outbound_type, token),
            "company_id": env.company.id,  # noqa: F821
            "project_id": project.id,
            "spec_model": "MODS-SPEC-%s" % outbound_type,
            "uom_text": "件",
        }
    )
    return product, catalog


def _parse_action_value(value):
    if not value:
        return {}
    if isinstance(value, dict):
        return value
    return eval(value, {"uid": env.uid})  # noqa: F821


def _run_derivative(item, failures):
    action = env.ref(item["action_xmlid"], raise_if_not_found=False)  # noqa: F821
    _expect(bool(action), "%s.action: expected bound action" % item["code"], failures)
    if not action:
        return {}
    context = _parse_action_value(action.context)
    project = _project()
    partner = _supplier()
    warehouse = _warehouse()
    location = warehouse.lot_stock_id
    product, catalog = _product_and_catalog(project, item["outbound_type"])
    vals = {
        "project_id": project.id,
        "outbound_type": context.get("default_outbound_type") or item["outbound_type"],
        "warehouse_id": warehouse.id,
        "source_location_id": location.id,
        "receiver_id": partner.id,
        "purpose": "MODS %s reason" % item["outbound_type"],
        "line_ids": [
            (
                0,
                0,
                {
                    "product_id": product.id,
                    "material_catalog_id": catalog.id,
                    "material_spec": catalog.spec_model,
                    "product_uom_id": product.uom_id.id,
                    "qty": 2.0,
                    "unit_price": 15.0,
                },
            )
        ],
    }
    if item["outbound_type"] == "transfer":
        vals.update({"dest_warehouse_id": warehouse.id, "dest_location_id": location.id})
    outbound = env["sc.material.outbound"].sudo().with_context(**context).create(vals)  # noqa: F821
    _expect(outbound.outbound_type == item["outbound_type"], "%s.outbound_type: expected action default" % item["code"], failures)
    domain = ["&", ("id", "=", outbound.id)] + list(eval(action.domain or "[]"))  # noqa: S307
    visible = env["sc.material.outbound"].sudo().search(domain, limit=1)  # noqa: F821
    _expect(visible.id == outbound.id, "%s.action_domain: expected created record visible" % item["code"], failures)
    outbound.action_submit()
    outbound.action_issue()
    outbound.invalidate_recordset()
    _expect(outbound.state == "issued", "%s.state: expected issued" % item["code"], failures)

    transfer_inbound = outbound.transfer_inbound_id if item["outbound_type"] == "transfer" else False
    if item["outbound_type"] == "transfer":
        _expect(bool(transfer_inbound), "%s.transfer_inbound: expected generated inbound" % item["code"], failures)
        if transfer_inbound:
            transfer_inbound.invalidate_recordset()
            _expect(transfer_inbound.state == "received", "%s.transfer_inbound.state: expected received" % item["code"], failures)
            _expect(
                transfer_inbound.source_transfer_outbound_id.id == outbound.id,
                "%s.transfer_inbound.source: expected source outbound" % item["code"],
                failures,
            )

    ledger_count = env["project.cost.ledger"].sudo().search_count(  # noqa: F821
        [("source_model", "=", "sc.material.outbound"), ("source_id", "=", outbound.id)]
    )
    if item["expect_cost_ledger"]:
        _expect(ledger_count >= 1, "%s.cost_ledger: expected cost ledger" % item["code"], failures)
    else:
        _expect(ledger_count == 0, "%s.cost_ledger: expected no cost ledger" % item["code"], failures)

    env.invalidate_all()  # noqa: F821
    summaries = env["sc.material.stock.summary"].sudo().search(  # noqa: F821
        [
            ("project_id", "=", project.id),
            ("material_code", "=", catalog.code),
            ("material_spec", "=", catalog.spec_model),
        ],
    )
    _expect(bool(summaries), "%s.stock_summary: expected summary row" % item["code"], failures)
    if summaries:
        in_qty = sum(summaries.mapped("in_qty"))
        out_qty = sum(summaries.mapped("out_qty"))
        stock_qty = sum(summaries.mapped("stock_qty"))
        _expect(out_qty == 2.0, "%s.stock_summary.out_qty: expected 2" % item["code"], failures)
        if item["outbound_type"] == "transfer":
            _expect(in_qty == 2.0, "%s.stock_summary.in_qty: expected 2" % item["code"], failures)
            _expect(stock_qty == 0.0, "%s.stock_summary.stock_qty: expected 0" % item["code"], failures)
        else:
            _expect(stock_qty == -2.0, "%s.stock_summary.stock_qty: expected -2" % item["code"], failures)

    return {
        "code": item["code"],
        "outbound": outbound.id,
        "transfer_inbound": transfer_inbound.id if transfer_inbound else False,
        "outbound_type": outbound.outbound_type,
        "ledger_count": ledger_count,
        "summaries": summaries.ids,
    }


failures = []
rows = []
policy = False
original_policy_values = {}

try:
    _ensure_groups()
    policy = _material_outbound_policy()
    if policy:
        original_policy_values = {
            "active": policy.active,
            "approval_required": policy.approval_required,
            "mode": policy.mode,
        }
        policy.write({"active": True, "approval_required": False, "mode": "none"})
    for item in DERIVATIVES:
        rows.append(_run_derivative(item, failures))
except Exception as err:
    failures.append("unexpected error: %s" % err)
    failures.append(traceback.format_exc())
finally:
    if policy and original_policy_values:
        try:
            policy.write(original_policy_values)
        except Exception as restore_err:
            failures.append("restore material outbound policy failed: %s" % restore_err)

result = {
    "audit": "material_outbound_derivative_strategy_audit",
    "status": "PASS" if not failures else "FAIL",
    "rows": rows,
    "failures": failures,
}
print("MATERIAL_OUTBOUND_DERIVATIVE_STRATEGY_AUDIT: %s" % json.dumps(result, ensure_ascii=False, sort_keys=True))
if failures:
    print("FAILURES:")
    for failure in failures:
        print("- %s" % failure)

sys.exit(0 if not failures else 1)
