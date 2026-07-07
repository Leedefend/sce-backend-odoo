# -*- coding: utf-8 -*-
import json
import sys
import traceback

from odoo import fields
from odoo.tools.safe_eval import safe_eval


CATEGORIES = [
    ("material.plan", "smart_construction_core.action_project_material_plan_my"),
    ("material.purchase.request", "smart_construction_core.action_sc_material_purchase_request"),
    ("material.acceptance", "smart_construction_core.action_sc_material_acceptance"),
    ("material.rfq", "smart_construction_core.action_sc_material_rfq"),
    ("material.inbound", "smart_construction_core.action_sc_material_inbound_handling"),
    ("material.outbound", "smart_construction_core.action_sc_material_outbound"),
    ("material.return", "smart_construction_core.action_sc_material_return"),
    ("material.transfer", "smart_construction_core.action_sc_material_transfer"),
    ("material.loss", "smart_construction_core.action_sc_material_loss"),
    ("material.settlement", "smart_construction_core.action_sc_material_settlement"),
]


def _token():
    return env["ir.sequence"].sudo().next_by_code("sc.business.fact") or str(fields.Datetime.now())  # noqa: F821


def _parse(value, default):
    if not value:
        return default
    if isinstance(value, (dict, list, tuple)):
        return value
    return safe_eval(value, {"uid": env.uid})  # noqa: F821


def _project():
    return env["project.project"].sudo().create(  # noqa: F821
        {
            "name": "MBCR Project %s" % _token(),
            "company_id": env.company.id,  # noqa: F821
            "manager_id": env.user.id,  # noqa: F821
        }
    )


def _supplier():
    return env["res.partner"].sudo().create(  # noqa: F821
        {
            "name": "MBCR Supplier %s" % _token(),
            "supplier_rank": 1,
        }
    )


def _material_catalog(project):
    return env["sc.material.catalog"].sudo().create(  # noqa: F821
        {
            "name": "MBCR Material %s" % _token(),
            "code": "MBCR-%s" % _token(),
            "company_id": env.company.id,  # noqa: F821
            "project_id": project.id,
            "spec_model": "MBCR-SPEC",
            "uom_text": "件",
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
    return env["stock.warehouse"].sudo().search([("company_id", "in", [env.company.id, False])], limit=1)  # noqa: F821


def _context_defaults(model_name, context):
    model_fields = env[model_name]._fields  # noqa: F821
    return {
        key[len("default_") :]: value
        for key, value in (context or {}).items()
        if isinstance(key, str) and key.startswith("default_")
        and key[len("default_") :] in model_fields
    }


def _line_vals(shared, qty_field="qty", price_field=None):
    product = shared["product"]
    vals = {
        "material_catalog_id": shared["material"].id,
        "product_id": product.id,
        "product_uom_id": product.uom_id.id,
        "material_spec": "MBCR-SPEC",
        qty_field: 2.0,
    }
    if price_field:
        vals[price_field] = 10.0
    return vals


def _base_vals(model_name, context, shared):
    vals = _context_defaults(model_name, context)
    project = shared["project"]
    supplier = shared["supplier"]
    warehouse = shared["warehouse"]
    location = warehouse.lot_stock_id
    product = shared["product"]

    if model_name == "project.material.plan":
        vals.update(
            {
                "project_id": project.id,
                "date_plan": fields.Date.context_today(env["project.material.plan"]),  # noqa: F821
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "material_catalog_id": shared["material"].id,
                            "product_id": product.id,
                            "quantity": 2.0,
                            "bill_qty": 2.0,
                            "uom_id": product.uom_id.id,
                            "material_uom_text": "件",
                            "vendor_id": supplier.id,
                        },
                    )
                ],
            }
        )
    elif model_name == "sc.material.purchase.request":
        vals.update(
            {
                "project_id": project.id,
                "request_date": fields.Date.context_today(env[model_name]),  # noqa: F821
                "purpose": "MBCR采购申请",
                "line_ids": [(0, 0, _line_vals(shared, qty_field="qty", price_field="estimated_unit_price"))],
            }
        )
    elif model_name == "sc.material.acceptance":
        vals.update(
            {
                "project_id": project.id,
                "supplier_id": supplier.id,
                "warehouse_id": warehouse.id,
                "dest_location_id": location.id,
                "line_ids": [
                    (
                        0,
                        0,
                        dict(
                            _line_vals(shared, qty_field="accepted_qty"),
                            planned_qty=2.0,
                            received_qty=2.0,
                        ),
                    )
                ],
            }
        )
    elif model_name == "sc.material.rfq":
        vals.update(
            {
                "project_id": project.id,
                "rfq_date": fields.Date.context_today(env[model_name]),  # noqa: F821
                "line_ids": [
                    (
                        0,
                        0,
                        dict(
                            _line_vals(shared, qty_field="qty", price_field="unit_price"),
                            supplier_id=supplier.id,
                            selected=True,
                        ),
                    )
                ],
            }
        )
    elif model_name == "sc.material.inbound":
        vals.update(
            {
                "project_id": project.id,
                "supplier_id": supplier.id,
                "warehouse_id": warehouse.id,
                "dest_location_id": location.id,
                "line_ids": [(0, 0, _line_vals(shared, qty_field="qty", price_field="unit_price"))],
            }
        )
    elif model_name == "sc.material.outbound":
        vals.update(
            {
                "project_id": project.id,
                "receiver_id": supplier.id,
                "warehouse_id": warehouse.id,
                "source_location_id": location.id,
                "dest_warehouse_id": warehouse.id if vals.get("outbound_type") == "transfer" else False,
                "dest_location_id": location.id if vals.get("outbound_type") == "transfer" else False,
                "purpose": "MBCR损耗原因" if vals.get("outbound_type") == "loss" else "MBCR材料出库",
                "line_ids": [(0, 0, _line_vals(shared, qty_field="qty"))],
            }
        )
    elif model_name == "sc.material.settlement":
        vals.update(
            {
                "project_id": project.id,
                "supplier_id": supplier.id,
                "settlement_date": fields.Date.context_today(env[model_name]),  # noqa: F821
                "line_ids": [(0, 0, _line_vals(shared, qty_field="qty", price_field="unit_price"))],
            }
        )
    else:
        raise AssertionError("unsupported material category model: %s" % model_name)
    return vals


def _shared_records():
    project = _project()
    return {
        "project": project,
        "supplier": _supplier(),
        "material": _material_catalog(project),
        "product": _product(),
        "warehouse": _warehouse(),
    }


def _run_category(code, action_xmlid, shared, failures):
    action = env.ref(action_xmlid, raise_if_not_found=False)  # noqa: F821
    if not action:
        failures.append("%s: missing action %s" % (code, action_xmlid))
        return {}
    context = _parse(action.context, {})
    domain = _parse(action.domain, [])
    model_name = action.res_model
    vals = _base_vals(model_name, context, shared)
    record = env[model_name].sudo().with_context(**context).create(vals)  # noqa: F821
    domain_with_record = ["&", ("id", "=", record.id)] + list(domain) if domain else [("id", "=", record.id)]
    matched = env[model_name].sudo().search(domain_with_record, limit=1)  # noqa: F821
    if matched.id != record.id:
        failures.append(
            "%s: created %s/%s is not visible through action domain %s"
            % (code, model_name, record.id, action.domain)
        )
    return {
        "code": code,
        "action": action_xmlid,
        "model": model_name,
        "record_id": record.id,
        "visible": matched.id == record.id,
    }


failures = []
rows = []

try:
    shared = _shared_records()
    for code, action_xmlid in CATEGORIES:
        with env.cr.savepoint():  # noqa: F821
            rows.append(_run_category(code, action_xmlid, shared, failures))
except Exception as err:
    failures.append("unexpected error: %s" % err)
    failures.append(traceback.format_exc())

result = {
    "audit": "material_business_category_runtime_audit",
    "status": "PASS" if not failures else "FAIL",
    "category_count": len(CATEGORIES),
    "rows": rows,
    "failures": failures,
}
print("MATERIAL_BUSINESS_CATEGORY_RUNTIME_AUDIT: %s" % json.dumps(result, ensure_ascii=False, sort_keys=True))
if failures:
    print("FAILURES:")
    for failure in failures:
        print("- %s" % failure)

sys.exit(0 if not failures else 1)
