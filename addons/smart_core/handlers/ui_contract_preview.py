# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo import api


BUSINESS_CONFIG_GROUP = "smart_core.group_smart_core_business_config_admin"
PLATFORM_ADMIN_GROUP = "smart_core.group_smart_core_admin"


class PreviewAccessDenied(Exception):
    """Raised before projection when a caller cannot consume draft context."""


def build_projection_environments(env, su_env, params: dict, projection_context: dict):
    """Return read-only projection environments with an optional verified preview."""
    preview_token = str(params.get("preview_token") or params.get("previewToken") or "").strip()
    preview_role_key = str(params.get("preview_role_key") or params.get("previewRoleKey") or "").strip()
    if preview_token:
        user = env.user
        allowed = int(user.id or 0) == 1 or user.has_group(BUSINESS_CONFIG_GROUP) or user.has_group(PLATFORM_ADMIN_GROUP)
        if not allowed:
            raise PreviewAccessDenied
        projection_context.update({
            "business_config_preview_token": preview_token,
            "business_config_preview_user_id": int(user.id),
            "business_config_preview_role_key": preview_role_key,
        })
    try:
        return (
            api.Environment(env.cr, env.uid, projection_context),
            api.Environment(su_env.cr, su_env.uid, projection_context),
        )
    except Exception:
        return env, su_env
