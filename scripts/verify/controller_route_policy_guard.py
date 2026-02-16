#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import ast
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
CONTROLLERS_ROOT = ROOT / "addons/smart_construction_core/controllers"
POLICY = {
    "frontend_api.py": {
        "/api/login": {"type": "json", "auth": "public", "csrf": False, "methods": {"POST"}, "cors": "*"},
        "/api/logout": {"type": "json", "auth": "public", "csrf": False, "methods": {"POST"}, "cors": "*"},
        "/api/session/get": {"type": "json", "auth": "public", "csrf": False, "methods": {"POST"}, "cors": "*"},
        "/api/menu/tree": {"type": "json", "auth": "user", "csrf": False, "methods": {"POST"}, "cors": "*"},
        "/api/user_menus": {"type": "json", "auth": "user", "csrf": False, "methods": {"POST"}, "cors": "*"},
    },
    "scene_template_controller.py": {
        "/api/scenes/export": {"type": "http", "auth": "public", "csrf": False, "methods": {"GET"}},
        "/api/scenes/import": {"type": "http", "auth": "public", "csrf": False, "methods": {"POST"}},
    },
    "pack_controller.py": {
        "/api/packs/publish": {"type": "http", "auth": "public", "csrf": False, "methods": {"POST"}},
        "/api/packs/catalog": {"type": "http", "auth": "public", "csrf": False, "methods": {"GET"}},
        "/api/packs/install": {"type": "http", "auth": "public", "csrf": False, "methods": {"POST"}},
        "/api/packs/upgrade": {"type": "http", "auth": "public", "csrf": False, "methods": {"POST"}},
    },
}


def _literal_value(node: ast.AST):
    if isinstance(node, ast.Constant):
        return node.value
    return None


def _methods_value(node: ast.AST) -> set[str] | None:
    if isinstance(node, (ast.List, ast.Tuple, ast.Set)):
        out: set[str] = set()
        for item in node.elts:
            val = _literal_value(item)
            if isinstance(val, str):
                out.add(val.upper())
        return out
    return None


def _extract_route_specs(path: Path) -> dict[str, dict]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return {}
    specs: dict[str, dict] = {}
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef):
            continue
        for deco in node.decorator_list:
            if not isinstance(deco, ast.Call):
                continue
            func = deco.func
            if not isinstance(func, ast.Attribute) or func.attr != "route":
                continue
            if not deco.args:
                continue
            first = deco.args[0]
            route_path = _literal_value(first) if isinstance(first, ast.Constant) else None
            if not isinstance(route_path, str):
                continue
            record: dict = {}
            for kw in deco.keywords:
                if kw.arg == "methods":
                    methods = _methods_value(kw.value)
                    if methods is not None:
                        record["methods"] = methods
                else:
                    record[kw.arg] = _literal_value(kw.value)
            specs[route_path] = record
    return specs


def main() -> int:
    if not CONTROLLERS_ROOT.is_dir():
        print("[controller_route_policy_guard] FAIL")
        print(f"missing dir: {CONTROLLERS_ROOT.relative_to(ROOT).as_posix()}")
        return 1

    violations: list[str] = []
    for filename, expected_map in sorted(POLICY.items()):
        file_path = CONTROLLERS_ROOT / filename
        if not file_path.is_file():
            violations.append(f"missing allowlist controller file: {file_path.relative_to(ROOT).as_posix()}")
            continue
        actual_specs = _extract_route_specs(file_path)
        rel = file_path.relative_to(ROOT).as_posix()
        for route, expected in expected_map.items():
            actual = actual_specs.get(route)
            if not isinstance(actual, dict):
                violations.append(f"{rel}: route missing for policy check: {route}")
                continue
            for key, val in expected.items():
                if key == "methods":
                    actual_methods = actual.get("methods") or set()
                    if set(actual_methods) != set(val):
                        violations.append(
                            f"{rel}: route {route} methods mismatch expected={sorted(val)} actual={sorted(actual_methods)}"
                        )
                    continue
                if actual.get(key) != val:
                    violations.append(
                        f"{rel}: route {route} {key} mismatch expected={val!r} actual={actual.get(key)!r}"
                    )

    if violations:
        print("[controller_route_policy_guard] FAIL")
        for item in violations:
            print(item)
        return 1

    print("[controller_route_policy_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
