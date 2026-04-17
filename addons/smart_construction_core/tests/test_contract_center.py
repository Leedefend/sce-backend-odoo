# -*- coding: utf-8 -*-
from lxml import etree

from odoo.tests import TransactionCase
from odoo.tests.common import tagged


@tagged("post_install", "-at_install", "sc_regression", "contract")
class TestConstructionContract(TransactionCase):
    def _ensure_tax_group(self):
        country = self.env.ref("base.cn", raise_if_not_found=False)
        company = self.env.ref("base.main_company")
        group = self.env["account.tax.group"].search(
            [("name", "=", "增值税"), ("company_id", "=", company.id)], limit=1
        )
        if not group:
            vals = {
                "name": "增值税",
                "sequence": 10,
                "company_id": company.id,
            }
            if country:
                vals["country_id"] = country.id
            group = self.env["account.tax.group"].create(vals)
        return group

    def _create_test_tax(self, name, amount, tax_use):
        company = self.env.ref("base.main_company")
        country = self.env.ref("base.cn", raise_if_not_found=False)
        tax_group = self._ensure_tax_group()
        existing = self.env["account.tax"].search(
            [
                ("name", "=", name),
                ("company_id", "=", company.id),
            ],
            limit=1,
        )
        if existing:
            return existing
        vals = {
            "name": name,
            "amount_type": "percent",
            "amount": amount,
            "type_tax_use": tax_use,
            "tax_group_id": tax_group.id,
            "company_id": company.id,
            "active": True,
        }
        if country:
            vals["country_id"] = country.id
        return self.env["account.tax"].create(vals)

    def setUp(self):
        super().setUp()
        self.project = self.env["project.project"].create({"name": "合同中心测试项目"})
        self.partner = self.env["res.partner"].create({"name": "测试客户"})
        self.uom_unit = self.env.ref("uom.product_uom_unit")
        self.wbs = self.env["construction.work.breakdown"].create({
            "name": "结构工程",
            "code": "WBS-TEST",
            "project_id": self.project.id,
        })
        self.tax_sale_9 = self._create_test_tax("销项VAT 9%", 9, "sale")
        self.budget = self.env["project.budget"].create({
            "name": "控制版",
            "project_id": self.project.id,
        })
        self.boq_line_1 = self.env["project.budget.boq.line"].create({
            "budget_id": self.budget.id,
            "name": "主体结构",
            "wbs_id": self.wbs.id,
            "uom_id": self.uom_unit.id,
            "qty_bidded": 10,
            "price_bidded": 1000.0,
        })
        self.boq_line_2 = self.env["project.budget.boq.line"].create({
            "budget_id": self.budget.id,
            "name": "装修工程",
            "wbs_id": self.wbs.id,
            "uom_id": self.uom_unit.id,
            "qty_bidded": 5,
            "price_bidded": 500.0,
        })

    def _create_user(self, login, group_xmlids):
        company = self.env.ref("base.main_company")
        groups = [(6, 0, [self.env.ref(xmlid).id for xmlid in group_xmlids])]
        return self.env["res.users"].with_context(no_reset_password=True).create(
            {
                "name": login,
                "login": login,
                "email": f"{login}@example.com",
                "company_id": company.id,
                "company_ids": [(6, 0, [company.id])],
                "groups_id": groups,
            }
        )

    @tagged("post_install", "-at_install", "sc_regression", "contract")
    def test_contract_state_and_amount(self):
        contract = self.env["construction.contract"].create(
            {
                "type": "out",
                "subject": "测试合同",
                "project_id": self.project.id,
                "partner_id": self.partner.id,
                "tax_id": self.tax_sale_9.id,
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "boq_line_id": self.boq_line_1.id,
                            "qty_contract": 10,
                            "price_contract": 1000.0,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "boq_line_id": self.boq_line_2.id,
                            "qty_contract": 5,
                            "price_contract": 500.0,
                        },
                    ),
                ],
            }
        )
        self.assertNotEqual(contract.name, "新建")
        self.assertEqual(contract.line_amount_total, 12500.0)
        self.assertEqual(contract.amount_untaxed, 12500.0)
        self.assertAlmostEqual(contract.amount_tax, 1125.0)
        self.assertAlmostEqual(contract.amount_total, 13625.0)
        contract.action_confirm()
        self.assertEqual(contract.state, "confirmed")
        contract.action_set_running()
        self.assertEqual(contract.state, "running")
        contract.action_close()
        self.assertEqual(contract.state, "closed")

    def test_contract_workflow_buttons_follow_execution_groups(self):
        contract_user = self._create_user(
            "contract_button_user",
            ["smart_construction_core.group_sc_cap_contract_user"],
        )
        finance_read = self._create_user(
            "contract_button_finance_read",
            ["smart_construction_core.group_sc_cap_finance_read"],
        )

        exec_view = (
            self.env["construction.contract"]
            .with_user(contract_user)
            .sudo(False)
            .get_view(
                self.env.ref("smart_construction_core.view_construction_contract_form").id,
                view_type="form",
            )
        )
        exec_arch = etree.fromstring(exec_view["arch"].encode())
        exec_buttons = {
            button.get("name")
            for button in exec_arch.xpath("//header/button[@type='object']")
        }
        self.assertTrue(
            {
                "action_generate_lines_from_budget",
                "action_confirm",
                "action_set_running",
                "action_close",
                "action_cancel",
                "action_reset_draft",
            }.issubset(exec_buttons)
        )

        readonly_view = self.env.ref("smart_construction_core.view_construction_contract_form")
        readonly_arch = etree.fromstring(readonly_view.arch_db.encode())
        readonly_buttons = readonly_arch.xpath("//header/button[@type='object']")
        required_groups = {
            "smart_construction_core.group_sc_cap_contract_user",
            "smart_construction_core.group_sc_cap_contract_manager",
        }
        self.assertTrue(readonly_buttons)
        for button in readonly_buttons:
            groups = {item.strip() for item in (button.get("groups") or "").split(",") if item.strip()}
            self.assertEqual(groups, required_groups)

    @tagged("post_install", "-at_install", "sc_regression", "contract")
    def test_generate_lines_from_budget(self):
        contract = self.env["construction.contract"].create(
            {
                "type": "out",
                "subject": "生成清单合同",
                "project_id": self.project.id,
                "partner_id": self.partner.id,
                "budget_id": self.budget.id,
            }
        )
        contract.action_generate_lines_from_budget()
        self.assertEqual(len(contract.line_ids), 2)
        first_line = contract.line_ids.sorted(key=lambda l: l.sequence)[0]
        self.assertEqual(first_line.boq_line_id, self.boq_line_1)
        self.assertEqual(first_line.qty_contract, 10)
        self.assertEqual(first_line.price_contract, 1000.0)
