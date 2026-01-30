# -*- coding: utf-8 -*-
from odoo.addons.smart_core.core.base_handler import BaseIntentHandler


class SystemPingConstructionHandler(BaseIntentHandler):
    INTENT_TYPE = "system.ping.construction"
    DESCRIPTION = "Construction demo ping (extension loader)"
    VERSION = "1.0.0"
    ETAG_ENABLED = False

    def handle(self):
        return {
            "module": "smart_construction_core",
            "version": self.VERSION,
        }, {}
