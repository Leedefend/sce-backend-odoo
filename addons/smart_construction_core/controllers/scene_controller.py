# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo import http
from odoo.http import request

from odoo.exceptions import AccessDenied
from odoo.addons.smart_core.security.auth import get_user_from_token

from .api_base import fail, fail_from_exception, ok


def _has_admin(user):
    return user.has_group("smart_construction_core.group_sc_cap_config_admin") or user.has_group("base.group_system")


def _parse_bool(val, default=False):
    if val is None:
        return default
    if isinstance(val, bool):
        return val
    return str(val).strip().lower() in {"1", "true", "yes", "y"}


class SceneController(http.Controller):
    @http.route("/api/scenes/my", type="http", auth="public", methods=["GET"], csrf=False)
    def my_scenes(self, **params):
        try:
            user = get_user_from_token()
            env = request.env(user=user)
            Scene = env["sc.scene"].sudo()
            include_tests = _parse_bool(params.get("include_tests"), False) and _has_admin(user)
            domain = [("active", "=", True), ("state", "=", "published")]
            if not include_tests:
                domain.append(("is_test", "=", False))
            scenes = Scene.search(domain, order="sequence, id")
            out = [scene.to_public_dict(user) for scene in scenes if scene._user_allowed(user)]
            pref = env["sc.user.preference"].sudo().search([("user_id", "=", user.id)], limit=1)
            default_scene_code = None
            if pref and pref.default_scene_id:
                default_scene_code = pref.default_scene_id.code
            if not default_scene_code:
                default_scene = next((s for s in out if s.get("is_default")), None)
                default_scene_code = default_scene["code"] if default_scene else None
            payload = {
                "scenes": out,
                "count": len(out),
                "default_scene": default_scene_code,
            }
            return ok(payload, status=200)
        except AccessDenied as exc:
            return fail("AUTH_REQUIRED", str(exc), http_status=401)
        except Exception as exc:
            return fail_from_exception(exc, http_status=500)
