# -*- coding: utf-8 -*-
import uuid

from .source_authority import build_source_authority_contract

TRACE_HEADER_KEYS = ("X-Trace-Id", "X-Request-Id")
SOURCE_KIND = "request_trace_id_projection"
SOURCE_AUTHORITIES = ("http.headers", "uuid")
NO_BUSINESS_FACT_AUTHORITY = True


def source_authority_contract() -> dict:
    return build_source_authority_contract(
        kind=SOURCE_KIND,
        authorities=SOURCE_AUTHORITIES,
        no_business_fact_authority=NO_BUSINESS_FACT_AUTHORITY,
        runtime_carrier="trace",
    )


def get_trace_id(headers) -> str:
    for key in TRACE_HEADER_KEYS:
        val = (headers.get(key) or "").strip()
        if val:
            return val
    return uuid.uuid4().hex[:12]
