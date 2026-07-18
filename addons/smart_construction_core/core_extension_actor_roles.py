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
        if text.startswith(prefix):
            roles.add(text[len(prefix):])
    try:
        if user.has_group("smart_construction_core.group_sc_cap_project_manager"):
            roles.add("pm")
        elif user.has_group("smart_construction_core.group_sc_cap_project_read"):
            roles.add("project_member")
        if user.has_group("smart_construction_core.group_sc_super_admin") or user.has_group("smart_construction_core.group_sc_business_full"):
            roles.add("executive")
    except Exception:
        _logger.debug("Unable to resolve release actor role codes from groups.", exc_info=True)
    return sorted(roles)
