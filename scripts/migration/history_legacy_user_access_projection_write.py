#!/usr/bin/env python3
"""Project legacy user role and project-scope facts into runtime access."""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

from odoo import fields


def repo_root() -> Path:
    env_root = os.getenv("MIGRATION_REPO_ROOT")
    candidates = []
    if env_root:
        candidates.append(Path(env_root))
    candidates.extend([Path("/mnt"), Path.cwd()])
    for candidate in candidates:
        if (candidate / "addons/smart_construction_core/__manifest__.py").exists():
            return candidate
    return Path.cwd()


def resolve_artifact_root() -> Path:
    env_root = os.getenv("MIGRATION_ARTIFACT_ROOT")
    candidates = [Path(env_root)] if env_root else []
    candidates.append(repo_root() / "artifacts/migration")
    for candidate in candidates:
        try:
            candidate.mkdir(parents=True, exist_ok=True)
            probe = candidate / ".write_probe"
            probe.write_text("ok\n", encoding="utf-8")
            probe.unlink()
            return candidate
        except Exception:
            continue
    return Path(f"/tmp/history_continuity/{env.cr.dbname}/adhoc")  # noqa: F821


def ensure_allowed_db() -> None:
    allowlist = {
        item.strip()
        for item in os.getenv("MIGRATION_REPLAY_DB_ALLOWLIST", "sc_prod_sim,sc_migration_fresh").split(",")
        if item.strip()
    }
    if env.cr.dbname not in allowlist:  # noqa: F821
        raise RuntimeError({"db_name_not_allowed_for_projection": env.cr.dbname, "allowlist": sorted(allowlist)})  # noqa: F821


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def group(xmlid: str):
    try:
        return env.ref(xmlid)  # noqa: F821
    except ValueError:
        return env["res.groups"]  # noqa: F821


def role_group_xmlids(role_name: str) -> set[str]:
    name = (role_name or "").strip()
    groups: set[str] = set()
    if not name or name.isdigit() or "通用角色" in name or "管理员角色" in name:
        return groups

    manager_markers = ("经理", "负责人", "审批", "总经理", "董事长", "管理")
    is_manager = any(marker in name for marker in manager_markers)

    if any(marker in name for marker in ("项目", "工程", "施工", "资料", "机械", "项目部")):
        groups.add(
            "smart_construction_core.group_sc_cap_project_manager"
            if is_manager
            else "smart_construction_core.group_sc_cap_project_user"
        )
    if any(marker in name for marker in ("经营", "合同", "招投标")):
        groups.add(
            "smart_construction_core.group_sc_cap_contract_manager"
            if is_manager
            else "smart_construction_core.group_sc_cap_contract_user"
        )
    if any(marker in name for marker in ("财务", "出纳", "审计", "保证金")):
        groups.add(
            "smart_construction_core.group_sc_cap_finance_manager"
            if is_manager
            else "smart_construction_core.group_sc_cap_finance_user"
        )
    if "材料" in name:
        groups.add(
            "smart_construction_core.group_sc_cap_material_manager"
            if is_manager
            else "smart_construction_core.group_sc_cap_material_user"
        )
    if "采购" in name:
        groups.add(
            "smart_construction_core.group_sc_cap_purchase_manager"
            if is_manager
            else "smart_construction_core.group_sc_cap_purchase_user"
        )
    if any(marker in name for marker in ("成本", "成控", "预算")):
        groups.add(
            "smart_construction_core.group_sc_cap_cost_manager"
            if is_manager
            else "smart_construction_core.group_sc_cap_cost_user"
        )
    if "结算" in name:
        groups.add(
            "smart_construction_core.group_sc_cap_settlement_manager"
            if is_manager
            else "smart_construction_core.group_sc_cap_settlement_user"
        )

    if any(marker in name for marker in ("总经理", "副总经理", "董事长")):
        groups.update(
            {
                "smart_construction_core.group_sc_cap_project_manager",
                "smart_construction_core.group_sc_cap_contract_manager",
                "smart_construction_core.group_sc_cap_finance_manager",
                "smart_construction_core.group_sc_cap_material_manager",
                "smart_construction_core.group_sc_cap_purchase_manager",
                "smart_construction_core.group_sc_cap_cost_manager",
                "smart_construction_core.group_sc_cap_settlement_manager",
                "smart_construction_core.group_sc_cap_contact_manager",
                "smart_construction_core.group_sc_cap_data_read",
            }
        )

    return groups


def normalized_project_ref(raw: str | None) -> str | None:
    text = (raw or "").strip()
    if not text:
        return None
    bracketed = re.findall(r"\[([^\]]+)\]", text)
    if len(bracketed) == 1 and text == f"[{bracketed[0]}]":
        return bracketed[0].strip() or None
    if bracketed:
        return None
    return text


ensure_allowed_db()
artifact_root = resolve_artifact_root()
output_json = artifact_root / "history_legacy_user_access_projection_write_result_v1.json"

Role = env["sc.legacy.user.role"].sudo().with_context(active_test=False)  # noqa: F821
Scope = env["sc.legacy.user.project.scope"].sudo().with_context(active_test=False)  # noqa: F821
Project = env["project.project"].sudo().with_context(active_test=False)  # noqa: F821

roles_total = Role.search_count([])
roles_projected = 0
roles_unmapped = 0
user_group_links_added = 0
projected_users: set[int] = set()
projection_by_role: dict[str, int] = {}

for role in Role.search([]):
    xmlids = sorted(role_group_xmlids(role.role_name or ""))
    groups = env["res.groups"].sudo()  # noqa: F821
    for xmlid in xmlids:
        groups |= group(xmlid)
    before_group_ids = set(role.user_id.groups_id.ids) if role.user_id else set()
    if groups and role.user_id:
        role.user_id.sudo().write({"groups_id": [(4, group_id) for group_id in groups.ids]})
        after_group_ids = set(role.user_id.groups_id.ids)
        user_group_links_added += len(after_group_ids - before_group_ids)
        projected_users.add(role.user_id.id)
    role.write(
        {
            "projected_group_ids": [(6, 0, groups.ids)],
            "projection_state": "projected" if groups else "unmapped",
            "projection_note": "legacy role name projected to runtime capability groups" if groups else "no safe runtime mapping from legacy role name",
        }
    )
    if groups:
        roles_projected += 1
        projection_by_role[role.role_name or ""] = projection_by_role.get(role.role_name or "", 0) + 1
    else:
        roles_unmapped += 1

env.cr.execute(  # noqa: F821
    """
    WITH normalized AS (
      SELECT
        s.id AS scope_id,
        CASE
          WHEN COALESCE(s.project_legacy_id, '') ~ '^\\[[^\\]]+\\]$'
          THEN substring(s.project_legacy_id from '^\\[([^\\]]+)\\]$')
          WHEN COALESCE(s.project_legacy_id, '') LIKE '[%%'
          THEN NULL
          ELSE NULLIF(s.project_legacy_id, '')
        END AS project_ref
      FROM sc_legacy_user_project_scope s
    ),
    resolved AS (
      SELECT n.scope_id, n.project_ref, p.id AS project_id
      FROM normalized n
      JOIN project_project p ON p.legacy_parent_id::text = n.project_ref
      WHERE n.project_ref IS NOT NULL
    )
    UPDATE sc_legacy_user_project_scope s
       SET project_id = r.project_id,
           resolved_project_ref = r.project_ref,
           write_uid = %s,
           write_date = NOW()
      FROM resolved r
     WHERE s.id = r.scope_id
       AND (s.project_id IS DISTINCT FROM r.project_id OR s.resolved_project_ref IS DISTINCT FROM r.project_ref)
    """,
    [env.uid],  # noqa: F821
)
resolved_scope_updates = env.cr.rowcount  # noqa: F821

current_scopes = Scope.search([("scope_state", "=", "current"), ("user_id", "!=", False), ("project_id", "!=", False)])
eligible_project_scope_rows = len(current_scopes)
scope_access_applied = 0
subscriber_pairs_added = 0

project_user_group = group("smart_construction_core.group_sc_cap_project_user")
for scope in current_scopes:
    user = scope.user_id
    project = scope.project_id
    if project_user_group and project_user_group not in user.groups_id:
        before = set(user.groups_id.ids)
        user.sudo().write({"groups_id": [(4, project_user_group.id)]})
        user_group_links_added += len(set(user.groups_id.ids) - before)
        projected_users.add(user.id)
    partner = user.partner_id
    if partner and partner not in project.message_partner_ids:
        project.message_subscribe(partner_ids=[partner.id])
        subscriber_pairs_added += 1
    if not scope.project_access_applied:
        scope.write(
            {
                "project_access_applied": True,
                "project_access_note": "current legacy scope linked by project legacy_parent_id and applied as project follower access",
                "project_access_applied_at": fields.Datetime.now(),  # noqa: F821
            }
        )
        scope_access_applied += 1

env.cr.commit()  # noqa: F821

counts = {
    "legacy_roles_total": roles_total,
    "legacy_roles_projected": roles_projected,
    "legacy_roles_unmapped": roles_unmapped,
    "projected_users": len(projected_users),
    "user_group_links_added": user_group_links_added,
    "legacy_scope_rows_total": Scope.search_count([]),
    "legacy_scope_rows_current": Scope.search_count([("scope_state", "=", "current")]),
    "legacy_scope_rows_with_project": Scope.search_count([("project_id", "!=", False)]),
    "legacy_scope_rows_current_with_project": Scope.search_count([("scope_state", "=", "current"), ("project_id", "!=", False)]),
    "resolved_scope_updates": resolved_scope_updates,
    "eligible_project_scope_rows": eligible_project_scope_rows,
    "scope_access_applied": scope_access_applied,
    "subscriber_pairs_added": subscriber_pairs_added,
    "runtime_projects_with_legacy_follower": Project.search_count(
        [("message_partner_ids.user_ids.login", "like", "legacy_%"), ("legacy_project_id", "!=", False)]
    ),
}

payload = {
    "status": "PASS",
    "mode": "history_legacy_user_access_projection_write",
    "database": env.cr.dbname,  # noqa: F821
    "counts": counts,
    "projection_by_role": dict(sorted(projection_by_role.items(), key=lambda item: (-item[1], item[0]))),
    "db_writes": user_group_links_added + resolved_scope_updates + scope_access_applied + subscriber_pairs_added,
    "decision": "legacy_user_access_projected_to_runtime",
}
write_json(output_json, payload)
print("HISTORY_LEGACY_USER_ACCESS_PROJECTION_WRITE=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
