# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Dict

from odoo.addons.smart_core.utils.reason_codes import (
    REASON_ACCESS_RESTRICTED,
    REASON_DONE,
    REASON_INTERNAL_ERROR,
    REASON_INVALID_ID,
    REASON_IDEMPOTENCY_CONFLICT,
    REASON_NOT_FOUND,
    REASON_OK,
    REASON_PARTIAL_FAILED,
    REASON_PERMISSION_DENIED,
    REASON_UNSUPPORTED_SOURCE,
    REASON_USER_ERROR,
    capability_suggested_action,
    failure_meta_for_reason,
)


def my_work_failure_meta_for_exception(exc: Exception) -> Dict[str, object]:
    from odoo.exceptions import AccessError, UserError

    if isinstance(exc, AccessError):
        return {"reason_code": REASON_PERMISSION_DENIED, **failure_meta_for_reason(REASON_PERMISSION_DENIED)}
    if isinstance(exc, UserError):
        msg = str(exc) or ""
        if "不存在" in msg:
            return {"reason_code": REASON_NOT_FOUND, **failure_meta_for_reason(REASON_NOT_FOUND)}
        if "无效" in msg:
            return {"reason_code": REASON_INVALID_ID, **failure_meta_for_reason(REASON_INVALID_ID)}
        if "仅支持" in msg:
            return {"reason_code": REASON_UNSUPPORTED_SOURCE, **failure_meta_for_reason(REASON_UNSUPPORTED_SOURCE)}
        return {"reason_code": REASON_USER_ERROR, **failure_meta_for_reason(REASON_USER_ERROR)}
    return {"reason_code": REASON_INTERNAL_ERROR, **failure_meta_for_reason(REASON_INTERNAL_ERROR)}


def suggested_action_for_capability_reason(*, reason_code: str, state: str) -> str:
    return capability_suggested_action(reason_code=reason_code, state=state)
