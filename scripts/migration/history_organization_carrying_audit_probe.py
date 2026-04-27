#!/usr/bin/env python3
"""Audit legacy branch-company and department facts against current organization carriers."""

from __future__ import annotations

import json
import os
from pathlib import Path


def artifact_root() -> Path:
    candidates = []
    env_root = os.getenv("MIGRATION_ARTIFACT_ROOT")
    if env_root:
        candidates.append(Path(env_root))
    candidates.append(Path("/mnt/artifacts/migration"))
    candidates.append(Path(f"/tmp/history_organization_carrying/{env.cr.dbname}"))  # noqa: F821
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


def model_exists(model_name: str) -> bool:
    return model_name in env  # noqa: F821


def field_exists(model_name: str, field_name: str) -> bool:
    return model_exists(model_name) and field_name in env[model_name]._fields  # noqa: F821


def count(model_name: str, domain=None, *, active_test=False) -> int | None:
    if not model_exists(model_name):
        return None
    return int(env[model_name].sudo().with_context(active_test=active_test).search_count(domain or []))  # noqa: F821


def text_domain(field_name: str) -> list[tuple[str, str, object]]:
    return [(field_name, "not in", [False, ""])]


def parent_text_domain() -> list[tuple[str, str, object]]:
    return [("parent_legacy_department_id", "not in", [False, "", "-1", "0"])]


def distinct_values(model_name: str, field_name: str, *, limit: int = 20) -> dict[str, object]:
    if not field_exists(model_name, field_name):
        return {"model": model_name, "field": field_name, "available": False}
    Model = env[model_name].sudo().with_context(active_test=False)  # noqa: F821
    rows = Model.read_group(text_domain(field_name), [field_name], [field_name], lazy=False)
    values = []
    for row in rows:
        raw = row.get(field_name)
        if isinstance(raw, (tuple, list)):
            raw = raw[1] if len(raw) > 1 else raw[0]
        value = str(raw or "").strip()
        if value:
            values.append({"value": value, "count": int(row.get("__count") or 0)})
    values.sort(key=lambda item: (-item["count"], item["value"]))
    return {
        "model": model_name,
        "field": field_name,
        "available": True,
        "distinct_count": len(values),
        "row_count_with_value": sum(item["count"] for item in values),
        "sample": values[:limit],
    }


def sample_records(model_name: str, fields: list[str], domain=None, *, limit: int = 8) -> list[dict[str, object]]:
    if not model_exists(model_name):
        return []
    available_fields = [field for field in fields if field_exists(model_name, field)]
    if not available_fields:
        return []
    records = env[model_name].sudo().with_context(active_test=False).search(domain or [], limit=limit)  # noqa: F821
    return records.read(available_fields)


def legacy_department_summary() -> dict[str, object]:
    model = "sc.legacy.department"
    if not model_exists(model):
        return {"model": model, "exists": False}
    total = count(model) or 0
    with_parent_ref = count(model, parent_text_domain()) if field_exists(model, "parent_legacy_department_id") else None
    with_parent_link = (
        count(model, parent_text_domain() + [("parent_id", "!=", False)])
        if field_exists(model, "parent_legacy_department_id") and field_exists(model, "parent_id")
        else None
    )
    is_company = distinct_values(model, "is_company")
    is_child_company = distinct_values(model, "is_child_company")
    state = distinct_values(model, "state")
    root_count = count(model, [("parent_legacy_department_id", "in", [False, ""])]) if field_exists(model, "parent_legacy_department_id") else None
    return {
        "model": model,
        "exists": True,
        "total": total,
        "active": count(model, [("active", "=", True)]) if field_exists(model, "active") else None,
        "root_count": root_count,
        "with_parent_legacy_ref": with_parent_ref,
        "with_parent_record_link": with_parent_link,
        "parent_link_gap_count": (
            max(0, int(with_parent_ref or 0) - int(with_parent_link or 0))
            if with_parent_ref is not None and with_parent_link is not None
            else None
        ),
        "is_company": is_company,
        "is_child_company": is_child_company,
        "state": state,
        "sample": sample_records(
            model,
            [
                "legacy_department_id",
                "name",
                "parent_legacy_department_id",
                "depth",
                "identity_path",
                "is_company",
                "is_child_company",
                "charge_leader_legacy_user_id",
                "charge_leader_name",
            ],
            limit=10,
        ),
    }


def user_department_summary() -> dict[str, object]:
    model = "sc.legacy.user.profile"
    if not model_exists(model):
        return {"model": model, "exists": False}
    total = count(model) or 0
    with_dept_legacy = count(model, text_domain("legacy_department_id")) if field_exists(model, "legacy_department_id") else None
    with_legacy_department_link = count(model, [("department_id", "!=", False)]) if field_exists(model, "department_id") else None
    with_res_user = count(model, [("user_id", "!=", False)]) if field_exists(model, "user_id") else None
    active_user_with_dept = 0
    missing_legacy_department_link = 0
    if field_exists(model, "user_id") and field_exists(model, "legacy_department_id"):
        Profile = env[model].sudo().with_context(active_test=False)  # noqa: F821
        for profile in Profile.search([("user_id", "!=", False), ("legacy_department_id", "not in", [False, ""])]):
            if profile.user_id.active:
                active_user_with_dept += 1
                if field_exists(model, "department_id") and not profile.department_id:
                    missing_legacy_department_link += 1
    return {
        "model": model,
        "exists": True,
        "total": total,
        "with_res_user": with_res_user,
        "with_legacy_department_id": with_dept_legacy,
        "with_legacy_department_record_link": with_legacy_department_link,
        "active_user_with_legacy_department": active_user_with_dept,
        "active_user_missing_legacy_department_record_link": missing_legacy_department_link,
        "department_names": distinct_values(model, "department_name"),
        "sample": sample_records(
            model,
            ["legacy_user_id", "display_name", "generated_login", "legacy_department_id", "department_name", "user_id"],
            [("legacy_department_id", "not in", [False, ""])],
            limit=10,
        ),
    }


def formal_org_summary() -> dict[str, object]:
    companies = []
    for company in env["res.company"].sudo().search([], order="id"):  # noqa: F821
        companies.append({"id": company.id, "name": company.name})
    departments = {"model": "hr.department", "exists": model_exists("hr.department")}
    if model_exists("hr.department"):
        departments.update(
            {
                "total": count("hr.department") or 0,
                "with_company": count("hr.department", [("company_id", "!=", False)]) if field_exists("hr.department", "company_id") else None,
                "sample": sample_records("hr.department", ["name", "company_id", "parent_id", "manager_id"], limit=10),
            }
        )
    return {
        "res_company": {"total": len(companies), "companies": companies},
        "hr_department": departments,
    }


def business_org_field_summary() -> list[dict[str, object]]:
    specs = [
        ("project.project", ["legacy_company_id", "legacy_company_name"]),
        ("sc.legacy.user.role", ["company_legacy_id"]),
        ("sc.legacy.user.project.scope", ["company_legacy_id"]),
        ("sc.legacy.salary.line", ["company_legacy_id", "company_name", "department_legacy_id", "department_name", "department_summary_legacy_id", "department_summary"]),
        ("sc.legacy.expense.reimbursement.line", ["company_legacy_id", "company_name", "department_legacy_id", "department_name"]),
        ("sc.legacy.personnel.movement", ["department_legacy_id", "department_name", "position_legacy_id"]),
        ("sc.legacy.attendance.checkin", ["department_legacy_id", "department_name"]),
        ("sc.legacy.purchase.contract.fact", ["applicant_department_legacy_id", "applicant_department"]),
    ]
    rows = []
    for model_name, fields in specs:
        if not model_exists(model_name):
            rows.append({"model": model_name, "exists": False})
            continue
        model_row = {"model": model_name, "exists": True, "total": count(model_name) or 0, "fields": []}
        for field in fields:
            model_row["fields"].append(distinct_values(model_name, field, limit=12))
        rows.append(model_row)
    return rows


BRANCH_COMPANY_POLICY = "legacy_branch_company_as_hr_department_org_unit"
legacy_department = legacy_department_summary()
user_department = user_department_summary()
formal_org = formal_org_summary()
business_fields = business_org_field_summary()

gap_items = []
legacy_department_total = int(legacy_department.get("total") or 0)
hr_department_total = int((formal_org.get("hr_department") or {}).get("total") or 0)
if legacy_department_total and not hr_department_total:
    hr_exists = bool((formal_org.get("hr_department") or {}).get("exists"))
    gap_items.append(
        {
            "code": "legacy_departments_not_formally_materialized",
            "severity": "P0",
            "detail": (
                "Legacy departments exist only in sc.legacy.department; "
                + ("hr.department has no rows." if hr_exists else "hr.department is not available in the current module set.")
            ),
        }
    )
if int(legacy_department.get("parent_link_gap_count") or 0):
    gap_items.append(
        {
            "code": "legacy_department_tree_parent_link_gap",
            "severity": "P1",
            "detail": f"{legacy_department.get('parent_link_gap_count')} legacy departments have parent text but no parent record link.",
        }
    )
if int(user_department.get("active_user_missing_legacy_department_record_link") or 0):
    gap_items.append(
        {
            "code": "active_user_department_link_gap",
            "severity": "P0",
            "detail": f"{user_department.get('active_user_missing_legacy_department_record_link')} active mapped users have legacy department id but no legacy department record link.",
        }
    )

branch_candidate_fields = []
for row in business_fields:
    for field in row.get("fields", []):
        field_name = field.get("field")
        if field.get("available") and field_name and "company" in field_name and int(field.get("distinct_count") or 0) > 1:
            branch_candidate_fields.append(
                {
                    "model": row["model"],
                    "field": field_name,
                    "distinct_count": field.get("distinct_count"),
                    "sample": field.get("sample"),
                }
            )
if branch_candidate_fields and len((formal_org.get("res_company") or {}).get("companies") or []) == 1:
    if hr_department_total:
        branch_company_carrying = {
            "policy": BRANCH_COMPANY_POLICY,
            "status": "carried_as_organization_unit",
            "evidence": branch_candidate_fields[:8],
        }
    else:
        branch_company_carrying = {
            "policy": BRANCH_COMPANY_POLICY,
            "status": "gap_no_formal_org_unit_carrier",
            "evidence": branch_candidate_fields[:8],
        }
        gap_items.append(
            {
                "code": "branch_company_facts_not_formally_carried_as_org_unit",
                "severity": "P1",
                "detail": "Multiple legacy branch-company ids/names are present; policy forbids creating res.company for branches, but no formal department/org-unit carrier is available yet.",
                "evidence": branch_candidate_fields[:8],
            }
        )
else:
    branch_company_carrying = {
        "policy": BRANCH_COMPANY_POLICY,
        "status": "no_branch_company_field_gap_detected",
        "evidence": branch_candidate_fields[:8],
    }

payload = {
    "status": "PASS",
    "database": env.cr.dbname,  # noqa: F821
    "mode": "history_organization_carrying_audit_probe",
    "decision": "organization_carrying_gap_present" if gap_items else "organization_carrying_ready",
    "db_writes": 0,
    "gap_count": len(gap_items),
    "gaps": gap_items,
    "formal_organization": formal_org,
    "branch_company_carrying": branch_company_carrying,
    "legacy_department": legacy_department,
    "user_department": user_department,
    "business_org_fields": business_fields,
}

root = artifact_root()
output_json = root / "history_organization_carrying_audit_probe_result_v1.json"
output_report = root / "history_organization_carrying_audit_probe_report_v1.md"
output_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
report = [
    "# History Organization Carrying Audit v1",
    "",
    f"Status: {payload['status']}",
    f"Decision: `{payload['decision']}`",
    f"Gap count: {payload['gap_count']}",
    "",
    "## Gaps",
    "",
    "```json",
    json.dumps(gap_items, ensure_ascii=False, indent=2),
    "```",
    "",
    "## Formal Organization",
    "",
    "```json",
    json.dumps(formal_org, ensure_ascii=False, indent=2),
    "```",
    "",
    "## Legacy Department",
    "",
    "```json",
    json.dumps(legacy_department, ensure_ascii=False, indent=2),
    "```",
    "",
    "## User Department",
    "",
    "```json",
    json.dumps(user_department, ensure_ascii=False, indent=2),
    "```",
]
output_report.write_text("\n".join(report) + "\n", encoding="utf-8")
print(
    "HISTORY_ORGANIZATION_CARRYING_AUDIT_PROBE="
    + json.dumps(
        {
            "status": payload["status"],
            "database": payload["database"],
            "decision": payload["decision"],
            "gap_count": payload["gap_count"],
            "gaps": gap_items,
            "legacy_department_total": legacy_department.get("total"),
            "hr_department_total": (formal_org.get("hr_department") or {}).get("total"),
            "active_user_with_legacy_department": user_department.get("active_user_with_legacy_department"),
            "branch_company_carrying_status": branch_company_carrying.get("status"),
        },
        ensure_ascii=False,
        sort_keys=True,
    )
)
