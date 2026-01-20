# -*- coding: utf-8 -*-
import base64
import sys
import traceback

from odoo import fields


def _ensure_groups(env):
    user = env.user.sudo()
    for xmlid in (
        "smart_construction_core.group_sc_cap_project_manager",
        "smart_construction_core.group_sc_cap_finance_user",
        "smart_construction_core.group_sc_cap_finance_manager",
    ):
        group = env.ref(xmlid, raise_if_not_found=False)
        if group and group.id not in user.groups_id.ids:
            user.write({"groups_id": [(4, group.id)]})


def _get_tax(env, company):
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
    if tax:
        return tax
    return Tax.create(
        {
            "name": "P3 Smoke Tax",
            "amount_type": "percent",
            "amount": 0.0,
            "type_tax_use": "purchase",
            "price_include": False,
            "company_id": company.id,
        }
    )


def _ensure_funding_baseline(env, project):
    Baseline = env["project.funding.baseline"]
    baseline = Baseline.search(
        [("project_id", "=", project.id), ("state", "=", "active")],
        limit=1,
    )
    if baseline:
        return baseline
    return Baseline.create(
        {"project_id": project.id, "total_amount": 1000.0, "state": "active"}
    )


def _ensure_attachment(env, payment):
    env["ir.attachment"].create(
        {
            "name": "p3_smoke.txt",
            "datas": base64.b64encode(b"p3 smoke"),
            "res_model": "payment.request",
            "res_id": payment.id,
            "type": "binary",
            "mimetype": "text/plain",
        }
    )


failures = []

try:
    company = env.company
    _ensure_groups(env)

    partner = env["res.partner"].create({"name": "P3 Smoke Partner"})
    project = env["project.project"].create(
        {
            "name": "P3 Smoke Project",
            "code": "P3-SMOKE",
            "funding_enabled": True,
            "company_id": company.id,
        }
    )
    _ensure_funding_baseline(env, project)

    tax = _get_tax(env, company)
    contract = env["construction.contract"].create(
        {
            "subject": "P3 Smoke Contract",
            "type": "in",
            "project_id": project.id,
            "partner_id": partner.id,
            "company_id": company.id,
            "currency_id": company.currency_id.id,
            "tax_id": tax.id,
        }
    )

    settlement_amount = 1000.0
    payment_amount = 400.0

    settlement = env["sc.settlement.order"].create(
        {
            "project_id": project.id,
            "partner_id": partner.id,
            "contract_id": contract.id,
            "company_id": company.id,
            "currency_id": company.currency_id.id,
        }
    )
    env["sc.settlement.order.line"].create(
        {
            "settlement_id": settlement.id,
            "contract_id": contract.id,
            "name": "P3 Smoke Line",
            "qty": 1.0,
            "price_unit": settlement_amount,
        }
    )

    Uom = env["uom.uom"].sudo()
    uom = Uom.search([], limit=1)
    Product = env["product.product"].sudo()
    product = Product.search([], limit=1)
    if not product:
        product = Product.create(
            {"name": "P3 Smoke Product", "type": "service", "uom_id": uom.id, "uom_po_id": uom.id}
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
                        "name": "P3 Smoke PO Line",
                        "product_id": product.id,
                        "product_qty": 1.0,
                        "product_uom": uom.id,
                        "price_unit": settlement_amount,
                        "date_planned": fields.Datetime.now(),
                    },
                )
            ],
        }
    )
    po.write({"state": "purchase"})
    settlement.write({"purchase_order_ids": [(6, 0, [po.id])]})
    settlement.write({"state": "approve"})

    payment = env["payment.request"].create(
        {
            "project_id": project.id,
            "partner_id": partner.id,
            "contract_id": contract.id,
            "settlement_id": settlement.id,
            "currency_id": company.currency_id.id,
            "amount": payment_amount,
            "type": "pay",
        }
    )
    _ensure_attachment(env, payment)
    payment.action_submit()
    payment.write({"validation_status": "validated"})
    payment.action_on_tier_approved()
    payment._ensure_payment_ledger(amount=payment.amount)
    payment.action_done()

    env.cr.commit()
    env.flush_all()

    Summary = env["sc.contract.recon.summary"]
    Summary.create({"contract_id": contract.id})
    summary = Summary.search([("contract_id", "=", contract.id)], limit=1)
    summary_count = Summary.search_count([])

    if summary_count < 1:
        failures.append("summary_count < 1")

    if summary:
        expected_delta = settlement_amount - payment_amount
        if summary.delta != expected_delta:
            failures.append("delta mismatch")
        if summary.settlement_ids_count != 1:
            failures.append("settlement count mismatch")
        if summary.payment_ids_count != 1:
            failures.append("payment count mismatch")
    else:
        failures.append("no summary sample")

    print("RECON_SUMMARY_COUNT: %s" % summary_count)
    if summary:
        print(
            "RECON_SAMPLE: contract=%s settlement_total=%s payment_total=%s delta=%s"
            % (
                summary.contract_id.id,
                summary.settlement_total,
                summary.payment_total,
                summary.delta,
            )
        )
        print(
            "RECON_EXPLAIN: settlement_count=%s payment_count=%s"
            % (summary.settlement_ids_count, summary.payment_ids_count)
        )

    if not failures:
        print("RECON_ASSERT: PASS")

except Exception as err:
    failures.append(f"unexpected error: {err}")
    failures.append(traceback.format_exc())

result = "PASS" if not failures else "FAIL"
print("RESULT: %s" % result)

if failures:
    print("FAILURES:")
    for msg in failures:
        print("- %s" % msg)

sys.exit(0 if result == "PASS" else 1)
