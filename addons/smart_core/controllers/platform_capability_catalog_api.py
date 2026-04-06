# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo import http

from .platform_capability_catalog_logic import CapabilityCatalogController


class PlatformCapabilityCatalogAPI(http.Controller):
    @http.route("/api/capabilities/export", type="http", auth="public", methods=["GET"], csrf=False)
    def export_capabilities(self, **params):
        return CapabilityCatalogController().export_capabilities(**params)

    @http.route("/api/capabilities/search", type="http", auth="public", methods=["GET"], csrf=False)
    def search_capabilities(self, **params):
        return CapabilityCatalogController().search_capabilities(**params)

    @http.route("/api/capabilities/lint", type="http", auth="public", methods=["GET"], csrf=False)
    def lint_capabilities(self, **params):
        return CapabilityCatalogController().lint_capabilities(**params)
