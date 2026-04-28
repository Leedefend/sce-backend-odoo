"""Normalize prod-sim business chooser data surfaced to real users.

This script is intentionally scoped to simulated production databases. It
archives verification fixtures that leaked into relation pickers and hides
technical placeholder names from new business forms without deleting linked
business documents.
"""

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path


ALLOWLIST = {
    item.strip()
    for item in os.getenv("MIGRATION_REPLAY_DB_ALLOWLIST", "sc_prod_sim").split(",")
    if item.strip()
}


def artifact_root() -> Path:
    candidates = []
    env_root = os.getenv("MIGRATION_ARTIFACT_ROOT") or os.getenv("ARTIFACT_ROOT")
    if env_root:
        candidates.append(Path(env_root))
    candidates.extend([
        Path("/mnt/artifacts/migration"),
        Path(f"/tmp/prod_sim_business_surface_data_normalize/{env.cr.dbname}"),  # noqa: F821
    ])
    for root in candidates:
        try:
            root.mkdir(parents=True, exist_ok=True)
            probe = root / ".write_probe"
            probe.write_text("ok\n", encoding="utf-8")
            probe.unlink()
            return root
        except Exception:
            continue
    raise RuntimeError({"artifact_root_unavailable": [str(path) for path in candidates]})


db_name = env.cr.dbname
if db_name not in ALLOWLIST:
    raise RuntimeError(f"database {db_name!r} is not in MIGRATION_REPLAY_DB_ALLOWLIST")

Project = env["project.project"].sudo().with_context(active_test=False)
Partner = env["res.partner"].sudo().with_context(active_test=False)
Users = env["res.users"].sudo().with_context(active_test=False)
Contract = env["construction.contract"].sudo()
Diary = env["sc.construction.diary"].sudo() if "sc.construction.diary" in env else None

summary = {
    "mode": "prod_sim_business_surface_data_normalize_write",
    "database": db_name,
    "timestamp": datetime.now(timezone.utc).isoformat(),
    "archived_projects": [],
    "renamed_projects": [],
    "archived_partners": [],
    "archived_users": [],
    "renamed_partners": [],
}


def project_link_count(project):
    count = Contract.search_count([("project_id", "=", project.id)])
    if Diary:
        count += Diary.search_count([("project_id", "=", project.id)])
    return count


def archive_records(records, bucket):
    records = records.filtered(lambda rec: "active" in rec._fields and rec.active)
    if not records:
        return
    summary[bucket].extend([{"id": rec.id, "name": rec.display_name} for rec in records])
    records.write({"active": False})


def archive_partners(records):
    records = records.filtered(lambda rec: rec.active)
    if not records:
        return
    normal = Partner.browse()
    linked_to_inactive_users = Partner.browse()
    skipped = Partner.browse()
    for partner in records:
        users = Users.search([("partner_id", "=", partner.id)])
        if not users:
            normal |= partner
        elif all(not user.active for user in users):
            linked_to_inactive_users |= partner
        else:
            skipped |= partner
    if normal:
        archive_records(normal, "archived_partners")
    if linked_to_inactive_users:
        summary["archived_partners"].extend([
            {"id": rec.id, "name": rec.display_name, "method": "inactive_user_partner_sql"}
            for rec in linked_to_inactive_users
        ])
        env.cr.execute(
            "UPDATE res_partner SET active = false WHERE id = ANY(%s)",
            [linked_to_inactive_users.ids],
        )
        linked_to_inactive_users.invalidate_recordset(["active"])
    if skipped:
        summary.setdefault("skipped_partners", []).extend([
            {"id": rec.id, "name": rec.display_name, "reason": "linked_active_user"}
            for rec in skipped
        ])


role_smoke_projects = Project.search([("name", "=", "Role Smoke User")])
archive_records(role_smoke_projects, "archived_projects")

uuid_projects = Project.search([]).filtered(lambda rec: bool(re.fullmatch(r"[0-9a-f]{32}", (rec.name or "").strip())))
uuid_projects_without_links = uuid_projects.filtered(lambda rec: project_link_count(rec) == 0)
archive_records(uuid_projects_without_links, "archived_projects")
for project in uuid_projects - uuid_projects_without_links:
    old_name = project.name
    new_name = f"待确认项目-{old_name[:8]}"
    summary["renamed_projects"].append({"id": project.id, "old_name": old_name, "new_name": new_name})
    project.write({"name": new_name})

fixture_users = Users.search([
    "|",
    ("name", "ilike", "Fixture"),
    ("name", "=", "Business Full Smoke User"),
])
archive_records(fixture_users, "archived_users")
if summary["archived_users"]:
    env.flush_all()
    env.cr.commit()

fixture_partners = Partner.search([
    "|",
    ("name", "ilike", "Fixture"),
    ("name", "=", "Business Full Smoke User"),
])
archive_partners(fixture_partners)

unknown_partners = Partner.search([("name", "ilike", "Unknown legacy supplier")])
unknown_without_contracts = unknown_partners.filtered(lambda rec: Contract.search_count([("partner_id", "=", rec.id)]) == 0)
archive_partners(unknown_without_contracts)
for partner in unknown_partners - unknown_without_contracts:
    old_name = partner.name
    suffix = old_name.replace("Unknown legacy supplier-", "").strip() or str(partner.id)
    new_name = f"待确认供应商-{suffix}"
    summary["renamed_partners"].append({"id": partner.id, "old_name": old_name, "new_name": new_name})
    partner.write({"name": new_name})

env.flush_all()
env.cr.commit()

output = artifact_root() / "prod_sim_business_surface_data_normalize_result_v1.json"
output.write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
print("PROD_SIM_BUSINESS_SURFACE_DATA_NORMALIZE=" + json.dumps(summary, ensure_ascii=False, sort_keys=True))
