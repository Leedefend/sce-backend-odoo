# -*- coding: utf-8 -*-

from unittest.mock import patch

from odoo.tests.common import TransactionCase, tagged

from odoo.addons.smart_core.handlers.scene_governance import (
    SceneGovernanceExportContractHandler,
    SceneGovernanceRollbackHandler,
    SceneGovernanceSetChannelHandler,
)


@tagged("sc_smoke", "scene_governance_backend")
class TestSceneGovernancePayloadBackend(TransactionCase):
    def test_set_channel_accepts_flat_payload(self):
        handler = SceneGovernanceSetChannelHandler(self.env, payload={})

        class _Svc:
            def set_company_channel(self, company_id, channel, reason, trace_id=None):
                return {
                    "action": "set_channel",
                    "company_id": int(company_id),
                    "to_channel": str(channel),
                    "from_channel": "stable",
                }

        with patch("odoo.addons.smart_core.handlers.scene_governance._service", return_value=_Svc()):
            result = handler.handle({"channel": "dev", "reason": "snapshot"})
        self.assertTrue(result.get("ok"))
        data = result.get("data") or {}
        self.assertEqual(data.get("action"), "set_channel")
        self.assertEqual(data.get("to_channel"), "dev")

    def test_rollback_accepts_flat_payload(self):
        handler = SceneGovernanceRollbackHandler(self.env, payload={})

        class _Svc:
            def rollback_stable(self, reason, trace_id=None):
                return {"action": "rollback", "to_channel": "stable"}

        with patch("odoo.addons.smart_core.handlers.scene_governance._service", return_value=_Svc()):
            result = handler.handle({"reason": "snapshot"})
        self.assertTrue(result.get("ok"))
        self.assertEqual((result.get("data") or {}).get("action"), "rollback")

    def test_export_contract_accepts_flat_payload(self):
        handler = SceneGovernanceExportContractHandler(self.env, payload={})

        class _Svc:
            def export_contract(self, channel, reason, trace_id=None):
                return {"action": "export_contract", "to_channel": str(channel)}

        with patch("odoo.addons.smart_core.handlers.scene_governance._service", return_value=_Svc()):
            result = handler.handle({"channel": "stable", "reason": "snapshot"})
        self.assertTrue(result.get("ok"))
        self.assertEqual((result.get("data") or {}).get("action"), "export_contract")
