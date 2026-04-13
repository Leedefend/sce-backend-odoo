# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo import http
from odoo.http import request
from odoo.exceptions import UserError, ValidationError, AccessError

from .api_base import (
    fail,
    fail_from_exception,
    ok,
)
from odoo.addons.smart_core.core.industry_runtime_service_adapter import (
    build_portal_execute_button_contract,
)


class PlatformPortalExecuteAPI(http.Controller):
    @http.route(
        "/api/contract/portal_execute_button",
        type="http",
        auth="user",
        methods=["GET"],
        csrf=False,
    )
    def portal_execute_button_contract(self, **params):
        model = (params.get("model") or "").strip() or None
        method = (params.get("method") or "").strip() or None
        res_id = params.get("res_id") or params.get("record_id")
        res_id = int(res_id) if str(res_id or "").isdigit() else None

        data = build_portal_execute_button_contract(request.env, model, res_id, method)
        return ok(data, status=200)

    @http.route(
        "/api/portal/execute_button",
        type="http",
        auth="user",
        methods=["POST"],
        csrf=False,
    )
    def portal_execute_button(self, **params):
        payload = _merge_payload(params)
        model = (payload.get("model") or "").strip()
        method = (payload.get("method") or "").strip()
        res_id = payload.get("res_id") or payload.get("record_id")
        context = payload.get("context") if isinstance(payload.get("context"), dict) else None

        if not model or not method or not res_id:
            return fail("BAD_REQUEST", "model/res_id/method required", http_status=400)

        contract = build_portal_execute_button_contract(request.env, model, res_id, method)
        if not contract.get("allowed"):
            error = contract.get("error") or {}
            code = error.get("code") or "not_allowed"
            message = error.get("message") or "not allowed"
            status = 404 if code in ("missing_method", "missing_record") else 403
            return fail(code, message, details=error, http_status=status)

        try:
            result = _execute_button_service().execute(
                model, res_id, method, context=context
            )
        except (UserError, ValidationError, AccessError) as error:
            return fail("record_error", str(error), details={"error": str(error)}, http_status=400)
        except Exception as error:
            return fail_from_exception(error, http_status=500)

        return ok(result, status=200)


def _merge_payload(params):
    payload = dict(params or {})
    try:
        if request.jsonrequest:
            payload.update(request.jsonrequest)
    except Exception:
        pass
    return payload


def _execute_button_service():
    return request.env["sc.execute_button.service"]
