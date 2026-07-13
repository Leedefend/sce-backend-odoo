#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


CHECKS = [
    {
        "id": "boq_import_wizard_model",
        "path": "addons/smart_construction_core/wizard/project_boq_import_wizard.py",
        "needles": [
            '_name = "project.boq.import.wizard"',
            "def action_import",
            "def _parse_file",
            "project.boq.line",
            "boq_category",
            "clear_mode",
        ],
    },
    {
        "id": "boq_import_manifest_loaded",
        "path": "addons/smart_construction_core/__manifest__.py",
        "needles": [
            "views/core/project_boq_import_views.xml",
            "views/core/boq_views.xml",
        ],
    },
    {
        "id": "boq_import_views_and_action",
        "path": "addons/smart_construction_core/views/core/project_boq_import_views.xml",
        "needles": [
            "action_project_boq_import_wizard",
            "project.boq.import.wizard",
            'name="file"',
            'filename="filename"',
            "action_import",
        ],
    },
    {
        "id": "boq_project_entry_action",
        "path": "addons/smart_construction_core/models/core/project_core.py",
        "needles": [
            "def action_open_boq_import",
            "action_project_boq_import_wizard",
            "project.boq.line",
            "boq_imported",
            "boq_status",
        ],
    },
]


def run_check(check: dict[str, object]) -> dict[str, object]:
    path = ROOT / str(check["path"])
    missing: list[str] = []
    if not path.exists():
        return {"id": check["id"], "path": str(check["path"]), "ok": False, "missing": ["file"]}
    text = path.read_text(encoding="utf-8")
    for needle in check["needles"]:
        if str(needle) not in text:
            missing.append(str(needle))
    return {"id": check["id"], "path": str(check["path"]), "ok": not missing, "missing": missing}


def main() -> int:
    results = [run_check(check) for check in CHECKS]
    failed = [item for item in results if not item["ok"]]
    report = {
        "journey": "E2E-02 BOQ import",
        "status": "preflight_passed" if not failed else "preflight_failed",
        "acceptance_points": [
            "Project-scoped BOQ import wizard exists.",
            "CSV/XLS/XLSX parsing entrypoints are present.",
            "Imported rows target project.boq.line.",
            "Project entry action opens the import wizard.",
            "BOQ imported/status fields exist for downstream checks.",
        ],
        "results": results,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    if failed:
        return 1
    print("[e2e_boq_import_fixed_data_preflight] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
