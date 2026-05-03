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
    SOURCE_KIND = "intent_delivery_catalog_projection"
    SOURCE_AUTHORITIES = ("handler_registry", "ir.model.access", "res.groups")

    def handle(self, payload=None, ctx=None):
        builder = IntentSurfaceBuilder()
        intents, intents_meta = builder.collect(self.env, self.env.user)
        intent_catalog = builder.collect_catalog(self.env, self.env.user)
        return {
            "intents": intents,
            "intents_meta": intents_meta,
            "intent_catalog": intent_catalog,
        }, {
            "schema_version": "1.0.0",
            "source_kind": self.SOURCE_KIND,
            "source_authorities": list(self.SOURCE_AUTHORITIES),
        }
