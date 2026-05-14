# -*- coding: utf-8 -*-
"""Platform-admin responsibility checks owned by smart_core."""

from __future__ import annotations

PLATFORM_ADMIN_GROUP = "smart_core.group_smart_core_admin"
LEGACY_PLATFORM_ADMIN_GROUP = "smart_construction_core.group_sc_cap_config_admin"
SYSTEM_ADMIN_GROUP = "base.group_system"


def platform_admin_group_xmlids(*, include_legacy: bool = True, include_system: bool = False) -> list[str]:
    xmlids = [PLATFORM_ADMIN_GROUP]
    if include_legacy:
        xmlids.append(LEGACY_PLATFORM_ADMIN_GROUP)
    if include_system:
        xmlids.append(SYSTEM_ADMIN_GROUP)
    return xmlids


def user_is_platform_admin(user, *, include_system: bool = True) -> bool:
    if not user:
        return False
    for xmlid in platform_admin_group_xmlids(include_legacy=True, include_system=include_system):
        try:
            if user.has_group(xmlid):
                return True
        except Exception:
            continue
    return False


def platform_admin_groups(env, *, include_legacy: bool = True, include_system: bool = False):
    groups = []
    for xmlid in platform_admin_group_xmlids(include_legacy=include_legacy, include_system=include_system):
        group = env.ref(xmlid, raise_if_not_found=False)
        if group:
            groups.append(group)
    return groups
