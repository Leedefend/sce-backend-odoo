# -*- coding: utf-8 -*-
from __future__ import annotations

from ..utils.reason_codes import (
    REASON_BUSINESS_RULE_FAILED,
    REASON_CONFLICT,
    REASON_DRY_RUN,
    REASON_FILTER_NO_MATCH,
    REASON_IDEMPOTENCY_CONFLICT,
    REASON_METHOD_NOT_CALLABLE,
    REASON_MISSING_PARAMS,
    REASON_NO_WORK_ITEMS,
    REASON_NOT_FOUND,
    REASON_OK,
    REASON_PERMISSION_DENIED,
    REASON_PAYMENT_NOT_FULLY_PAID,
    REASON_READONLY_PROJECTION_MUTATION_DENIED,
    REASON_REPLAY_WINDOW_EXPIRED,
    REASON_SYSTEM_ERROR,
    REASON_UNSUPPORTED_BUTTON_TYPE,
    REASON_WRITE_FAILED,
    failure_meta_for_reason,
)

SOURCE_KIND = "reason_code_handler_projection"
SOURCE_AUTHORITIES = ("reason_code_metadata_registry",)
NO_BUSINESS_FACT_AUTHORITY = True


def source_authority_contract() -> dict:
    return {
        "kind": SOURCE_KIND,
        "authorities": list(SOURCE_AUTHORITIES),
        "projection_only": True,
        "rebuildable": True,
        "no_business_fact_authority": NO_BUSINESS_FACT_AUTHORITY,
        "metadata_proxy_only": True,
    }


def batch_failure_meta(reason_code: str):
    return failure_meta_for_reason(reason_code)
