# -*- coding: utf-8 -*-
import base64
import re
import sys
import traceback

from odoo import fields
from odoo.exceptions import UserError, ValidationError


def _guard_code(err):
    message = str(err)
    match = re.search(r"\[SC_GUARD:([A-Z0-9_]+)\]", message)
    return match.group(1) if match else None


def _expect_guard(label, code, func, failures):
    try:
        func()
    except Exception as err:
        actual = _guard_code(err)
        if actual != code:
            failures.append(f"{label}: expected {code}, got {actual or type(err).__name__}")
            return False
        return True
    failures.append(f"{label}: expected guard {code}, got success")
    return False


def _expect_state(label, record, state, failures):
    if record.state != state:
        failures.append(f"{label}: expected state={state}, got {record.state}")
        return False
    return True


def _audit_events(env, model, res_id):
    Audit = env["sc.audit.log"].sudo()
    events = Audit.search(
        [("model", "=", model), ("res_id", "=", res_id)],
        order="id asc",
    ).mapped("event_code")
    return sorted({e for e in events if e})


def _ensure_events(label, actual, expected, failures):
    missing = [e for e in expected if e not in actual]
    if missing:
        failures.append(f"{label}: missing audit events {missing}")
        return False
    return True


failures = []
audit_summary = {}

try:
    company = env.company

    user = env.user.sudo()
    for xmlid in (
        "smart_construction_core.group_sc_cap_project_manager",
        "smart_construction_core.group_sc_cap_finance_user",
        "smart_construction_core.group_sc_cap_finance_manager",
    ):
        group = env.ref(xmlid, raise_if_not_found=False)
        if group and group.id not in user.groups_id.ids:
            user.write({"groups_id": [(4, group.id)]})

    partner = env["res.partner"].create({"name": "P2 Smoke Partner"})

    project = env["project.project"].create(
        {
            "name": "P2 Smoke Project",
            "code": "P2-SMOKE",
            "funding_enabled": True,
            "company_id": company.id,
        }
    )

    project_b = env["project.project"].create(
        {
            "name": "P2 Smoke Project B",
            "code": "P2-SMOKE-B",
            "company_id": company.id,
        }
    )

    wbs = env["construction.work.breakdown"].create(
        {
            "name": "P2 Smoke WBS",
            "project_id": project.id,
            "level_type": "sub_section",
        }
    )

    # Funding baseline for payment gate.
    env["project.funding.baseline"].create(
        {
            "project_id": project.id,
            "total_amount": 1000.0,
            "state": "active",
        }
    )

    # -------------------- Task --------------------
    task = env["project.task"].create(
        {
            "name": "P2 Smoke Task",
            "project_id": project.id,
            "work_id": wbs.id,
        }
    )
    _expect_guard(
        "TASK direct state write",
        "TASK_GUARD_DIRECT_STATE_WRITE",
        lambda: task.write({"state": "ready"}),
        failures,
    )
    task.action_prepare_task()
    _expect_state("TASK prepare", task, "ready", failures)
    task.action_start_task()
    _expect_state("TASK start", task, "in_progress", failures)
    if "progress_rate" in task._fields:
        task.write({"progress_rate": 1.0})
    if "progress" in task._fields:
        task.write({"progress": 1.0})
    task.action_mark_done()
    _expect_state("TASK done", task, "done", failures)
    task.action_cancel_task(reason="smoke cancel")
    _expect_state("TASK cancel", task, "cancelled", failures)

    task_events = _audit_events(env, "project.task", task.id)
    audit_summary["task"] = task_events
    _ensure_events(
        "TASK audit",
        task_events,
        ["task_ready", "task_started", "task_done", "task_cancelled"],
        failures,
    )

    # -------------------- Progress --------------------
    progress = env["project.progress.entry"].create(
        {
            "project_id": project.id,
            "wbs_id": wbs.id,
            "qty_done": 1.0,
            "qty_cum": 1.0,
            "progress_rate": 1.0,
        }
    )
    _expect_guard(
        "PROGRESS direct state write",
        "PROGRESS_GUARD_DIRECT_STATE_WRITE",
        lambda: progress.write({"state": "submitted"}),
        failures,
    )
    progress.action_submit_progress()
    _expect_state("PROGRESS submit", progress, "submitted", failures)
    _expect_guard(
        "PROGRESS immutable write",
        "PROGRESS_GUARD_IMMUTABLE",
        lambda: progress.write({"note": "blocked"}),
        failures,
    )
    _expect_guard(
        "PROGRESS immutable unlink",
        "PROGRESS_GUARD_IMMUTABLE",
        lambda: progress.unlink(),
        failures,
    )
    _expect_guard(
        "PROGRESS revert no reason",
        "AUDIT_REASON_REQUIRED",
        lambda: progress.action_revert_progress(),
        failures,
    )
    progress.action_revert_progress(reason="smoke revert")
    _expect_state("PROGRESS revert", progress, "draft", failures)

    progress_events = _audit_events(env, "project.progress.entry", progress.id)
    audit_summary["progress"] = progress_events
    _ensure_events(
        "PROGRESS audit",
        progress_events,
        ["progress_submitted", "progress_reverted"],
        failures,
    )

    # -------------------- Ledger lock --------------------
    cost_code = env["project.cost.code"].create(
        {"name": "P2 Smoke Cost", "code": "P2-001", "type": "labor"}
    )
    today = fields.Date.today()
    period_value = today.strftime("%Y-%m")
    period = env["project.cost.period"].create(
        {"project_id": project.id, "period": period_value}
    )

    ledger = env["project.cost.ledger"].create(
        {
            "project_id": project.id,
            "period_id": period.id,
            "cost_code_id": cost_code.id,
            "date": today,
            "amount": 100.0,
        }
    )
    period.action_lock_period(reason="smoke lock")

    _expect_guard(
        "LEDGER create blocked",
        "PERIOD_LOCKED",
        lambda: env["project.cost.ledger"].create(
            {
                "project_id": project.id,
                "period_id": period.id,
                "cost_code_id": cost_code.id,
                "date": today,
                "amount": 50.0,
            }
        ),
        failures,
    )
    _expect_guard(
        "LEDGER write blocked",
        "PERIOD_LOCKED",
        lambda: ledger.write({"note": "blocked"}),
        failures,
    )
    _expect_guard(
        "LEDGER unlink blocked",
        "PERIOD_LOCKED",
        lambda: ledger.unlink(),
        failures,
    )
    _expect_guard(
        "PERIOD unlock no reason",
        "AUDIT_REASON_REQUIRED",
        lambda: period.action_unlock_period(),
        failures,
    )
    period.action_unlock_period(reason="smoke unlock")

    period_events = _audit_events(env, "project.cost.period", period.id)
    audit_summary["ledger_lock"] = period_events
    _ensure_events(
        "LEDGER audit",
        period_events,
        ["period_locked", "period_unlocked"],
        failures,
    )

    # -------------------- Contract link --------------------
    Tax = env["account.tax"].sudo()
    tax = Tax.search(
        [
            ("company_id", "=", company.id),
            ("type_tax_use", "in", ["purchase", "all"]),
            ("amount_type", "=", "percent"),
            ("price_include", "=", False),
        ],
        limit=1,
    )
    if not tax:
        tax = Tax.create(
            {
                "name": "P2 Smoke Tax",
                "amount_type": "percent",
                "amount": 0.0,
                "type_tax_use": "purchase",
                "price_include": False,
                "company_id": company.id,
            }
        )

    contract = env["construction.contract"].create(
        {
            "subject": "P2 Smoke Contract",
            "type": "in",
            "project_id": project.id,
            "partner_id": partner.id,
            "company_id": company.id,
            "currency_id": company.currency_id.id,
            "tax_id": tax.id,
        }
    )
    contract_b = env["construction.contract"].create(
        {
            "subject": "P2 Smoke Contract B",
            "type": "in",
            "project_id": project_b.id,
            "partner_id": partner.id,
            "company_id": company.id,
            "currency_id": company.currency_id.id,
            "tax_id": tax.id,
        }
    )

    settlement_required = env["sc.settlement.order"].create(
        {
            "project_id": project.id,
            "partner_id": partner.id,
            "company_id": company.id,
            "currency_id": company.currency_id.id,
        }
    )

    _expect_guard(
        "SETTLEMENT line contract required",
        "SETTLEMENT_CONTRACT_REQUIRED",
        lambda: env["sc.settlement.order.line"].create(
            {"settlement_id": settlement_required.id, "name": "Line no contract"}
        ),
        failures,
    )
    _expect_guard(
        "SETTLEMENT line contract mismatch",
        "SETTLEMENT_CONTRACT_MISMATCH",
        lambda: env["sc.settlement.order.line"].create(
            {
                "settlement_id": settlement_required.id,
                "contract_id": contract_b.id,
                "name": "Line mismatch",
            }
        ),
        failures,
    )

    settlement = env["sc.settlement.order"].create(
        {
            "project_id": project.id,
            "partner_id": partner.id,
            "contract_id": contract.id,
            "company_id": company.id,
            "currency_id": company.currency_id.id,
        }
    )
    settlement_line = env["sc.settlement.order.line"].create(
        {
            "settlement_id": settlement.id,
            "contract_id": contract.id,
            "name": "P2 Smoke Settlement Line",
            "qty": 1.0,
            "price_unit": 1000.0,
        }
    )
    settlement_line.action_bind_contract(contract.id)
    _expect_guard(
        "SETTLEMENT unbind no reason",
        "AUDIT_REASON_REQUIRED",
        lambda: settlement_line.action_unbind_contract(),
        failures,
    )
    settlement_line.action_unbind_contract(reason="smoke unbind")

    contract_events = _audit_events(env, "sc.settlement.order.line", settlement_line.id)
    audit_summary["contract_link"] = contract_events
    _ensure_events(
        "CONTRACT audit",
        contract_events,
        ["contract_bound", "contract_unbound"],
        failures,
    )

    # -------------------- Payment --------------------
    payment_no_attach = env["payment.request"].create(
        {
            "project_id": project.id,
            "partner_id": partner.id,
            "contract_id": contract.id,
            "currency_id": company.currency_id.id,
            "amount": 100.0,
            "type": "pay",
        }
    )
    _expect_guard(
        "PAYMENT attachments required",
        "PAYMENT_ATTACHMENTS_REQUIRED",
        lambda: payment_no_attach.action_submit(),
        failures,
    )

    # Prepare settlement + purchase order for payment flow.
    Uom = env["uom.uom"].sudo()
    uom = Uom.search([], limit=1)
    Product = env["product.product"].sudo()
    product = Product.search([], limit=1)
    if not product:
        product = Product.create(
            {"name": "P2 Smoke Product", "type": "service", "uom_id": uom.id, "uom_po_id": uom.id}
        )

    po = env["purchase.order"].create(
        {
            "partner_id": partner.id,
            "company_id": company.id,
            "currency_id": company.currency_id.id,
            "order_line": [
                (
                    0,
                    0,
                    {
                        "name": "P2 Smoke PO Line",
                        "product_id": product.id,
                        "product_qty": 1.0,
                        "product_uom": uom.id,
                        "price_unit": 1000.0,
                        "date_planned": fields.Datetime.now(),
                    },
                )
            ],
        }
    )
    po.write({"state": "purchase"})
    settlement.write({"purchase_order_ids": [(6, 0, [po.id])], "state": "approve"})

    payment = env["payment.request"].create(
        {
            "project_id": project.id,
            "partner_id": partner.id,
            "contract_id": contract.id,
            "settlement_id": settlement.id,
            "currency_id": company.currency_id.id,
            "amount": 100.0,
            "type": "pay",
        }
    )

    _expect_guard(
        "PAYMENT direct state write",
        "PAYMENT_GUARD_DIRECT_STATE_WRITE",
        lambda: payment.write({"state": "submit"}),
        failures,
    )

    env["ir.attachment"].create(
        {
            "name": "p2_smoke.txt",
            "datas": base64.b64encode(b"p2 smoke"),
            "res_model": "payment.request",
            "res_id": payment.id,
            "type": "binary",
            "mimetype": "text/plain",
        }
    )

    payment.action_submit()
    _expect_state("PAYMENT submit", payment, "submit", failures)

    _expect_guard(
        "PAYMENT reject no reason",
        "AUDIT_REASON_REQUIRED",
        lambda: payment.action_on_tier_rejected(),
        failures,
    )

    _expect_guard(
        "PAYMENT approve not validated",
        "PAYMENT_TIER_INCOMPLETE",
        lambda: payment.action_on_tier_approved(),
        failures,
    )

    payment.write({"validation_status": "validated"})
    payment.action_on_tier_approved()
    _expect_state("PAYMENT approved", payment, "approved", failures)

    payment._ensure_payment_ledger(amount=payment.amount)
    payment.action_done()
    _expect_state("PAYMENT done", payment, "done", failures)

    payment_events = _audit_events(env, "payment.request", payment.id)
    audit_summary["payment"] = payment_events
    _ensure_events(
        "PAYMENT audit",
        payment_events,
        ["payment_submitted", "payment_approved", "payment_paid"],
        failures,
    )

except Exception as err:
    failures.append(f"unexpected error: {err}")
    failures.append(traceback.format_exc())

result = "PASS" if not failures else "FAIL"
print("RESULT: %s" % result)

for key in ("task", "progress", "ledger_lock", "contract_link", "payment"):
    events = audit_summary.get(key, [])
    label = key.upper()
    print("AUDIT_EVENTS %s: %s" % (label, ",".join(events)))

if failures:
    print("FAILURES:")
    for msg in failures:
        print("- %s" % msg)

sys.exit(0 if result == "PASS" else 1)
