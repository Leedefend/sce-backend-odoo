# -*- coding: utf-8 -*-

from odoo.exceptions import AccessError, UserError
from odoo.tests.common import TransactionCase, tagged

from odoo.addons.smart_construction_core.handlers.reason_codes import (
    REASON_IDEMPOTENCY_CONFLICT,
    REASON_INTERNAL_ERROR,
    REASON_INVALID_ID,
    REASON_PERMISSION_DENIED,
    REASON_REPLAY_WINDOW_EXPIRED,
    REASON_UNSUPPORTED_SOURCE,
    REASON_USER_ERROR,
    my_work_failure_meta_for_exception,
    suggested_action_for_capability_reason,
)
from odoo.addons.smart_core.utils.reason_codes import failure_meta_for_reason


@tagged("sc_smoke", "reason_codes_backend")
class TestReasonCodesBackend(TransactionCase):
    def test_my_work_failure_meta_mapping(self):
        self.assertEqual(
            my_work_failure_meta_for_exception(AccessError("denied")).get("reason_code"),
            REASON_PERMISSION_DENIED,
        )
        self.assertEqual(
            my_work_failure_meta_for_exception(UserError("待办 ID 无效")).get("reason_code"),
            REASON_INVALID_ID,
        )
        self.assertEqual(
            my_work_failure_meta_for_exception(UserError("仅支持完成 mail.activity 类型待办")).get("reason_code"),
            REASON_UNSUPPORTED_SOURCE,
        )
        self.assertEqual(
            my_work_failure_meta_for_exception(UserError("其他业务异常")).get("reason_code"),
            REASON_USER_ERROR,
        )
        internal = my_work_failure_meta_for_exception(Exception("x"))
        self.assertEqual(internal.get("reason_code"), REASON_INTERNAL_ERROR)
        self.assertTrue(bool(internal.get("retryable")))

    def test_capability_suggested_action_mapping(self):
        self.assertEqual(
            suggested_action_for_capability_reason(reason_code="PERMISSION_DENIED", state="LOCKED"),
            "request_access",
        )
        self.assertEqual(
            suggested_action_for_capability_reason(reason_code="FEATURE_DISABLED", state="LOCKED"),
            "enable_feature_flag",
        )
        self.assertEqual(
            suggested_action_for_capability_reason(reason_code="", state="PREVIEW"),
            "wait_release",
        )

    def test_idempotency_conflict_meta_mapping(self):
        meta = failure_meta_for_reason(REASON_IDEMPOTENCY_CONFLICT)
        self.assertFalse(bool(meta.get("retryable")))
        self.assertEqual(meta.get("error_category"), "conflict")
        self.assertEqual(meta.get("suggested_action"), "use_new_request_id")

    def test_replay_window_expired_meta_mapping(self):
        meta = failure_meta_for_reason(REASON_REPLAY_WINDOW_EXPIRED)
        self.assertTrue(bool(meta.get("retryable")))
        self.assertEqual(meta.get("error_category"), "conflict")
        self.assertEqual(meta.get("suggested_action"), "retry")
