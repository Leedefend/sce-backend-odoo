# -*- coding: utf-8 -*-
from odoo import fields

from ..registry import SeedStep, register


PROJECT_EXEC_CODE = "DEMO-PJ-EXEC"
STAGE_PROJECT_CODES = [
    "DEMO-PJ-STAGE-DRAFT",
    "DEMO-PJ-STAGE-RUN",
    "DEMO-PJ-STAGE-PAUSE",
    "DEMO-PJ-STAGE-CLOSING",
    "DEMO-PJ-STAGE-DONE",
    "DEMO-PJ-STAGE-WARRANTY",
    "DEMO-PJ-STAGE-CLOSED",
]
DEMO_INVOICE_RATIO_BY_STATE = {
    "draft": 0.0,
    "in_progress": 0.7,
    "paused": 0.7,
    "closing": 0.95,
    "done": 1.0,
    "warranty": 1.0,
    "closed": 1.0,
}
DEMO_INVOICE_WARN_RATIO_BY_STATE = {
    "draft": 0.0,
    "in_progress": 0.5,
    "paused": 0.5,
    "closing": 0.8,
    "done": 0.9,
    "warranty": 0.9,
    "closed": 0.9,
}
DEMO_WARN_PROJECT_CODES = {
    "DEMO-PJ-INIT",
    "DEMO-PJ-TENDER",
}


def _ensure_funding_baseline(env, project):
    Funding = env["project.funding.baseline"].sudo()
    project.sudo().write({"funding_enabled": True})
    baseline = Funding.search(
        [("project_id", "=", project.id), ("state", "=", "active")], limit=1
    )
    if baseline:
        baseline.write({"total_amount": 2000000.0})
        return baseline
    return Funding.create(
        {
            "project_id": project.id,
            "total_amount": 2000000.0,
            "state": "active",
        }
    )


def _ensure_settlement(env, project, contract):
    Settlement = env["sc.settlement.order"].sudo()
    Line = env["sc.settlement.order.line"].sudo()
    settlement = Settlement.search(
        [("project_id", "=", project.id), ("contract_id", "=", contract.id)], limit=1
    )
    vals = {
        "name": f"SET-{project.project_code}-01",
        "project_id": project.id,
        "contract_id": contract.id,
        "partner_id": contract.partner_id.id,
        "settlement_type": "out" if contract.type == "in" else "in",
        "date_settlement": fields.Date.context_today(env.user),
    }
    if settlement:
        settlement.write(vals)
    else:
        settlement = Settlement.create(vals)

    line_vals = [
        {"settlement_id": settlement.id, "name": "结算项A", "qty": 1, "price_unit": 260000.0},
        {"settlement_id": settlement.id, "name": "结算项B", "qty": 1, "price_unit": 140000.0},
    ]
    for vals in line_vals:
        existing = Line.search(
            [("settlement_id", "=", settlement.id), ("name", "=", vals["name"])], limit=1
        )
        if existing:
            existing.write(vals)
        else:
            Line.create(vals)

    env.cr.execute(
        "UPDATE sc_settlement_order SET state=%s WHERE id=%s",
        ("approve", settlement.id),
    )
    env.invalidate_all()
    return settlement


def _ensure_purchase_order(env, settlement, split_first_line=False):
    Purchase = env["purchase.order"].sudo()
    PurchaseLine = env["purchase.order.line"].sudo()
    Product = env["product.product"].sudo()
    uom_unit = env.ref("uom.product_uom_unit", raise_if_not_found=False)
    if not uom_unit:
        uom_unit = env["uom.uom"].sudo().search([], limit=1)

    product = Product.search([("name", "=", "演示采购服务")], limit=1)
    if not product:
        product = Product.create(
            {
                "name": "演示采购服务",
                "type": "service",
                "uom_id": uom_unit.id if uom_unit else False,
                "uom_po_id": uom_unit.id if uom_unit else False,
                "purchase_ok": True,
                "sale_ok": False,
            }
        )

    po = Purchase.search(
        [
            ("partner_id", "=", settlement.partner_id.id),
            ("origin", "=", settlement.name),
        ],
        limit=1,
    )
    if not po:
        po = Purchase.create(
            {
                "partner_id": settlement.partner_id.id,
                "date_order": fields.Datetime.now(),
                "origin": settlement.name,
            }
        )

    original_state = po.state
    if original_state != "draft":
        env.cr.execute(
            "UPDATE purchase_order SET state=%s WHERE id=%s",
            ("draft", po.id),
        )
        env.invalidate_all()

    total = settlement.amount_total or sum(settlement.line_ids.mapped("amount")) or 0.0
    line = PurchaseLine.search([("order_id", "=", po.id)], limit=1)
    desired_lines = []
    settlement_lines = settlement.line_ids
    if not settlement_lines:
        desired_lines.append(
            {
                "name": "演示采购行",
                "amount": total,
                "split": False,
            }
        )
    else:
        for idx, sline in enumerate(settlement_lines):
            amount = sline.amount or 0.0
            if split_first_line and idx == 0:
                desired_lines.append(
                    {
                        "name": f"{sline.name}-批次1",
                        "amount": round(amount * 0.6, 2),
                        "split": True,
                    }
                )
                desired_lines.append(
                    {
                        "name": f"{sline.name}-批次2",
                        "amount": amount - round(amount * 0.6, 2),
                        "split": True,
                    }
                )
            else:
                desired_lines.append(
                    {
                        "name": sline.name,
                        "amount": amount,
                        "split": False,
                    }
                )
    for spec in desired_lines:
        line_vals = {
            "order_id": po.id,
            "name": spec["name"],
            "product_id": product.id,
            "product_qty": 1.0,
            "product_uom": uom_unit.id if uom_unit else product.uom_po_id.id,
            "price_unit": spec["amount"],
            "date_planned": fields.Datetime.now(),
        }
        existing = PurchaseLine.search(
            [("order_id", "=", po.id), ("name", "=", spec["name"])], limit=1
        )
        if existing:
            existing.write(line_vals)
        else:
            PurchaseLine.create(line_vals)

    desired_names = {spec["name"] for spec in desired_lines}
    stale_lines = PurchaseLine.search([("order_id", "=", po.id), ("name", "not in", list(desired_names))])
    if stale_lines:
        stale_lines.unlink()

    env.cr.execute(
        "UPDATE purchase_order SET state=%s WHERE id=%s",
        ("purchase", po.id),
    )
    env.invalidate_all()
    settlement.purchase_order_ids = [(4, po.id)]


def _ensure_invoice_info(env, settlement, ratio):
    total = settlement.amount_total or sum(settlement.line_ids.mapped("amount")) or 0.0
    invoice_amount = round(total * ratio, 2)
    settlement.write(
        {
            "invoice_ref": settlement.invoice_ref or f"INV-{settlement.name}",
            "invoice_amount": invoice_amount,
            "invoice_date": fields.Date.context_today(env.user),
        }
    )


def _ensure_payments(env, project, pay_contract, receive_contract, settlement):
    Payment = env["payment.request"].sudo()
    pay = Payment.search(
        [
            ("project_id", "=", project.id),
            ("type", "=", "pay"),
            ("contract_id", "=", pay_contract.id),
        ],
        limit=1,
    )
    if not pay:
        pay = Payment.create(
            {
                "type": "pay",
                "project_id": project.id,
                "partner_id": pay_contract.partner_id.id,
                "contract_id": pay_contract.id,
                "settlement_id": settlement.id,
                "amount": 160000.0,
                "state": "draft",
            }
        )
    receive = Payment.search(
        [
            ("project_id", "=", project.id),
            ("type", "=", "receive"),
            ("contract_id", "=", receive_contract.id),
        ],
        limit=1,
    )
    if not receive:
        receive = Payment.create(
            {
                "type": "receive",
                "project_id": project.id,
                "partner_id": receive_contract.partner_id.id,
                "contract_id": receive_contract.id,
                "amount": 120000.0,
                "state": "draft",
            }
        )

    env.cr.execute(
        "UPDATE payment_request SET state=%s, validation_status=%s WHERE id in %s",
        ("done", "validated", tuple([pay.id, receive.id])),
    )
    env.invalidate_all()


def _get_project(env, code):
    return env["project.project"].sudo().search([("project_code", "=", code)], limit=1)


def _get_or_create_partner(env, name):
    Partner = env["res.partner"].sudo()
    partner = Partner.search([("name", "=", name)], limit=1)
    if partner:
        if partner.company_type != "company":
            partner.company_type = "company"
        return partner
    return Partner.create({"name": name, "company_type": "company"})


def _get_dictionary(env, xmlid, domain):
    rec = env.ref(xmlid, raise_if_not_found=False)
    if rec:
        return rec
    return env["sc.dictionary"].sudo().search(domain, limit=1)


def _ensure_contract(env, vals):
    Contract = env["construction.contract"].sudo()
    contract = Contract.search(
        [("project_id", "=", vals["project_id"]), ("subject", "=", vals["subject"])], limit=1
    )
    if contract:
        contract.write(vals)
    else:
        contract = Contract.create(vals)
    return contract


def run(env):
    projects = [
        _get_project(env, PROJECT_EXEC_CODE),
    ]
    for code in STAGE_PROJECT_CODES:
        projects.append(_get_project(env, code))
    projects = [p for p in projects if p]

    owner = _get_or_create_partner(env, "演示业主 · 城市建设集团")
    subcontract = _get_or_create_partner(env, "演示分包 · 桥梁施工队")

    contract_category = _get_dictionary(
        env,
        "smart_construction_seed.seed_dict_contract_category_build",
        [("type", "=", "contract_category")],
    )
    contract_type_out = _get_dictionary(
        env,
        "smart_construction_seed.seed_dict_contract_type_out",
        [("type", "=", "contract_type")],
    )
    contract_type_in = _get_dictionary(
        env,
        "smart_construction_seed.seed_dict_contract_type_in",
        [("type", "=", "contract_type")],
    )

    sale_tax = env.ref("smart_construction_seed.tax_sale_9", raise_if_not_found=False)
    purchase_tax = env.ref("smart_construction_seed.tax_purchase_13", raise_if_not_found=False)

    today = fields.Date.context_today(env.user)
    ContractLine = env["construction.contract.line"].sudo()
    warn_codes = DEMO_WARN_PROJECT_CODES
    split_codes = {"DEMO-PJ-TENDER"}

    for project in projects:
        out_vals = {
            "subject": f"{project.name}-收入合同",
            "type": "out",
            "project_id": project.id,
            "partner_id": owner.id,
            "category_id": contract_category.id if contract_category else False,
            "contract_type_id": contract_type_out.id if contract_type_out else False,
            "date_contract": today,
            "date_start": today,
            "date_end": today,
            "state": "confirmed",
        }
        if sale_tax:
            out_vals["tax_id"] = sale_tax.id
        out_contract = _ensure_contract(env, out_vals)

        in_vals = {
            "subject": f"{project.name}-分包合同",
            "type": "in",
            "project_id": project.id,
            "partner_id": subcontract.id,
            "category_id": contract_category.id if contract_category else False,
            "contract_type_id": contract_type_in.id if contract_type_in else False,
            "date_contract": today,
            "date_start": today,
            "date_end": today,
            "state": "confirmed",
        }
        if purchase_tax:
            in_vals["tax_id"] = purchase_tax.id
        in_contract = _ensure_contract(env, in_vals)

        for contract, lines in [
            (
                out_contract,
                [
                    {"sequence": 10, "qty_contract": 1, "price_contract": 880000.0},
                    {"sequence": 20, "qty_contract": 1, "price_contract": 320000.0},
                ],
            ),
            (
                in_contract,
                [
                    {"sequence": 10, "qty_contract": 1, "price_contract": 240000.0},
                    {"sequence": 20, "qty_contract": 1, "price_contract": 160000.0},
                ],
            ),
        ]:
            for vals in lines:
                existing = ContractLine.search(
                    [("contract_id", "=", contract.id), ("sequence", "=", vals["sequence"])],
                    limit=1,
                )
                payload = dict(vals)
                payload["contract_id"] = contract.id
                payload["price_contract"] = vals["price_contract"]
                if existing:
                    existing.write(payload)
                else:
                    ContractLine.create(payload)

        _ensure_funding_baseline(env, project)
        settlement = _ensure_settlement(env, project, in_contract)
        split_first = project.project_code in split_codes
        _ensure_purchase_order(env, settlement, split_first_line=split_first)
        if project.project_code in warn_codes:
            ratio = DEMO_INVOICE_WARN_RATIO_BY_STATE.get(project.lifecycle_state, 1.0)
        else:
            ratio = DEMO_INVOICE_RATIO_BY_STATE.get(project.lifecycle_state, 1.0)
        _ensure_invoice_info(env, settlement, ratio)
        _ensure_payments(env, project, in_contract, out_contract, settlement)


register(
    SeedStep(
        name="demo_40_contracts",
        description="Seed contract records for demo project.",
        run=run,
    )
)
