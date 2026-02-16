#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import ast
from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parents[2]
CORE_EXTENSION = ROOT / "addons/smart_construction_core/core_extension.py"
CORE_CONTROLLERS = ROOT / "addons/smart_construction_core/controllers"
SYSTEM_INIT_HANDLER = ROOT / "addons/smart_core/handlers/system_init.py"

FORBIDDEN_HOOK_SHAPE_RE = re.compile(r'data\[\s*["\'](?:scenes|capabilities)["\']\s*\]')
FORBIDDEN_RUNTIME_ROUTE_RE = re.compile(r'@http\.route\(\s*["\'](?:/api/v1/intent|/api/contract/get)')
FORBIDDEN_RUNTIME_IMPORT_RE = re.compile(
    r"(?:from\s+odoo\.addons\.smart_core\.utils\.contract_governance\s+import)"
    r"|(?:from\s+odoo\.addons\.smart_core\.handlers\.system_init\s+import)"
    r"|(?:from\s+odoo\.addons\.smart_core\.core\.scene_provider\s+import)"
    r"|(?:import\s+odoo\.addons\.smart_core\.core\.scene_provider)"
)
FORBIDDEN_SYSTEM_INIT_SCENE_REGISTRY_RE = re.compile(
    r"(?:from\s+odoo\.addons\.smart_construction_scene\.scene_registry\s+import)"
)


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


def main() -> int:
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
            if key != "ext_facts":
                violations.append(
                    "addons/smart_construction_core/core_extension.py: "
                    f"smart_core_extend_system_init must not write data['{key}'] (allowed: data['ext_facts'])"
                )
        if "ext_facts" not in text:
            violations.append(
                "addons/smart_construction_core/core_extension.py: "
                "smart_core_extend_system_init must write into data['ext_facts'] namespace"
            )

    if SYSTEM_INIT_HANDLER.is_file():
        sys_init_text = SYSTEM_INIT_HANDLER.read_text(encoding="utf-8", errors="ignore")
        if FORBIDDEN_SYSTEM_INIT_SCENE_REGISTRY_RE.search(sys_init_text):
            violations.append(
                "addons/smart_core/handlers/system_init.py: scene registry import must go through "
                "smart_core.core.scene_provider"
            )

    for path in _iter_controller_files():
        rel = path.relative_to(ROOT).as_posix()
        text = path.read_text(encoding="utf-8", errors="ignore")
        if FORBIDDEN_RUNTIME_ROUTE_RE.search(text):
            violations.append(
                f"{rel}: controllers in smart_construction_core must not expose "
                "/api/v1/intent or /api/contract/get runtime endpoints"
            )
        if FORBIDDEN_RUNTIME_IMPORT_RE.search(text):
            violations.append(
                f"{rel}: controllers in smart_construction_core must not import "
                "smart_core runtime contract assemblers/governance"
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
