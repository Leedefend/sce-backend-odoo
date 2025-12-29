# -*- coding: utf-8 -*-
from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install", "sc_smoke")
class TestContractLinkIntegrity(TransactionCase):
    def setUp(self):
        super().setUp()
        self.company = self.env.company
        self.partner = self.env["res.partner"].create({"name": "Test Partner"})
        self.project = self.env["project.project"].create(
            {"name": "Link Test Project", "company_id": self.company.id}
        )
        self.tax_sale = self.env["account.tax"].create(
            {
                "name": "Test VAT 9",
                "amount_type": "percent",
                "amount": 9.0,
                "type_tax_use": "sale",
                "company_id": self.company.id,
            }
        )
        self.contract = self.env["construction.contract"].create(
            {
                "subject": "Link Integrity Contract",
                "project_id": self.project.id,
                "partner_id": self.partner.id,
                "type": "out",
                "tax_id": self.tax_sale.id,
            }
        )
        self.env["construction.contract.line"].create(
            {
                "contract_id": self.contract.id,
                "qty_contract": 1.0,
                "price_contract": 100.0,
            }
        )
        self.contract.action_confirm()

    def test_referenced_contract_cannot_reset_or_cancel(self):
        # 创建引用单据（付款申请）
        self.env["payment.request"].create(
            {
                "project_id": self.project.id,
                "partner_id": self.partner.id,
                "contract_id": self.contract.id,
                "amount": 50.0,
                "currency_id": self.company.currency_id.id,
            }
        )
        # 被引用的合同不可重置/取消
        with self.assertRaises(UserError):
            self.contract.action_reset_draft()
        with self.assertRaises(UserError):
            self.contract.action_cancel()
