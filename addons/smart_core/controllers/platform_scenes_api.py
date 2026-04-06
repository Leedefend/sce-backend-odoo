# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo import http

from .platform_scene_logic import SceneController


class PlatformScenesAPI(http.Controller):
    @http.route("/api/scenes/my", type="http", auth="public", methods=["GET"], csrf=False)
    def my_scenes(self, **params):
        return SceneController().my_scenes(**params)
