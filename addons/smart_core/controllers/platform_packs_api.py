# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo import http

from .platform_packs_logic import PackController


class PlatformPacksAPI(http.Controller):
    @http.route("/api/packs/catalog", type="http", auth="public", methods=["GET"], csrf=False)
    def catalog(self, **params):
        return PackController().catalog(**params)

    @http.route("/api/packs/publish", type="http", auth="public", methods=["POST"], csrf=False)
    def publish_pack(self, **params):
        return PackController().publish_pack(**params)

    @http.route("/api/packs/install", type="http", auth="public", methods=["POST"], csrf=False)
    def install_pack(self, **params):
        return PackController().install_pack(**params)

    @http.route("/api/packs/upgrade", type="http", auth="public", methods=["POST"], csrf=False)
    def upgrade_pack(self, **params):
        return PackController().upgrade_pack(**params)
