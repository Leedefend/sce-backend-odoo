# -*- coding: utf-8 -*-

from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase, tagged

from odoo.addons.smart_construction_core.services.project_decision_engine_service import (
    ProjectDecisionEngineService,
)


@tagged("sc_smoke", "evidence_production_backend")
class TestEvidenceProductionBackend(TransactionCase):
    def setUp(self):
        super().setUp()
        self.project = self.env["project.project"].create(
            {
                "name": "Evidence Production Project",
                "manager_id": self.env.user.id,
                "user_id": self.env.user.id,
                "lifecycle_state": "in_progress",
            }
        )
        self.partner = self.env["res.partner"].create({"name": "Evidence Partner"})
        self.cost_code = self.env["project.cost.code"].search([], limit=1)
        if not self.cost_code:
            self.cost_code = self.env["project.cost.code"].create(
                {
                    "name": "Evidence Cost Code",
                    "code": "EV-001",
                    "type": "other",
                }
            )

    def test_decision_engine_uses_evidence_summary(self):
        self.env["project.cost.ledger"].create(
            {
                "project_id": self.project.id,
                "cost_code_id": self.cost_code.id,
                "amount": 100.0,
            }
        )
        payment = self.env["payment.request"].create(
            {
                "project_id": self.project.id,
                "partner_id": self.partner.id,
                "amount": 60.0,
                "type": "pay",
            }
        )
        decision_service = ProjectDecisionEngineService(self.env)
        before = decision_service.decide(self.project)
        self.assertEqual(before.get("primary_action_key"), "settlement_enter")

        evidence = self.env["sc.business.evidence"].sudo().search(
            [
                ("source_model", "=", "payment.request"),
                ("source_id", "=", payment.id),
                ("evidence_type", "=", "payment"),
            ],
            limit=1,
        )
        self.assertTrue(evidence)
        evidence.with_context(allow_evidence_mutation=True).unlink()

        after_delete = decision_service.decide(self.project)
        self.assertEqual(after_delete.get("primary_action_key"), "payment_enter")

        self.env["sc.evidence.builder"].build(payment, event_code="test_rebuild_payment")
        after_rebuild = decision_service.decide(self.project)
        self.assertEqual(after_rebuild.get("primary_action_key"), "settlement_enter")

    def test_business_evidence_is_immutable(self):
        payment = self.env["payment.request"].create(
            {
                "project_id": self.project.id,
                "partner_id": self.partner.id,
                "amount": 88.0,
                "type": "pay",
            }
        )
        evidence = self.env["sc.business.evidence"].sudo().search(
            [
                ("source_model", "=", "payment.request"),
                ("source_id", "=", payment.id),
                ("evidence_type", "=", "payment"),
            ],
            limit=1,
        )
        self.assertTrue(evidence)
        with self.assertRaises(UserError):
            evidence.write({"name": "tampered"})
        with self.assertRaises(UserError):
            evidence.unlink()
