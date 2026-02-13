# -*- coding: utf-8 -*-

from unittest.mock import patch

from odoo.tests.common import TransactionCase, tagged

from odoo.addons.smart_construction_core.handlers.payment_request_approval import (
    PaymentRequestApproveHandler,
    PaymentRequestDoneHandler,
    PaymentRequestRejectHandler,
    PaymentRequestSubmitHandler,
)
from odoo.addons.smart_core.handlers.reason_codes import (
    REASON_IDEMPOTENCY_CONFLICT,
    REASON_MISSING_PARAMS,
    REASON_NOT_FOUND,
    REASON_OK,
)


@tagged("sc_smoke", "payment_request_approval_backend")
class TestPaymentRequestApprovalIntentBackend(TransactionCase):
    # Test corpus references for intent surface gates:
    # payment.request.submit
    # payment.request.approve
    # payment.request.reject
    # payment.request.done
    def _create_payment_request_minimal(self):
        project = self.env["project.project"].create({"name": "Intent PR Project"})
        partner = self.env["res.partner"].create({"name": "Intent PR Partner"})
        return self.env["payment.request"].sudo().create(
            {
                "name": "INTENT-PR-001",
                "type": "pay",
                "project_id": project.id,
                "partner_id": partner.id,
                "amount": 100,
                "state": "draft",
            }
        )

    def test_payment_request_submit_missing_id(self):
        handler = PaymentRequestSubmitHandler(self.env, payload={})
        result = handler.handle({"request_id": "req-pr-submit-missing"})
        self.assertFalse(result.get("ok"))
        self.assertEqual(int(result.get("code") or 0), 400)
        err = result.get("error") or {}
        self.assertEqual(err.get("reason_code"), REASON_MISSING_PARAMS)
        data = result.get("data") or {}
        self.assertEqual(data.get("request_id"), "req-pr-submit-missing")
        self.assertEqual(data.get("idempotency_key"), "req-pr-submit-missing")

    def test_payment_request_submit_not_found(self):
        handler = PaymentRequestSubmitHandler(self.env, payload={})
        result = handler.handle({"id": 999999999, "request_id": "req-pr-submit-not-found"})
        self.assertFalse(result.get("ok"))
        self.assertEqual(int(result.get("code") or 0), 404)
        err = result.get("error") or {}
        self.assertEqual(err.get("reason_code"), REASON_NOT_FOUND)

    def test_payment_request_submit_conflict_contract_shape(self):
        payment_request = self._create_payment_request_minimal()
        handler = PaymentRequestSubmitHandler(self.env, payload={})
        with patch(
            "odoo.addons.smart_construction_core.handlers.payment_request_approval.resolve_idempotency_decision",
            return_value={
                "conflict": True,
                "replay_entry": None,
                "replay_payload": None,
                "replay_window_expired": False,
            },
        ):
            result = handler.handle({"id": payment_request.id, "request_id": "req-pr-submit-conflict"})
        self.assertFalse(result.get("ok"))
        self.assertEqual(int(result.get("code") or 0), 409)
        err = result.get("error") or {}
        self.assertEqual(err.get("reason_code"), REASON_IDEMPOTENCY_CONFLICT)
        data = result.get("data") or {}
        self.assertEqual(data.get("request_id"), "req-pr-submit-conflict")
        self.assertEqual(data.get("idempotency_key"), "req-pr-submit-conflict")

    def test_payment_request_submit_replay_contract_shape(self):
        payment_request = self._create_payment_request_minimal()
        handler = PaymentRequestSubmitHandler(self.env, payload={})
        with patch(
            "odoo.addons.smart_construction_core.handlers.payment_request_approval.resolve_idempotency_decision",
            return_value={
                "conflict": False,
                "replay_entry": {"audit_id": 77, "trace_id": "trace-replay-submit"},
                "replay_payload": {
                    "success": True,
                    "reason_code": REASON_OK,
                    "intent_action": "submit",
                    "payment_request": {"id": payment_request.id, "state": "submit"},
                },
                "replay_window_expired": False,
            },
        ):
            result = handler.handle({"id": payment_request.id, "request_id": "req-pr-submit-replay"})
        self.assertTrue(result.get("ok"))
        data = result.get("data") or {}
        self.assertTrue(bool(data.get("idempotent_replay")))
        self.assertEqual(int(data.get("replay_from_audit_id") or 0), 77)
        self.assertEqual(str(data.get("replay_original_trace_id") or ""), "trace-replay-submit")
        self.assertEqual(data.get("request_id"), "req-pr-submit-replay")

    def test_payment_request_submit_success_contract_with_mocked_method(self):
        payment_request = self._create_payment_request_minimal()
        handler = PaymentRequestSubmitHandler(self.env, payload={})
        with patch("odoo.addons.smart_construction_core.models.core.payment_request.PaymentRequest.action_submit", autospec=True, return_value=None):
            result = handler.handle({"id": payment_request.id, "request_id": "req-pr-submit-success"})
        self.assertTrue(result.get("ok"))
        data = result.get("data") or {}
        self.assertEqual(data.get("reason_code"), REASON_OK)
        self.assertEqual(data.get("intent_action"), "submit")
        self.assertEqual(((data.get("payment_request") or {}).get("id")), payment_request.id)
        self.assertFalse(bool(data.get("idempotent_replay")))

    def test_payment_request_approve_success_contract_with_mocked_method(self):
        payment_request = self._create_payment_request_minimal()
        payment_request.sudo().with_context(allow_transition=True).write({"state": "submit"})
        handler = PaymentRequestApproveHandler(self.env, payload={})
        with patch("odoo.addons.smart_construction_core.models.core.payment_request.PaymentRequest.action_approve", autospec=True, return_value=None):
            result = handler.handle({"id": payment_request.id, "request_id": "req-pr-approve-success"})
        self.assertTrue(result.get("ok"))
        data = result.get("data") or {}
        self.assertEqual(data.get("reason_code"), REASON_OK)
        self.assertEqual(data.get("intent_action"), "approve")
        self.assertEqual(((data.get("payment_request") or {}).get("id")), payment_request.id)

    def test_payment_request_approve_conflict_contract_shape(self):
        payment_request = self._create_payment_request_minimal()
        handler = PaymentRequestApproveHandler(self.env, payload={})
        with patch(
            "odoo.addons.smart_construction_core.handlers.payment_request_approval.resolve_idempotency_decision",
            return_value={
                "conflict": True,
                "replay_entry": None,
                "replay_payload": None,
                "replay_window_expired": False,
            },
        ):
            result = handler.handle({"id": payment_request.id, "request_id": "req-pr-approve-conflict"})
        self.assertFalse(result.get("ok"))
        self.assertEqual(int(result.get("code") or 0), 409)
        err = result.get("error") or {}
        self.assertEqual(err.get("reason_code"), REASON_IDEMPOTENCY_CONFLICT)

    def test_payment_request_reject_missing_reason(self):
        payment_request = self._create_payment_request_minimal()
        handler = PaymentRequestRejectHandler(self.env, payload={})
        result = handler.handle({"id": payment_request.id, "request_id": "req-pr-reject-missing-reason"})
        self.assertFalse(result.get("ok"))
        self.assertEqual(int(result.get("code") or 0), 400)
        err = result.get("error") or {}
        self.assertEqual(err.get("reason_code"), REASON_MISSING_PARAMS)

    def test_payment_request_reject_success_contract_with_mocked_method(self):
        payment_request = self._create_payment_request_minimal()
        payment_request.sudo().with_context(allow_transition=True).write({"state": "submit"})
        handler = PaymentRequestRejectHandler(self.env, payload={})
        with patch(
            "odoo.addons.smart_construction_core.models.core.payment_request.PaymentRequest.action_on_tier_rejected",
            autospec=True,
            return_value=None,
        ):
            result = handler.handle(
                {
                    "id": payment_request.id,
                    "request_id": "req-pr-reject-success",
                    "reason": "smoke reject",
                }
            )
        self.assertTrue(result.get("ok"))
        data = result.get("data") or {}
        self.assertEqual(data.get("reason_code"), REASON_OK)
        self.assertEqual(data.get("intent_action"), "reject")
        self.assertEqual(((data.get("payment_request") or {}).get("id")), payment_request.id)

    def test_payment_request_done_success_contract_with_mocked_method(self):
        payment_request = self._create_payment_request_minimal()
        payment_request.sudo().with_context(allow_transition=True).write({"state": "approved"})
        handler = PaymentRequestDoneHandler(self.env, payload={})
        with patch(
            "odoo.addons.smart_construction_core.models.core.payment_request.PaymentRequest.action_done",
            autospec=True,
            return_value=None,
        ):
            result = handler.handle({"id": payment_request.id, "request_id": "req-pr-done-success"})
        self.assertTrue(result.get("ok"))
        data = result.get("data") or {}
        self.assertEqual(data.get("reason_code"), REASON_OK)
        self.assertEqual(data.get("intent_action"), "done")
        self.assertEqual(((data.get("payment_request") or {}).get("id")), payment_request.id)
