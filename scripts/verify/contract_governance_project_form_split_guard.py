#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GOVERNANCE = ROOT / "addons/smart_core/utils/contract_governance.py"
PROJECT_FORM = ROOT / "addons/smart_core/utils/contract_governance_project_form.py"
CI = ROOT / "make/ci.mk"

MAX_GOVERNANCE_LINES = 2708


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore") if path.is_file() else ""


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    errors: list[str] = []
    governance_text = _read(GOVERNANCE)
    project_form_text = _read(PROJECT_FORM)
    ci_text = _read(CI)

    if not governance_text:
        errors.append(f"missing governance file: {GOVERNANCE.relative_to(ROOT)}")
    if not project_form_text:
        errors.append(f"missing project form module: {PROJECT_FORM.relative_to(ROOT)}")

    if governance_text:
        line_count = len(governance_text.splitlines())
        if line_count > MAX_GOVERNANCE_LINES:
            errors.append(f"contract_governance.py line budget exceeded: {line_count} > {MAX_GOVERNANCE_LINES}")
        for token in [
            "def _load_project_form_module()",
            "contract_governance_project_form.py",
            "return _project_form.normalize_legacy_project_form_profile(",
            "return _project_form.pick_project_form_fields(",
            "_project_form.filter_project_form_layout(",
            "def _build_project_lifecycle_summary(data: dict) -> None:",
            "_project_form.build_project_lifecycle_summary(data)",
        ]:
            if token not in governance_text:
                errors.append(f"contract_governance.py missing project form split token: {token}")

    if project_form_text:
        for token in [
            "def normalize_legacy_project_form_profile(",
            "def pick_project_form_fields(",
            "def filter_project_form_layout(",
            "def build_project_lifecycle_summary(",
            "\"action_noise_markers\"",
            "for key in (\"children\", \"tabs\", \"pages\", \"nodes\", \"items\")",
            "\"owner_layer\": \"business_fact\"",
            "\"source\": \"contract_governance.workflow_facts\"",
            "\"progress_percent\": 0 if state_keys else None",
            "\"transitions\": transitions[:8]",
        ]:
            if token not in project_form_text:
                errors.append(f"project form module missing token: {token}")
        for token in (".search(", ".write(", "requests.", "env[", "registry["):
            if token in project_form_text:
                errors.append(f"project form module must remain projection-only; found token: {token}")

    if "python3 scripts/verify/contract_governance_project_form_split_guard.py" not in ci_text:
        errors.append("ci.local.quick must run contract_governance_project_form_split_guard.py")

    if not errors:
        governance = _load(GOVERNANCE, "contract_governance_project_form_split_under_guard")
        governance.register_legacy_project_form_governance_model("project.project")
        governance.register_legacy_project_form_profile(
            "project.project",
            {
                "primary_fields": ["code", "", "message_ids"],
                "create_hidden_fields": ["state", ""],
                "action_priorities": ["submit", ""],
                "action_noise_markers": [" Rating "],
                "search_noise_markers": [" Filter "],
                "action_group_labels": {"main": "Main", "": "Ignored"},
                "max_fields": 4,
            },
        )
        profile_data = {
            "head": {"model": "project.project", "view_type": "form"},
            "model": "project.project",
            "governance": {"primary_model": "project.project"},
            "views": {
                "form": {
                    "model": "project.project",
                    "layout": [
                        {
                            "type": "page",
                            "name": "business",
                            "children": [
                                {"type": "field", "name": "manager_id"},
                                {"type": "field", "name": "message_ids"},
                            ],
                        }
                    ],
                }
            },
            "fields": {
                "name": {"type": "char"},
                "code": {"type": "char"},
                "manager_id": {"type": "many2one"},
                "state": {"type": "selection", "required": True, "readonly": False},
                "budget_total": {"type": "float", "required": True, "readonly": False},
                "message_ids": {"type": "one2many"},
            },
        }
        profile = governance._legacy_project_form_profile(profile_data)
        if profile.get("primary_fields") != ["code", "message_ids"]:
            errors.append("project form profile must normalize primary fields without empty entries")
        if profile.get("action_noise_markers") != ["rating"]:
            errors.append("project form profile must lowercase action noise markers")
        if profile.get("search_noise_markers") != ["filter"]:
            errors.append("project form profile must lowercase search noise markers")
        if profile.get("action_group_labels") != {"main": "Main"}:
            errors.append("project form profile must normalize action group labels")
        selected = governance._pick_project_form_fields(profile_data)
        if selected != ["code", "manager_id", "name", "state"]:
            errors.append(f"project form fields must merge primary/page/order/required fields, got {selected!r}")
        layout_data = {
            **profile_data,
            "views": {
                "form": {
                    "layout": [
                        {
                            "type": "notebook",
                            "pages": [
                                {
                                    "type": "page",
                                    "name": "keep",
                                    "children": [
                                        {"type": "field", "name": "code"},
                                        {"type": "field", "name": "message_ids"},
                                    ],
                                },
                                {
                                    "type": "page",
                                    "name": "drop",
                                    "children": [{"type": "field", "name": "message_ids"}],
                                },
                            ],
                        }
                    ]
                }
            },
        }
        governance._filter_project_form_layout(layout_data, ["code", "manager_id", "state"])
        layout = (((layout_data.get("views") or {}).get("form") or {}).get("layout")) or []
        notebook = layout[0] if layout and isinstance(layout[0], dict) else {}
        pages = notebook.get("pages") or []
        kept_page_names = [row.get("name") for row in pages if isinstance(row, dict)]
        if kept_page_names != ["keep"]:
            errors.append(f"project form layout must prune empty pages, got {kept_page_names!r}")
        keep_children = pages[0].get("children") if pages else []
        if [row.get("name") for row in keep_children if isinstance(row, dict)] != ["code"]:
            errors.append("project form layout must prune disallowed page fields")
        if [row.get("name") for row in layout if isinstance(row, dict) and row.get("type") == "field"] != [
            "manager_id",
            "state",
        ]:
            errors.append("project form layout must backfill selected fields missing from native layout")

        transitions = [
            {"trigger": {"label": f"Transition {idx}", "kind": "server"}}
            for idx in range(10)
        ]
        data = {
            "workflow": {
                "state_field": "lifecycle_state",
                "states": [
                    {"key": "draft", "label": "Draft"},
                    {"key": "", "label": "Ignored"},
                    {"key": "done"},
                    "noise",
                ],
                "transitions": transitions,
                "highlight_states": ["done"],
            }
        }
        governance._build_project_lifecycle_summary(data)
        lifecycle = data.get("lifecycle") or {}
        workflow_surface = data.get("workflow_surface") or {}
        if lifecycle.get("state_field") != "lifecycle_state":
            errors.append("project lifecycle must preserve explicit state_field")
        if lifecycle.get("steps") != [{"key": "draft", "label": "Draft"}, {"key": "done", "label": "done"}]:
            errors.append("project lifecycle must normalize states and default labels")
        if len(lifecycle.get("allowed_transitions") or []) != 8:
            errors.append("project lifecycle must cap allowed transitions at 8")
        if workflow_surface.get("owner_layer") != "business_fact":
            errors.append("project workflow_surface must remain business_fact owned")
        if workflow_surface.get("states") != lifecycle.get("steps"):
            errors.append("project workflow_surface states must mirror lifecycle steps")
        if workflow_surface.get("highlight_states") != ["done"]:
            errors.append("project workflow_surface must preserve highlight states lists")

        default_data = {"workflow": {"states": [], "transitions": []}}
        governance._build_project_lifecycle_summary(default_data)
        if (default_data.get("lifecycle") or {}).get("state_field") != "stage_id":
            errors.append("project lifecycle must default state_field to stage_id")
        if (default_data.get("lifecycle") or {}).get("progress_percent") is not None:
            errors.append("project lifecycle without states must use progress_percent=None")

    if errors:
        print("[contract_governance_project_form_split_guard] FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("[contract_governance_project_form_split_guard] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
