#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


CHECKS = [
    {
        "id": "task_from_boq_wizard_model",
        "path": "addons/smart_construction_core/wizard/project_task_from_boq_wizard.py",
        "needles": [
            '_name = "project.task.from.boq.wizard"',
            "project.boq.line",
            "project.task",
            "boq_generated",
            "boq_group_key",
            "boq_quantity_total",
            "boq_amount_total",
        ],
    },
    {
        "id": "task_from_boq_manifest_loaded",
        "path": "addons/smart_construction_core/__manifest__.py",
        "needles": [
            "views/core/project_task_from_boq_views.xml",
            "views/core/task_boq_views.xml",
            "views/support/work_breakdown_views.xml",
        ],
    },
    {
        "id": "task_from_boq_action_view",
        "path": "addons/smart_construction_core/views/core/project_task_from_boq_views.xml",
        "needles": [
            "project.task.from.boq.wizard",
            "action_generate",
            "project_id",
        ],
    },
    {
        "id": "project_generation_entrypoints",
        "path": "addons/smart_construction_core/models/core/project_core.py",
        "needles": [
            "def action_generate_structure_from_boq",
            "def action_generate_wbs_from_boq",
            "wbs_ready",
            "wbs_count",
            "project.boq.line",
        ],
    },
    {
        "id": "task_boq_link_fields",
        "path": "addons/smart_construction_core/models/support/task_extend.py",
        "needles": [
            "boq_line_ids",
            "boq_quantity_total",
            "boq_amount_total",
            "boq_uom_id",
        ],
    },
]


def run_check(check: dict[str, object]) -> dict[str, object]:
    path = ROOT / str(check["path"])
    if not path.exists():
        return {"id": check["id"], "path": str(check["path"]), "ok": False, "missing": ["file"]}
    text = path.read_text(encoding="utf-8")
    missing = [str(needle) for needle in check["needles"] if str(needle) not in text]
    return {"id": check["id"], "path": str(check["path"]), "ok": not missing, "missing": missing}


def main() -> int:
    results = [run_check(check) for check in CHECKS]
    failed = [item for item in results if not item["ok"]]
    report = {
        "journey": "E2E-03 BOQ to WBS/task generation",
        "status": "preflight_passed" if not failed else "preflight_failed",
        "acceptance_points": [
            "Wizard can derive generated project tasks from project.boq.line rows.",
            "Project entrypoints expose BOQ-to-structure generation.",
            "Generated tasks keep BOQ group, quantity, amount, and linked line evidence.",
            "WBS/work breakdown views are loaded for user verification.",
        ],
        "results": results,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    if failed:
        return 1
    print("[e2e_boq_to_wbs_task_preflight] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
