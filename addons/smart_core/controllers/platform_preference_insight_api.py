# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo import http

from .platform_preference_logic import PreferenceController
from .platform_insight_logic import InsightController


class PlatformPreferenceInsightAPI(http.Controller):
    @http.route("/api/preferences/get", type="http", auth="public", methods=["GET", "POST"], csrf=False)
    def pref_get(self, **params):
        return PreferenceController().pref_get(**params)

    @http.route("/api/preferences/set", type="http", auth="public", methods=["POST"], csrf=False)
    def pref_set(self, **params):
        return PreferenceController().pref_set(**params)

    @http.route("/api/insight", type="http", auth="user", methods=["GET"], csrf=False)
    def get_insight(self, **params):
        return InsightController().get_insight(**params)
