# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase, tagged

from odoo.addons.smart_core.controllers.intent_dispatcher import _permission_error_details
from odoo.addons.smart_core.utils.reason_codes import REASON_PERMISSION_DENIED


@tagged("post_install", "-at_install", "intent_dispatcher_permission_contract", "smart_core")
class TestIntentDispatcherPermissionErrorContract(TransactionCase):

    def test_api_data_permission_error_includes_model_and_op(self):
        details = _permission_error_details(
            "api.data",
            {"model": "construction.contract", "op": "list"},
            "Access denied",
        )
        self.assertEqual(details.get("intent"), "api.data")
        self.assertEqual(details.get("reason_code"), REASON_PERMISSION_DENIED)
        self.assertEqual(details.get("model"), "construction.contract")
        self.assertEqual(details.get("op"), "list")
        self.assertTrue(details.get("cause"))

    def test_non_api_data_permission_error_does_not_inject_model_op(self):
        details = _permission_error_details("system.init", {}, "forbidden")
        self.assertEqual(details.get("intent"), "system.init")
        self.assertEqual(details.get("reason_code"), REASON_PERMISSION_DENIED)
        self.assertNotIn("model", details)
        self.assertNotIn("op", details)

    def test_api_data_write_permission_error_infers_op_from_intent(self):
        details = _permission_error_details(
            "api.data.write",
            {"model": "project.project"},
            "forbidden",
        )
        self.assertEqual(details.get("intent"), "api.data.write")
        self.assertEqual(details.get("reason_code"), REASON_PERMISSION_DENIED)
        self.assertEqual(details.get("model"), "project.project")
        self.assertEqual(details.get("op"), "write")

    def test_api_data_batch_permission_error_uses_batch_action(self):
        details = _permission_error_details(
            "api.data.batch",
            {"model": "project.project", "action": "archive"},
            "forbidden",
        )
        self.assertEqual(details.get("intent"), "api.data.batch")
        self.assertEqual(details.get("reason_code"), REASON_PERMISSION_DENIED)
        self.assertEqual(details.get("model"), "project.project")
        self.assertEqual(details.get("op"), "batch.archive")
