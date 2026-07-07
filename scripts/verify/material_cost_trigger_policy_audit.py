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
        "smart_construction_core.group_sc_cap_business_config_admin",
    ):
        group = env.ref(xmlid, raise_if_not_found=False)  # noqa: F821
        if group and group.id not in user.groups_id.ids:
            user.write({"groups_id": [(4, group.id)]})
    env.invalidate_all()  # noqa: F821


def _category(code):
    return env["sc.business.category"].sudo().search([("code", "=", code)], limit=1)  # noqa: F821


def _policy(category):
    try:
        value = json.loads(category.ledger_policy_json or "{}")
    except (TypeError, ValueError):
        value = {}
    return value if isinstance(value, dict) else {}


def _set_triggers(category, **triggers):
    policy = _policy(category)
    cost_triggers = policy.get("cost_triggers")
    if not isinstance(cost_triggers, dict):
        cost_triggers = {}
        policy["cost_triggers"] = cost_triggers
    cost_triggers.update(triggers)
    category.write({"ledger_policy_json": json.dumps(policy, ensure_ascii=False, sort_keys=True)})


def _project():
    return env["project.project"].sudo().create(  # noqa: F821
        {
            "name": "MCTP Project %s" % _token(),
            "company_id": env.company.id,  # noqa: F821
            "manager_id": env.user.id,  # noqa: F821
        }
    )


def _partner():
    return env["res.partner"].sudo().create(  # noqa: F821
        {
            "name": "MCTP Partner %s" % _token(),
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
            "name": "MCTP Warehouse",
            "code": "MCTP",
            "company_id": env.company.id,  # noqa: F821
        }
    )


def _material(project):
    token = _token()
    return env["sc.material.catalog"].sudo().create(  # noqa: F821
        {
            "name": "MCTP Material %s" % token,
            "code": "MCTP-%s" % token,
            "company_id": env.company.id,  # noqa: F821
            "project_id": project.id,
            "spec_model": "MCTP-SPEC",
            "uom_text": "件",
        }
    )


def _shared():
    project = _project()
    return {
        "project": project,
        "partner": _partner(),
        "product": _product(),
        "warehouse": _warehouse(),
        "material": _material(project),
    }


def _line_vals(shared, qty, price):
    return {
        "product_id": shared["product"].id,
        "material_catalog_id": shared["material"].id,
        "product_uom_id": shared["product"].uom_id.id,
        "material_spec": "MCTP-SPEC",
        "qty": qty,
        "unit_price": price,
    }


def _run_outbound(shared):
    outbound = env["sc.material.outbound"].sudo().create(  # noqa: F821
        {
            "project_id": shared["project"].id,
            "receiver_id": shared["partner"].id,
            "warehouse_id": shared["warehouse"].id,
            "source_location_id": shared["warehouse"].lot_stock_id.id,
            "purpose": "MCTP领用",
            "line_ids": [(0, 0, _line_vals(shared, 2.0, 13.0))],
        }
    )
    outbound.action_submit()
    outbound.action_issue()
    return outbound


def _run_settlement(shared):
    settlement = env["sc.material.settlement"].sudo().create(  # noqa: F821
        {
            "project_id": shared["project"].id,
            "supplier_id": shared["partner"].id,
            "line_ids": [(0, 0, _line_vals(shared, 3.0, 17.0))],
        }
    )
    settlement.action_submit()
    settlement.action_confirm()
    return settlement


def _ledgers(model, record_id):
    return env["project.cost.ledger"].sudo().search(  # noqa: F821
        [
            ("source_model", "=", model),
            ("source_id", "=", record_id),
        ]
    )


failures = []
evidence = {}
original_policies = {}

try:
    _ensure_groups()
    outbound_category = _category("material.outbound")
    settlement_category = _category("material.settlement")
    _expect(bool(outbound_category), "material.outbound category missing", failures)
    _expect(bool(settlement_category), "material.settlement category missing", failures)
    if failures:
        raise RuntimeError("required categories missing")
    original_policies[outbound_category.code] = outbound_category.ledger_policy_json
    original_policies[settlement_category.code] = settlement_category.ledger_policy_json

    _set_triggers(outbound_category, issue_project_cost_ledger=False)
    disabled_outbound = _run_outbound(_shared())
    disabled_outbound_ledgers = _ledgers("sc.material.outbound", disabled_outbound.id)
    _expect(
        not disabled_outbound_ledgers,
        "outbound disabled policy: expected no cost ledger",
        failures,
    )

    _set_triggers(outbound_category, issue_project_cost_ledger=True)
    enabled_outbound = _run_outbound(_shared())
    enabled_outbound_ledgers = _ledgers("sc.material.outbound", enabled_outbound.id)
    _expect(
        sum(enabled_outbound_ledgers.mapped("amount")) >= 26.0,
        "outbound enabled policy: expected cost ledger amount >= 26",
        failures,
    )

    _set_triggers(settlement_category, confirm_project_cost_ledger=False, confirm_payment_request=False)
    disabled_settlement = _run_settlement(_shared())
    disabled_settlement_ledgers = _ledgers("sc.material.settlement", disabled_settlement.id)
    _expect(
        not disabled_settlement_ledgers,
        "settlement disabled policy: expected no cost ledger",
        failures,
    )
    _expect(
        not disabled_settlement.payment_request_id,
        "settlement disabled policy: expected no payment request",
        failures,
    )

    _set_triggers(settlement_category, confirm_project_cost_ledger=True, confirm_payment_request=True)
    enabled_settlement = _run_settlement(_shared())
    enabled_settlement_ledgers = _ledgers("sc.material.settlement", enabled_settlement.id)
    _expect(
        sum(enabled_settlement_ledgers.mapped("amount")) >= 51.0,
        "settlement enabled policy: expected cost ledger amount >= 51",
        failures,
    )
    _expect(
        bool(enabled_settlement.payment_request_id),
        "settlement enabled policy: expected payment request",
        failures,
    )

    evidence = {
        "disabled_outbound": disabled_outbound.id,
        "disabled_outbound_cost_ledger_count": len(disabled_outbound_ledgers),
        "enabled_outbound": enabled_outbound.id,
        "enabled_outbound_cost_ledger_amount": sum(enabled_outbound_ledgers.mapped("amount")),
        "disabled_settlement": disabled_settlement.id,
        "disabled_settlement_cost_ledger_count": len(disabled_settlement_ledgers),
        "disabled_settlement_payment_request": disabled_settlement.payment_request_id.id,
        "enabled_settlement": enabled_settlement.id,
        "enabled_settlement_cost_ledger_amount": sum(enabled_settlement_ledgers.mapped("amount")),
        "enabled_settlement_payment_request": enabled_settlement.payment_request_id.id,
    }
except Exception as err:
    failures.append("unexpected error: %s" % err)
    failures.append(traceback.format_exc())
finally:
    for code, raw_policy in original_policies.items():
        category = _category(code)
        if category:
            category.write({"ledger_policy_json": raw_policy or "{}"})

result = {
    "audit": "material_cost_trigger_policy_audit",
    "status": "PASS" if not failures else "FAIL",
    "evidence": evidence,
    "failures": failures,
}
print("MATERIAL_COST_TRIGGER_POLICY_AUDIT: %s" % json.dumps(result, ensure_ascii=False, sort_keys=True))
if failures:
    print("FAILURES:")
    for failure in failures:
        print("- %s" % failure)

sys.exit(0 if not failures else 1)
