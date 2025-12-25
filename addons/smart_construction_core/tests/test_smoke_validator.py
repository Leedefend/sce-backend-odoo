# -*- coding: utf-8 -*-
from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install", "sc_smoke", "smoke_validator")
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
        rule = next(
            r
            for r in payload["rules"]
            if (r.get("code") or r.get("rule")) == "SC.VAL.3WAY.001"
        )
        issue_ids = [i["res_id"] for i in rule.get("issues", [])]
        self.assertIn(bad_pr.id, issue_ids)

    def test_payment_request_submit_happy_path(self):
        # 构造完整链路：项目 -> 合同 -> 采购 -> 结算 -> 付款申请
        project = self.env["project.project"].create({"name": "PR Happy Project"})
        partner = self.env["res.partner"].create({"name": "Happy Vendor"})
        company = self.env.ref("base.main_company")
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
        finance_group = self.env.ref("smart_construction_core.group_sc_cap_finance_user")
        fin_user = self.env["res.users"].with_context(no_reset_password=True).create({
            "name": "Happy Finance",
            "login": "happy_fin",
            "company_id": company.id,
            "company_ids": [(6, 0, [company.id])],
            "groups_id": [(6, 0, [finance_group.id])],
            "email": "fin+happy@test.com",
        })
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

    def test_validator_scope_only_checks_target_payment_request(self):
        """
        验证 scope 仅校验目标单据：good_pr 需通过，bad_pr 需失败。
        """

        validator = self.env["sc.data.validator"]

        # bad_pr：缺少 settlement_id，但处于必须有关联的状态
        project1 = self.env["project.project"].create({"name": "Scope Project BAD"})
        partner1 = self.env["res.partner"].create({"name": "Scope Vendor BAD"})
        bad_pr = self.env["payment.request"].create(
            {
                "name": "VAL-PR-BAD-SCOPE",
                "type": "pay",
                "project_id": project1.id,
                "partner_id": partner1.id,
                "amount": 100,
                "state": "approve",
            }
        )

        # good_pr：完整链路，处于同样状态
        project2 = self.env["project.project"].create({"name": "Scope Project GOOD"})
        partner2 = self.env["res.partner"].create({"name": "Scope Vendor GOOD"})
        contract2 = self.env["construction.contract"].create(
            {"subject": "Scope Contract", "type": "in", "project_id": project2.id, "partner_id": partner2.id}
        )
        product2 = self.env["product.product"].create(
            {
                "name": "Scope Product",
                "type": "product",
                "uom_id": self.env.ref("uom.product_uom_unit").id,
                "uom_po_id": self.env.ref("uom.product_uom_unit").id,
            }
        )
        po2 = self.env["purchase.order"].create(
            {
                "partner_id": partner2.id,
                "project_id": project2.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "name": "Line",
                            "product_id": product2.id,
                            "product_qty": 1,
                            "product_uom": product2.uom_po_id.id,
                            "price_unit": 10,
                        },
                    )
                ],
            }
        )
        po2.button_confirm()
        settle2 = self.env["sc.settlement.order"].create(
            {
                "project_id": project2.id,
                "partner_id": partner2.id,
                "contract_id": contract2.id,
                "purchase_order_ids": [(6, 0, [po2.id])],
                "line_ids": [(0, 0, {"name": "Settlement Line", "qty": 1, "price_unit": 10})],
                "state": "approve",
            }
        )
        good_pr = self.env["payment.request"].sudo().create(
            {
                "name": "VAL-PR-GOOD-SCOPE",
                "type": "pay",
                "project_id": project2.id,
                "partner_id": partner2.id,
                "contract_id": contract2.id,
                "settlement_id": settle2.id,
                "amount": 5,
                "state": "approve",
            }
        )

        # scope 指向 good_pr：应通过
        validator.validate_or_raise(
            scope={
                "res_model": "payment.request",
                "res_ids": [good_pr.id],
                "project_id": good_pr.project_id.id,
                "company_id": good_pr.company_id.id,
            }
        )

        # scope 指向 bad_pr：应抛异常
        with self.assertRaises(UserError):
            validator.validate_or_raise(
                scope={
                    "res_model": "payment.request",
                    "res_ids": [bad_pr.id],
                    "project_id": bad_pr.project_id.id,
                    "company_id": bad_pr.company_id.id,
                }
            )

    def test_payment_request_overpay_blocked(self):
        project = self.env["project.project"].create({"name": "Overpay Project"})
        partner = self.env["res.partner"].create({"name": "Overpay Vendor"})
        company = self.env.ref("base.main_company")
        contract = self.env["construction.contract"].create(
            {"subject": "Overpay Contract", "type": "in", "project_id": project.id, "partner_id": partner.id}
        )
        product = self.env["product.product"].create(
            {
                "name": "Overpay Product",
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
                            "price_unit": 100,
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
                "line_ids": [(0, 0, {"name": "Settlement Line", "qty": 1, "price_unit": 100})],
                "state": "approve",
            }
        )
        finance_group = self.env.ref("smart_construction_core.group_sc_cap_finance_user")
        finance_mgr_group = self.env.ref("smart_construction_core.group_sc_cap_finance_manager")
        fin_user = self.env["res.users"].with_context(no_reset_password=True).create({
            "name": "Fin Overpay",
            "login": "fin_overpay",
            "company_id": company.id,
            "company_ids": [(6, 0, [company.id])],
            "groups_id": [(6, 0, [finance_group.id])],
            "email": "fin+overpay@test.com",
        })
        fin_mgr = self.env["res.users"].with_context(no_reset_password=True).create({
            "name": "FinMgr Overpay",
            "login": "finmgr_overpay",
            "company_id": company.id,
            "company_ids": [(6, 0, [company.id])],
            "groups_id": [(6, 0, [finance_mgr_group.id])],
            "email": "finmgr+overpay@test.com",
        })
        # 第一笔 80 正常通过
        pr1 = self.env["payment.request"].sudo().create(
            {
                "name": "PR-1",
                "type": "pay",
                "project_id": project.id,
                "partner_id": partner.id,
                "contract_id": contract.id,
                "settlement_id": settle.id,
                "amount": 80,
                "state": "draft",
            }
        )
        pr1.with_user(fin_user).action_submit()
        pr1.with_user(fin_mgr).action_approve()
        self.assertIn(pr1.state, ("approve", "approved"))

        # 第二笔超付（结算剩余 20，尝试付款 30），应阻断
        pr2 = self.env["payment.request"].sudo().create(
            {
                "name": "PR-2",
                "type": "pay",
                "project_id": project.id,
                "partner_id": partner.id,
                "contract_id": contract.id,
                "settlement_id": settle.id,
                "amount": 30,
                "state": "draft",
            }
        )
        with self.assertRaises(UserError):
            pr2.with_user(fin_user).action_submit()

    def test_payment_request_paid_payable_consistent(self):
        """口径一致性：已付/可付/风险/validator 同源。"""
        project = self.env["project.project"].create({"name": "PaidPayable Project"})
        partner = self.env["res.partner"].create({"name": "PaidPayable Vendor"})
        contract = self.env["construction.contract"].create(
            {"subject": "PaidPayable Contract", "type": "in", "project_id": project.id, "partner_id": partner.id}
        )
        product = self.env["product.product"].create(
            {
                "name": "PaidPayable Product",
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
                            "price_unit": 100,
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
                "line_ids": [(0, 0, {"name": "Settlement Line", "qty": 1, "price_unit": 100})],
                "state": "approve",
            }
        )
        company = self.env.ref("base.main_company")
        finance_group = self.env.ref("smart_construction_core.group_sc_cap_finance_user")
        finance_mgr_group = self.env.ref("smart_construction_core.group_sc_cap_finance_manager")
        fin_user = self.env["res.users"].with_context(no_reset_password=True).create({
            "name": "Fin PaidPayable",
            "login": "fin_paidpayable",
            "company_id": company.id,
            "company_ids": [(6, 0, [company.id])],
            "groups_id": [(6, 0, [finance_group.id])],
            "email": "fin+paidpayable@test.com",
        })
        fin_mgr = self.env["res.users"].with_context(no_reset_password=True).create({
            "name": "FinMgr PaidPayable",
            "login": "finmgr_paidpayable",
            "company_id": company.id,
            "company_ids": [(6, 0, [company.id])],
            "groups_id": [(6, 0, [finance_mgr_group.id])],
            "email": "finmgr+paidpayable@test.com",
        })

        # 第一笔 80 提交+审批，计入已付
        pr1 = self.env["payment.request"].sudo().create(
            {
                "name": "PR-PP-1",
                "type": "pay",
                "project_id": project.id,
                "partner_id": partner.id,
                "contract_id": contract.id,
                "settlement_id": settle.id,
                "amount": 80,
                "state": "draft",
            }
        )
        pr1.with_user(fin_user).action_submit()
        pr1.with_user(fin_mgr).action_approve()

        settle.invalidate_recordset()
        self.assertEqual(settle.amount_paid, 80)
        self.assertEqual(settle.amount_payable, 20)

        # 第二笔 30（超付），风险标记 + validator 报错
        pr2 = self.env["payment.request"].sudo().create(
            {
                "name": "PR-PP-2",
                "type": "pay",
                "project_id": project.id,
                "partner_id": partner.id,
                "contract_id": contract.id,
                "settlement_id": settle.id,
                "amount": 30,
                "state": "draft",
            }
        )
        self.assertTrue(pr2.is_overpay_risk)
        with self.assertRaises(UserError):
            self.env["sc.data.validator"].validate_or_raise(
                scope={
                    "res_model": "payment.request",
                    "res_ids": [pr2.id],
                    "project_id": pr2.project_id.id,
                    "company_id": pr2.company_id.id,
                }
            )

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
