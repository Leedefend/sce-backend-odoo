# -*- coding: utf-8 -*-
"""Rollback-only smoke for document_state approval policy switches.

The expected business semantics:
- approval enabled: submit/confirm enters an approval path or requires the
  configured approver capability group.
- approval disabled: submit/confirm proceeds without approver restriction.
"""

def _env():
    return globals()["env"]


def _policy(model_name):
    policy = _env()["sc.approval.policy"].sudo().search([("target_model", "=", model_name)], limit=1)
    if not policy:
        raise AssertionError("missing approval policy for %s" % model_name)
    return policy


def _set_policy(model_name, enabled):
    policy = _policy(model_name)
    values = {
        "active": True,
        "approval_required": bool(enabled),
        "mode": "single" if enabled else "none",
        "runtime_state": "tier_validation",
    }
    policy.write(values)
    policy.sync_tier_definitions()
    return policy


def _project(name):
    return _env()["project.project"].sudo().create({"name": name, "code": name.upper().replace(" ", "-")[:32]})


def _partner(name):
    return _env()["res.partner"].sudo().create({"name": name})


def _expense(project):
    return _env()["sc.expense.claim"].sudo().create(
        {
            "project_id": project.id,
            "amount": 100.0,
            "summary": "Document state policy switch smoke",
        }
    )


def _settlement(project, partner):
    contract = _env()["construction.contract"].sudo().create(
        {
            "subject": "Policy Switch Settlement Contract",
            "type": "in",
            "project_id": project.id,
            "partner_id": partner.id,
        }
    )
    return _env()["sc.settlement.order"].sudo().create(
        {
            "project_id": project.id,
            "partner_id": partner.id,
            "contract_id": contract.id,
            "line_ids": [
                (
                    0,
                    0,
                    {
                        "name": "Policy switch line",
                        "contract_id": contract.id,
                        "qty": 1.0,
                        "price_unit": 100.0,
                    },
                )
            ],
        }
    )


def _product():
    uom = _env().ref("uom.product_uom_unit")
    return _env()["product.product"].sudo().create(
        {
            "name": "Policy Switch Product",
            "type": "product",
            "uom_id": uom.id,
            "uom_po_id": uom.id,
        }
    )


def _purchase_order(project, partner, product):
    return _env()["purchase.order"].sudo().create(
        {
            "partner_id": partner.id,
            "project_id": project.id,
            "order_line": [
                (
                    0,
                    0,
                    {
                        "name": "Policy Switch Item",
                        "product_id": product.id,
                        "product_qty": 1.0,
                        "product_uom": product.uom_po_id.id,
                        "price_unit": 100.0,
                    },
                )
            ],
        }
    )


def _construction_contract(project, partner):
    contract = _env()["construction.contract"].sudo().create(
        {
            "subject": "Policy Switch Construction Contract",
            "type": "in",
            "project_id": project.id,
            "partner_id": partner.id,
        }
    )
    _env()["construction.contract.line"].sudo().create(
        {
            "contract_id": contract.id,
            "qty_contract": 1.0,
            "price_contract": 100.0,
        }
    )
    return contract


def _general_contract(project, _partner):
    return _env()["sc.general.contract"].sudo().create(
        {
            "project_id": project.id,
            "contract_name": "Policy Switch General Contract",
            "amount_total": 100.0,
        }
    )


def _legacy_purchase_contract(project, _partner):
    return _env()["sc.legacy.purchase.contract.fact"].sudo().create(
        {
            "project_id": project.id,
            "contract_name": "Policy Switch Legacy Purchase Contract",
            "total_amount": 100.0,
        }
    )


def _create_purchase_user():
    group = _env().ref("smart_construction_core.group_sc_cap_purchase_user")
    return _env()["res.users"].with_context(no_reset_password=True).sudo().create(
        {
            "name": "Policy Switch Purchase User",
            "login": "policy_switch_purchase_user",
            "email": "policy_switch_purchase_user@example.invalid",
            "groups_id": [(6, 0, [_env().ref("base.group_user").id, group.id])],
        }
    )


def _check_submit_switch(model_name, factory, approved_state):
    project = _project("Policy Switch %s" % model_name.replace(".", " "))
    partner = _partner("Policy Switch Partner %s" % model_name)

    _set_policy(model_name, True)
    record = factory(project, partner)
    record.action_submit()
    record.invalidate_recordset()
    print("%s_ENABLED_SUBMIT_STATE=%s" % (model_name, record.state))
    assert record.state == "submit", record.state

    _set_policy(model_name, False)
    record = factory(project, partner)
    record.action_submit()
    record.invalidate_recordset()
    print("%s_DISABLED_SUBMIT_STATE=%s" % (model_name, record.state))
    assert record.state == approved_state, record.state


def _check_purchase_confirm_switch():
    env = _env()
    project = _project("Policy Switch Purchase")
    partner = _partner("Policy Switch Purchase Partner")
    product = _product()
    user = _create_purchase_user()

    _set_policy("purchase.order", True)
    order = _purchase_order(project, partner, product)
    order.with_user(user).button_confirm()
    order.invalidate_recordset()
    reviews = env["tier.review"].sudo().search(
        [("model", "=", "purchase.order"), ("res_id", "=", order.id)]
    )
    print("purchase.order_ENABLED_SUBMIT_STATE=%s/%s/reviews=%s" % (order.state, order.validation_status, len(reviews)))
    assert order.state in ("draft", "sent"), order.state
    assert order.validation_status in ("pending", "waiting"), order.validation_status
    assert len(reviews) == 1, len(reviews)

    _set_policy("purchase.order", False)
    order = _purchase_order(project, partner, product)
    order.with_user(user).button_confirm()
    order.invalidate_recordset()
    print("purchase.order_DISABLED_NON_APPROVER_STATE=%s" % order.state)
    assert order.state in ("purchase", "done"), order.state


def _check_confirm_switch(model_name, factory, confirmed_state):
    env = _env()
    project = _project("Policy Switch %s" % model_name.replace(".", " "))
    partner = _partner("Policy Switch Partner %s" % model_name)

    _set_policy(model_name, True)
    record = factory(project, partner)
    record.action_confirm()
    record.invalidate_recordset()
    reviews = env["tier.review"].sudo().search(
        [("model", "=", model_name), ("res_id", "=", record.id)]
    )
    print("%s_ENABLED_CONFIRM_STATE=%s/%s/reviews=%s" % (model_name, record.state, record.validation_status, len(reviews)))
    assert record.state == "draft", record.state
    assert record.validation_status in ("pending", "waiting"), record.validation_status
    assert len(reviews) == 1, len(reviews)

    _set_policy(model_name, False)
    record = factory(project, partner)
    record.action_confirm()
    record.invalidate_recordset()
    print("%s_DISABLED_CONFIRM_STATE=%s" % (model_name, record.state))
    assert record.state == confirmed_state, record.state


def main():
    try:
        _check_submit_switch(
            "sc.expense.claim",
            lambda project, _partner: _expense(project),
            approved_state="approved",
        )
        _check_submit_switch(
            "sc.settlement.order",
            lambda project, partner: _settlement(project, partner),
            approved_state="approve",
        )
        _check_purchase_confirm_switch()
        _check_confirm_switch(
            "construction.contract",
            _construction_contract,
            confirmed_state="confirmed",
        )
        _check_confirm_switch(
            "sc.general.contract",
            _general_contract,
            confirmed_state="confirmed",
        )
        _check_submit_switch(
            "sc.legacy.purchase.contract.fact",
            _legacy_purchase_contract,
            approved_state="approved",
        )
        print("BUSINESS_DOCUMENT_STATE_POLICY_SWITCH_SMOKE=PASS")
    finally:
        _env().cr.rollback()
        print("BUSINESS_DOCUMENT_STATE_POLICY_SWITCH_ROLLBACK=OK")


main()
