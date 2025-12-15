# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase, tagged


@tagged("sc_smoke", "smoke_validator")
class TestValidatorSmoke(TransactionCase):

    def test_validator_runs(self):
        payload = self.env["sc.data.validator"].run(return_dict=True)
        self.assertIn("rules", payload)
        self.assertIn("issues_total", payload)
        # at least rule registry is wired
        self.assertGreaterEqual(len(payload["rules"]), 1)

    def test_validator_catches_missing_settlement(self):
        project = self.env["project.project"].create({"name": "Validator Project"})
        partner = self.env["res.partner"].create({"name": "Validator Partner"})
        bad_pr = self.env["payment.request"].create(
            {
                "name": "VAL-PR-BAD",
                "type": "pay",
                "project_id": project.id,
                "partner_id": partner.id,
                "amount": 100,
                "state": "approve",  # 规则要求此状态必须关联结算单
            }
        )
        payload = self.env["sc.data.validator"].run(return_dict=True)
        rule = next(r for r in payload["rules"] if r["rule"] == "SC.VAL.3WAY.001")
        issue_ids = [i["res_id"] for i in rule.get("issues", [])]
        self.assertIn(bad_pr.id, issue_ids)

    def test_payment_request_submit_happy_path(self):
        # 构造完整链路：项目 -> 合同 -> 采购 -> 结算 -> 付款申请
        project = self.env["project.project"].create({"name": "PR Happy Project"})
        partner = self.env["res.partner"].create({"name": "Happy Vendor"})
        contract = self.env["construction.contract"].create(
            {"subject": "Happy Contract", "type": "in", "project_id": project.id, "partner_id": partner.id}
        )
        product = self.env["product.product"].create(
            {
                "name": "Happy Product",
                "type": "product",
                "uom_id": self.env.ref("uom.product_uom_unit").id,
                "uom_po_id": self.env.ref("uom.product_uom_unit").id,
            }
        )
        po = self.env["purchase.order"].create(
            {
                "partner_id": partner.id,
                "project_id": project.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "name": "Line",
                            "product_id": product.id,
                            "product_qty": 1,
                            "product_uom": product.uom_po_id.id,
                            "price_unit": 10,
                        },
                    )
                ],
            }
        )
        po.button_confirm()
        settle = self.env["sc.settlement.order"].create(
            {
                "project_id": project.id,
                "partner_id": partner.id,
                "contract_id": contract.id,
                "purchase_order_ids": [(6, 0, [po.id])],
                "line_ids": [(0, 0, {"name": "Settlement Line", "qty": 1, "price_unit": 10})],
                "state": "approve",
            }
        )
        fin_user = self.env.ref("smart_construction_core.user_sc_fin_01")
        fin_user.write({"email": "fin+happy@test.com"})
        pr = self.env["payment.request"].sudo().create(
            {
                "name": "PR Happy",
                "type": "pay",
                "project_id": project.id,
                "partner_id": partner.id,
                "contract_id": contract.id,
                "settlement_id": settle.id,
                "amount": 5,
                "state": "draft",
            }
        )
        # 调用提交按钮，不应抛异常
        pr.with_user(fin_user).action_submit()
        self.assertEqual(pr.state, "submit")

    def test_settlement_approve_happy_path(self):
        project = self.env["project.project"].create({"name": "Settle Happy Project"})
        partner = self.env["res.partner"].create({"name": "Happy Vendor"})
        contract = self.env["construction.contract"].create(
            {"subject": "Happy Contract 2", "type": "in", "project_id": project.id, "partner_id": partner.id}
        )
        product = self.env["product.product"].create(
            {
                "name": "Happy Product 2",
                "type": "product",
                "uom_id": self.env.ref("uom.product_uom_unit").id,
                "uom_po_id": self.env.ref("uom.product_uom_unit").id,
            }
        )
        po = self.env["purchase.order"].create(
            {
                "partner_id": partner.id,
                "project_id": project.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "name": "Line",
                            "product_id": product.id,
                            "product_qty": 1,
                            "product_uom": product.uom_po_id.id,
                            "price_unit": 20,
                        },
                    )
                ],
            }
        )
        po.button_confirm()
        settle = self.env["sc.settlement.order"].create(
            {
                "project_id": project.id,
                "partner_id": partner.id,
                "contract_id": contract.id,
                "purchase_order_ids": [(6, 0, [po.id])],
                "line_ids": [(0, 0, {"name": "Settlement Line", "qty": 1, "price_unit": 20})],
                "state": "draft",
            }
        )
        settle.action_submit()
        settle.action_approve()
        self.assertEqual(settle.state, "approve")
