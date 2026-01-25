# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Dict, Optional

from odoo.http import request

from .utils.trace import get_trace_id

CONTRACT_VERSION = "v1"


def _server_time() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def _json_response(payload: Dict[str, Any], status: int = 200):
    body = json.dumps(payload, ensure_ascii=False, default=str)
    headers = [("Content-Type", "application/json; charset=utf-8")]
    return request.make_response(body, headers=headers, status=status)


def ok(data: Any, warnings: Optional[list] = None, status: int = 200):
    trace_id = get_trace_id()
    payload = {
        "ok": True,
        "contract_version": CONTRACT_VERSION,
        "server_time": _server_time(),
        "trace_id": trace_id,
        "warnings": warnings or [],
        "data": data,
    }
    return _json_response(payload, status=status)


def fail(
    code: str,
    message: str,
    details: Optional[Dict[str, Any]] = None,
    http_status: int = 400,
    warnings: Optional[list] = None,
):
    trace_id = get_trace_id()
    error = {
        "code": str(code),
        "message": message,
        "details": details or {},
        "trace_id": trace_id,
    }
    payload = {
        "ok": False,
        "contract_version": CONTRACT_VERSION,
        "server_time": _server_time(),
        "trace_id": trace_id,
        "warnings": warnings or [],
        "error": error,
    }
    return _json_response(payload, status=http_status)


def fail_from_exception(exc: Exception, http_status: int = 500):
    # Hide tracebacks; collapse to a stable server error payload.
    return fail(
        "SERVER_ERROR",
        "Internal server error",
        details={"error": str(exc)},
        http_status=http_status,
    )
