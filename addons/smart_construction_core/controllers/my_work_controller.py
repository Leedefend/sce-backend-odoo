# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo import http
from odoo.http import request

from odoo.exceptions import AccessDenied
from odoo.addons.smart_core.security.auth import get_user_from_token
from odoo.addons.smart_construction_core.handlers.my_work_summary import MyWorkSummaryHandler

from .api_base import fail, fail_from_exception, ok


class MyWorkController(http.Controller):
    @http.route("/api/my-work", type="http", auth="public", methods=["POST"], csrf=False)
    def my_work_summary(self, **params):
        payload = dict(params or {})
        try:
            if request.jsonrequest and isinstance(request.jsonrequest, dict):
                payload.update(request.jsonrequest)
        except Exception:
            pass
        try:
            user = get_user_from_token()
            env = request.env(user=user)
            handler = MyWorkSummaryHandler(env, request=request, payload={"params": payload})
            result = handler.run(payload={"params": payload}) or {}
            if not isinstance(result, dict):
                return ok({})
            if result.get("ok") is False:
                return ok({"status": "error", "message": "my work summary failed"})
            data = result.get("data") if isinstance(result.get("data"), dict) else {}
            return ok(data)
        except AccessDenied as exc:
            return fail("AUTH_REQUIRED", str(exc), http_status=401)
        except Exception as exc:
            return fail_from_exception(exc, http_status=500)
