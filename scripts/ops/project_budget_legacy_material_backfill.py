# -*- coding: utf-8 -*-
"""Backfill legacy material budget facts into formal project budgets.

Run inside Odoo shell:
    odoo shell -d sc_demo < scripts/ops/project_budget_legacy_material_backfill.py
"""

import json
import re
import sys
import traceback
from collections import defaultdict


SOURCE_MODEL = "sc.legacy.material_stock_fact"
SOURCE_FACT_TYPE = "material_budget_item"
VERSION = "LEGACY-MATERIAL-BUDGET"
NOTE_ID_RE = re.compile(r"legacy_material_stock_fact_id=(\d+)")


def _text(value):
    value = "" if value is None or value is False else str(value)
    return value.strip()


def _project_name(project):
    return _text(project.display_name) or ("项目%s" % project.id)


def _legacy_line_note(row):
    parts = [
        "legacy_material_stock_fact_id=%s" % row["id"],
        "legacy_record_id=%s" % _text(row["legacy_record_id"]),
        "source_table=%s" % _text(row["source_table"]),
    ]
    material_uom = _text(row.get("material_uom"))
    if material_uom:
        parts.append("legacy_uom=%s" % material_uom)
    material_spec = _text(row.get("material_spec"))
    if material_spec:
        parts.append("legacy_spec=%s" % material_spec)
    document_no = _text(row.get("document_no"))
    if document_no:
        parts.append("legacy_document_no=%s" % document_no)
    return "; ".join(parts)


def _uom_lookup():
    Uom = env["uom.uom"].sudo().with_context(active_test=False)  # noqa: F821
    lookup = {}
    for uom in Uom.search([]):
        candidates = {uom.display_name}
        name = uom.name
        if isinstance(name, dict):
            candidates.update(name.values())
        else:
            candidates.add(name)
        for candidate in candidates:
            key = _text(candidate)
            if key:
                lookup.setdefault(key, uom.id)
    aliases = {
        "个": "件",
        "支": "件",
        "根": "件",
        "套": "件",
        "项": "件",
        "时": "小时",
        "日": "天",
        "吨": "t",
        "立方": "m³",
        "方": "m³",
        "平方": "m²",
        "米": "m",
    }
    for source, target in aliases.items():
        if target in lookup and source not in lookup:
            lookup[source] = lookup[target]
    return lookup


def _fetch_source_rows():
    env.cr.execute(  # noqa: F821
        """
        SELECT
            id, project_id, source_table, legacy_record_id, document_no,
            material_code, material_name, material_spec, material_uom,
            qty, unit_price, amount_total, document_date, document_state
        FROM sc_legacy_material_stock_fact
        WHERE active
          AND fact_type = %s
          AND project_id IS NOT NULL
        ORDER BY project_id, source_table, document_no, id
        """,
        [SOURCE_FACT_TYPE],
    )
    return env.cr.dictfetchall()  # noqa: F821


def _existing_source_ids(budget):
    source_ids = set()
    for line in budget.line_ids:
        match = NOTE_ID_RE.search(_text(line.note))
        if match:
            source_ids.add(int(match.group(1)))
    return source_ids


def main():
    Budget = env["project.budget"].sudo().with_context(active_test=False)  # noqa: F821
    Line = env["project.budget.boq.line"].sudo().with_context(active_test=False)  # noqa: F821
    Project = env["project.project"].sudo().with_context(active_test=False)  # noqa: F821

    rows = _fetch_source_rows()
    rows_by_project = defaultdict(list)
    for row in rows:
        rows_by_project[row["project_id"]].append(row)

    uom_by_name = _uom_lookup()
    created_budgets = 0
    created_lines = 0
    skipped_lines = 0
    unmapped_uoms = defaultdict(int)
    by_project = {}

    for project_id, project_rows in rows_by_project.items():
        project = Project.browse(project_id)
        if not project.exists():
            continue

        budget = Budget.search([("project_id", "=", project.id), ("version", "=", VERSION)], limit=1)
        if not budget:
            budget = Budget.create(
                {
                    "name": "历史材料预算基线 - %s" % _project_name(project),
                    "project_id": project.id,
                    "budget_kind": "material",
                    "version": VERSION,
                    "version_no": VERSION,
                    "target_type": "drawing_budget",
                    "source_channel": "system",
                    "is_active": True,
                    "is_baseline": True,
                    "amount_revenue_target": 0.0,
                    "amount_cost_target": sum(float(row.get("amount_total") or 0.0) for row in project_rows),
                    "legacy_source_model": SOURCE_MODEL,
                    "legacy_record_id": "%s:%s:project:%s" % (SOURCE_MODEL, SOURCE_FACT_TYPE, project.id),
                    "note": "由历史材料预算/清单事实投影；源表 sc_legacy_material_stock_fact，事实类型 %s；源金额/数量按历史值保留。"
                    % SOURCE_FACT_TYPE,
                }
            )
            created_budgets += 1
        else:
            updates = {}
            if budget.legacy_source_model != SOURCE_MODEL:
                updates["legacy_source_model"] = SOURCE_MODEL
            if budget.legacy_record_id != "%s:%s:project:%s" % (SOURCE_MODEL, SOURCE_FACT_TYPE, project.id):
                updates["legacy_record_id"] = "%s:%s:project:%s" % (SOURCE_MODEL, SOURCE_FACT_TYPE, project.id)
            if budget.budget_kind != "material":
                updates["budget_kind"] = "material"
            if budget.source_channel != "system":
                updates["source_channel"] = "system"
            if updates:
                budget.write(updates)

        existing_ids = _existing_source_ids(budget)
        vals_list = []
        for sequence, row in enumerate(project_rows, start=10):
            if row["id"] in existing_ids:
                skipped_lines += 1
                continue
            uom_name = _text(row.get("material_uom"))
            uom_id = uom_by_name.get(uom_name)
            if uom_name and not uom_id:
                unmapped_uoms[uom_name] += 1
            qty = float(row.get("qty") or 0.0)
            price = float(row.get("unit_price") or 0.0)
            name = _text(row.get("material_name")) or _text(row.get("material_code")) or "历史预算清单%s" % row["id"]
            vals = {
                "budget_id": budget.id,
                "sequence": sequence,
                "boq_code": _text(row.get("document_no")) or _text(row.get("material_code")) or str(row["id"]),
                "name": name,
                "qty_bidded": qty,
                "price_bidded": price,
                "measure_rule": "qty",
                "cost_collection_method": "non_contract",
                "cost_allocation_method": "manual",
                "revenue_recognition": "progress",
                "note": _legacy_line_note(row),
            }
            if uom_id:
                vals["uom_id"] = uom_id
            vals_list.append(vals)

        if vals_list:
            Line.create(vals_list)
            created_lines += len(vals_list)

        by_project[str(project.id)] = {
            "project_name": _project_name(project),
            "source_rows": len(project_rows),
            "created_lines": len(vals_list),
            "existing_lines": len(existing_ids),
            "budget_id": budget.id,
        }

    env.cr.commit()  # noqa: F821
    result = {
        "operation": "project_budget_legacy_material_backfill",
        "status": "PASS",
        "source_rows": len(rows),
        "source_projects": len(rows_by_project),
        "created_budgets": created_budgets,
        "created_lines": created_lines,
        "skipped_lines": skipped_lines,
        "unmapped_uoms": dict(sorted(unmapped_uoms.items())),
        "by_project": by_project,
    }
    print("PROJECT_BUDGET_LEGACY_MATERIAL_BACKFILL: %s" % json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


try:
    sys.exit(main())
except Exception as err:
    result = {
        "operation": "project_budget_legacy_material_backfill",
        "status": "FAIL",
        "error": str(err),
        "traceback": traceback.format_exc(),
    }
    print("PROJECT_BUDGET_LEGACY_MATERIAL_BACKFILL: %s" % json.dumps(result, ensure_ascii=False, sort_keys=True))
    sys.exit(1)
