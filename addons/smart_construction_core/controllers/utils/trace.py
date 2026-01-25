# -*- coding: utf-8 -*-
from __future__ import annotations

import uuid

from odoo.http import request

_TRACE_ATTR = "_sc_trace_id"


def new_trace_id() -> str:
    return str(uuid.uuid4())


def get_trace_id() -> str:
    if request is None:
        return new_trace_id()
    existing = getattr(request, _TRACE_ATTR, None)
    if existing:
        return existing
    trace_id = new_trace_id()
    setattr(request, _TRACE_ATTR, trace_id)
    return trace_id
