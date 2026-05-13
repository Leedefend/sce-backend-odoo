# -*- coding: utf-8 -*-
"""Platform-admin responsibility checks owned by smart_core."""

from __future__ import annotations

PLATFORM_ADMIN_GROUP = "smart_core.group_smart_core_admin"
LEGACY_PLATFORM_ADMIN_GROUP = "smart_construction_core.group_sc_cap_config_admin"
SYSTEM_ADMIN_GROUP = "base.group_system"


def user_is_platform_admin(user, *, include_system: bool = True) -> bool:
    if not user:
        return False
    group_xmlids = [PLATFORM_ADMIN_GROUP, LEGACY_PLATFORM_ADMIN_GROUP]
    if include_system:
        group_xmlids.append(SYSTEM_ADMIN_GROUP)
    for xmlid in group_xmlids:
        try:
            if user.has_group(xmlid):
                return True
        except Exception:
            continue
    return False


def platform_admin_groups(env, *, include_legacy: bool = True, include_system: bool = False):
    xmlids = [PLATFORM_ADMIN_GROUP]
    if include_legacy:
        xmlids.append(LEGACY_PLATFORM_ADMIN_GROUP)
    if include_system:
        xmlids.append(SYSTEM_ADMIN_GROUP)
    groups = []
    for xmlid in xmlids:
        group = env.ref(xmlid, raise_if_not_found=False)
        if group:
            groups.append(group)
    return groups
