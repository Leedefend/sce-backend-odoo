# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo.addons.smart_core.core.base_handler import BaseIntentHandler
from odoo.addons.smart_core.handlers.system_init import SystemInitHandler


class SystemInitInspectHandler(BaseIntentHandler):
    INTENT_TYPE = "system.init.inspect"
    DESCRIPTION = "返回 system.init 启动链 inspect/debug 诊断面"
    VERSION = "1.0.0"
    ETAG_ENABLED = False
    REQUIRED_GROUPS = ["base.group_user"]

    def handle(self, payload=None, ctx=None):
        params = payload.get("params") if isinstance(payload, dict) and isinstance(payload.get("params"), dict) else payload
        params = dict(params or {}) if isinstance(params, dict) else {}
        params["_build_mode"] = "debug"
        params.setdefault("with_preload", False)
        delegate = SystemInitHandler(
            self.env,
            su_env=self.su_env,
            request=self.request,
            context=self.context,
            payload={"params": params},
        )
        return delegate.handle(payload={"params": params}, ctx=ctx)
