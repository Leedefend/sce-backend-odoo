# -*- coding: utf-8 -*-
from odoo import SUPERUSER_ID, api, fields


def post_init_hook(env_or_cr, registry=None):
    """补全 demo 物资计划行并标记为已批准（幂等）。"""
    # 兼容 Odoo 调用签名：可能传 env，也可能传 cr + registry
    if registry is None and hasattr(env_or_cr, "cr"):
        env = env_or_cr
    else:
        env = api.Environment(env_or_cr, SUPERUSER_ID, {})

    plan = env.ref("smart_construction_demo.sc_demo_material_plan_001", raise_if_not_found=False)
    if not plan:
        return
    cost_rebar = env.ref("smart_construction_demo.sc_demo_cost_rebar", raise_if_not_found=False)
    cost_conc = env.ref("smart_construction_demo.sc_demo_cost_concrete", raise_if_not_found=False)
    wbs_earth = env.ref("smart_construction_demo.sc_demo_wbs_earthwork", raise_if_not_found=False)
    wbs_struct = env.ref("smart_construction_demo.sc_demo_wbs_structure", raise_if_not_found=False)

    tmpl_rebar = env.ref("smart_construction_demo.sc_demo_product_rebar_template", raise_if_not_found=False)
    tmpl_concrete = env.ref("smart_construction_demo.sc_demo_product_concrete_template", raise_if_not_found=False)
    product_rebar = tmpl_rebar.product_variant_id if tmpl_rebar else False
    product_concrete = tmpl_concrete.product_variant_id if tmpl_concrete else False

    # 补充计划行（仅在空时创建）
    if not plan.line_ids:
        vendor_a = env.ref("smart_construction_demo.sc_demo_supplier_a", raise_if_not_found=False)
        vendor_b = env.ref("smart_construction_demo.sc_demo_supplier_b", raise_if_not_found=False)
        line_vals = []
        if product_rebar:
            line_vals.append(
                {
                    "plan_id": plan.id,
                    "product_id": product_rebar.id,
                    "spec": "HRB400 Φ16，理论重量",
                    "quantity": 50,
                    "vendor_id": vendor_a.id if vendor_a else False,
                    "note": "主体结构钢筋",
                }
            )
        if product_concrete:
            line_vals.append(
                {
                    "plan_id": plan.id,
                    "product_id": product_concrete.id,
                    "spec": "C30 泵送",
                    "quantity": 80,
                    "vendor_id": vendor_b.id if vendor_b else False,
                    "note": "基础混凝土",
                }
            )
        if line_vals:
            env["project.material.plan.line"].sudo().create(line_vals)

    # 补单号 & 审批通过
    update_vals = {}
    seq = env["ir.sequence"]
    if plan.name == "新建":
        new_name = seq.next_by_code("project.material.plan")
        if new_name:
            update_vals["name"] = new_name

    if plan.state != "approved":
        now = fields.Datetime.now()
        update_vals.update(
            {
                "state": "approved",
                "submitted_by": env.user.id,
                "submitted_at": now,
                "approved_by": env.user.id,
                "approved_at": now,
            }
        )

    if update_vals:
        plan.write(update_vals)

    # Demo 采购单：按供应商自动生成 2 张 PO（幂等）
    PurchaseOrder = env["purchase.order"].sudo()
    PurchaseOrderLine = env["purchase.order.line"].sudo()
    Settlement = env["sc.settlement.order"].sudo()
    PaymentRequest = env["payment.request"].sudo()
    if "plan_id" in PurchaseOrder._fields:
        for vendor in plan.line_ids.mapped("vendor_id"):
            if not vendor:
                continue
            existing = PurchaseOrder.search(
                [("plan_id", "=", plan.id), ("partner_id", "=", vendor.id)],
                limit=1,
            )
            if existing:
                continue

            order = PurchaseOrder.create(
                {
                    "partner_id": vendor.id,
                    "company_id": plan.company_id.id if plan.company_id else False,
                    "project_id": plan.project_id.id,
                    "plan_id": plan.id,
                    "origin": plan.name,
                }
            )

            # 针对当前供应商的行
            vendor_lines = plan.line_ids.filtered(lambda l: l.vendor_id == vendor)
            for line in vendor_lines:
                product = line.product_id
                qty = line.quantity or 1.0
                uom = line.uom_id or product.uom_po_id or product.uom_id
                price = 0.0
                cost_code = False
                wbs = False
                if product_rebar and product == product_rebar:
                    price = 4200.0
                    cost_code = cost_rebar
                    wbs = wbs_struct
                if product_concrete and product == product_concrete:
                    price = 420.0
                    cost_code = cost_conc
                    wbs = wbs_earth
                PurchaseOrderLine.create(
                    {
                        "order_id": order.id,
                        "name": line.spec or product.display_name,
                        "product_id": product.id,
                        "product_qty": qty,
                        "product_uom": uom.id,
                        "price_unit": price,
                        "date_planned": fields.Date.context_today(plan),
                        "plan_line_id": line.id if "plan_line_id" in PurchaseOrderLine._fields else False,
                        "company_id": plan.company_id.id if plan.company_id else False,
                        "project_id": plan.project_id.id,
                        "cost_code_id": cost_code.id if cost_code else False,
                        "wbs_id": wbs.id if wbs else False,
                    }
                )
            try:
                order.button_confirm()
            except Exception:
                # 若确认失败（如缺少配置），保持草稿状态便于演示
                pass

    # 生成结算单（按供应商汇总采购）并关联付款申请
    for vendor in plan.line_ids.mapped("vendor_id"):
        if not vendor:
            continue
        pos = PurchaseOrder.search(
            [("plan_id", "=", plan.id), ("partner_id", "=", vendor.id)],
        )
        if not pos:
            continue
        settlement = Settlement.search(
            [("project_id", "=", plan.project_id.id), ("partner_id", "=", vendor.id)],
            limit=1,
        )
        if not settlement:
            total = sum(pos.mapped("amount_total"))
            contract_val = False
            supplier_a = env.ref("smart_construction_demo.sc_demo_supplier_a", raise_if_not_found=False)
            supplier_b = env.ref("smart_construction_demo.sc_demo_supplier_b", raise_if_not_found=False)
            if supplier_a and vendor == supplier_a:
                contract_val = env.ref("smart_construction_demo.sc_demo_contract_cost_001", raise_if_not_found=False)
            if supplier_b and vendor == supplier_b:
                contract_val = env.ref("smart_construction_demo.sc_demo_contract_cost_002", raise_if_not_found=False)
            settlement = Settlement.create(
                {
                    "project_id": plan.project_id.id,
                    "contract_id": contract_val.id if contract_val else False,
                    "partner_id": vendor.id,
                    "settlement_type": "out",
                    "date_settlement": fields.Date.context_today(plan),
                    "purchase_order_ids": [(6, 0, pos.ids)],
                    "line_ids": [
                        (
                            0,
                            0,
                            {
                                "name": "采购结算",
                                "qty": 1,
                                "price_unit": total,
                            },
                        )
                    ],
                    "state": "approve",
                }
            )
        else:
            if not settlement.purchase_order_ids and pos:
                settlement.purchase_order_ids = [(6, 0, pos.ids)]

        # 将付款申请绑定供应商A的结算单
        supplier_a = env.ref("smart_construction_demo.sc_demo_supplier_a", raise_if_not_found=False)
        supplier_b = env.ref("smart_construction_demo.sc_demo_supplier_b", raise_if_not_found=False)
        if supplier_a and vendor == supplier_a:
            pay_ref = env.ref("smart_construction_demo.sc_demo_payment_request_001", raise_if_not_found=False)
            if pay_ref:
                pay = PaymentRequest.browse(pay_ref.id)
                if pay and not pay.settlement_id:
                    pay.settlement_id = settlement.id
                if pay.state != "approved":
                    pay.write({"state": "approved"})
                # 自动入账资金流水
                ledger = env["sc.treasury.ledger"].sudo().search([("payment_request_id", "=", pay.id)], limit=1)
                if not ledger:
                    env["sc.treasury.ledger"].sudo().with_context(allow_ledger_auto=True).create(
                        {
                            "project_id": pay.project_id.id,
                            "partner_id": pay.partner_id.id,
                            "settlement_id": settlement.id,
                            "payment_request_id": pay.id,
                            "direction": "out",
                            "amount": pay.amount,
                            "currency_id": pay.currency_id.id,
                            "note": "Demo 自动入账（供应商A）",
                        }
                    )
                if pay.state != "done":
                    pay.write({"state": "done"})
        if supplier_b and vendor == supplier_b:
            pay_ref_b = env.ref("smart_construction_demo.sc_demo_payment_request_002", raise_if_not_found=False)
            if pay_ref_b:
                pay_b = PaymentRequest.browse(pay_ref_b.id)
                if pay_b and not pay_b.settlement_id:
                    pay_b.settlement_id = settlement.id
                if pay_b.state != "approved":
                    pay_b.write({"state": "approved"})
                ledger_b = env["sc.treasury.ledger"].sudo().search([("payment_request_id", "=", pay_b.id)], limit=1)
                if not ledger_b:
                    env["sc.treasury.ledger"].sudo().with_context(allow_ledger_auto=True).create(
                        {
                            "project_id": pay_b.project_id.id,
                            "partner_id": pay_b.partner_id.id,
                            "settlement_id": settlement.id,
                            "payment_request_id": pay_b.id,
                            "direction": "out",
                            "amount": pay_b.amount,
                            "currency_id": pay_b.currency_id.id,
                            "note": "Demo 自动入账（供应商B）",
                        }
                    )
                if pay_b.state != "done":
                    pay_b.write({"state": "done"})

    # 收入收款：将进度结算绑定收款申请并入账
    settle_in = env.ref("smart_construction_demo.sc_demo_settlement_in_001", raise_if_not_found=False)
    pay_receive = env.ref("smart_construction_demo.sc_demo_payment_request_receive_001", raise_if_not_found=False)
    if settle_in and pay_receive:
        pay_rec = PaymentRequest.browse(pay_receive.id)
        if pay_rec and not pay_rec.settlement_id:
            pay_rec.settlement_id = settle_in.id
        if pay_rec.state != "approved":
            pay_rec.write({"state": "approved"})
        ledger_in = env["sc.treasury.ledger"].sudo().search([("payment_request_id", "=", pay_rec.id)], limit=1)
        if not ledger_in:
            env["sc.treasury.ledger"].sudo().with_context(allow_ledger_auto=True).create(
                {
                    "project_id": pay_rec.project_id.id,
                    "partner_id": pay_rec.partner_id.id,
                    "settlement_id": settle_in.id,
                    "payment_request_id": pay_rec.id,
                    "direction": "in",
                    "amount": pay_rec.amount,
                    "currency_id": pay_rec.currency_id.id,
                    "note": "Demo 自动入账（收款）",
                }
            )
        if pay_rec.state != "done":
            pay_rec.write({"state": "done"})
