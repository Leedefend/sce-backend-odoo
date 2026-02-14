# -*- coding: utf-8 -*-

from odoo.tests.common import TransactionCase, tagged

from odoo.addons.smart_construction_core.handlers.payment_request_available_actions import (
    PaymentRequestAvailableActionsHandler,
)
from odoo.addons.smart_core.handlers.reason_codes import (
    REASON_BUSINESS_RULE_FAILED,
    REASON_MISSING_PARAMS,
    REASON_NOT_FOUND,
    REASON_OK,
)


@tagged("sc_smoke", "payment_request_available_actions_backend")
class TestPaymentRequestAvailableActionsBackend(TransactionCase):
    def _create_payment_request_minimal(self):
        project = self.env["project.project"].create({"name": "Action Matrix Project"})
        partner = self.env["res.partner"].create({"name": "Action Matrix Partner"})
        return self.env["payment.request"].sudo().create(
            {
                "name": "INTENT-ACTIONS-PR-001",
                "type": "pay",
                "project_id": project.id,
                "partner_id": partner.id,
                "amount": 100,
                "state": "draft",
            }
        )

    def test_available_actions_missing_id(self):
        handler = PaymentRequestAvailableActionsHandler(self.env, payload={})
        result = handler.handle({"request_id": "req-pr-actions-missing"})
        self.assertFalse(result.get("ok"))
        self.assertEqual(int(result.get("code") or 0), 400)
        self.assertEqual(((result.get("error") or {}).get("reason_code")), REASON_MISSING_PARAMS)

    def test_available_actions_not_found(self):
        handler = PaymentRequestAvailableActionsHandler(self.env, payload={})
        result = handler.handle({"id": 999999999})
        self.assertFalse(result.get("ok"))
        self.assertEqual(int(result.get("code") or 0), 404)
        self.assertEqual(((result.get("error") or {}).get("reason_code")), REASON_NOT_FOUND)

    def test_available_actions_success_shape(self):
        payment = self._create_payment_request_minimal()
        handler = PaymentRequestAvailableActionsHandler(self.env, payload={})
        result = handler.handle({"id": payment.id})
        self.assertTrue(result.get("ok"))
        data = result.get("data") or {}
        self.assertEqual(data.get("reason_code"), REASON_OK)
        self.assertEqual(data.get("primary_action_key"), "reject")
        actions = data.get("actions") or []
        keys = {str(item.get("key") or "") for item in actions if isinstance(item, dict)}
        self.assertEqual(keys, {"submit", "approve", "reject", "done"})
        by_key = {str(item.get("key") or ""): item for item in actions if isinstance(item, dict)}
        submit = by_key.get("submit") or {}
        self.assertEqual(submit.get("execute_intent"), "payment.request.execute")
        self.assertEqual((submit.get("execute_params") or {}).get("id"), payment.id)
        self.assertEqual((submit.get("execute_params") or {}).get("action"), "submit")
        self.assertTrue(bool(submit.get("idempotency_required")))
        self.assertEqual(submit.get("reason_code"), "PAYMENT_ATTACHMENTS_REQUIRED")
        self.assertFalse(bool(submit.get("allowed")))
        self.assertEqual(submit.get("current_state"), "draft")
        self.assertEqual(submit.get("next_state_hint"), "submit")
        self.assertTrue(bool(submit.get("allowed_by_state")))
        self.assertTrue(bool(submit.get("allowed_by_method")))
        self.assertFalse(bool(submit.get("allowed_by_precheck")))
        self.assertTrue(str(submit.get("blocked_message") or "").strip())
        self.assertTrue(str(submit.get("suggested_action") or "").strip())
        self.assertEqual(submit.get("required_role_key"), "finance")
        self.assertEqual(submit.get("required_role_label"), "财务")
        self.assertEqual(submit.get("required_group_xmlid"), "smart_construction_custom.group_sc_role_finance")
        self.assertTrue(str(submit.get("handoff_hint") or "").strip())
        self.assertIsInstance(submit.get("actor_matches_required_role"), bool)
        self.assertIsInstance(submit.get("handoff_required"), bool)
        self.assertEqual(int(submit.get("delivery_priority") or 0), 10)
        reject = by_key.get("reject") or {}
        self.assertEqual(reject.get("reason_code"), REASON_BUSINESS_RULE_FAILED)
        self.assertTrue(bool(reject.get("requires_reason")))
        self.assertEqual(reject.get("required_role_key"), "executive")
        self.assertEqual(reject.get("required_role_label"), "管理层")
        self.assertEqual(reject.get("required_group_xmlid"), "smart_construction_custom.group_sc_role_executive")
        self.assertIsInstance(reject.get("actor_matches_required_role"), bool)
        self.assertIsInstance(reject.get("handoff_required"), bool)
        self.assertEqual(int(reject.get("delivery_priority") or 0), 30)
        submit = next(item for item in actions if item.get("key") == "submit")
        self.assertFalse(bool(submit.get("allowed")))
        reject = next(item for item in actions if item.get("key") == "reject")
        self.assertIn("reason", list(reject.get("required_params") or []))
