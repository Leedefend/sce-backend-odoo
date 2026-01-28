# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo import http
from odoo.http import request
from odoo.exceptions import UserError, ValidationError, AccessError

from .api_base import fail, fail_from_exception, ok
from odoo.addons.smart_construction_core.services.portal_execute_button_service import (
    PortalExecuteButtonService,
)


class PortalExecuteButtonController(http.Controller):
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

        service = PortalExecuteButtonService(request.env)
        data = service.build_contract(model=model, res_id=res_id, method=method)
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

        service = PortalExecuteButtonService(request.env)
        contract = service.build_contract(model=model, res_id=res_id, method=method)
        if not contract.get("allowed"):
            error = contract.get("error") or {}
            code = error.get("code") or "not_allowed"
            message = error.get("message") or "not allowed"
            status = 404 if code in ("missing_method", "missing_record") else 403
            return fail(code, message, details=error, http_status=status)

        try:
            result = request.env["sc.execute_button.service"].execute(
                model, res_id, method, context=context
            )
        except (UserError, ValidationError, AccessError) as exc:
            return fail("record_error", str(exc), details={"error": str(exc)}, http_status=400)
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
