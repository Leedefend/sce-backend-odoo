# -*- coding: utf-8 -*-
"""Audit legacy material budget projection into formal project budgets.

Run inside Odoo shell:
    odoo shell -d sc_demo < scripts/verify/project_budget_legacy_material_audit.py
"""

import json
import re
import sys
import traceback
from collections import Counter, defaultdict


SOURCE_MODEL = "sc.legacy.material_stock_fact"
SOURCE_FACT_TYPE = "material_budget_item"
VERSION = "LEGACY-MATERIAL-BUDGET"
NOTE_ID_RE = re.compile(r"legacy_material_stock_fact_id=(\d+)")


def _text(value):
    value = "" if value is None or value is False else str(value)
    return value.strip()


def _fetch_source_rows():
    env.cr.execute(  # noqa: F821
        """
        SELECT id, project_id
        FROM sc_legacy_material_stock_fact
        WHERE active
          AND fact_type = %s
          AND project_id IS NOT NULL
        ORDER BY project_id, id
        """,
        [SOURCE_FACT_TYPE],
    )
    return env.cr.dictfetchall()  # noqa: F821


def _line_source_id(line):
    match = NOTE_ID_RE.search(_text(line.note))
    return int(match.group(1)) if match else None


def main():
    Budget = env["project.budget"].sudo().with_context(active_test=False)  # noqa: F821
    source_rows = _fetch_source_rows()
    source_ids_by_project = defaultdict(set)
    for row in source_rows:
        source_ids_by_project[row["project_id"]].add(row["id"])

    budgets = Budget.search([("version", "=", VERSION)])
    budget_by_project = {budget.project_id.id: budget for budget in budgets}
    projected_ids_by_project = defaultdict(set)
    duplicate_source_ids = Counter()
    lines_without_source_id = []

    for budget in budgets:
        for line in budget.line_ids:
            source_id = _line_source_id(line)
            if not source_id:
                lines_without_source_id.append(line.id)
                continue
            if source_id in projected_ids_by_project[budget.project_id.id]:
                duplicate_source_ids[source_id] += 1
            projected_ids_by_project[budget.project_id.id].add(source_id)

    failures = []
    if len(budgets) != len(source_ids_by_project):
        failures.append(
            {
                "check": "budget_project_count",
                "source_projects": len(source_ids_by_project),
                "projected_budgets": len(budgets),
            }
        )

    missing_budget_projects = sorted(set(source_ids_by_project) - set(budget_by_project))
    if missing_budget_projects:
        failures.append({"check": "missing_budget_projects", "project_ids": missing_budget_projects[:50]})

    total_source_ids = set()
    total_projected_ids = set()
    project_breakdown = {}
    for project_id, source_ids in source_ids_by_project.items():
        projected_ids = projected_ids_by_project.get(project_id, set())
        total_source_ids.update(source_ids)
        total_projected_ids.update(projected_ids)
        missing_ids = sorted(source_ids - projected_ids)
        extra_ids = sorted(projected_ids - source_ids)
        project_breakdown[str(project_id)] = {
            "source_rows": len(source_ids),
            "projected_lines": len(projected_ids),
            "missing": len(missing_ids),
            "extra": len(extra_ids),
            "budget_id": budget_by_project.get(project_id).id if budget_by_project.get(project_id) else False,
        }
        if missing_ids or extra_ids:
            failures.append(
                {
                    "check": "project_line_source_alignment",
                    "project_id": project_id,
                    "source_rows": len(source_ids),
                    "projected_lines": len(projected_ids),
                    "missing_sample": missing_ids[:20],
                    "extra_sample": extra_ids[:20],
                }
            )

    if lines_without_source_id:
        failures.append({"check": "lines_without_source_id", "line_ids": lines_without_source_id[:50]})
    if duplicate_source_ids:
        failures.append(
            {
                "check": "duplicate_source_ids",
                "duplicates": dict(sorted(duplicate_source_ids.items())[:50]),
            }
        )

    result = {
        "audit": "project_budget_legacy_material_audit",
        "status": "PASS" if not failures else "FAIL",
        "source_rows": len(source_rows),
        "source_projects": len(source_ids_by_project),
        "projected_budgets": len(budgets),
        "projected_lines": sum(len(ids) for ids in projected_ids_by_project.values()),
        "source_ids_projected": len(total_source_ids & total_projected_ids),
        "failures": failures,
        "project_breakdown": project_breakdown,
    }
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    print("PROJECT_BUDGET_LEGACY_MATERIAL_AUDIT: %s" % json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if not failures else 1


try:
    sys.exit(main())
except Exception as err:
    result = {
        "audit": "project_budget_legacy_material_audit",
        "status": "FAIL",
        "error": str(err),
        "traceback": traceback.format_exc(),
    }
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    print("PROJECT_BUDGET_LEGACY_MATERIAL_AUDIT: %s" % json.dumps(result, ensure_ascii=False, sort_keys=True))
    sys.exit(1)
