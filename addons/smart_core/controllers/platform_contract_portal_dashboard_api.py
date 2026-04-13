# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from datetime import datetime

from odoo import http
from odoo.http import request

from odoo.addons.smart_core.core.trace import get_trace_id
from odoo.addons.smart_core.core.industry_runtime_service_adapter import (
    build_portal_dashboard,
)


CONTRACT_VERSION = "v1"


def _server_time() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def _json_response(payload, status=200):
    return request.make_response(
        json.dumps(payload, ensure_ascii=False, default=str),
        headers=[("Content-Type", "application/json; charset=utf-8")],
        status=status,
    )


def _ok(data, status=200):
    trace_id = get_trace_id(request.httprequest.headers)
    return _json_response(
        {
            "ok": True,
            "data": data,
            "error": None,
            "meta": {
                "contract_version": CONTRACT_VERSION,
                "server_time": _server_time(),
                "trace_id": trace_id,
                "warnings": [],
            },
            "effect": None,
        },
        status=status,
    )


def _fail(code, message, details=None, http_status=400):
    trace_id = get_trace_id(request.httprequest.headers)
    return _json_response(
        {
            "ok": False,
            "data": None,
            "error": {
                "code": str(code),
                "message": message,
                "details": details or {},
                "trace_id": trace_id,
            },
            "meta": {
                "contract_version": CONTRACT_VERSION,
                "server_time": _server_time(),
                "trace_id": trace_id,
                "warnings": [],
            },
            "effect": None,
        },
        status=http_status,
    )


def _fail_from_exception(error, http_status=500):
    return _fail(
        "SERVER_ERROR",
        "Internal server error",
        details={"error": str(error)},
        http_status=http_status,
    )


class PlatformContractPortalDashboardAPI(http.Controller):
    @http.route("/api/contract/portal_dashboard", type="http", auth="user", methods=["GET", "POST"], csrf=False)
    def portal_dashboard(self, **params):
        del params
        try:
            data = build_portal_dashboard(request.env)
        except Exception as error:
            return _fail_from_exception(error, http_status=500)

        data["schema_version"] = "portal-dashboard-v1"
        return _ok(data, status=200)
