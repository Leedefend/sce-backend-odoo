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


def split_role_tokens(raw: str | None) -> list[str]:
    return [item.strip() for item in re.split(r"[,，;；/、\n]+", raw or "") if item.strip()]


def role_group_xmlids(role_name: str) -> set[str]:
    name = (role_name or "").strip()
    groups: set[str] = set()
    if not name or name.isdigit():
        return groups

    if "通用角色" in name or "行政部" in name or "公司员工" in name:
        groups.add("smart_construction_core.group_sc_role_general_user")
    if "管理员角色" in name:
        groups.add("smart_construction_core.group_sc_role_business_admin")
    if any(marker in name for marker in ("总经理", "副总经理", "董事长", "管理层")):
        groups.add("smart_construction_core.group_sc_role_executive")

    if "临时财务" in name or "受限财务" in name:
        groups.add("smart_construction_core.group_sc_role_temporary_finance")
    elif "财务经理" in name:
        groups.add("smart_construction_core.group_sc_role_finance_manager")
    elif any(marker in name for marker in ("财务助理", "财务部", "出纳", "财务", "税务经办")):
        groups.add("smart_construction_core.group_sc_role_finance_user")

    if any(marker in name for marker in ("经营部", "经营", "招投标")):
        groups.add("smart_construction_core.group_sc_role_operation_user")
    if any(marker in name for marker in ("合同管理员", "合同管理", "合同")):
        groups.add("smart_construction_core.group_sc_role_contract_admin")
    if any(marker in name for marker in ("客户", "供应商", "客商", "往来单位")):
        groups.add("smart_construction_core.group_sc_role_partner_manager")

    if any(marker in name for marker in ("项目负责人", "临时项目负责人", "项目经理")):
        groups.add("smart_construction_core.group_sc_role_project_manager")
    elif any(marker in name for marker in ("项目部", "工程部", "项目人员", "工程", "施工")):
        groups.add("smart_construction_core.group_sc_role_project_user")

    if any(marker in name for marker in ("物资主管", "材料主管")):
        groups.add("smart_construction_core.group_sc_role_material_manager")
    elif any(marker in name for marker in ("物资", "材料")):
        groups.add("smart_construction_core.group_sc_role_material_user")

    if "采购" in name:
        groups.add("smart_construction_core.group_sc_role_purchase_user")
    if any(marker in name for marker in ("成本", "成控", "预算")):
        groups.add("smart_construction_core.group_sc_role_cost_user")
    if "结算主管" in name:
        groups.add("smart_construction_core.group_sc_role_settlement_manager")
    elif "结算" in name:
        groups.add("smart_construction_core.group_sc_role_settlement_user")

    return groups


def role_group_xmlids_from_text(raw: str | None) -> set[str]:
    groups: set[str] = set()
    for token in split_role_tokens(raw):
        groups.update(role_group_xmlids(token))
    return groups


def cleanup_direct_runtime_groups(user, role_groups):
    assignable = env["res.groups"].sudo().search([("sc_assignable_user_permission", "=", True)])  # noqa: F821
    removable_xmlids = {
        "smart_construction_core.group_sc_cap_business_initiator",
        "smart_construction_core.group_sc_cap_project_read",
        "smart_construction_core.group_sc_cap_project_user",
        "smart_construction_core.group_sc_cap_project_manager",
        "smart_construction_core.group_sc_cap_contract_read",
        "smart_construction_core.group_sc_cap_contract_user",
        "smart_construction_core.group_sc_cap_contract_manager",
        "smart_construction_core.group_sc_cap_cost_read",
        "smart_construction_core.group_sc_cap_cost_user",
        "smart_construction_core.group_sc_cap_cost_manager",
        "smart_construction_core.group_sc_cap_material_read",
        "smart_construction_core.group_sc_cap_material_user",
        "smart_construction_core.group_sc_cap_material_manager",
        "smart_construction_core.group_sc_cap_purchase_read",
        "smart_construction_core.group_sc_cap_purchase_user",
        "smart_construction_core.group_sc_cap_purchase_manager",
        "smart_construction_core.group_sc_cap_finance_read",
        "smart_construction_core.group_sc_cap_finance_user",
        "smart_construction_core.group_sc_cap_finance_manager",
        "smart_construction_core.group_sc_cap_settlement_read",
        "smart_construction_core.group_sc_cap_settlement_user",
        "smart_construction_core.group_sc_cap_settlement_manager",
        "smart_construction_core.group_sc_cap_data_read",
        "smart_construction_core.group_sc_cap_contact_manager",
        "smart_construction_core.group_sc_cap_business_config_admin",
    }
    removable = env["res.groups"].sudo()  # noqa: F821
    for xmlid in removable_xmlids:
        removable |= group(xmlid)
    internal_group = group("smart_construction_core.group_sc_internal_user")
    keep_groups = user.groups_id - assignable - removable
    target_groups = keep_groups | role_groups
    if internal_group and not user.share:
        target_groups |= internal_group
    before_ids = set(user.groups_id.ids)
    user.sudo().write({"groups_id": [(6, 0, target_groups.ids)]})
    after_ids = set(user.groups_id.ids)
    return {"added": len(after_ids - before_ids), "removed": len(before_ids - after_ids)}


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
Profile = env["sc.legacy.user.profile"].sudo().with_context(active_test=False)  # noqa: F821
Scope = env["sc.legacy.user.project.scope"].sudo().with_context(active_test=False)  # noqa: F821
Project = env["project.project"].sudo().with_context(active_test=False)  # noqa: F821

roles_total = Role.search_count([])
roles_projected = 0
roles_unmapped = 0
user_group_links_added = 0
user_group_links_removed = 0
projected_users: set[int] = set()
projection_by_role: dict[str, int] = {}
projection_by_profile_role: dict[str, int] = {}

profiles_total = Profile.search_count([("user_id", "!=", False)])
profiles_projected = 0
profiles_unmapped = 0

for profile in Profile.search([("user_id", "!=", False)]):
    xmlids = role_group_xmlids_from_text(profile.role_summary)
    groups = env["res.groups"].sudo()  # noqa: F821
    for xmlid in sorted(xmlids):
        groups |= group(xmlid)
    if not groups:
        # Keep scoped project users operational even when the old role name is not explicit enough.
        has_current_scope = Scope.search_count(
            [("user_id", "=", profile.user_id.id), ("scope_state", "=", "current"), ("project_id", "!=", False)]
        )
        if has_current_scope:
            groups |= group("smart_construction_core.group_sc_role_project_user")
    if groups:
        delta = cleanup_direct_runtime_groups(profile.user_id, groups)
        user_group_links_added += delta["added"]
        user_group_links_removed += delta["removed"]
        projected_users.add(profile.user_id.id)
        profiles_projected += 1
        for token in split_role_tokens(profile.role_summary):
            projection_by_profile_role[token] = projection_by_profile_role.get(token, 0) + 1
    else:
        profiles_unmapped += 1

for role in Role.search([]):
    xmlids = sorted(role_group_xmlids(role.role_name or ""))
    groups = env["res.groups"].sudo()  # noqa: F821
    for xmlid in xmlids:
        groups |= group(xmlid)
    role.write(
        {
            "projected_group_ids": [(6, 0, groups.ids)],
            "projection_state": "projected" if groups and role.user_id else "unmapped",
            "projection_note": (
                "legacy role name projected to default business role groups"
                if groups
                else "no safe default business role mapping from legacy role name"
            ),
        }
    )
    if groups and role.user_id:
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

project_user_group = group("smart_construction_core.group_sc_role_project_user")
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
    "legacy_profiles_with_user_total": profiles_total,
    "legacy_profiles_projected_to_business_roles": profiles_projected,
    "legacy_profiles_unmapped_to_business_roles": profiles_unmapped,
    "legacy_roles_total": roles_total,
    "legacy_roles_projected": roles_projected,
    "legacy_roles_unmapped": roles_unmapped,
    "projected_users": len(projected_users),
    "user_group_links_added": user_group_links_added,
    "user_group_links_removed": user_group_links_removed,
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
    "projection_by_profile_role": dict(sorted(projection_by_profile_role.items(), key=lambda item: (-item[1], item[0]))),
    "db_writes": user_group_links_added + user_group_links_removed + resolved_scope_updates + scope_access_applied + subscriber_pairs_added,
    "decision": "legacy_user_access_projected_to_default_business_role_groups",
}
write_json(output_json, payload)
print("HISTORY_LEGACY_USER_ACCESS_PROJECTION_WRITE=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
