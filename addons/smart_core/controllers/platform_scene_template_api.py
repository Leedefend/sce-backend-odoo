# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo import http

from .platform_scene_template_logic import SceneTemplateController


class PlatformSceneTemplateAPI(http.Controller):
    @http.route("/api/scenes/export", type="http", auth="public", methods=["GET"], csrf=False)
    def export_scenes(self, **params):
        return SceneTemplateController().export_scenes(**params)

    @http.route("/api/scenes/import", type="http", auth="public", methods=["POST"], csrf=False)
    def import_scenes(self, **params):
        return SceneTemplateController().import_scenes(**params)
