# -*- coding: utf-8 -*-
from __future__ import annotations

import logging

_logger = logging.getLogger(__name__)


def resolve_release_actor_role_codes(user) -> list[str]:
    if not user:
        return []
    roles = set()
    try:
        group_xmlids = set(user.groups_id.get_external_id().values())
    except Exception:
        group_xmlids = set()
    prefix = "smart_construction_core.group_sc_role_"
    for xmlid in group_xmlids:
        text = str(xmlid or "").strip()
        role_prefix = prefix if text.startswith(prefix) else "smart_construction_custom.group_sc_role_"
        if text.startswith(role_prefix):
            roles.add(text[len(role_prefix):])
    try:
        if user.has_group("smart_construction_core.group_sc_cap_project_manager") or user.has_group("smart_construction_core.group_sc_cap_project_read"):
            roles.add("pm")
        if user.has_group("smart_construction_core.group_sc_super_admin") or user.has_group("smart_construction_core.group_sc_business_full"):
            roles.add("executive")
    except Exception:
        _logger.debug("Unable to resolve release actor role codes from groups.", exc_info=True)
    return sorted(roles)
