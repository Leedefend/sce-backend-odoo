# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo import http
from .api_base import fail


class UiContractController(http.Controller):

    @http.route("/api/ui/contract", type="http", auth="user", methods=["GET", "POST"], csrf=False)
    def ui_contract(self, **params):
        return fail(
            "GONE",
            "legacy /api/ui/contract endpoint is disabled; use /api/v1/intent system.init scene-ready contracts",
            http_status=410,
        )
