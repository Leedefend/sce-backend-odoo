# -*- coding: utf-8 -*-
from __future__ import annotations

import os

from odoo.addons.smart_core.security.platform_admin import user_is_platform_admin


class RequestDiagnosticsCollector:
    SOURCE_KIND = "request_diagnostics_projection"
    SOURCE_AUTHORITIES = ("http.headers", "system_init_params", "odoo_env", "res.users")
    NO_BUSINESS_FACT_AUTHORITY = True

    @classmethod
    def source_authority_contract(cls) -> dict:
        return {
            "kind": cls.SOURCE_KIND,
            "authorities": list(cls.SOURCE_AUTHORITIES),
            "projection_only": True,
            "rebuildable": True,
            "no_business_fact_authority": cls.NO_BUSINESS_FACT_AUTHORITY,
            "diagnostics_only": True,
        }

    @staticmethod
    def diagnostics_enabled(env) -> bool:
        env_flag = (os.environ.get("ENV") or "").lower()
        if env_flag in {"dev", "test", "local"}:
            return True
        try:
            return user_is_platform_admin(env.user)
        except Exception:
            return False

    @staticmethod
    def get_request_header(name: str) -> str | None:
        try:
            from odoo import http

            request = http.request
            if not request or not request.httprequest:
                return None
            return request.httprequest.headers.get(name)
        except Exception:
            return None

    def collect_system_init(self, env, params: dict) -> dict:
        try:
            from odoo import http

            request = http.request
            headers = request.httprequest.headers
            x_odoo_db = headers.get("X-Odoo-DB")
            x_db = headers.get("X-DB")
            authorization = headers.get("Authorization")
        except Exception:
            x_odoo_db = None
            x_db = None
            authorization = None

        return {
            "effective_db": env.cr.dbname if hasattr(env, "cr") and env.cr else "unknown",
            "db_source": "env_cr",
            "header_x_odoo_db": x_odoo_db,
            "header_x_db": x_db,
            "has_authorization": bool(authorization),
            "effective_root_xmlid": params.get("root_xmlid") if isinstance(params, dict) else None,
            "root_source": "params" if params and params.get("root_xmlid") else "default",
            "uid": env.uid,
            "login": env.user.login if hasattr(env, "user") else "unknown",
            "params_keys": list(params.keys()) if isinstance(params, dict) else [],
            "scene_channel_param": params.get("scene_channel") if isinstance(params, dict) else None,
            "scene_use_pinned_param": params.get("scene_use_pinned") if isinstance(params, dict) else None,
            "scene_rollback_param": params.get("scene_rollback") if isinstance(params, dict) else None,
        }
