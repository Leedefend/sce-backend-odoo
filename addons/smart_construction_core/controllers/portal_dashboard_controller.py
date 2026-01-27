# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo import http
from odoo.http import request

from .api_base import fail_from_exception, ok


class PortalDashboardController(http.Controller):

    @http.route("/api/contract/portal_dashboard", type="http", auth="user", methods=["GET", "POST"], csrf=False)
    def portal_dashboard(self, **params):
        try:
            from odoo.addons.smart_construction_core.services.portal_dashboard_service import (
                PortalDashboardService,
            )

            service = PortalDashboardService(request.env)
            data = service.build_dashboard()
        except Exception as exc:
            return fail_from_exception(exc, http_status=500)

        data["schema_version"] = "portal-dashboard-v1"
        return ok(data, status=200)
