# -*- coding: utf-8 -*-
from __future__ import annotations

from . import system_init  # ensure handlers package loaded
from odoo.addons.smart_core.core.base_handler import BaseIntentHandler
import logging

_logger = logging.getLogger(__name__)


class PermissionCheckHandler(BaseIntentHandler):
    INTENT_TYPE = "permission.check"
    DESCRIPTION = "Check entitlement/permission for intent or capability"

    def handle(self, payload, ctx):
        params = getattr(self, "params", {})
        if not isinstance(params, dict):
            params = {}
        cap_key = params.get("capability_key") or params.get("capability") or params.get("key")
        required_flag = params.get("required_flag")
        debug = bool(params.get("debug") or params.get("_debug"))
        registry = getattr(self.env, "registry", None)
        model_present = bool(registry and hasattr(registry, "models") and "sc.entitlement" in registry.models)
        try:
            Entitlement = self.env["sc.entitlement"]
        except Exception:
            Entitlement = None
        if not Entitlement:
            data = {"allow": True}
            if required_flag:
                data.update({
                    "reason": "ENTITLEMENT_UNAVAILABLE",
                    "details": {"required_flag": required_flag, "capability_key": cap_key},
                })
            if debug:
                data["debug"] = {
                    "reason": "entitlement_model_missing",
                    "db": self.env.cr.dbname,
                    "model_present": model_present,
                }
            return {"ok": True, "data": data}
        ent = Entitlement.get_effective(self.env.user.company_id) if Entitlement else None
        flags = ent.effective_flags_json or {} if ent else {}
        cap = None
        if cap_key:
            cap = self.env["sc.capability"].sudo().search([("key", "=", cap_key)], limit=1)
        required_flag = (cap.required_flag if cap else None) or required_flag
        if required_flag:
            allow = Entitlement._flag_enabled(flags, required_flag)
            _logger.warning(
                "[permission.check] cap=%s required_flag=%s flags=%s allow=%s",
                cap.key if cap else cap_key,
                required_flag,
                flags,
                allow,
            )
            if not allow:
                data = {
                    "allow": False,
                    "reason": "FEATURE_DISABLED",
                    "details": {"required_flag": required_flag, "capability_key": cap.key if cap else cap_key},
                }
                if debug:
                    data["debug"] = {
                        "flags": flags,
                        "required_flag": required_flag,
                        "cap_found": bool(cap),
                        "db": self.env.cr.dbname,
                    }
                return {"ok": True, "data": data}
        else:
            _logger.warning("[permission.check] cap_missing_or_no_flag cap=%s flags=%s", cap_key, flags)
        if debug:
            return {
                "ok": True,
                "data": {
                    "allow": True,
                    "debug": {
                        "flags": flags,
                        "required_flag": required_flag,
                        "cap_found": bool(cap),
                        "db": self.env.cr.dbname,
                    },
                },
            }
        return {"ok": True, "data": {"allow": True}}
