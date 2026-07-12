# -*- coding: utf-8 -*-
import base64

from odoo import fields
from odoo.exceptions import AccessError
from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install", "sc_gate", "e2e_fixed_journey")
class TestE2EFixedJourneys(TransactionCase):
    def setUp(self):
        super().setUp()
        self.company = self.env.ref("base.main_company")
        self.uom_unit = self.env.ref("uom.product_uom_unit")
        self.cost_user = self._role_user(
            "e2e_cost_user",
            [
                "smart_construction_core.group_sc_cap_cost_user",
            ],
        )
        self.project_manager = self._role_user(
            "e2e_project_manager",
            [
                "smart_construction_core.group_sc_cap_project_manager",
                "smart_construction_core.group_sc_cap_cost_user",
            ],
        )
        self.settlement_user = self._role_user(
            "e2e_settlement_user",
            [
                "smart_construction_core.group_sc_cap_project_read",
                "smart_construction_core.group_sc_cap_contract_read",
                "smart_construction_core.group_sc_cap_settlement_user",
                "purchase.group_purchase_user",
            ],
        )
        self.settlement_manager = self._role_user(
            "e2e_settlement_manager",
            [
                "smart_construction_core.group_sc_cap_project_manager",
                "smart_construction_core.group_sc_cap_contract_read",
                "smart_construction_core.group_sc_cap_settlement_manager",
                "purchase.group_purchase_user",
            ],
        )
        self.finance_user = self._role_user(
            "e2e_finance_user",
            [
                "smart_construction_core.group_sc_cap_project_read",
                "smart_construction_core.group_sc_cap_contract_read",
                "smart_construction_core.group_sc_cap_finance_user",
            ],
        )
        self.ordinary_member = self._role_user(
            "e2e_ordinary_member",
            [
                "smart_construction_core.group_sc_cap_project_read",
            ],
        )

    def _role_user(self, login, xmlids):
        groups = self.env["res.groups"].browse([self.env.ref(xmlid).id for xmlid in xmlids])
        return (
            self.env["res.users"]
            .with_context(no_reset_password=True)
            .create(
                {
                    "name": login.replace("_", " ").title(),
                    "login": "%s@example.com" % login,
                    "email": "%s@example.com" % login,
                    "company_id": self.company.id,
                    "company_ids": [(6, 0, [self.company.id])],
                    "groups_id": [(6, 0, groups.ids)],
                }
            )
        )

    def _project(self, name, manager=None, followers=None):
        manager = manager or self.env.user
        followers = followers or []
        project = self.env["project.project"].create(
            {
                "name": name,
                "user_id": manager.id,
                "manager_id": manager.id,
                "company_id": self.company.id,
                "privacy_visibility": "followers",
            }
        )
        if followers:
            project.message_subscribe(partner_ids=[user.partner_id.id for user in followers])
        return project

    def _project_as_manager(self, name):
        return self.env["project.project"].create(
            {
                "name": name,
                "user_id": self.project_manager.id,
                "manager_id": self.project_manager.id,
                "company_id": self.company.id,
                "privacy_visibility": "followers",
            }
        )

    def _partner(self, name):
        return self.env["res.partner"].create({"name": name})

    def _tax(self, name="E2E Fixed VAT"):
        existing = self.env["account.tax"].search(
            [
                ("name", "=", name),
                ("company_id", "=", self.company.id),
                ("type_tax_use", "=", "purchase"),
            ],
            limit=1,
        )
        if existing:
            return existing
        return self.env["account.tax"].create(
            {
                "name": name,
                "amount": 0.0,
                "amount_type": "percent",
                "type_tax_use": "purchase",
                "price_include": False,
                "company_id": self.company.id,
            }
        )

    def _contract(self, project, partner):
        return self.env["construction.contract"].create(
            {
                "subject": "E2E Fixed Contract",
                "type": "in",
                "project_id": project.id,
                "partner_id": partner.id,
                "company_id": self.company.id,
                "currency_id": self.company.currency_id.id,
                "tax_id": self._tax().id,
            }
        )

    def _purchase_order(self, partner, amount):
        product = self.env["product.product"].sudo().create(
            {
                "name": "E2E Fixed Service",
                "type": "service",
                "uom_id": self.uom_unit.id,
                "uom_po_id": self.uom_unit.id,
            }
        )
        return self.env["purchase.order"].create(
            {
                "partner_id": partner.id,
                "company_id": self.company.id,
                "currency_id": self.company.currency_id.id,
                "state": "purchase",
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "name": product.name,
                            "product_id": product.id,
                            "product_qty": 1.0,
                            "product_uom": self.uom_unit.id,
                            "price_unit": amount,
                            "date_planned": fields.Datetime.now(),
                        },
                    )
                ],
            }
        )

    def _payment_request(self, project, partner, contract, amount, user=None):
        env = self.env(user=user) if user else self.env
        return env["payment.request"].create(
            {
                "project_id": project.id,
                "partner_id": partner.id,
                "contract_id": contract.id,
                "type": "pay",
                "amount": amount,
                "currency_id": self.company.currency_id.id,
            }
        )

    def _import_fixed_boq(self, project, user=None):
        env = self.env(user=user) if user else self.env
        csv_content = "\n".join(
            [
                "清单编码,清单名称,单位,工程量,综合单价,合价",
                "010101001001,土方开挖,%s,2,100,200" % self.uom_unit.name,
                "010101001002,土方回填,%s,3,80,240" % self.uom_unit.name,
            ]
        )
        wizard = env["project.boq.import.wizard"].create(
            {
                "project_id": project.id,
                "section_type": "building",
                "boq_category": "boq",
                "single_name": "固定单项工程",
                "unit_name": "固定单位工程",
                "source_type": "contract",
                "version": "E2E-FIXED",
                "clear_mode": "append",
                "file": base64.b64encode(csv_content.encode("utf-8")),
                "filename": "fixed_boq.csv",
            }
        )
        action = wizard.action_import()
        self.assertEqual(action["res_model"], "project.boq.line")
        lines = env["project.boq.line"].search(
            [("project_id", "=", project.id), ("version", "=", "E2E-FIXED")]
        )
        self.assertTrue(lines, "role user must be able to read imported BOQ lines")
        return lines

    def test_e2e_02_boq_import_fixed_data(self):
        project = self._project(
            "E2E-02 BOQ Import",
            manager=self.project_manager,
            followers=[self.cost_user],
        )

        lines = self._import_fixed_boq(project, user=self.cost_user)

        self.assertEqual(len(lines), 2)
        self.assertEqual(set(lines.mapped("code")), {"010101001001", "010101001002"})
        self.assertAlmostEqual(sum(lines.mapped("quantity")), 5.0)
        self.assertAlmostEqual(sum(lines.mapped("amount")), 440.0)
        project.invalidate_recordset()
        self.assertTrue(project.boq_imported)
        self.assertEqual(project.boq_status, "imported")
        self.assertTrue(
            self.cost_user.has_group("smart_construction_core.group_sc_cap_cost_user")
        )

    def test_e2e_03_boq_generates_wbs_and_tasks(self):
        project = self._project(
            "E2E-03 BOQ To Task",
            manager=self.project_manager,
            followers=[self.cost_user],
        )
        lines = self._import_fixed_boq(project, user=self.cost_user)

        manager_env = self.env(user=self.project_manager)
        wizard = manager_env["project.task.from.boq.wizard"].create(
            {
                "project_id": project.id,
                "group_mode": "code6",
                "overwrite": True,
            }
        )
        action = wizard.action_generate_tasks()

        self.assertEqual(action["res_model"], "project.task")
        tasks = manager_env["project.task"].search(
            [("project_id", "=", project.id), ("boq_generated", "=", True)]
        )
        self.assertEqual(len(tasks), 1)
        task = tasks[0]
        self.assertEqual(task.boq_group_key, "010101")
        self.assertEqual(set(task.boq_line_ids.ids), set(lines.ids))
        self.assertAlmostEqual(task.boq_quantity_total, 5.0)
        self.assertAlmostEqual(task.boq_amount_total, 440.0)
        self.assertTrue(lines.mapped("structure_id"))
        project.invalidate_recordset()
        self.assertTrue(project.wbs_ready)
        self.assertTrue(
            self.project_manager.has_group("smart_construction_core.group_sc_cap_project_manager")
        )

    def test_e2e_06_finance_user_starts_payment_request_fixed_data(self):
        project = self._project(
            "E2E-06 Payment Request",
            manager=self.project_manager,
            followers=[self.finance_user],
        )
        partner = self._partner("E2E Payment Supplier")
        contract = self._contract(project, partner)

        request = self._payment_request(
            project,
            partner,
            contract,
            360.0,
            user=self.finance_user,
        )

        self.assertEqual(request.state, "draft")
        self.assertEqual(request.project_id.id, project.id)
        self.assertEqual(request.contract_id.id, contract.id)
        self.assertAlmostEqual(request.amount, 360.0)
        self.assertTrue(
            self.finance_user.has_group("smart_construction_core.group_sc_cap_finance_user")
        )

    def test_e2e_10_project_and_payment_cross_project_denial_fixed_data(self):
        own_project = self._project(
            "E2E-10 Own Project",
            manager=self.project_manager,
            followers=[self.ordinary_member, self.finance_user],
        )
        other_project = self._project(
            "E2E-10 Other Project",
            manager=self.project_manager,
        )
        own_partner = self._partner("E2E-10 Own Supplier")
        other_partner = self._partner("E2E-10 Other Supplier")
        own_contract = self._contract(own_project, own_partner)
        other_contract = self._contract(other_project, other_partner)
        own_request = self._payment_request(own_project, own_partner, own_contract, 100.0)
        other_request = self._payment_request(other_project, other_partner, other_contract, 200.0)

        member_projects = self.env(user=self.ordinary_member)["project.project"].search(
            [("id", "in", [own_project.id, other_project.id])]
        )
        self.assertEqual(member_projects.ids, [own_project.id])
        with self.assertRaises(AccessError):
            self.env(user=self.ordinary_member)["project.project"].browse(other_project.id).read(
                ["name"]
            )

        finance_requests = self.env(user=self.finance_user)["payment.request"].search(
            [("id", "in", [own_request.id, other_request.id])]
        )
        self.assertEqual(finance_requests.ids, [own_request.id])
        with self.assertRaises(AccessError):
            self.env(user=self.finance_user)["payment.request"].browse(other_request.id).read(
                ["name"]
            )

    def test_e2e_08_settlement_submit_approve_done_fixed_data(self):
        project = self._project(
            "E2E-08 Settlement Approval",
            manager=self.project_manager,
            followers=[self.settlement_user],
        )
        partner = self._partner("E2E Settlement Supplier")
        contract = self._contract(project, partner)
        purchase_order = self._purchase_order(partner, 1200.0)
        settlement_env = self.env(user=self.settlement_user)
        settlement = settlement_env["sc.settlement.order"].create(
            {
                "project_id": project.id,
                "partner_id": partner.id,
                "contract_id": contract.id,
                "settlement_type": "out",
                "purchase_order_ids": [(6, 0, purchase_order.ids)],
                "company_id": self.company.id,
                "currency_id": self.company.currency_id.id,
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "name": "E2E Settlement Line",
                            "contract_id": contract.id,
                            "qty": 1.0,
                            "price_unit": 1200.0,
                        },
                    )
                ],
            }
        )

        settlement.action_submit()
        settlement.invalidate_recordset()
        self.assertEqual(settlement.state, "submit")
        self.assertTrue(settlement.review_ids)
        self.env.cr.execute(
            "UPDATE sc_settlement_order SET validation_status=%s WHERE id=%s",
            ("validated", settlement.id),
        )
        settlement.invalidate_recordset()
        manager_settlement = self.env(user=self.settlement_manager)["sc.settlement.order"].browse(
            settlement.id
        )
        manager_settlement.action_on_tier_approved()
        manager_settlement.invalidate_recordset()
        self.assertEqual(manager_settlement.state, "approve")
        manager_settlement.action_done()
        manager_settlement.invalidate_recordset()
        self.assertEqual(manager_settlement.state, "done")
        self.assertAlmostEqual(manager_settlement.amount_total, 1200.0)
        self.assertTrue(
            self.settlement_user.has_group("smart_construction_core.group_sc_cap_settlement_user")
        )
        self.assertTrue(
            self.settlement_manager.has_group(
                "smart_construction_core.group_sc_cap_settlement_manager"
            )
        )
