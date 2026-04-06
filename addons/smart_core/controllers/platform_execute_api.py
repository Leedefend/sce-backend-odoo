# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from datetime import datetime

from odoo import http
from odoo.http import request

from odoo.addons.smart_core.handlers.ui_contract import UiContractHandler
from odoo.addons.smart_core.core.trace import get_trace_id


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
            "contract_version": CONTRACT_VERSION,
            "server_time": _server_time(),
            "trace_id": trace_id,
            "warnings": [],
            "data": data,
        },
        status=status,
    )


def _fail(code, message, details=None, http_status=400):
    trace_id = get_trace_id(request.httprequest.headers)
    return _json_response(
        {
            "ok": False,
            "contract_version": CONTRACT_VERSION,
            "server_time": _server_time(),
            "trace_id": trace_id,
            "warnings": [],
            "error": {
                "code": str(code),
                "message": message,
                "details": details or {},
                "trace_id": trace_id,
            },
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


def _merge_payload(params):
    payload = dict(params or {})
    try:
        if request.jsonrequest:
            payload.update(request.jsonrequest)
    except Exception:
        pass
    return payload


def _is_method_allowed(model, method):
    payload = {
        "op": "model",
        "model": model,
        "view_type": "form",
        "source_mode": "execute_guard",
    }
    handler = UiContractHandler(request.env, request=request, payload=payload)
    res = handler.handle(payload=payload)
    if not isinstance(res, dict) or res.get("ok") is False:
        return False
    data = res.get("data") or {}
    views = data.get("views") or {}
    form = views.get("form") or {}
    buttons = []
    buttons.extend(data.get("buttons") or [])
    buttons.extend(form.get("header_buttons") or [])
    buttons.extend(form.get("stat_buttons") or form.get("button_box") or [])
    for btn in buttons:
        if not isinstance(btn, dict):
            continue
        if btn.get("kind") != "object":
            continue
        button_payload = btn.get("payload") or {}
        if button_payload.get("method") == method:
            return True
    return False


class PlatformExecuteAPI(http.Controller):
    @http.route("/api/execute_button", type="http", auth="user", methods=["POST"], csrf=False)
    def execute_button(self, **params):
        payload = _merge_payload(params)
        model = (payload.get("model") or "").strip()
        method = (payload.get("method") or payload.get("method_name") or "").strip()
        res_id = payload.get("res_id") or payload.get("record_id")
        context = payload.get("context") if isinstance(payload.get("context"), dict) else None

        if not model or not method or not res_id:
            return _fail("BAD_REQUEST", "model/res_id/method required", http_status=400)

        if not _is_method_allowed(model, method):
            return _fail("NOT_ALLOWED", "method not allowed", details={"method": method}, http_status=403)

        try:
            result = request.env["sc.execute_button.service"].execute(model, res_id, method, context=context)
        except Exception as error:
            return _fail_from_exception(error, http_status=500)

        return _ok(result, status=200)
