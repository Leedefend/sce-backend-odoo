#!/usr/bin/env python3
"""Materialize legacy organization facts into hr.department without creating companies."""

from __future__ import annotations

import json
import os
import re
import hashlib
from pathlib import Path


ALLOWED_DBS = {
    item.strip()
    for item in os.getenv("MIGRATION_REPLAY_DB_ALLOWLIST", "sc_prod_sim").split(",")
    if item.strip()
}
MAIN_COMPANY_NAME = os.getenv("HISTORY_ORG_MAIN_COMPANY_NAME", "四川保盛建设集团有限公司").strip()
BRANCH_NAME_HINTS = ("分公司", "直属项目", "综合平台", "项目实施")
ROOT_PARENT_SENTINELS = {"-1", "0"}
FORMAL_DEPARTMENT_NAMES = {
    "四川保盛建设集团有限公司",
    "总经理",
    "工程部",
    "经营部",
    "财务部",
    "行政部",
    "综合行政部",
    "项目部",
    "材料部",
    "采购部",
    "成本部",
    "商务部",
    "质安部",
}
PROJECT_LIKE_TOKENS = (
    "工程",
    "项目",
    "施工",
    "改造",
    "维修",
    "建设",
    "总承包",
    "分包",
    "采购",
    "装修",
    "安装",
)


def artifact_root() -> Path:
    candidates = []
    env_root = os.getenv("MIGRATION_ARTIFACT_ROOT")
    if env_root:
        candidates.append(Path(env_root))
    candidates.append(Path("/mnt/artifacts/migration"))
    candidates.append(Path(f"/tmp/history_organization_department_materialize/{env.cr.dbname}"))  # noqa: F821
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


def clean_text(value) -> str:
    return str(value or "").strip()


def xml_name(prefix: str, raw: str) -> str:
    token = re.sub(r"[^0-9A-Za-z_]+", "_", clean_text(raw)).strip("_").lower()
    if token:
        return f"{prefix}_{token}"
    digest = hashlib.sha1(clean_text(raw).encode("utf-8")).hexdigest()[:12]
    return f"{prefix}_{digest}"


def external_record(xmlid_name: str, model: str, res_id: int):
    row = IMD.search([("module", "=", "migration_assets"), ("name", "=", xmlid_name)], limit=1)
    if row:
        if row.model != model or row.res_id != res_id:
            row.write({"model": model, "res_id": res_id})
        return row
    return IMD.create({"module": "migration_assets", "name": xmlid_name, "model": model, "res_id": res_id})


def record_by_external(xmlid_name: str, model: str):
    row = IMD.search([("module", "=", "migration_assets"), ("name", "=", xmlid_name), ("model", "=", model)], limit=1)
    if not row:
        return env[model].browse()  # noqa: F821
    return env[model].sudo().browse(row.res_id).exists()  # noqa: F821


def upsert_department(xmlid_name: str, vals: dict[str, object]) -> tuple[object, bool]:
    existing = record_by_external(xmlid_name, "hr.department")
    if existing:
        updates = {}
        for key, value in vals.items():
            current = getattr(existing, key)
            if hasattr(current, "id"):
                current = current.id
            if current != value:
                updates[key] = value
        if updates:
            existing.write(updates)
        return existing, False
    department = Department.create(vals)
    external_record(xmlid_name, "hr.department", department.id)
    return department, True


def legacy_department_xmlid(legacy_id: str) -> str:
    return xml_name("legacy_department_sc", legacy_id)


def branch_department_xmlid(company_legacy_id: str, name: str) -> str:
    return xml_name("legacy_branch_department_sc", f"{company_legacy_id}_{name}")


def is_root_parent(parent_legacy_id: str) -> bool:
    return not parent_legacy_id or parent_legacy_id in ROOT_PARENT_SENTINELS


def should_materialize_formal_department(legacy) -> bool:
    name = clean_text(legacy.name)
    if not name:
        return False
    legacy_id = clean_text(legacy.legacy_department_id)
    if name == MAIN_COMPANY_NAME and legacy_id != "1":
        return False
    if "保证金" in name:
        return False
    if legacy_id == "1" or name in FORMAL_DEPARTMENT_NAMES:
        return True
    if any(token in name for token in PROJECT_LIKE_TOKENS):
        return False
    if any(hint in name for hint in BRANCH_NAME_HINTS) and len(name) <= 20:
        return True
    return clean_text(legacy.is_child_company) == "1"


if env.cr.dbname not in ALLOWED_DBS:  # noqa: F821
    raise RuntimeError({"db_name_not_allowed_for_org_materialize": env.cr.dbname, "allowlist": sorted(ALLOWED_DBS)})  # noqa: F821

if "hr.department" not in env:  # noqa: F821
    raise RuntimeError({"hr_department_unavailable": "Install/upgrade hr dependency before materializing organization."})

Department = env["hr.department"].sudo().with_context(active_test=False)  # noqa: F821
LegacyDepartment = env["sc.legacy.department"].sudo().with_context(active_test=False)  # noqa: F821
Profile = env["sc.legacy.user.profile"].sudo().with_context(active_test=False)  # noqa: F821
Role = env["sc.legacy.user.role"].sudo().with_context(active_test=False)  # noqa: F821
IMD = env["ir.model.data"].sudo()  # noqa: F821
Company = env["res.company"].sudo()  # noqa: F821

main_company = Company.search([("name", "=", MAIN_COMPANY_NAME)], limit=1) or env.company  # noqa: F821
if not main_company:
    raise RuntimeError({"main_company_not_found": MAIN_COMPANY_NAME})

created = []
updated = []
archived_non_formal = []
archived_duplicate_formal = []
linked_profiles = 0
legacy_parent_linked = 0
derived_departments = []
derived_parent_departments = []
missing_parent_legacy_ids: set[str] = set()
recursive_parent_links: list[dict[str, str]] = []
parent_write_errors: list[dict[str, str]] = []

legacy_rows = LegacyDepartment.search([], order="legacy_department_id,id")
legacy_by_id = {clean_text(row.legacy_department_id): row for row in legacy_rows if clean_text(row.legacy_department_id)}

profile_department_facts: dict[str, str] = {}
for profile in Profile.search([("legacy_department_id", "not in", [False, ""])]):
    legacy_id = clean_text(profile.legacy_department_id)
    if not legacy_id or legacy_id in legacy_by_id or legacy_id in profile_department_facts:
        continue
    profile_department_facts[legacy_id] = clean_text(profile.department_name)

for legacy_id, department_name in sorted(profile_department_facts.items(), key=lambda item: item[0]):
    department = LegacyDepartment.create(
        {
            "legacy_department_id": legacy_id,
            "name": department_name or f"legacy_department_{legacy_id}",
            "source_table": "BASE_SYSTEM_USER.department_derived",
            "note": "Derived from sc.legacy.user.profile because the legacy department fact row was absent.",
            "active": True,
        }
    )
    legacy_by_id[legacy_id] = department
    derived_departments.append(
        {
            "legacy_department_id": legacy_id,
            "name": department.name,
            "legacy_department_record_id": department.id,
            "source": "sc.legacy.user.profile",
        }
    )

if derived_departments:
    legacy_rows = LegacyDepartment.search([], order="legacy_department_id,id")
    legacy_by_id = {clean_text(row.legacy_department_id): row for row in legacy_rows if clean_text(row.legacy_department_id)}

missing_parent_facts = sorted(
    {
        clean_text(row.parent_legacy_department_id)
        for row in legacy_rows
        if clean_text(row.parent_legacy_department_id)
        and clean_text(row.parent_legacy_department_id) not in ROOT_PARENT_SENTINELS
        and clean_text(row.parent_legacy_department_id) not in legacy_by_id
    }
)
for parent_legacy_id in missing_parent_facts:
    department = LegacyDepartment.create(
        {
            "legacy_department_id": parent_legacy_id,
            "name": f"legacy_department_{parent_legacy_id}",
            "source_table": "BASE_ORGANIZATION_DEPARTMENT.parent_derived",
            "note": "Derived from child department parent_legacy_department_id because the parent fact row was absent.",
            "active": True,
        }
    )
    legacy_by_id[parent_legacy_id] = department
    derived_parent_departments.append(
        {
            "legacy_department_id": parent_legacy_id,
            "name": department.name,
            "legacy_department_record_id": department.id,
            "source": "sc.legacy.department.parent_legacy_department_id",
        }
    )

if derived_parent_departments:
    legacy_rows = LegacyDepartment.search([], order="legacy_department_id,id")
    legacy_by_id = {clean_text(row.legacy_department_id): row for row in legacy_rows if clean_text(row.legacy_department_id)}


def safe_parent_link(child_legacy_id: str, parent_legacy_id: str) -> bool:
    if not parent_legacy_id:
        return True
    if child_legacy_id == parent_legacy_id:
        recursive_parent_links.append({"legacy_department_id": child_legacy_id, "parent_legacy_department_id": parent_legacy_id})
        return False
    seen = {child_legacy_id}
    current = parent_legacy_id
    while current:
        if current in seen:
            recursive_parent_links.append({"legacy_department_id": child_legacy_id, "parent_legacy_department_id": parent_legacy_id})
            return False
        seen.add(current)
        parent = legacy_by_id.get(current)
        if not parent:
            return True
        current = clean_text(parent.parent_legacy_department_id)
    return True

for legacy in legacy_rows:
    legacy_id = clean_text(legacy.legacy_department_id)
    if not legacy_id:
        continue
    if not should_materialize_formal_department(legacy):
        existing = record_by_external(legacy_department_xmlid(legacy_id), "hr.department")
        if existing and existing.active:
            existing.write({"active": False})
            archived_non_formal.append(
                {
                    "legacy_department_id": legacy_id,
                    "hr_department_id": existing.id,
                    "name": existing.name,
                    "reason": "project_or_non_formal_legacy_department",
                }
            )
        continue
    dept, was_created = upsert_department(
        legacy_department_xmlid(legacy_id),
        {
            "name": clean_text(legacy.name) or f"legacy_department_{legacy_id}",
            "company_id": main_company.id,
            "active": True,
        },
    )
    (created if was_created else updated).append(
        {
            "legacy_department_id": legacy_id,
            "hr_department_id": dept.id,
            "name": dept.name,
            "source": "sc.legacy.department",
            "created": was_created,
        }
    )

for legacy in legacy_rows:
    legacy_id = clean_text(legacy.legacy_department_id)
    if not legacy_id:
        continue
    if not should_materialize_formal_department(legacy):
        continue
    dept = record_by_external(legacy_department_xmlid(legacy_id), "hr.department")
    if not dept:
        continue
    parent_legacy_id = clean_text(legacy.parent_legacy_department_id)
    if is_root_parent(parent_legacy_id):
        parent_legacy_id = ""
    if not safe_parent_link(legacy_id, parent_legacy_id):
        continue
    parent_department = record_by_external(legacy_department_xmlid(parent_legacy_id), "hr.department") if parent_legacy_id else Department.browse()
    if parent_legacy_id and not parent_department:
        missing_parent_legacy_ids.add(parent_legacy_id)
    if parent_department and dept.parent_id != parent_department:
        try:
            with env.cr.savepoint():  # noqa: F821
                dept.write({"parent_id": parent_department.id})
        except Exception as exc:
            parent_write_errors.append(
                {
                    "legacy_department_id": legacy_id,
                    "parent_legacy_department_id": parent_legacy_id,
                    "error": str(exc),
                }
            )
            continue
    if parent_legacy_id and legacy.parent_id != legacy_by_id.get(parent_legacy_id):
        legacy_parent = legacy_by_id.get(parent_legacy_id)
        if legacy_parent:
            legacy.write({"parent_id": legacy_parent.id})
            legacy_parent_linked += 1

root_department = record_by_external(legacy_department_xmlid("1"), "hr.department")
role_department_created = []
role_department_seen = []
stale_role_department = record_by_external("legacy_role_department_sc_empty", "hr.department")
if stale_role_department and stale_role_department.active:
    stale_role_department.write({"active": False})
    archived_non_formal.append(
        {
            "legacy_department_id": "legacy_role_department_sc_empty",
            "hr_department_id": stale_role_department.id,
            "name": stale_role_department.name,
            "reason": "stale_chinese_role_department_external_id_collision",
        }
    )
role_names = {
    clean_text(row["role_name"])
    for row in Role.search_read([("role_name", "not in", [False, ""])], ["role_name"])
}
role_names.update({"综合行政部"})
for name in sorted(role_names.intersection(FORMAL_DEPARTMENT_NAMES - {MAIN_COMPANY_NAME})):
    xmlid_name = xml_name("legacy_role_department_sc", name)
    existing_same_name = Department.search(
        [
            ("name", "=", name),
            ("company_id", "=", main_company.id),
            ("active", "=", True),
        ],
        order="id",
        limit=1,
    )
    if existing_same_name:
        stale_role_department = record_by_external(xmlid_name, "hr.department")
        if stale_role_department and stale_role_department.id != existing_same_name.id and stale_role_department.active:
            stale_role_department.write({"active": False})
            archived_non_formal.append(
                {
                    "legacy_department_id": xmlid_name,
                    "hr_department_id": stale_role_department.id,
                    "name": stale_role_department.name,
                    "reason": "duplicate_role_department_replaced_by_legacy_department",
                }
            )
        external_record(xmlid_name, "hr.department", existing_same_name.id)
        role_department_seen.append(
            {
                "name": existing_same_name.name,
                "hr_department_id": existing_same_name.id,
                "created": False,
                "source": "sc.legacy.user.role.role_name",
            }
        )
        continue
    dept, was_created = upsert_department(
        xmlid_name,
        {
            "name": name,
            "company_id": main_company.id,
            "parent_id": root_department.id if root_department else False,
            "active": True,
        },
    )
    (role_department_created if was_created else role_department_seen).append(
        {
            "name": dept.name,
            "hr_department_id": dept.id,
            "created": was_created,
            "source": "sc.legacy.user.role.role_name",
        }
    )

for name in sorted(FORMAL_DEPARTMENT_NAMES):
    duplicates = Department.search(
        [
            ("name", "=", name),
            ("company_id", "=", main_company.id),
            ("active", "=", True),
        ],
        order="id",
    )
    if len(duplicates) <= 1:
        continue
    canonical = duplicates[0]
    for duplicate in duplicates[1:]:
        for row in IMD.search([("model", "=", "hr.department"), ("res_id", "=", duplicate.id)]):
            row.write({"res_id": canonical.id})
        duplicate.write({"active": False})
        archived_duplicate_formal.append(
            {
                "name": duplicate.name,
                "hr_department_id": duplicate.id,
                "canonical_hr_department_id": canonical.id,
                "reason": "duplicate_formal_department_name",
            }
        )

for profile in Profile.search([("legacy_department_id", "not in", [False, ""])]):
    legacy = legacy_by_id.get(clean_text(profile.legacy_department_id))
    if legacy and profile.department_id != legacy:
        profile.write({"department_id": legacy.id})
        linked_profiles += 1

branch_created = []
branch_seen: set[tuple[str, str]] = set()
project_model = env["project.project"].sudo().with_context(active_test=False) if "project.project" in env else None  # noqa: F821
if project_model and {"legacy_company_id", "legacy_company_name"}.issubset(project_model._fields):
    rows = project_model.read_group(
        [("legacy_company_name", "not in", [False, "", MAIN_COMPANY_NAME])],
        ["legacy_company_id", "legacy_company_name"],
        ["legacy_company_id", "legacy_company_name"],
        lazy=False,
    )
    for row in rows:
        name = clean_text(row.get("legacy_company_name"))
        company_legacy_id = clean_text(row.get("legacy_company_id"))
        if not name or not any(hint in name for hint in BRANCH_NAME_HINTS):
            continue
        key = (company_legacy_id, name)
        if key in branch_seen:
            continue
        branch_seen.add(key)
        dept, was_created = upsert_department(
            branch_department_xmlid(company_legacy_id, name),
            {
                "name": name,
                "company_id": main_company.id,
                "active": True,
            },
        )
        branch_created.append(
            {
                "legacy_company_id": company_legacy_id,
                "name": name,
                "hr_department_id": dept.id,
                "created": was_created,
                "source": "legacy_company_as_department",
            }
        )

env.cr.commit()  # noqa: F821
payload = {
    "status": "PASS",
    "database": env.cr.dbname,  # noqa: F821
    "mode": "history_organization_department_materialize_write",
    "decision": "legacy_departments_and_branch_units_materialized_as_hr_department",
    "main_company": {"id": main_company.id, "name": main_company.name},
    "legacy_department_count": len(legacy_rows),
    "derived_department_count": len(derived_departments),
    "derived_parent_department_count": len(derived_parent_departments),
    "created_count": sum(1 for row in created if row["created"]),
    "updated_or_seen_count": len(updated),
    "archived_non_formal_count": len(archived_non_formal),
    "archived_duplicate_formal_count": len(archived_duplicate_formal),
    "branch_department_count": len(branch_created),
    "role_department_count": len(role_department_created) + len(role_department_seen),
    "role_department_created_count": len(role_department_created),
    "linked_profiles": linked_profiles,
    "legacy_parent_linked": legacy_parent_linked,
    "missing_parent_legacy_ids": sorted(missing_parent_legacy_ids),
    "recursive_parent_links": recursive_parent_links,
    "parent_write_errors": parent_write_errors,
    "derived_departments_sample": derived_departments[:20],
    "derived_parent_departments_sample": derived_parent_departments[:20],
    "created_sample": [row for row in created if row["created"]][:20],
    "archived_non_formal_sample": archived_non_formal[:20],
    "archived_duplicate_formal_sample": archived_duplicate_formal[:20],
    "role_departments": role_department_created + role_department_seen,
    "branch_departments": branch_created,
    "db_writes": len(created) + len(updated) + len(archived_non_formal) + len(archived_duplicate_formal) + len(branch_created) + len(role_department_created) + len(role_department_seen) + linked_profiles + legacy_parent_linked,
}
output = artifact_root() / "history_organization_department_materialize_write_result_v1.json"
output.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print("HISTORY_ORGANIZATION_DEPARTMENT_MATERIALIZE_WRITE=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
