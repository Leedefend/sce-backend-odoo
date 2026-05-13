# -*- coding: utf-8 -*-
"""Compatibility shim for platform-admin responsibility checks."""

from __future__ import annotations

from odoo.addons.smart_core.security.platform_admin import (
    LEGACY_PLATFORM_ADMIN_GROUP,
    PLATFORM_ADMIN_GROUP,
    SYSTEM_ADMIN_GROUP,
    platform_admin_groups,
    user_is_platform_admin,
)

__all__ = [
    "LEGACY_PLATFORM_ADMIN_GROUP",
    "PLATFORM_ADMIN_GROUP",
    "SYSTEM_ADMIN_GROUP",
    "platform_admin_groups",
    "user_is_platform_admin",
]
