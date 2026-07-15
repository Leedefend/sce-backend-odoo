#!/usr/bin/env python3
"""Audit historical user role resolution without emitting user profile data."""

from __future__ import annotations

import json
import os
from collections import Counter
from pathlib import Path

from odoo.addons.smart_construction_core.core_extension_policy_maps import (
    ROLE_GROUPS_CAPABILITY_FALLBACK,
    ROLE_GROUPS_EXPLICIT,
    ROLE_PRECEDENCE,
    ROLE_SURFACE_OVERRIDES,
)
from odoo.addons.smart_core.identity.identity_resolver import IdentityResolver


def _resolver() -> IdentityResolver:
    resolver = IdentityResolver()
    resolver._role_groups_explicit = ROLE_GROUPS_EXPLICIT
    resolver._role_groups_capability_fallback = ROLE_GROUPS_CAPABILITY_FALLBACK
    resolver._role_precedence = ROLE_PRECEDENCE
    resolver._role_surface_map = {**resolver._role_surface_map, **ROLE_SURFACE_OVERRIDES}
    return resolver


resolver = _resolver()
Users = env["res.users"].sudo().with_context(active_test=False)  # noqa: F821
users = Users.search([("share", "=", False)], order="id asc")
role_counts = Counter()
source_counts = Counter()
active_role_counts = Counter()
restricted_ids = []
for user in users:
    xmlids = set(user.groups_id.get_external_id().values())
    role, evidence = resolver.resolve_role_code_with_evidence(xmlids)
    source = str((evidence or {}).get("source") or "missing")
    role_counts[role] += 1
    source_counts[source] += 1
    if user.active:
        active_role_counts[role] += 1
    if role == "restricted":
        restricted_ids.append(user.id)

legacy_role_rows = env["sc.legacy.user.role"].sudo().search(  # noqa: F821
    [("user_id", "in", restricted_ids), ("active", "=", True)]
)
legacy_role_name_counts = Counter(
    str(name or "missing") for name in legacy_role_rows.mapped("role_name")
)
payload = {
    "schema_version": 1,
    "database": env.cr.dbname,  # noqa: F821
    "internal_user_count": len(users),
    "role_counts": dict(sorted(role_counts.items())),
    "active_role_counts": dict(sorted(active_role_counts.items())),
    "source_counts": dict(sorted(source_counts.items())),
    "restricted_user_count": len(restricted_ids),
    "restricted_active_user_count": sum(1 for user in users if user.id in restricted_ids and user.active),
    "restricted_with_active_legacy_role_count": len(set(legacy_role_rows.mapped("user_id").ids)),
    "restricted_legacy_role_name_counts": dict(sorted(legacy_role_name_counts.items())),
    "database_writes": 0,
}
report = Path(os.getenv("USER_DATA_ROLE_REPORT_PATH", "/tmp/user-data-role-boundary.json"))
report.parent.mkdir(parents=True, exist_ok=True)
report.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
env.cr.rollback()  # noqa: F821
print("USER_DATA_ROLE_BOUNDARY=" + json.dumps(payload, sort_keys=True))
