# -*- coding: utf-8 -*-
import base64

from odoo import fields
from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install", "sc_gate", "e2e_fixed_journey")
class TestE2EFixedJourneys(TransactionCase):
    def setUp(self):
        super().setUp()
        self.company = self.env.ref("base.main_company")
        self.uom_unit = self.env.ref("uom.product_uom_unit")

    def _project(self, name):
        return self.env["project.project"].create(
            {
                "name": name,
                "manager_id": self.env.user.id,
                "company_id": self.company.id,
            }
        )

    def _partner(self, name):
        return self.env["res.partner"].create({"name": name})

    def _tax(self, name="E2E Fixed VAT"):
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

    def _import_fixed_boq(self, project):
        csv_content = "\n".join(
            [
                "清单编码,清单名称,单位,工程量,综合单价,合价",
                "010101001001,土方开挖,m3,2,100,200",
                "010101001002,土方回填,m3,3,80,240",
            ]
        )
        wizard = self.env["project.boq.import.wizard"].create(
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
        return self.env["project.boq.line"].search(
            [("project_id", "=", project.id), ("version", "=", "E2E-FIXED")]
        )

    def test_e2e_02_boq_import_fixed_data(self):
        project = self._project("E2E-02 BOQ Import")

        lines = self._import_fixed_boq(project)

        self.assertEqual(len(lines), 2)
        self.assertEqual(set(lines.mapped("code")), {"010101001001", "010101001002"})
        self.assertAlmostEqual(sum(lines.mapped("quantity")), 5.0)
        self.assertAlmostEqual(sum(lines.mapped("amount")), 440.0)
        project.invalidate_recordset()
        self.assertTrue(project.boq_imported)
        self.assertEqual(project.boq_status, "imported")

    def test_e2e_03_boq_generates_wbs_and_tasks(self):
        project = self._project("E2E-03 BOQ To Task")
        lines = self._import_fixed_boq(project)

        wizard = self.env["project.task.from.boq.wizard"].create(
            {
                "project_id": project.id,
                "group_mode": "code6",
                "overwrite": True,
            }
        )
        action = wizard.action_generate_tasks()

        self.assertEqual(action["res_model"], "project.task")
        tasks = self.env["project.task"].search(
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

    def test_e2e_08_settlement_submit_approve_done_fixed_data(self):
        project = self._project("E2E-08 Settlement Approval")
        partner = self._partner("E2E Settlement Supplier")
        contract = self._contract(project, partner)
        purchase_order = self._purchase_order(partner, 1200.0)
        settlement = self.env["sc.settlement.order"].create(
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
        settlement.action_on_tier_approved()
        settlement.invalidate_recordset()
        self.assertEqual(settlement.state, "approve")
        settlement.action_done()
        settlement.invalidate_recordset()
        self.assertEqual(settlement.state, "done")
        self.assertAlmostEqual(settlement.amount_total, 1200.0)
