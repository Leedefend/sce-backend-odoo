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
        "smart_construction_core.group_sc_cap_material_user",
        "smart_construction_core.group_sc_cap_material_manager",
    ):
        group = env.ref(xmlid, raise_if_not_found=False)  # noqa: F821
        if group and group.id not in user.groups_id.ids:
            user.write({"groups_id": [(4, group.id)]})
    env.invalidate_all()  # noqa: F821


def _set_validated(record):
    env.flush_all()  # noqa: F821
    env.cr.execute("UPDATE sc_material_outbound SET validation_status=%s WHERE id=%s", ("validated", record.id))  # noqa: F821
    env.invalidate_all()  # noqa: F821
    record.invalidate_recordset()
    if record.validation_status != "validated":
        record.sudo().with_context(skip_validation_check=True).write({"validation_status": "validated"})
        env.flush_all()  # noqa: F821
        env.invalidate_all()  # noqa: F821
        record.invalidate_recordset()


def _policy():
    policy = env.ref("smart_construction_core.approval_policy_material_outbound", raise_if_not_found=False)  # noqa: F821
    if not policy:
        policy = env["sc.approval.policy"].sudo().search([("target_model", "=", "sc.material.outbound")], limit=1)  # noqa: F821
    return policy.sudo()


def _project():
    return env["project.project"].sudo().create(  # noqa: F821
        {
            "name": "MLAP Project %s" % _token(),
            "manager_id": env.user.id,  # noqa: F821
            "company_id": env.company.id,  # noqa: F821
        }
    )


def _warehouse():
    warehouse = env["stock.warehouse"].sudo().search([("company_id", "in", [env.company.id, False])], limit=1)  # noqa: F821
    if not warehouse:
        raise AssertionError("missing warehouse")
    return warehouse


def _product_and_catalog(project, suffix):
    uom = env.ref("uom.product_uom_unit", raise_if_not_found=False) or env["uom.uom"].sudo().search([], limit=1)  # noqa: F821
    token = _token()
    product = env["product.product"].sudo().create(  # noqa: F821
        {
            "name": "MLAP %s Material %s" % (suffix, token),
            "default_code": "MLAP-%s-%s" % (suffix, token),
            "type": "product",
            "uom_id": uom.id,
            "uom_po_id": uom.id,
        }
    )
    catalog = env["sc.material.catalog"].sudo().create(  # noqa: F821
        {
            "name": "MLAP %s Catalog %s" % (suffix, token),
            "code": "MLAP-CAT-%s-%s" % (suffix, token),
            "company_id": env.company.id,  # noqa: F821
            "project_id": project.id,
            "spec_model": "MLAP-SPEC-%s" % suffix,
            "uom_text": "件",
        }
    )
    return product, catalog


def _create_loss_outbound(suffix):
    project = _project()
    warehouse = _warehouse()
    product, catalog = _product_and_catalog(project, suffix)
    outbound = env["sc.material.outbound"].sudo().create(  # noqa: F821
        {
            "project_id": project.id,
            "outbound_type": "loss",
            "warehouse_id": warehouse.id,
            "source_location_id": warehouse.lot_stock_id.id,
            "purpose": "MLAP损耗原因%s" % suffix,
            "line_ids": [
                (
                    0,
                    0,
                    {
                        "product_id": product.id,
                        "material_catalog_id": catalog.id,
                        "material_spec": catalog.spec_model,
                        "product_uom_id": product.uom_id.id,
                        "qty": 3.0,
                        "unit_price": 12.0,
                    },
                )
            ],
        }
    )
    outbound.action_submit()
    outbound.invalidate_recordset()
    return outbound


def _ledger_count(outbound):
    return env["project.cost.ledger"].sudo().search_count(  # noqa: F821
        [("source_model", "=", "sc.material.outbound"), ("source_id", "=", outbound.id)]
    )


failures = []
evidence = {}
policy = False
original_policy_values = {}

try:
    _ensure_groups()
    policy = _policy()
    _expect(bool(policy), "material_outbound_policy: expected policy", failures)
    if policy:
        original_policy_values = {
            "active": policy.active,
            "approval_required": policy.approval_required,
            "mode": policy.mode,
        }

        policy.write({"active": True, "approval_required": False, "mode": "none"})
        optional_loss = _create_loss_outbound("OPTIONAL")
        optional_loss.action_issue()
        optional_loss.invalidate_recordset()
        _expect(optional_loss.state == "issued", "optional_loss.state: expected issued", failures)
        _expect(_ledger_count(optional_loss) >= 1, "optional_loss.cost_ledger: expected ledger", failures)

        policy.write({"active": True, "approval_required": True, "mode": "single"})
        required_loss = _create_loss_outbound("REQUIRED")
        required_loss.action_issue()
        required_loss.invalidate_recordset()
        _expect(required_loss.state == "submitted", "required_loss.state: expected submitted before approval", failures)
        _expect(
            required_loss.validation_status in ("waiting", "pending", "no"),
            "required_loss.validation_status: expected approval requested",
            failures,
        )
        _expect(_ledger_count(required_loss) == 0, "required_loss.cost_ledger_before_approval: expected no ledger", failures)

        required_loss.action_issue()
        required_loss.invalidate_recordset()
        _expect(required_loss.state == "submitted", "required_loss.state_after_second_issue: expected still submitted", failures)
        _expect(_ledger_count(required_loss) == 0, "required_loss.cost_ledger_after_second_issue: expected no ledger", failures)
        _set_validated(required_loss)
        required_loss.action_on_tier_approved()
        required_loss.invalidate_recordset()
        _expect(required_loss.state == "issued", "required_loss.state: expected issued after approval", failures)
        _expect(_ledger_count(required_loss) >= 1, "required_loss.cost_ledger_after_approval: expected ledger", failures)

        evidence = {
            "policy": policy.id,
            "optional_loss": optional_loss.id,
            "required_loss": required_loss.id,
            "required_loss_validation_status": required_loss.validation_status,
            "required_loss_ledger_count": _ledger_count(required_loss),
        }
except Exception as err:
    failures.append("unexpected error: %s" % err)
    failures.append(traceback.format_exc())
finally:
    if policy and original_policy_values:
        try:
            policy.write(original_policy_values)
        except Exception as restore_err:
            failures.append("restore policy failed: %s" % restore_err)

result = {
    "audit": "material_loss_approval_policy_audit",
    "status": "PASS" if not failures else "FAIL",
    "evidence": evidence,
    "failures": failures,
}
print("MATERIAL_LOSS_APPROVAL_POLICY_AUDIT: %s" % json.dumps(result, ensure_ascii=False, sort_keys=True))
if failures:
    print("FAILURES:")
    for failure in failures:
        print("- %s" % failure)

sys.exit(0 if not failures else 1)
