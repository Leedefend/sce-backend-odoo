# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo import http
from odoo.http import request

from odoo.addons.smart_core.handlers.ui_contract import UiContractHandler

from .api_base import fail, fail_from_exception, ok


class ExecuteController(http.Controller):

    @http.route("/api/execute_button", type="http", auth="user", methods=["POST"], csrf=False)
    def execute_button(self, **params):
        payload = _merge_payload(params)
        model = (payload.get("model") or "").strip()
        method = (payload.get("method") or payload.get("method_name") or "").strip()
        res_id = payload.get("res_id") or payload.get("record_id")
        context = payload.get("context") if isinstance(payload.get("context"), dict) else None

        if not model or not method or not res_id:
            return fail("BAD_REQUEST", "model/res_id/method required", http_status=400)

        if not _is_method_allowed(model, method):
            return fail("NOT_ALLOWED", "method not allowed", details={"method": method}, http_status=403)

        try:
            result = request.env["sc.execute_button.service"].execute(model, res_id, method, context=context)
        except Exception as exc:
            return fail_from_exception(exc, http_status=500)

        return ok(result, status=200)


def _merge_payload(params):
    payload = dict(params or {})
    try:
        if request.jsonrequest:
            payload.update(request.jsonrequest)
    except Exception:
        pass
    return payload


def _is_method_allowed(model, method):
    payload = {"op": "model", "model": model, "view_type": "form"}
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
        payload = btn.get("payload") or {}
        if payload.get("method") == method:
            return True
    return False
