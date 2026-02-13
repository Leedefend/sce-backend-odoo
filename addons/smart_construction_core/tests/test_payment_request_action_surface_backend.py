# -*- coding: utf-8 -*-

from unittest.mock import patch

from odoo.tests.common import TransactionCase, tagged

from odoo.addons.smart_construction_core.handlers.payment_request_available_actions import (
    PaymentRequestAvailableActionsHandler,
)
from odoo.addons.smart_construction_core.handlers.payment_request_execute import (
    PaymentRequestExecuteHandler,
)
from odoo.addons.smart_core.handlers.reason_codes import (
    REASON_BUSINESS_RULE_FAILED,
    REASON_MISSING_PARAMS,
    REASON_NOT_FOUND,
    REASON_OK,
    REASON_UNSUPPORTED_BUTTON_TYPE,
)


@tagged("sc_smoke", "payment_request_action_surface_backend")
class TestPaymentRequestActionSurfaceBackend(TransactionCase):
    def _create_payment_request_minimal(self):
        project = self.env["project.project"].create({"name": "Action Surface Project"})
        partner = self.env["res.partner"].create({"name": "Action Surface Partner"})
        return self.env["payment.request"].sudo().create(
            {
                "name": "INTENT-ACTION-SURFACE-001",
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
        self.assertFalse(bool(submit.get("requires_reason")))
        self.assertEqual(submit.get("current_state"), "draft")
        self.assertEqual(submit.get("next_state_hint"), "submit")
        self.assertTrue(str(submit.get("blocked_message") or "").strip())
        self.assertTrue(str(submit.get("suggested_action") or "").strip())
        reject = by_key.get("reject") or {}
        self.assertEqual(reject.get("reason_code"), REASON_BUSINESS_RULE_FAILED)
        self.assertTrue(bool(reject.get("requires_reason")))

    def test_execute_missing_action(self):
        payment = self._create_payment_request_minimal()
        handler = PaymentRequestExecuteHandler(self.env, payload={})
        result = handler.handle({"id": payment.id})
        self.assertFalse(result.get("ok"))
        self.assertEqual(int(result.get("code") or 0), 400)
        self.assertEqual(((result.get("error") or {}).get("reason_code")), REASON_MISSING_PARAMS)

    def test_execute_unsupported_action(self):
        payment = self._create_payment_request_minimal()
        handler = PaymentRequestExecuteHandler(self.env, payload={})
        result = handler.handle({"id": payment.id, "action": "archive"})
        self.assertFalse(result.get("ok"))
        self.assertEqual(int(result.get("code") or 0), 400)
        self.assertEqual(((result.get("error") or {}).get("reason_code")), REASON_UNSUPPORTED_BUTTON_TYPE)

    def test_execute_submit_success(self):
        payment = self._create_payment_request_minimal()
        handler = PaymentRequestExecuteHandler(self.env, payload={})
        with patch(
            "odoo.addons.smart_construction_core.models.core.payment_request.PaymentRequest.action_submit",
            autospec=True,
            return_value=None,
        ):
            result = handler.handle(
                {
                    "id": payment.id,
                    "action": "submit",
                    "request_id": "req-pr-exec-submit",
                }
            )
        self.assertTrue(result.get("ok"))
        data = result.get("data") or {}
        self.assertEqual(data.get("reason_code"), REASON_OK)
        self.assertEqual(data.get("intent_action"), "submit")
