# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo import http, fields
from odoo.http import request

from odoo.exceptions import AccessDenied
from odoo.addons.smart_core.security.auth import get_user_from_token

from .api_base import fail, fail_from_exception, ok


def _get_json_body():
    body = request.httprequest.get_json(force=True, silent=True)
    return body if isinstance(body, dict) else {}


class PreferenceController(http.Controller):
    @http.route("/api/preferences/get", type="http", auth="public", methods=["GET", "POST"], csrf=False)
    def pref_get(self, **params):
        try:
            user = get_user_from_token()
            env = request.env(user=user)
            pref = env["sc.user.preference"].get_or_create(env, user)
            payload = {
                "default_scene": pref.default_scene_id.code if pref.default_scene_id else None,
                "pinned_tile_keys": pref.pinned_tile_keys or [],
                "recent_tiles": pref.recent_tiles or [],
            }
            env["sc.scene.audit.log"].sudo().create({
                "event": "update_pref",
                "actor_user_id": user.id,
                "payload_diff": payload,
                "created_at": fields.Datetime.now(),
            })
            return ok(payload, status=200)
        except AccessDenied as exc:
            return fail("AUTH_REQUIRED", str(exc), http_status=401)
        except Exception as exc:
            return fail_from_exception(exc, http_status=500)

    @http.route("/api/preferences/set", type="http", auth="public", methods=["POST"], csrf=False)
    def pref_set(self, **params):
        try:
            user = get_user_from_token()
            env = request.env(user=user)
            pref = env["sc.user.preference"].get_or_create(env, user)
            body = _get_json_body()
            default_scene_code = body.get("default_scene")
            if default_scene_code:
                scene = env["sc.scene"].sudo().search(
                    [("code", "=", default_scene_code), ("state", "=", "published")],
                    limit=1,
                )
                if scene and scene._user_allowed(user):
                    pref.default_scene_id = scene.id
            if isinstance(body.get("pinned_tile_keys"), list):
                pref.pinned_tile_keys = body.get("pinned_tile_keys")
            if isinstance(body.get("recent_tiles"), list):
                pref.recent_tiles = body.get("recent_tiles")
            payload = {
                "default_scene": pref.default_scene_id.code if pref.default_scene_id else None,
                "pinned_tile_keys": pref.pinned_tile_keys or [],
                "recent_tiles": pref.recent_tiles or [],
            }
            return ok(payload, status=200)
        except AccessDenied as exc:
            return fail("AUTH_REQUIRED", str(exc), http_status=401)
        except Exception as exc:
            return fail_from_exception(exc, http_status=500)
