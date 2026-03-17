# -*- coding: utf-8 -*-

from odoo.tests.common import TransactionCase, tagged

from odoo.addons.smart_construction_core.handlers.risk_action_execute import RiskActionExecuteHandler
from odoo.addons.smart_core.handlers.reason_codes import REASON_MISSING_PARAMS, REASON_OK


@tagged("sc_smoke", "risk_action_execute_backend")
class TestRiskActionExecuteBackend(TransactionCase):
    def _create_project(self):
        return self.env["project.project"].create({"name": "Risk Exec Project"})

    def test_risk_action_execute_create_and_claim(self):
        project = self._create_project()
        handler = RiskActionExecuteHandler(self.env, payload={})
        result = handler.handle(
            {
                "action": "claim",
                "project_id": project.id,
                "name": "关键路径阻塞",
                "risk_level": "high",
                "note": "需要立即协调",
            }
        )
        self.assertTrue(result.get("ok"))
        data = result.get("data") or {}
        self.assertEqual(data.get("reason_code"), REASON_OK)
        risk_action = data.get("risk_action") or {}
        self.assertEqual(risk_action.get("state"), "claimed")
        self.assertEqual(int(risk_action.get("project_id") or 0), project.id)

    def test_risk_action_execute_missing_params(self):
        handler = RiskActionExecuteHandler(self.env, payload={})
        result = handler.handle({"action": "claim"})
        self.assertFalse(result.get("ok"))
        self.assertEqual(int(result.get("code") or 0), 400)
        error = result.get("error") or {}
        self.assertEqual(error.get("reason_code"), REASON_MISSING_PARAMS)

    def test_risk_action_execute_escalate_and_close(self):
        project = self._create_project()
        action = self.env["project.risk.action"].create(
            {
                "name": "回款超期",
                "project_id": project.id,
                "state": "open",
                "risk_level": "medium",
            }
        )
        handler = RiskActionExecuteHandler(self.env, payload={})
        escalate = handler.handle({"action": "escalate", "risk_action_id": action.id, "note": "升级财务关注"})
        self.assertTrue(escalate.get("ok"))
        action.invalidate_recordset(["state", "note"])
        self.assertEqual(action.state, "escalated")

        close = handler.handle({"action": "close", "risk_action_id": action.id, "note": "已处置"})
        self.assertTrue(close.get("ok"))
        action.invalidate_recordset(["state", "note"])
        self.assertEqual(action.state, "closed")
