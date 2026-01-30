# -*- coding: utf-8 -*-
import uuid

TRACE_HEADER_KEYS = ("X-Trace-Id", "X-Request-Id")


def get_trace_id(headers) -> str:
    for key in TRACE_HEADER_KEYS:
        val = (headers.get(key) or "").strip()
        if val:
            return val
    return uuid.uuid4().hex[:12]
