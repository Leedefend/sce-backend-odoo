#!/usr/bin/env python3
"""Initialize SCBS direct projects for the new-system runtime project list.

This is not a history replay step. It only normalizes the user-visible runtime
surface for the 40 user-confirmed direct projects created from SCBS facts.
"""

from __future__ import annotations

import json
import os
from collections import Counter
from pathlib import Path


def artifact_root() -> Path:
    root = Path(os.getenv("MIGRATION_ARTIFACT_ROOT", "/mnt/artifacts/migration"))
    root.mkdir(parents=True, exist_ok=True)
    return root


def clean(value: object) -> str:
    if value is None or value is False:
        return ""
    return str(value).strip()


def money(value: object) -> float:
    return round(float(value or 0.0), 2)


ARTIFACT_ROOT = artifact_root()
OUTPUT_JSON = ARTIFACT_ROOT / "scbs_direct_project_runtime_surface_write_result_v1.json"
OUTPUT_MD = ARTIFACT_ROOT / "scbs_direct_project_runtime_surface_write_report_v1.md"

Project = env["project.project"].sudo().with_context(active_test=False)  # noqa: F821
projects = Project.search([("other_system_id", "like", "SCBS:SCBS_GCMC_PROJECT_CANDIDATE:%")], order="id")

PaymentExecution = env["sc.payment.execution"].sudo() if "sc.payment.execution" in env else None  # noqa: F821
GeneralContract = env["sc.general.contract"].sudo() if "sc.general.contract" in env else None  # noqa: F821
MaterialInbound = env["sc.material.inbound"].sudo() if "sc.material.inbound" in env else None  # noqa: F821
PaymentAdjustment = (  # noqa: F821
    env["sc.legacy.payment.adjustment.fact"].sudo()
    if "sc.legacy.payment.adjustment.fact" in env
    else None
)
Users = env["res.users"].sudo().with_context(active_test=False)  # noqa: F821


def matched_active_user(name: str):
    if not name:
        return None
    matches = Users.search(["|", ("name", "=", name), ("login", "=", name)])
    active = matches.filtered(lambda user: user.active)
    if len(active) == 1:
        return active[0]
    return None


def fact_summary(project):
    people = Counter()
    dates: list[str] = []
    counts = {
        "payment_rows": 0,
        "contract_rows": 0,
        "inbound_rows": 0,
        "adjustment_rows": 0,
    }
    amounts = {
        "payment_amount": 0.0,
        "contract_amount": 0.0,
        "inbound_amount": 0.0,
        "adjustment_amount": 0.0,
    }
    if PaymentExecution is not None:
        payments = PaymentExecution.search([("project_id", "=", project.id)])
        counts["payment_rows"] = len(payments)
        amounts["payment_amount"] = money(sum((row.paid_amount or row.planned_amount or 0.0) for row in payments))
        for row in payments:
            for field_name in ("creator_name", "handler_name"):
                value = clean(getattr(row, field_name, ""))
                if value and value.lower() != "admin":
                    people[value] += 1
            if row.date_payment:
                dates.append(str(row.date_payment))
    if GeneralContract is not None:
        contracts = GeneralContract.search([("project_id", "=", project.id)])
        counts["contract_rows"] = len(contracts)
        amounts["contract_amount"] = money(sum((row.amount_total or 0.0) for row in contracts))
        for row in contracts:
            for field_name in ("applicant_name", "contact_name"):
                value = clean(getattr(row, field_name, ""))
                if value and value.lower() != "admin":
                    people[value] += 1
            if row.contract_date:
                dates.append(str(row.contract_date))
    if MaterialInbound is not None:
        inbound = MaterialInbound.search([("project_id", "=", project.id)])
        counts["inbound_rows"] = len(inbound)
        amounts["inbound_amount"] = money(sum((row.amount_total or 0.0) for row in inbound))
        for row in inbound:
            if row.inbound_date:
                dates.append(str(row.inbound_date))
    if PaymentAdjustment is not None:
        adjustments = PaymentAdjustment.search([("project_id", "=", project.id)])
        counts["adjustment_rows"] = len(adjustments)
        amounts["adjustment_amount"] = money(sum((row.source_amount or 0.0) for row in adjustments))
        for row in adjustments:
            if row.document_date:
                dates.append(str(row.document_date))
    top_name, top_count = ("", 0)
    if people:
        top_name, top_count = people.most_common(1)[0]
    return {
        "counts": counts,
        "amounts": amounts,
        "first_fact_date": min(dates) if dates else "",
        "latest_fact_date": max(dates) if dates else "",
        "top_person_name": top_name,
        "top_person_count": top_count,
        "top_person_user": matched_active_user(top_name),
    }


rows = []
updated = 0
blocked_lifecycle = 0
assigned_manager = 0
skipped_manager = 0
for project in projects:
    summary = fact_summary(project)
    values = {}
    if project.operation_strategy != "direct":
        values["operation_strategy"] = "direct"
    if clean(project.business_nature) != "公司直营":
        values["business_nature"] = "公司直营"
    current_manager = clean(project.manager_id.name if project.manager_id else "")
    user = summary["top_person_user"]
    if user and (not project.manager_id or current_manager == "OdooBot"):
        values["manager_id"] = user.id
        assigned_manager += 1
    elif not user:
        skipped_manager += 1

    status = "unchanged"
    error = ""
    if values:
        project.write(values)
        updated += 1
        status = "updated"

    lifecycle_status = "kept"
    has_business_facts = any(summary["counts"].values())
    if project.lifecycle_state == "draft" and has_business_facts:
        try:
            project.action_set_lifecycle_state("in_progress")
            lifecycle_status = "updated"
        except Exception as exc:  # noqa: BLE001
            blocked_lifecycle += 1
            lifecycle_status = "blocked"
            error = clean(exc)

    rows.append(
        {
            "project_id": project.id,
            "project_name": project.name,
            "project_code": project.project_code or "",
            "status": status,
            "lifecycle_status": lifecycle_status,
            "manager": project.manager_id.display_name if project.manager_id else "",
            "business_nature": project.business_nature or "",
            "operation_strategy": project.operation_strategy or "",
            "first_fact_date": summary["first_fact_date"],
            "latest_fact_date": summary["latest_fact_date"],
            "top_person_name": summary["top_person_name"],
            "top_person_count": summary["top_person_count"],
            "top_person_user": user.display_name if user else "",
            "counts": summary["counts"],
            "amounts": summary["amounts"],
            "error": error,
        }
    )

env.cr.commit()  # noqa: F821

payload = {
    "status": "PASS" if len(projects) == 40 and not blocked_lifecycle else "PARTIAL",
    "database": env.cr.dbname,  # noqa: F821
    "project_count": len(projects),
    "updated_projects": updated,
    "manager_assigned_projects": assigned_manager,
    "manager_skipped_projects": skipped_manager,
    "lifecycle_blocked_projects": blocked_lifecycle,
    "rows": rows,
}

OUTPUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
lines = [
    "# SCBS Direct Project Runtime Surface Write",
    "",
    f"Status: `{payload['status']}`",
    f"Database: `{payload['database']}`",
    "",
    "| Metric | Value |",
    "| --- | ---: |",
    f"| projects | {payload['project_count']} |",
    f"| updated projects | {payload['updated_projects']} |",
    f"| manager assigned | {payload['manager_assigned_projects']} |",
    f"| manager skipped | {payload['manager_skipped_projects']} |",
    f"| lifecycle blocked | {payload['lifecycle_blocked_projects']} |",
    "",
    "## Project Rows",
    "",
    "| project | state | manager | first fact | latest fact | payment | contract | inbound | adjustment |",
    "| --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: |",
]
for row in rows:
    counts = row["counts"]
    lines.append(
        "| {project_name} | {lifecycle_status} | {manager} | {first_fact_date} | {latest_fact_date} | "
        "{payment_rows} | {contract_rows} | {inbound_rows} | {adjustment_rows} |".format(
            **row,
            **counts,
        )
    )
OUTPUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
