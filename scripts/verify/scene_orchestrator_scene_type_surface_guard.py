#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
COMPILER = ROOT / "addons" / "smart_core" / "core" / "scene_dsl_compiler.py"


def _assert(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def _load_scene_compile():
    spec = importlib.util.spec_from_file_location("scene_dsl_compiler_scene_type_guard", COMPILER)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"spec unavailable: {COMPILER}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    fn = getattr(module, "scene_compile", None)
    if not callable(fn):
        raise RuntimeError("scene_compile not found")
    return fn


def main() -> int:
    errors: list[str] = []
    if not COMPILER.is_file():
        errors.append(f"missing file: {COMPILER}")
    if errors:
        print("[scene_orchestrator_scene_type_surface_guard] FAIL")
        for item in errors:
            print(f" - {item}")
        return 1

    compiler_text = COMPILER.read_text(encoding="utf-8")
    for token in (
        "_infer_scene_type",
        "_shape_search_surface",
        "_shape_workflow_surface",
        "_shape_validation_surface",
        "surface_profile",
    ):
        _assert(token in compiler_text, f"compiler missing scene-type surface token: {token}", errors)

    try:
        scene_compile = _load_scene_compile()
        base_contract = {
            "views": {
                "tree": {"fields": ["name", "stage_id"]},
                "form": {"fields": ["name", "budget", "manager_id"], "statusbar": {"field": "state"}},
            },
            "search": {
                "fields": ["name", "manager_id"],
                "filters": ["my_projects", "active"],
                "group_by": ["manager_id", "state"],
            },
            "workflow": {"state_field": "state", "states": ["draft", "done"], "transitions": ["approve"]},
            "validator": {"required_fields": ["name", "budget"], "field_rules": {"budget": {"min": 0}}},
            "actions": {"items": [{"key": "create", "placement": "toolbar"}, {"key": "archive", "placement": "row"}]},
        }

        form_payload = {
            "code": "projects.intake",
            "layout": {"kind": "form"},
            "blocks": [{"type": "form_block", "source": "ui_base_contract.views.form", "fields": ["name"]}],
        }
        workspace_payload = {
            "code": "workspace.home",
            "layout": {"kind": "workspace"},
            "blocks": [{"type": "list_block", "source": "ui_base_contract.views.tree"}],
        }

        form_compiled = scene_compile(form_payload, scene_key="projects.intake", ui_base_contract=base_contract, provider_registry={})
        workspace_compiled = scene_compile(workspace_payload, scene_key="workspace.home", ui_base_contract=base_contract, provider_registry={})

        form_meta = form_compiled.get("meta") if isinstance(form_compiled.get("meta"), dict) else {}
        form_profile = form_meta.get("surface_profile") if isinstance(form_meta.get("surface_profile"), dict) else {}
        form_search = form_compiled.get("search_surface") if isinstance(form_compiled.get("search_surface"), dict) else {}
        form_validation = form_compiled.get("validation_surface") if isinstance(form_compiled.get("validation_surface"), dict) else {}
        _assert(form_profile.get("scene_type") == "form", "form scene_type inference failed", errors)
        _assert(form_search.get("group_by") == [], "form search group_by should be trimmed", errors)
        _assert(form_validation.get("required_fields") == ["name"], "form validation required_fields should follow field scope", errors)

        workspace_meta = workspace_compiled.get("meta") if isinstance(workspace_compiled.get("meta"), dict) else {}
        workspace_profile = workspace_meta.get("surface_profile") if isinstance(workspace_meta.get("surface_profile"), dict) else {}
        workspace_search = workspace_compiled.get("search_surface") if isinstance(workspace_compiled.get("search_surface"), dict) else {}
        workspace_workflow = workspace_compiled.get("workflow_surface") if isinstance(workspace_compiled.get("workflow_surface"), dict) else {}
        _assert(workspace_profile.get("scene_type") == "workspace", "workspace scene_type inference failed", errors)
        _assert(workspace_search.get("fields") == [], "workspace search fields should be trimmed", errors)
        _assert(workspace_search.get("group_by") == [], "workspace search group_by should be trimmed", errors)
        _assert(workspace_workflow.get("transitions") == [], "workspace workflow transitions should be trimmed", errors)
    except Exception as exc:
        errors.append(f"runtime sample failed: {exc}")

    if errors:
        print("[scene_orchestrator_scene_type_surface_guard] FAIL")
        for item in errors:
            print(f" - {item}")
        return 1

    print("[scene_orchestrator_scene_type_surface_guard] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

