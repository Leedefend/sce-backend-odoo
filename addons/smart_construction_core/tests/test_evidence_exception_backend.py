# -*- coding: utf-8 -*-

from odoo.tests.common import TransactionCase, tagged

from odoo.addons.smart_construction_core.handlers.risk_action_execute import RiskActionExecuteHandler


@tagged("sc_smoke", "evidence_exception_backend")
class TestEvidenceExceptionBackend(TransactionCase):
    def setUp(self):
        super().setUp()
        self.project = self.env["project.project"].create(
            {
                "name": "Evidence Exception Project",
                "manager_id": self.env.user.id,
                "user_id": self.env.user.id,
                "lifecycle_state": "in_progress",
            }
        )
        self.partner = self.env["res.partner"].create({"name": "Evidence Exception Partner"})
        self.cost_code = self.env["project.cost.code"].search([], limit=1)
        if not self.cost_code:
            self.cost_code = self.env["project.cost.code"].create(
                {
                    "name": "Evidence Exception Code",
                    "code": "EV-EX",
                    "type": "other",
                }
            )

    def _build_over_budget_signal(self):
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

    def test_high_risk_creates_exception_and_risk_action(self):
        self._build_over_budget_signal()
        analysis = self.env["sc.evidence.risk.engine"].analyze(self.project)
        self.assertGreater(int(analysis.get("risk_count") or 0), 0)

        exception = self.env["sc.evidence.exception"].search(
            [("project_id", "=", self.project.id), ("risk_code", "=", "payment_exceeds_cost")],
            limit=1,
        )
        self.assertTrue(exception)
        self.assertEqual(exception.status, "open")
        self.assertTrue(exception.risk_action_id)

    def test_risk_action_execute_updates_exception_lifecycle(self):
        self._build_over_budget_signal()
        self.env["sc.evidence.risk.engine"].analyze(self.project)
        exception = self.env["sc.evidence.exception"].search(
            [("project_id", "=", self.project.id), ("risk_code", "=", "payment_exceeds_cost")],
            limit=1,
        )
        self.assertTrue(exception)

        handler = RiskActionExecuteHandler(self.env, payload={})
        claim = handler.handle({"action": "claim", "exception_id": exception.id})
        self.assertTrue(claim.get("ok"))
        exception.invalidate_recordset(["status", "assigned_to"])
        self.assertEqual(exception.status, "processing")
        self.assertEqual(int(exception.assigned_to.id or 0), int(self.env.user.id))

        close = handler.handle({"action": "close", "exception_id": exception.id, "note": "已完成处置"})
        self.assertTrue(close.get("ok"))
        exception.invalidate_recordset(["status", "resolution_note"])
        self.assertEqual(exception.status, "resolved")
        self.assertEqual(exception.resolution_note, "已完成处置")
