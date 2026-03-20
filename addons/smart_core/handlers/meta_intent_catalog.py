# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo.addons.smart_core.core.base_handler import BaseIntentHandler
from odoo.addons.smart_core.core.intent_surface_builder import IntentSurfaceBuilder


class MetaIntentCatalogHandler(BaseIntentHandler):
    """Return full intent catalog for authenticated user."""

    INTENT_TYPE = "meta.intent_catalog"
    DESCRIPTION = "意图目录（全量）"
    VERSION = "1.0.0"
    ETAG_ENABLED = True
    REQUIRED_GROUPS = []

    def handle(self, payload=None, ctx=None):
        intents, intents_meta = IntentSurfaceBuilder().collect(self.env, self.env.user)
        return {
            "intents": intents,
            "intents_meta": intents_meta,
        }, {
            "schema_version": "1.0.0",
        }

