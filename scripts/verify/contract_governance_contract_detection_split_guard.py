#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GOVERNANCE = ROOT / "addons/smart_core/utils/contract_governance.py"
DETECTION = ROOT / "addons/smart_core/utils/contract_governance_contract_detection.py"
CI = ROOT / "make/ci.mk"

MAX_GOVERNANCE_LINES = 1899


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
    detection_text = _read(DETECTION)
    ci_text = _read(CI)

    if not governance_text:
        errors.append(f"missing governance file: {GOVERNANCE.relative_to(ROOT)}")
    if not detection_text:
        errors.append(f"missing contract detection module: {DETECTION.relative_to(ROOT)}")

    if governance_text:
        line_count = len(governance_text.splitlines())
        if line_count > MAX_GOVERNANCE_LINES:
            errors.append(f"contract_governance.py line budget exceeded: {line_count} > {MAX_GOVERNANCE_LINES}")
        for token in [
            "def _load_contract_detection_module()",
            "contract_governance_contract_detection.py",
            "_contract_detection.is_project_form_contract(",
            "_contract_detection.is_enterprise_company_form_contract(",
            "_contract_detection.is_enterprise_user_form_contract(",
            "_contract_detection.is_project_kanban_contract(",
            "_contract_detection.is_project_task_form_contract(",
            "_contract_detection.is_model_tree_contract(",
            "return _contract_detection.is_form_contract(data)",
        ]:
            if token not in governance_text:
                errors.append(f"contract_governance.py missing contract detection split token: {token}")

    if detection_text:
        for token in [
            "def is_project_form_contract(",
            "def is_enterprise_company_form_contract(",
            "def is_enterprise_user_form_contract(",
            "def is_project_kanban_contract(",
            "def is_project_task_form_contract(",
            "def is_model_tree_contract(",
            "def is_form_contract(",
            "current_view_type not in {\"kanban\", \"tree\", \"list\"}",
            "render_profile in {create_profile, edit_profile, readonly_profile}",
            "\"tree\" in view_type or \"list\" in view_type or has_tree_surface",
        ]:
            if token not in detection_text:
                errors.append(f"contract detection module missing token: {token}")
        for token in (".search(", ".write(", "requests.", "env[", "registry[", "open(", "Path("):
            if token in detection_text:
                errors.append(f"contract detection module must remain read-only; found token: {token}")

    if "python3 scripts/verify/contract_governance_contract_detection_split_guard.py" not in ci_text:
        errors.append("ci.local.quick must run contract_governance_contract_detection_split_guard.py")

    if not errors:
        detection = _load(DETECTION, "contract_governance_contract_detection_under_guard")
        form_data = {
            "head": {"model": "project.project", "view_type": "form"},
            "model": "project.project",
            "governance": {"primary_model": "project.project"},
            "views": {"form": {"model": "project.project"}},
        }
        if not detection.is_project_form_contract(
            form_data,
            primary_model="project.project",
            project_form_models={"project.project"},
        ):
            errors.append("project form detection must accept registered project form contracts")
        if detection.is_project_form_contract(
            form_data,
            primary_model="project.task",
            project_form_models={"project.project"},
        ):
            errors.append("project form detection must reject mismatched primary models")

        kanban_data = {
            "head": {"model": "project.project"},
            "model": "project.project",
            "view_type": "kanban",
            "governance": {"primary_model": "project.project"},
            "views": {"kanban": {"model": "project.project"}},
        }
        if not detection.is_project_kanban_contract(
            kanban_data,
            primary_model="project.project",
            project_kanban_models={"project.project"},
            create_profile="create",
            edit_profile="edit",
            readonly_profile="readonly",
        ):
            errors.append("project kanban detection must accept registered kanban surfaces")
        create_data = {**kanban_data, "render_profile": "create"}
        if detection.is_project_kanban_contract(
            create_data,
            primary_model="project.project",
            project_kanban_models={"project.project"},
            create_profile="create",
            edit_profile="edit",
            readonly_profile="readonly",
        ):
            errors.append("project kanban detection must reject form render profiles")

        tree_data = {
            "head": {"model": "project.project", "view_type": "tree"},
            "model": "project.project",
            "views": {"tree": {"model": "project.project"}},
        }
        if not detection.is_model_tree_contract(
            tree_data,
            primary_model="project.project",
            model_name="project.project",
        ):
            errors.append("tree detection must accept matching tree contracts")
        if not detection.is_form_contract({"views": {"form": {"model": "x"}}}):
            errors.append("form detection must accept contracts with a form view")
        if not detection.is_enterprise_company_form_contract(
            {"head": {"model": "res.company", "view_type": "form"}, "views": {"form": {}}},
            primary_model="res.company",
        ):
            errors.append("enterprise company detection must accept res.company form")
        if not detection.is_enterprise_user_form_contract(
            {"head": {"model": "res.users", "view_type": "form"}, "views": {"form": {}}},
            primary_model="res.users",
        ):
            errors.append("enterprise user detection must accept res.users form")

    if errors:
        print("[contract_governance_contract_detection_split_guard] FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("[contract_governance_contract_detection_split_guard] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
