# -*- coding: utf-8 -*-

from odoo.tests.common import TransactionCase, tagged


@tagged("sc_smoke", "evidence_consumption_backend")
class TestEvidenceConsumptionBackend(TransactionCase):
    def setUp(self):
        super().setUp()
        self.project = self.env["project.project"].create(
            {
                "name": "Evidence Consumption Project",
                "manager_id": self.env.user.id,
                "user_id": self.env.user.id,
                "lifecycle_state": "in_progress",
            }
        )
        self.partner = self.env["res.partner"].create({"name": "Evidence Consumption Partner"})
        self.cost_code = self.env["project.cost.code"].search([], limit=1)
        if not self.cost_code:
            self.cost_code = self.env["project.cost.code"].create(
                {
                    "name": "Evidence Consumption Code",
                    "code": "EV-CONSUME",
                    "type": "other",
                }
            )
        self.env["project.cost.ledger"].create(
            {
                "project_id": self.project.id,
                "cost_code_id": self.cost_code.id,
                "amount": 100.0,
            }
        )
        self.env["payment.request"].create(
            {
                "project_id": self.project.id,
                "partner_id": self.partner.id,
                "amount": 140.0,
                "type": "pay",
            }
        )

    def test_timeline_and_explainability_contracts(self):
        timeline = self.env["sc.evidence.timeline.service"].build_timeline("project.project", self.project.id)
        self.assertGreaterEqual(int(timeline.get("count") or 0), 2)
        self.assertTrue(timeline.get("items"))
        first_item = timeline["items"][0]
        self.assertTrue(first_item.get("trace_action"))
        self.assertTrue(first_item.get("checksum"))

        risks = self.env["sc.evidence.risk.engine"].analyze(self.project).get("risks") or []
        self.assertTrue(risks)
        explainable = [risk for risk in risks if risk.get("risk_code") == "payment_exceeds_cost"]
        self.assertTrue(explainable)
        self.assertTrue(explainable[0].get("reason"))
        self.assertTrue(explainable[0].get("evidence_refs"))
        self.assertTrue(explainable[0].get("severity"))

        decision = self.env["sc.evidence.action.engine"].decide(self.project)
        primary_action = decision.get("primary_action") or {}
        self.assertEqual(primary_action.get("action_key"), "settlement_enter")
        self.assertTrue(primary_action.get("reason"))
        self.assertTrue(primary_action.get("risk_codes"))
        self.assertTrue(primary_action.get("evidence_refs"))
