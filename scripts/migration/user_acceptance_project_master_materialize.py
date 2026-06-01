# -*- coding: utf-8 -*-
"""Materialize local project master data needed for user acceptance.

Old business facts are scoped by company/project/operation strategy.  An
acceptance database is not usable when historical projects are present but have
no company, because company/project/operation filters then hide valid facts.

This script does not reactivate archived projects. Archived records must stay
archived so visible project counts keep matching the user-facing old systems.

Default mode is dry-run. Set APPLY=1 to write.
"""

from __future__ import annotations

import json
import os
from collections import Counter, defaultdict


BUSINESS_MODELS = (
    "sc.general.contract",
    "sc.payment.execution",
    "sc.fund.account.operation",
    "payment.request",
    "sc.receipt.income",
    "sc.invoice.registration",
    "sc.material.acceptance",
    "sc.expense.claim",
    "sc.financing.loan",
)
VALID_OPERATION_STRATEGIES = {"direct", "joint"}


def _as_int(value) -> int:
    try:
        parsed = int(value or 0)
    except (TypeError, ValueError):
        return 0
    return parsed if parsed > 0 else 0


def _target_company_id() -> int:
    explicit = _as_int(os.getenv("USER_ACCEPTANCE_COMPANY_ID"))
    if explicit:
        return explicit
    return _as_int(getattr(env.company, "id", 0)) or 1  # noqa: F821


def _linked_project_company_map() -> dict[int, set[int]]:
    linked: dict[int, set[int]] = defaultdict(set)
    for model_name in BUSINESS_MODELS:
        if model_name not in env:  # noqa: F821
            continue
        Model = env[model_name].sudo().with_context(active_test=False)  # noqa: F821
        if "project_id" not in Model._fields:
            continue
        if "company_id" not in Model._fields:
            for row in Model.read_group([("project_id", "!=", False)], ["project_id"], ["project_id"], lazy=False):
                project = row.get("project_id")
                if project:
                    linked[int(project[0])]
            continue
        rows = Model.read_group(
            [("project_id", "!=", False)],
            ["project_id", "company_id"],
            ["project_id", "company_id"],
            lazy=False,
        )
        for row in rows:
            project = row.get("project_id")
            if not project:
                continue
            project_id = int(project[0])
            company = row.get("company_id")
            if company:
                linked[project_id].add(int(company[0]))
            else:
                linked[project_id]
    return linked


def main() -> None:
    apply = os.getenv("APPLY") == "1"
    default_company_id = _target_company_id()
    Project = env["project.project"].sudo().with_context(active_test=False)  # noqa: F821
    company = env["res.company"].sudo().browse(default_company_id).exists()  # noqa: F821
    if not company:
        raise RuntimeError(f"USER_ACCEPTANCE_COMPANY_ID not found: {default_company_id}")

    linked_companies = _linked_project_company_map()
    strategy_projects = Project.search([("operation_strategy", "in", sorted(VALID_OPERATION_STRATEGIES))])
    linked_projects = Project.browse(sorted(linked_companies)).exists()
    projects = (strategy_projects | linked_projects).filtered(
        lambda project: (project.operation_strategy or "") in VALID_OPERATION_STRATEGIES
    )

    plan = []
    errors = []
    for project in projects.sorted(key=lambda item: item.id):
        inferred_companies = linked_companies.get(project.id, set())
        target_company_id = 0
        if len(inferred_companies) == 1:
            target_company_id = next(iter(inferred_companies))
        elif len(inferred_companies) > 1:
            errors.append(
                {
                    "project_id": project.id,
                    "project_name": project.display_name,
                    "inferred_company_ids": sorted(inferred_companies),
                    "error": "ambiguous_linked_companies",
                }
            )
            continue
        else:
            target_company_id = default_company_id

        vals = {}
        if not project.company_id:
            vals["company_id"] = target_company_id
        if vals:
            plan.append(
                {
                    "project_id": project.id,
                    "project_name": project.display_name,
                    "operation_strategy": project.operation_strategy,
                    "old_company_id": project.company_id.id or None,
                    "target_company_id": target_company_id,
                    "old_active": bool(project.active),
                    "vals": vals,
                    "has_linked_business_facts": project.id in linked_companies,
                }
            )
            if apply:
                project.with_context(tracking_disable=True).write(vals)

    if errors:
        raise RuntimeError({"errors": errors[:100], "error_count": len(errors)})

    if apply:
        env.cr.commit()  # noqa: F821

    payload = {
        "status": "APPLIED" if apply else "DRY_RUN",
        "database": env.cr.dbname,  # noqa: F821
        "default_company_id": default_company_id,
        "candidate_project_count": len(projects),
        "linked_project_count": len(linked_companies),
        "write_count": len(plan),
        "operation_counts": dict(Counter(row["operation_strategy"] for row in plan)),
        "field_counts": dict(Counter(field for row in plan for field in row["vals"])),
        "archived_candidate_count": sum(1 for project in projects if not project.active),
        "sample": plan[:20],
    }
    print("USER_ACCEPTANCE_PROJECT_MASTER_MATERIALIZE=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))


main()
