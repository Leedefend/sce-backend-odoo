# -*- coding: utf-8 -*-
"""Historical import facade for canonical smart_core platform-admin checks."""

from __future__ import annotations

from odoo.addons.smart_core.security.platform_admin import (
    LEGACY_PLATFORM_ADMIN_GROUP,
    PLATFORM_ADMIN_GROUP,
    SYSTEM_ADMIN_GROUP,
    platform_admin_group_xmlids,
    platform_admin_groups,
    user_is_platform_admin,
)

__all__ = [
    "LEGACY_PLATFORM_ADMIN_GROUP",
    "PLATFORM_ADMIN_GROUP",
    "SYSTEM_ADMIN_GROUP",
    "platform_admin_group_xmlids",
    "platform_admin_groups",
    "user_is_platform_admin",
]
