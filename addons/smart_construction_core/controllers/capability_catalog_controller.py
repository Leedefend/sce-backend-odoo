# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo import http
from odoo.http import request

from odoo.exceptions import AccessDenied
from odoo.addons.smart_core.security.auth import get_user_from_token

from .api_base import fail, fail_from_exception, ok


class CapabilityCatalogController(http.Controller):
    @http.route("/api/capabilities/export", type="http", auth="public", methods=["GET"], csrf=False)
    def export_capabilities(self, **params):
        try:
            user = get_user_from_token()
            env = request.env(user=user)
            Cap = env["sc.capability"].sudo()
            records = Cap.search([("active", "=", True)], order="sequence, id")
            data = [rec.to_public_dict(user) for rec in records if rec._user_allowed(user)]
            payload = {"capabilities": data, "count": len(data)}
            return ok(payload, status=200)
        except AccessDenied as exc:
            return fail("AUTH_REQUIRED", str(exc), http_status=401)
        except Exception as exc:
            return fail_from_exception(exc, http_status=500)
