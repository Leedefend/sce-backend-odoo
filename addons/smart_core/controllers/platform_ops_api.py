# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo import http

from .platform_ops_logic import OpsController


class PlatformOpsAPI(http.Controller):
    @http.route("/api/ops/tenants", type="http", auth="public", methods=["GET"], csrf=False)
    def tenants(self, **params):
        return OpsController().tenants(**params)

    @http.route("/api/ops/audit/search", type="http", auth="public", methods=["GET"], csrf=False)
    def audit_search(self, **params):
        return OpsController().audit_search(**params)

    @http.route("/api/ops/job/status", type="http", auth="public", methods=["GET"], csrf=False)
    def job_status(self, **params):
        return OpsController().job_status(**params)

    @http.route("/api/ops/subscription/set", type="http", auth="public", methods=["POST"], csrf=False)
    def set_subscription(self, **params):
        return OpsController().set_subscription(**params)

    @http.route("/api/ops/packs/batch_upgrade", type="http", auth="public", methods=["POST"], csrf=False)
    def batch_upgrade(self, **params):
        return OpsController().batch_upgrade(**params)

    @http.route("/api/ops/packs/batch_rollback", type="http", auth="public", methods=["POST"], csrf=False)
    def batch_rollback(self, **params):
        return OpsController().batch_rollback(**params)
