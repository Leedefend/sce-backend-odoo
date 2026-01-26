# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo import http
from odoo.http import request

from odoo.addons.smart_construction_core.controllers.api_base import ok, fail
from odoo.addons.smart_construction_portal.services.portal_contract_service import (
    PortalContractService,
)


class PortalController(http.Controller):
    @http.route("/portal/lifecycle", type="http", auth="user", methods=["GET"], csrf=False)
    def portal_lifecycle(self, **params):
        if not _portal_enabled(request.env):
            return request.not_found()
        payload = _merge_payload(params)
        project_id = payload.get("project_id") or payload.get("id")
        return request.render(
            "smart_construction_portal.portal_lifecycle_page",
            {"project_id": project_id or ""},
        )

    @http.route("/api/portal/contract", type="http", auth="user", methods=["GET", "POST"], csrf=False)
    def portal_contract(self, **params):
        if not _portal_enabled(request.env):
            return fail("NOT_FOUND", "Portal disabled", http_status=404)
        payload = _merge_payload(params)
        route = payload.get("route") or "/portal/lifecycle"
        trace_id = payload.get("trace_id")
        service = PortalContractService(request.env)
        data = service.build_lifecycle_dashboard(route=route, trace_id=trace_id)
        return ok(data, status=200)


def _merge_payload(params):
    payload = dict(params or {})
    try:
        if request.jsonrequest:
            payload.update(request.jsonrequest)
    except Exception:
        pass
    return payload


def _portal_enabled(env):
    value = env["ir.config_parameter"].sudo().get_param("sc.portal.lifecycle.enabled", "1")
    return str(value).strip().lower() in {"1", "true", "yes", "on"}
