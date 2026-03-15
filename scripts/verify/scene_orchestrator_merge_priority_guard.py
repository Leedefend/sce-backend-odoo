#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
IO_SPEC = ROOT / "docs" / "architecture" / "scene_orchestrator_io_contract_and_industry_interface_spec_v1.md"
COMPILER = ROOT / "addons" / "smart_core" / "core" / "scene_dsl_compiler.py"


def _assert(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def _load_scene_compile():
    spec = importlib.util.spec_from_file_location("scene_dsl_compiler_guard", COMPILER)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"spec unavailable: {COMPILER}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    fn = getattr(module, "scene_compile", None)
    if not callable(fn):
        raise RuntimeError("scene_compile not found")
    return fn


def _runtime_sample_assert(errors: list[str]) -> None:
    scene_compile = _load_scene_compile()
    payload = {
        "code": "projects.list",
        "name": "项目列表",
        "target": {"route": "/s/projects.list", "action_id": 100},
        "actions": [{"key": "open_scene", "intent": "ui.contract"}],
    }
    base_contract = {
        "views": {"tree": {"fields": ["name", "stage_id"]}},
        "search": {"fields": ["name"], "filters": ["my_projects"]},
        "permissions": {"allowed": True},
        "workflow": {"state_field": "state", "states": ["draft", "done"]},
    }
    compiled = scene_compile(payload, scene_key="projects.list", ui_base_contract=base_contract, provider_registry={})
    meta = compiled.get("meta") if isinstance(compiled.get("meta"), dict) else {}
    pipeline = meta.get("compile_pipeline") if isinstance(meta.get("compile_pipeline"), list) else []
    verdict = meta.get("compile_verdict") if isinstance(meta.get("compile_verdict"), dict) else {}

    required_pipeline = [
        "profile_apply",
        "policy_apply",
        "provider_merge",
        "permission_workflow_gate",
    ]
    for stage in required_pipeline:
        _assert(stage in pipeline, f"runtime sample missing pipeline stage: {stage}", errors)
    stage_order = [pipeline.index(stage) for stage in required_pipeline if stage in pipeline]
    _assert(stage_order == sorted(stage_order), "runtime sample merge-priority stage order mismatch", errors)

    _assert(verdict.get("ok") is True, "runtime sample compile_verdict.ok must be true", errors)
    _assert(
        isinstance(compiled.get("permission_surface"), dict),
        "runtime sample missing permission_surface output",
        errors,
    )

    intent_mapping_payload = {
        "code": "projects.list",
        "name": "项目列表",
        "target": {"route": "/s/projects.list", "action_id": 100},
        "actions": [{"key": "create_project", "label": "新建项目"}],
    }
    intent_mapping_compiled = scene_compile(
        intent_mapping_payload,
        scene_key="projects.list",
        ui_base_contract=base_contract,
        provider_registry={},
    )
    mapped_actions = intent_mapping_compiled.get("actions") if isinstance(intent_mapping_compiled.get("actions"), list) else []
    mapped_create = next(
        (
            row for row in mapped_actions
            if isinstance(row, dict) and str(row.get("key") or "").strip() == "create_project"
        ),
        {},
    )
    _assert(
        str(mapped_create.get("intent") or "") == "record.create",
        "intent mapping sample expected create_project -> record.create",
        errors,
    )

    conflict_payload = {
        "code": "projects.list",
        "name": "项目列表",
        "target": {"route": "/s/projects.list", "action_id": 100},
        "actions": [{"key": "open_scene", "intent": "ui.contract"}],
        "policies": {
            "search_policy": {
                "default_filters": ["policy_only"],
            }
        },
        "providers": [{"key": "conflict_provider"}],
        "runtime": {"role_code": "project_manager"},
    }
    conflict_base_contract = {
        "views": {"tree": {"fields": ["name", "stage_id"]}},
        "search": {"fields": ["name"], "filters": ["base_only"]},
        "permissions": {"allowed": True},
    }
    conflict_provider_registry = {
        "conflict_provider": {
            "search_surface": {"filters": ["provider_only"]},
            "permission_surface": {"allowed": False},
            "actions": [{"key": "provider_action", "intent": "ui.contract"}],
        }
    }
    conflict_compiled = scene_compile(
        conflict_payload,
        scene_key="projects.list",
        ui_base_contract=conflict_base_contract,
        provider_registry=conflict_provider_registry,
    )
    conflict_meta = conflict_compiled.get("meta") if isinstance(conflict_compiled.get("meta"), dict) else {}
    resolver_meta = conflict_meta.get("merge_resolver") if isinstance(conflict_meta.get("merge_resolver"), dict) else {}
    conflicts = resolver_meta.get("conflicts") if isinstance(resolver_meta.get("conflicts"), list) else []

    _assert(
        conflict_compiled.get("search_surface", {}).get("filters") == ["provider_only"],
        "conflict sample expected provider to override policy/base filters",
        errors,
    )
    _assert(
        conflict_compiled.get("actions") == [],
        "conflict sample expected permission gate to prune actions",
        errors,
    )
    _assert(
        len(conflicts) >= 1,
        "conflict sample expected merge_resolver conflicts",
        errors,
    )


def main() -> int:
    errors: list[str] = []
    for path in (IO_SPEC, COMPILER):
        if not path.is_file():
            errors.append(f"missing file: {path}")
    if errors:
        print("[scene_orchestrator_merge_priority_guard] FAIL")
        for item in errors:
            print(f" - {item}")
        return 1

    io_text = IO_SPEC.read_text(encoding="utf-8")
    compiler_text = COMPILER.read_text(encoding="utf-8")

    priority_tokens = (
        "平台默认规则（Platform Default）",
        "原生能力事实（Base Fact）",
        "行业 Profile",
        "行业 Policy",
        "Provider 运行时增强",
        "权限与治理裁决（最终裁决层）",
    )
    for token in priority_tokens:
        _assert(token in io_text, f"io spec missing priority token: {token}", errors)

    order_tokens = (
        "Profile Apply",
        "Policy Apply",
        "Provider Merge",
        "Permission/Workflow Gate",
    )
    for token in order_tokens:
        _assert(token in io_text, f"io spec missing execution order token: {token}", errors)

    _assert("compile_pipeline" in compiler_text, "compiler missing compile_pipeline trace", errors)
    _assert("compile_verdict" in compiler_text, "compiler missing compile_verdict", errors)
    _assert("semantic_validate" in compiler_text, "compiler missing semantic validation stage", errors)

    try:
        _runtime_sample_assert(errors)
    except Exception as exc:
        errors.append(f"runtime sample failed: {exc}")

    if errors:
        print("[scene_orchestrator_merge_priority_guard] FAIL")
        for item in errors:
            print(f" - {item}")
        return 1

    print("[scene_orchestrator_merge_priority_guard] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
