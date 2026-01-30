# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo import http
from odoo.http import request

from odoo.exceptions import AccessDenied
from odoo.addons.smart_core.security.auth import get_user_from_token

from .api_base import fail, fail_from_exception, ok


class SceneController(http.Controller):
    @http.route("/api/scenes/my", type="http", auth="public", methods=["GET"], csrf=False)
    def my_scenes(self, **params):
        try:
            user = get_user_from_token()
            env = request.env(user=user)
            Scene = env["sc.scene"].sudo()
            scenes = Scene.search([("active", "=", True)], order="sequence, id")
            out = [scene.to_public_dict(user) for scene in scenes if scene._user_allowed(user)]
            default_scene = next((s for s in out if s.get("is_default")), None)
            payload = {
                "scenes": out,
                "count": len(out),
                "default_scene": default_scene["code"] if default_scene else None,
            }
            return ok(payload, status=200)
        except AccessDenied as exc:
            return fail("AUTH_REQUIRED", str(exc), http_status=401)
        except Exception as exc:
            return fail_from_exception(exc, http_status=500)
