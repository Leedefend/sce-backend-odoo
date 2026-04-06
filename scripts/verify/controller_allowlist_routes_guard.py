#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import ast
import json
from pathlib import Path
import sys

from controller_allowlist_policy import CONTROLLER_ROUTE_POLICY


ROOT = Path(__file__).resolve().parents[2]
ARTIFACT_JSON = ROOT / "artifacts" / "controller_allowlist_routes_guard.json"
ALLOWED_ROUTE_MAP = {
    rel_path: set(routes.keys()) for rel_path, routes in CONTROLLER_ROUTE_POLICY.items()
}


def _iter_allowlist_files():
    for rel_path in sorted(ALLOWED_ROUTE_MAP.keys()):
        path = ROOT / rel_path
        if path.is_file():
            yield path


def _extract_route_paths(fn: ast.FunctionDef) -> set[str]:
    paths: set[str] = set()
    for deco in fn.decorator_list:
        if not isinstance(deco, ast.Call):
            continue
        func = deco.func
        if not isinstance(func, ast.Attribute) or func.attr != "route":
            continue
        if deco.args:
            first = deco.args[0]
            if isinstance(first, ast.Constant) and isinstance(first.value, str):
                paths.add(str(first.value))
            elif isinstance(first, (ast.Tuple, ast.List)):
                for item in first.elts:
                    if isinstance(item, ast.Constant) and isinstance(item.value, str):
                        paths.add(str(item.value))
    return paths


def _collect_routes(text: str) -> set[str]:
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return set()
    routes: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            routes |= _extract_route_paths(node)
    return routes


def main() -> int:
    violations: list[str] = []
    missing_files: list[str] = []
    for rel_path in sorted(ALLOWED_ROUTE_MAP.keys()):
        policy_path = ROOT / rel_path
        if not policy_path.is_file():
            missing_files.append(rel_path)

    if missing_files:
        for rel_path in missing_files:
            violations.append(f"missing allowlist controller file: {rel_path}")

    for path in _iter_allowlist_files():
        rel = path.relative_to(ROOT).as_posix()
        expected = ALLOWED_ROUTE_MAP[rel]
        text = path.read_text(encoding="utf-8", errors="ignore")
        actual = _collect_routes(text)
        extra = sorted(actual - expected)
        missing = sorted(expected - actual)
        if extra:
            violations.append(f"{rel}: unexpected allowlist routes: {', '.join(extra)}")
        if missing:
            violations.append(f"{rel}: missing allowlist routes: {', '.join(missing)}")

    report = {
        "ok": not violations,
        "summary": {
            "policy_scope": "cross-module",
            "allowlist_size": len(ALLOWED_ROUTE_MAP),
            "violation_count": len(violations),
        },
        "violations": violations,
    }
    ARTIFACT_JSON.parent.mkdir(parents=True, exist_ok=True)
    ARTIFACT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(str(ARTIFACT_JSON))
    if violations:
        print("[controller_allowlist_routes_guard] FAIL")
        for item in violations:
            print(item)
        return 1

    print("[controller_allowlist_routes_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
