# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo import http
from odoo.http import request

from .api_base import fail_from_exception, ok


class CapabilityMatrixController(http.Controller):

    @http.route("/api/contract/capability_matrix", type="http", auth="user", methods=["GET", "POST"], csrf=False)
    def capability_matrix(self, **params):
        try:
            from odoo.addons.smart_construction_core.services.capability_matrix_service import (
                CapabilityMatrixService,
            )

            service = CapabilityMatrixService(request.env)
            data = service.build_matrix()
        except Exception as exc:
            return fail_from_exception(exc, http_status=500)

        data["schema_version"] = "capability-matrix-v1"
        return ok(data, status=200)
