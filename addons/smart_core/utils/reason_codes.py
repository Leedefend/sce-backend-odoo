# -*- coding: utf-8 -*-
from __future__ import annotations

# Shared reason-code constants for Phase 10 interaction contracts.
REASON_OK = "OK"
REASON_DONE = "DONE"
REASON_PARTIAL_FAILED = "PARTIAL_FAILED"
REASON_PERMISSION_DENIED = "PERMISSION_DENIED"
REASON_NOT_FOUND = "NOT_FOUND"
REASON_INVALID_ID = "INVALID_ID"
REASON_UNSUPPORTED_SOURCE = "UNSUPPORTED_SOURCE"
REASON_USER_ERROR = "USER_ERROR"
REASON_INTERNAL_ERROR = "INTERNAL_ERROR"
REASON_ACCESS_RESTRICTED = "ACCESS_RESTRICTED"
REASON_CONFLICT = "CONFLICT"
REASON_WRITE_FAILED = "WRITE_FAILED"
REASON_IDEMPOTENCY_CONFLICT = "IDEMPOTENCY_CONFLICT"
REASON_REPLAY_WINDOW_EXPIRED = "REPLAY_WINDOW_EXPIRED"
REASON_MISSING_PARAMS = "MISSING_PARAMS"
REASON_UNSUPPORTED_BUTTON_TYPE = "UNSUPPORTED_BUTTON_TYPE"
REASON_METHOD_NOT_CALLABLE = "METHOD_NOT_CALLABLE"
REASON_DRY_RUN = "DRY_RUN"
REASON_BUSINESS_RULE_FAILED = "BUSINESS_RULE_FAILED"
REASON_SYSTEM_ERROR = "SYSTEM_ERROR"
REASON_NO_WORK_ITEMS = "NO_WORK_ITEMS"
REASON_FILTER_NO_MATCH = "FILTER_NO_MATCH"


def failure_meta_for_reason(reason_code: str):
    code = str(reason_code or "").strip().upper()
    mapping = {
        REASON_NOT_FOUND: {
            "retryable": False,
            "error_category": "not_found",
            "suggested_action": "refresh_list",
        },
        REASON_CONFLICT: {
            "retryable": True,
            "error_category": "conflict",
            "suggested_action": "reload_then_retry",
        },
        REASON_IDEMPOTENCY_CONFLICT: {
            "retryable": False,
            "error_category": "conflict",
            "suggested_action": "use_new_request_id",
        },
        REASON_REPLAY_WINDOW_EXPIRED: {
            "retryable": True,
            "error_category": "conflict",
            "suggested_action": "retry",
        },
        REASON_PERMISSION_DENIED: {
            "retryable": False,
            "error_category": "permission",
            "suggested_action": "request_access",
        },
        REASON_WRITE_FAILED: {
            "retryable": True,
            "error_category": "transient",
            "suggested_action": "retry",
        },
        REASON_INVALID_ID: {
            "retryable": False,
            "error_category": "validation",
            "suggested_action": "fix_input",
        },
        REASON_UNSUPPORTED_SOURCE: {
            "retryable": False,
            "error_category": "validation",
            "suggested_action": "fix_input",
        },
        REASON_USER_ERROR: {
            "retryable": False,
            "error_category": "validation",
            "suggested_action": "fix_input",
        },
        REASON_INTERNAL_ERROR: {
            "retryable": True,
            "error_category": "transient",
            "suggested_action": "retry",
        },
        REASON_MISSING_PARAMS: {
            "retryable": False,
            "error_category": "validation",
            "suggested_action": "fix_input",
        },
        REASON_UNSUPPORTED_BUTTON_TYPE: {
            "retryable": False,
            "error_category": "validation",
            "suggested_action": "fix_input",
        },
        REASON_METHOD_NOT_CALLABLE: {
            "retryable": False,
            "error_category": "validation",
            "suggested_action": "contact_admin",
        },
        REASON_DRY_RUN: {
            "retryable": True,
            "error_category": "noop",
            "suggested_action": "execute",
        },
        REASON_BUSINESS_RULE_FAILED: {
            "retryable": False,
            "error_category": "validation",
            "suggested_action": "check_prerequisites",
        },
        REASON_SYSTEM_ERROR: {
            "retryable": True,
            "error_category": "transient",
            "suggested_action": "retry",
        },
        REASON_NO_WORK_ITEMS: {
            "retryable": False,
            "error_category": "empty",
            "suggested_action": "none",
        },
        REASON_FILTER_NO_MATCH: {
            "retryable": False,
            "error_category": "empty",
            "suggested_action": "clear_filters",
        },
    }
    return dict(mapping.get(code) or {"retryable": False, "error_category": "", "suggested_action": ""})


def capability_suggested_action(*, reason_code: str, state: str) -> str:
    code = str(reason_code or "").strip().upper()
    current_state = str(state or "").strip().upper()
    if current_state == "PREVIEW":
        return "wait_release"
    mapping = {
        REASON_PERMISSION_DENIED: "request_access",
        "FEATURE_DISABLED": "enable_feature_flag",
        "ENTITLEMENT_UNAVAILABLE": "upgrade_subscription",
        "ROLE_SCOPE_MISMATCH": "switch_role_or_scope",
        "CAPABILITY_SCOPE_MISMATCH": "switch_role_or_scope",
        REASON_ACCESS_RESTRICTED: "check_prerequisites",
    }
    return mapping.get(code, "contact_admin")
