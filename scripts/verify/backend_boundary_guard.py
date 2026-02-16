#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import ast
import json
from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parents[2]
CORE_EXTENSION = ROOT / "addons/smart_construction_core/core_extension.py"
CORE_CONTROLLERS = ROOT / "addons/smart_construction_core/controllers"
SYSTEM_INIT_HANDLER = ROOT / "addons/smart_core/handlers/system_init.py"
BASELINE_JSON = ROOT / "scripts/verify/baselines/backend_boundary_guard.json"

FORBIDDEN_HOOK_SHAPE_RE = re.compile(r'data\[\s*["\'](?:scenes|capabilities)["\']\s*\]')


def _extract_data_write_key(target: ast.expr) -> str | None:
    if not isinstance(target, ast.Subscript):
        return None
    if not isinstance(target.value, ast.Name) or target.value.id != "data":
        return None
    slice_node = target.slice
    if isinstance(slice_node, ast.Constant) and isinstance(slice_node.value, str):
        return slice_node.value
    return None


def _hook_data_write_keys(text: str) -> set[str]:
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return set()
    for node in tree.body:
        if not isinstance(node, ast.FunctionDef) or node.name != "smart_core_extend_system_init":
            continue
        keys: set[str] = set()
        for sub in ast.walk(node):
            if isinstance(sub, ast.Assign):
                for target in sub.targets:
                    key = _extract_data_write_key(target)
                    if key:
                        keys.add(key)
            elif isinstance(sub, ast.AnnAssign):
                key = _extract_data_write_key(sub.target)
                if key:
                    keys.add(key)
            elif isinstance(sub, ast.AugAssign):
                key = _extract_data_write_key(sub.target)
                if key:
                    keys.add(key)
        return keys
    return set()


def _iter_controller_files():
    if not CORE_CONTROLLERS.is_dir():
        return
    for path in CORE_CONTROLLERS.rglob("*.py"):
        yield path


def _find_forbidden_import_modules(text: str, forbidden_modules: tuple[str, ...]) -> set[str]:
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return set()
    hits: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            mod = str(node.module or "")
            for forbidden in forbidden_modules:
                if mod == forbidden or mod.startswith(f"{forbidden}."):
                    hits.add(forbidden)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                mod = str(alias.name or "")
                for forbidden in forbidden_modules:
                    if mod == forbidden or mod.startswith(f"{forbidden}."):
                        hits.add(forbidden)
    return hits


def _to_regex_list(items) -> list[re.Pattern]:
    out: list[re.Pattern] = []
    for item in items if isinstance(items, list) else []:
        pattern = str(item or "").strip()
        if pattern:
            out.append(re.compile(pattern))
    return out


def _load_policy() -> tuple[set[str], set[str], list[re.Pattern], list[re.Pattern], list[re.Pattern], tuple[str, ...]]:
    payload = {}
    if BASELINE_JSON.is_file():
        payload = json.loads(BASELINE_JSON.read_text(encoding="utf-8"))

    allowed_keys = {
        str(item or "").strip()
        for item in (payload.get("allowed_hook_write_keys") if isinstance(payload, dict) else [])
        if str(item or "").strip()
    }
    required_keys = {
        str(item or "").strip()
        for item in (payload.get("required_hook_write_keys") if isinstance(payload, dict) else [])
        if str(item or "").strip()
    }
    forbidden_route_patterns = _to_regex_list(payload.get("forbidden_runtime_route_patterns") if isinstance(payload, dict) else [])
    forbidden_import_patterns = _to_regex_list(payload.get("forbidden_runtime_import_patterns") if isinstance(payload, dict) else [])
    forbidden_sysinit_patterns = _to_regex_list(
        payload.get("forbidden_system_init_scene_registry_patterns") if isinstance(payload, dict) else []
    )
    forbidden_controller_modules = tuple(
        str(item or "").strip()
        for item in (payload.get("forbidden_controller_import_modules") if isinstance(payload, dict) else [])
        if str(item or "").strip()
    )

    if not allowed_keys:
        raise RuntimeError("backend boundary policy missing allowed_hook_write_keys")
    if not required_keys:
        raise RuntimeError("backend boundary policy missing required_hook_write_keys")
    if not forbidden_route_patterns:
        raise RuntimeError("backend boundary policy missing forbidden_runtime_route_patterns")
    if not forbidden_import_patterns:
        raise RuntimeError("backend boundary policy missing forbidden_runtime_import_patterns")
    if not forbidden_sysinit_patterns:
        raise RuntimeError("backend boundary policy missing forbidden_system_init_scene_registry_patterns")
    if not forbidden_controller_modules:
        raise RuntimeError("backend boundary policy missing forbidden_controller_import_modules")

    return (
        allowed_keys,
        required_keys,
        forbidden_route_patterns,
        forbidden_import_patterns,
        forbidden_sysinit_patterns,
        forbidden_controller_modules,
    )


def main() -> int:
    try:
        (
            allowed_hook_keys,
            required_hook_keys,
            forbidden_route_patterns,
            forbidden_import_patterns,
            forbidden_sysinit_patterns,
            forbidden_controller_modules,
        ) = _load_policy()
    except Exception as exc:
        print("[backend_boundary_guard] FAIL")
        print(f"failed to load policy: {exc}")
        return 1

    violations: list[str] = []

    if not CORE_EXTENSION.is_file():
        violations.append("addons/smart_construction_core/core_extension.py missing")
    else:
        text = CORE_EXTENSION.read_text(encoding="utf-8", errors="ignore")
        if FORBIDDEN_HOOK_SHAPE_RE.search(text):
            violations.append(
                "addons/smart_construction_core/core_extension.py: "
                "smart_core_extend_system_init must not write data['scenes']/data['capabilities']"
            )
        assigned_keys = sorted(_hook_data_write_keys(text))
        for key in assigned_keys:
            if key not in allowed_hook_keys:
                violations.append(
                    "addons/smart_construction_core/core_extension.py: "
                    f"smart_core_extend_system_init must not write data['{key}'] "
                    f"(allowed: {sorted(allowed_hook_keys)})"
                )
        for required in sorted(required_hook_keys):
            if required not in assigned_keys:
                violations.append(
                    "addons/smart_construction_core/core_extension.py: "
                    f"smart_core_extend_system_init must write into data['{required}'] namespace"
                )

    if SYSTEM_INIT_HANDLER.is_file():
        sys_init_text = SYSTEM_INIT_HANDLER.read_text(encoding="utf-8", errors="ignore")
        for pattern in forbidden_sysinit_patterns:
            if pattern.search(sys_init_text):
                violations.append(
                    "addons/smart_core/handlers/system_init.py: scene registry import must go through "
                    "smart_core.core.scene_provider"
                )
                break

    for path in _iter_controller_files():
        rel = path.relative_to(ROOT).as_posix()
        text = path.read_text(encoding="utf-8", errors="ignore")
        if any(pattern.search(text) for pattern in forbidden_route_patterns):
            violations.append(
                f"{rel}: controllers in smart_construction_core must not expose "
                "/api/v1/intent or /api/contract/get runtime endpoints"
            )
        if any(pattern.search(text) for pattern in forbidden_import_patterns):
            violations.append(
                f"{rel}: controllers in smart_construction_core must not import "
                "smart_core runtime contract assemblers/governance"
            )
        forbidden_modules = sorted(_find_forbidden_import_modules(text, forbidden_controller_modules))
        for module in forbidden_modules:
            violations.append(
                f"{rel}: controllers in smart_construction_core must not import {module}"
            )

    if violations:
        print("[backend_boundary_guard] FAIL")
        for item in violations:
            print(item)
        return 1

    print("[backend_boundary_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
