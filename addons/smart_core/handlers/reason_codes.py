# -*- coding: utf-8 -*-
from __future__ import annotations

# Shared reason codes for smart_core batch interaction contracts.
REASON_OK = "OK"
REASON_NOT_FOUND = "NOT_FOUND"
REASON_CONFLICT = "CONFLICT"
REASON_PERMISSION_DENIED = "PERMISSION_DENIED"
REASON_WRITE_FAILED = "WRITE_FAILED"


def batch_failure_meta(reason_code: str):
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
    }
    return dict(mapping.get(code) or {"retryable": False, "error_category": "", "suggested_action": ""})
