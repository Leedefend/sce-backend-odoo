# -*- coding: utf-8 -*-
from __future__ import annotations

import logging
from datetime import datetime, timezone
from email.utils import format_datetime

from odoo import http
from odoo.http import request

from odoo.exceptions import AccessDenied
from odoo.addons.smart_core.security.auth import get_user_from_token

from .api_base import fail, ok

_logger = logging.getLogger(__name__)
_LEGACY_SCENES_SUNSET_DATE = "2026-04-30"
_LEGACY_SCENES_SUNSET_HTTP = format_datetime(
    datetime(2026, 4, 30, 0, 0, 0, tzinfo=timezone.utc), usegmt=True
)
_LEGACY_SCENES_SUCCESSOR = "/api/v1/intent"
_LEGACY_SCENES_ENDPOINT_NAME = "scenes.my"


def _has_admin(user):
    return user.has_group("smart_construction_core.group_sc_cap_config_admin") or user.has_group("base.group_system")


def _parse_bool(val, default=False):
    if val is None:
        return default
    if isinstance(val, bool):
        return val
    return str(val).strip().lower() in {"1", "true", "yes", "y"}


def _legacy_response_headers():
    return [
        ("Deprecation", "true"),
        ("Sunset", _LEGACY_SCENES_SUNSET_HTTP),
        ("X-Legacy-Endpoint", _LEGACY_SCENES_ENDPOINT_NAME),
        ("Link", f"<{_LEGACY_SCENES_SUCCESSOR}>; rel=\"successor-version\""),
    ]


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
                "deprecation": {
                    "status": "deprecated",
                    "replacement": f"{_LEGACY_SCENES_SUCCESSOR} (intent=app.init)",
                    "sunset_date": _LEGACY_SCENES_SUNSET_DATE,
                },
            }
            _logger.warning(
                "[legacy_endpoint] /api/scenes/my called by uid=%s include_tests=%s; successor=%s",
                user.id,
                include_tests,
                _LEGACY_SCENES_SUCCESSOR,
            )
            return ok(
                payload,
                status=200,
                headers=_legacy_response_headers(),
            )
        except AccessDenied as exc:
            return fail("AUTH_REQUIRED", str(exc), http_status=401, headers=_legacy_response_headers())
        except Exception:
            return fail("SERVER_ERROR", "Internal server error", http_status=500, headers=_legacy_response_headers())
