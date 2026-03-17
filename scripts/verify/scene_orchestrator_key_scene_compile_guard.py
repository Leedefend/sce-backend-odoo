#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any, Dict, List


ROOT = Path(__file__).resolve().parents[2]
COMPILER_PATH = ROOT / "addons" / "smart_core" / "core" / "scene_dsl_compiler.py"
BASELINE_PATH = ROOT / "scripts" / "verify" / "baselines" / "scene_orchestrator_key_scene_compile_guard.json"


def _text(value: Any) -> str:
    return str(value or "").strip()


def _as_dict(value: Any) -> Dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _as_list(value: Any) -> List[Any]:
    return value if isinstance(value, list) else []


def _load_json(path: Path) -> Dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _load_scene_compile():
    spec = importlib.util.spec_from_file_location("scene_dsl_compiler_guard", COMPILER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"spec unavailable: {COMPILER_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    fn = getattr(module, "scene_compile", None)
    if not callable(fn):
        raise RuntimeError("scene_compile not found")
    return fn


def _scene_samples() -> List[Dict[str, Any]]:
    return [
        {
            "scene_key": "projects.list",
            "scene_payload": {
                "code": "projects.list",
                "name": "项目列表",
                "layout": {"kind": "list"},
                "zones": ["header", "toolbar", "main"],
                "blocks": [{"type": "list_block", "source": "ui_base_contract.views.tree"}],
                "actions": [
                    {"key": "create_project", "label": "创建项目", "placement": "toolbar"},
                    {"key": "export_projects", "label": "导出项目", "placement": "toolbar"},
                ],
            },
            "ui_base_contract": {
                "views": {
                    "tree": {
                        "fields": ["name", "stage_id", "manager_id"],
                        "columns": [{"name": "name"}, {"name": "stage_id"}, {"name": "manager_id"}],
                    }
                },
                "fields": {
                    "name": {"type": "char"},
                    "stage_id": {"type": "many2one"},
                    "manager_id": {"type": "many2one"},
                },
                "search": {
                    "fields": ["name", "manager_id"],
                    "filters": [{"key": "my_projects", "domain": [["manager_id", "=", "uid"]]}],
                    "group_by": ["stage_id"],
                },
                "permissions": {"effective": {"rights": {"read": True, "create": True, "write": True, "unlink": False}}},
                "workflow": {
                    "state_field": "state",
                    "states": ["draft", "running", "done"],
                    "transitions": [{"key": "start_project", "intent": "workflow.submit"}],
                },
                "validator": {"required_fields": ["name"]},
                "actions": {
                    "toolbar": [
                        {"key": "create_project", "label": "创建项目", "placement": "toolbar"},
                        {"key": "batch_submit", "label": "批量提交", "placement": "toolbar", "intent": "workflow.submit"},
                    ]
                },
            },
        },
        {
            "scene_key": "projects.intake",
            "scene_payload": {
                "code": "projects.intake",
                "name": "项目立项",
                "layout": {"kind": "form"},
                "zones": ["header", "main"],
                "blocks": [{"type": "form_block", "source": "ui_base_contract.views.form"}],
                "actions": [
                    {"key": "submit_intake", "label": "提交立项", "placement": "header", "intent": "workflow.submit"},
                    {"key": "save_draft", "label": "保存草稿", "placement": "header", "intent": "record.update"},
                ],
            },
            "ui_base_contract": {
                "views": {"form": {"fields": ["name", "owner_id", "budget"]}},
                "fields": {
                    "name": {"type": "char"},
                    "owner_id": {"type": "many2one"},
                    "budget": {"type": "float"},
                },
                "search": {"fields": ["name"], "filters": [{"key": "draft_only", "domain": [["state", "=", "draft"]]}]},
                "permissions": {"effective": {"rights": {"read": True, "create": True, "write": True, "unlink": False}}},
                "workflow": {
                    "state_field": "state",
                    "states": ["draft", "submitted", "approved"],
                    "transitions": [{"key": "submit_intake", "intent": "workflow.submit"}],
                },
                "validator": {"required_fields": ["name", "budget"]},
                "actions": {
                    "toolbar": [
                        {"key": "submit_intake", "label": "提交", "placement": "header"},
                        {"key": "approve_intake", "label": "审批", "placement": "header", "intent": "workflow.approve"},
                    ]
                },
            },
        },
        {
            "scene_key": "workspace.home",
            "scene_payload": {
                "code": "workspace.home",
                "name": "工作台",
                "layout": {"kind": "workspace"},
                "zones": ["header", "main"],
                "blocks": [{"type": "kanban_block", "source": "ui_base_contract.views.kanban"}],
                "actions": [
                    {"key": "open_projects", "label": "项目总览", "placement": "toolbar", "intent": "project.list"},
                    {"key": "open_risks", "label": "风险总览", "placement": "toolbar", "intent": "risk.list"},
                ],
            },
            "ui_base_contract": {
                "views": {"kanban": {"fields": ["name", "stage_id"]}},
                "fields": {
                    "name": {"type": "char"},
                    "stage_id": {"type": "many2one"},
                },
                "search": {"fields": ["name"], "filters": [{"key": "mine", "domain": [["user_id", "=", "uid"]]}]},
                "permissions": {"effective": {"rights": {"read": True, "create": False, "write": False, "unlink": False}}},
                "workflow": {
                    "state_field": "state",
                    "states": ["draft", "running"],
                    "transitions": [{"key": "noop", "intent": "ui.contract"}],
                },
                "validator": {"required_fields": []},
                "actions": {
                    "toolbar": [
                        {"key": "open_projects", "label": "项目总览", "placement": "toolbar"},
                        {"key": "open_tasks", "label": "任务中心", "placement": "toolbar", "intent": "task.list"},
                    ]
                },
            },
        },
    ]


def _assert(condition: bool, message: str, errors: List[str]) -> None:
    if not condition:
        errors.append(message)


def _nonempty_search(surface: Dict[str, Any]) -> bool:
    return bool(_as_list(surface.get("filters")) or _as_list(surface.get("fields")) or _as_list(surface.get("group_by")))


def _nonempty_workflow(surface: Dict[str, Any]) -> bool:
    return bool(_as_list(surface.get("states")) or _as_list(surface.get("transitions")) or _text(surface.get("state_field")))


def _nonempty_validation(surface: Dict[str, Any]) -> bool:
    return bool(_as_list(surface.get("required_fields")) or _as_list(surface.get("rules")))


def main() -> int:
    errors: List[str] = []
    if not COMPILER_PATH.is_file():
        errors.append(f"missing file: {COMPILER_PATH}")
    baseline = _load_json(BASELINE_PATH)
    if not baseline:
        errors.append(f"missing or invalid baseline: {BASELINE_PATH.relative_to(ROOT).as_posix()}")
    if errors:
        print("[scene_orchestrator_key_scene_compile_guard] FAIL")
        for item in errors:
            print(f" - {item}")
        return 1

    compile_fn = _load_scene_compile()
    required_scene_keys = [_text(item) for item in _as_list(baseline.get("required_scene_keys")) if _text(item)]
    required_scene_types = [_text(item) for item in _as_list(baseline.get("required_scene_types")) if _text(item)]
    required_pipeline = [_text(item) for item in _as_list(baseline.get("required_compile_pipeline")) if _text(item)]
    per_scene_expectations = _as_dict(baseline.get("per_scene_expectations"))

    seen_keys: List[str] = []
    seen_types: set[str] = set()
    for sample in _scene_samples():
        scene_key = _text(sample.get("scene_key"))
        scene_payload = _as_dict(sample.get("scene_payload"))
        ui_base_contract = _as_dict(sample.get("ui_base_contract"))
        provider_registry = _as_dict(sample.get("provider_registry"))

        compiled = compile_fn(
            scene_payload,
            scene_key=scene_key,
            ui_base_contract=ui_base_contract,
            provider_registry=provider_registry,
        )
        seen_keys.append(scene_key)

        meta = _as_dict(compiled.get("meta"))
        surface_profile = _as_dict(meta.get("surface_profile"))
        scene_type = _text(surface_profile.get("scene_type"))
        if scene_type:
            seen_types.add(scene_type)

        verdict = _as_dict(meta.get("compile_verdict"))
        binding = _as_dict(meta.get("binding"))
        action_surface = _as_dict(compiled.get("action_surface"))
        action_counts = _as_dict(action_surface.get("counts"))
        search_surface = _as_dict(compiled.get("search_surface"))
        workflow_surface = _as_dict(compiled.get("workflow_surface"))
        validation_surface = _as_dict(compiled.get("validation_surface"))
        compile_pipeline = [
            _text(item)
            for item in _as_list(meta.get("compile_pipeline"))
            if _text(item)
        ]

        _assert(bool(verdict.get("ok")), f"{scene_key} compile_verdict.ok must be true", errors)
        _assert(bool(verdict.get("base_contract_bound")), f"{scene_key} compile_verdict.base_contract_bound must be true", errors)

        expected = _as_dict(per_scene_expectations.get(scene_key))
        expected_scene_type = _text(expected.get("scene_type"))
        min_bound_block_count = int(expected.get("min_bound_block_count") or 0)
        min_action_total = int(expected.get("min_action_total") or 0)
        require_search_surface = bool(expected.get("require_search_surface"))
        require_workflow_surface = bool(expected.get("require_workflow_surface"))
        require_validation_surface = bool(expected.get("require_validation_surface"))

        if expected_scene_type:
            _assert(scene_type == expected_scene_type, f"{scene_key} scene_type mismatch: {scene_type} != {expected_scene_type}", errors)

        bound_block_count = int(binding.get("base_contract_bound_block_count") or 0)
        _assert(
            bound_block_count >= min_bound_block_count,
            f"{scene_key} base_contract_bound_block_count below threshold: {bound_block_count} < {min_bound_block_count}",
            errors,
        )
        action_total = int(action_counts.get("total") or 0)
        _assert(action_total >= min_action_total, f"{scene_key} action_surface total below threshold: {action_total} < {min_action_total}", errors)

        if require_search_surface:
            _assert(_nonempty_search(search_surface), f"{scene_key} search_surface must be non-empty", errors)
        if require_workflow_surface:
            _assert(_nonempty_workflow(workflow_surface), f"{scene_key} workflow_surface must be non-empty", errors)
        if require_validation_surface:
            _assert(_nonempty_validation(validation_surface), f"{scene_key} validation_surface must be non-empty", errors)

        for stage in required_pipeline:
            _assert(stage in compile_pipeline, f"{scene_key} compile_pipeline missing stage: {stage}", errors)

    for key in required_scene_keys:
        _assert(key in seen_keys, f"required scene missing from sample compilation: {key}", errors)
    for scene_type in required_scene_types:
        _assert(scene_type in seen_types, f"required scene_type missing from sample compilation: {scene_type}", errors)

    if errors:
        print("[scene_orchestrator_key_scene_compile_guard] FAIL")
        for item in errors:
            print(f" - {item}")
        return 1

    print("[scene_orchestrator_key_scene_compile_guard] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
