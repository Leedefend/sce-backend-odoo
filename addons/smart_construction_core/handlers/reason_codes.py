# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Dict

# Common reason-code constants used by Phase 10 interaction contracts.
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


def my_work_failure_meta_for_exception(exc: Exception) -> Dict[str, object]:
    from odoo.exceptions import AccessError, UserError

    if isinstance(exc, AccessError):
        return {
            "reason_code": REASON_PERMISSION_DENIED,
            "retryable": False,
            "error_category": "permission",
            "suggested_action": "request_access",
        }
    if isinstance(exc, UserError):
        msg = str(exc) or ""
        if "不存在" in msg:
            return {
                "reason_code": REASON_NOT_FOUND,
                "retryable": False,
                "error_category": "not_found",
                "suggested_action": "refresh_list",
            }
        if "无效" in msg:
            return {
                "reason_code": REASON_INVALID_ID,
                "retryable": False,
                "error_category": "validation",
                "suggested_action": "fix_input",
            }
        if "仅支持" in msg:
            return {
                "reason_code": REASON_UNSUPPORTED_SOURCE,
                "retryable": False,
                "error_category": "validation",
                "suggested_action": "fix_input",
            }
        return {
            "reason_code": REASON_USER_ERROR,
            "retryable": False,
            "error_category": "validation",
            "suggested_action": "fix_input",
        }
    return {
        "reason_code": REASON_INTERNAL_ERROR,
        "retryable": True,
        "error_category": "transient",
        "suggested_action": "retry",
    }


def suggested_action_for_capability_reason(*, reason_code: str, state: str) -> str:
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
