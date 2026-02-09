# -*- coding: utf-8 -*-
from __future__ import annotations

from ..utils.reason_codes import (
    REASON_CONFLICT,
    REASON_NOT_FOUND,
    REASON_OK,
    REASON_PERMISSION_DENIED,
    REASON_WRITE_FAILED,
    failure_meta_for_reason,
)


def batch_failure_meta(reason_code: str):
    return failure_meta_for_reason(reason_code)
