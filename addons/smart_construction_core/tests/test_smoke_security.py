# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install", "smoke", "sc_smoke", "smoke_security")
class TestSmokeSecurity(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create({"name": "Smoke Partner"})
        cls.project = cls.env["project.project"].create({"name": "Smoke Project"})
        cls.product = cls.env["product.product"].create(
            {
                "name": "Smoke Material",
                "type": "product",
                "uom_id": cls.env.ref("uom.product_uom_unit").id,
                "uom_po_id": cls.env.ref("uom.product_uom_unit").id,
            }
        )
        cls.contract = cls.env["construction.contract"].create(
            {
                "subject": "Smoke Contract",
                "type": "in",
                "project_id": cls.project.id,
                "partner_id": cls.partner.id,
            }
        )
        # 测试内创建用户与组，避免依赖 demo xmlid
        finance_group = cls.env.ref("smart_construction_core.group_sc_cap_finance_user")
        material_group = cls.env.ref("smart_construction_core.group_sc_cap_material_manager")
        admin_groups = [
            cls.env.ref("smart_construction_core.group_sc_cap_finance_manager"),
            cls.env.ref("smart_construction_core.group_sc_cap_settlement_manager"),
        ]
        company = cls.env.ref("base.main_company")
        cls.finance_user = cls.env["res.users"].with_context(no_reset_password=True).create({
            "name": "Smoke Finance",
            "login": "smoke_fin",
            "company_id": company.id,
            "company_ids": [(6, 0, [company.id])],
            "groups_id": [(6, 0, [finance_group.id])],
        })
        cls.material_manager = cls.env["res.users"].with_context(no_reset_password=True).create({
            "name": "Smoke Material",
            "login": "smoke_material",
            "company_id": company.id,
            "company_ids": [(6, 0, [company.id])],
            "groups_id": [(6, 0, [material_group.id])],
        })
        cls.admin_user = cls.env["res.users"].with_context(no_reset_password=True).create({
            "name": "Smoke Admin",
            "login": "smoke_admin",
            "company_id": company.id,
            "company_ids": [(6, 0, [company.id])],
            "groups_id": [(6, 0, [g.id for g in admin_groups])],
        })

    def test_finance_user_can_create_payment_request(self):
        request = self.env["payment.request"].with_user(self.finance_user).create(
            {
                "project_id": self.project.id,
                "partner_id": self.partner.id,
                "amount": 100,
                "type": "pay",
                "contract_id": self.contract.id,
            }
        )
        self.assertEqual(request.project_id, self.project)
        self.assertEqual(
            self.contract.with_user(self.finance_user).subject,
            self.contract.subject,
        )

    def test_material_manager_can_create_material_plan(self):
        plan = self.env["project.material.plan"].with_user(self.material_manager).create(
            {
                "project_id": self.project.id,
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "quantity": 1,
                            "uom_id": self.product.uom_po_id.id,
                        },
                    )
                ],
            }
        )
        self.assertEqual(plan.project_id, self.project)
        self.assertEqual(plan.state, "draft")

    def test_admin_can_create_settlement_order(self):
        settlement = self.env["sc.settlement.order"].with_user(self.admin_user).create(
            {
                "project_id": self.project.id,
                "partner_id": self.partner.id,
                "contract_id": self.contract.id,
                "line_ids": [(0, 0, {"name": "Line", "qty": 1, "price_unit": 50})],
            }
        )
        self.assertEqual(settlement.partner_id, self.partner)
        self.assertGreater(settlement.amount_total, 0)
