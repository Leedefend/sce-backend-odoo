#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import ast
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CONTROLLERS_DIR = ROOT / "addons" / "smart_core" / "controllers"
OUT = ROOT / "artifacts" / "architecture" / "envelope_consistency_audit_v1.json"
REQUIRED_ENVELOPE_KEYS = {"ok", "data", "error", "meta", "effect"}


def _extract_dict_string_keys(node: ast.AST) -> set[str]:
    if not isinstance(node, ast.Dict):
        return set()
    keys: set[str] = set()
    for key_node in node.keys:
        if isinstance(key_node, ast.Constant) and isinstance(key_node.value, str):
            keys.add(key_node.value)
    return keys


def _extract_envelope_keys(tree: ast.AST, function_name: str) -> list[str]:
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef) or node.name != function_name:
            continue
        for child in ast.walk(node):
            if not isinstance(child, ast.Call):
                continue
            fn = ast.unparse(child.func) if hasattr(ast, "unparse") else ""
            if "_json_response" not in fn and "make_json_response" not in fn:
                continue
            if not child.args:
                continue
            keys = _extract_dict_string_keys(child.args[0])
            if keys:
                return sorted(keys)
    return []


def _extract_route_delegation_signals(tree: ast.AST) -> list[str]:
    signals: list[str] = []
    api_base_imported_symbols: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module and node.module.endswith("api_base"):
            for alias in node.names:
                api_base_imported_symbols.add(alias.asname or alias.name)

    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef):
            continue
        decorators = [ast.unparse(dec) for dec in node.decorator_list if hasattr(ast, "unparse")]
        if not any("http.route" in deco for deco in decorators):
            continue

        return_calls: list[str] = []
        for child in ast.walk(node):
            if not isinstance(child, ast.Return):
                continue
            if not isinstance(child.value, ast.Call):
                continue
            fn = ast.unparse(child.value.func) if hasattr(ast, "unparse") else ""
            if fn:
                return_calls.append(fn)

        for fn in return_calls:
            if fn in api_base_imported_symbols:
                signals.append(f"route_return_api_base:{node.name}->{fn}")
                continue
            if "Controller()." in fn:
                signals.append(f"route_return_controller_delegate:{node.name}->{fn}")

    return sorted(set(signals))


def _audit_file(path: Path) -> dict:
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)

    route_methods = []
    api_route_methods = []
    make_json_calls = 0
    make_response_calls = 0
    build_error_calls = 0

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            decorators = [ast.unparse(dec) for dec in node.decorator_list if hasattr(ast, "unparse")]
            if any("http.route" in deco for deco in decorators):
                route_methods.append(node.name)
                if any("/api/" in deco for deco in decorators):
                    api_route_methods.append(node.name)

        if isinstance(node, ast.Call):
            fn = ast.unparse(node.func) if hasattr(ast, "unparse") else ""
            if "make_json_response" in fn:
                make_json_calls += 1
            if "make_response" in fn and "make_json_response" not in fn:
                make_response_calls += 1
            if "build_error_envelope" in fn:
                build_error_calls += 1

    ok_keys = _extract_envelope_keys(tree, "_ok")
    fail_keys = _extract_envelope_keys(tree, "_fail")
    route_delegation_signals = _extract_route_delegation_signals(tree)
    has_required_ok = REQUIRED_ENVELOPE_KEYS.issubset(set(ok_keys))
    has_required_fail = REQUIRED_ENVELOPE_KEYS.issubset(set(fail_keys))

    if len(route_methods) == 0:
        envelope_shape = "no_route"
    elif has_required_ok and has_required_fail:
        envelope_shape = "local_unified_v1"
    elif make_json_calls > 0 or build_error_calls > 0:
        envelope_shape = "delegated_envelope"
    elif route_delegation_signals:
        envelope_shape = "delegated_envelope"
    elif make_response_calls > 0:
        envelope_shape = "local_legacy_or_unknown"
    else:
        envelope_shape = "no_envelope_signal"

    return {
        "file": str(path.relative_to(ROOT)),
        "route_method_count": len(route_methods),
        "route_methods": route_methods,
        "api_route_method_count": len(api_route_methods),
        "api_route_methods": api_route_methods,
        "make_json_response_calls": make_json_calls,
        "make_response_calls": make_response_calls,
        "build_error_envelope_calls": build_error_calls,
        "ok_keys": ok_keys,
        "fail_keys": fail_keys,
        "route_delegation_signals": route_delegation_signals,
        "envelope_shape": envelope_shape,
    }


def main() -> int:
    rows = [_audit_file(path) for path in sorted(CONTROLLERS_DIR.glob("*.py"))]
    files_with_routes = [row for row in rows if row["route_method_count"] > 0]
    files_with_api_routes = [row for row in rows if row["api_route_method_count"] > 0]

    inconsistent_candidates = [
        row["file"]
        for row in files_with_api_routes
        if row["envelope_shape"] in {"local_legacy_or_unknown", "no_envelope_signal"}
    ]

    status = "PASS" if len(inconsistent_candidates) == 0 else "FAIL"

    payload = {
        "status": status,
        "summary": {
            "controller_files": len(rows),
            "files_with_routes": len(files_with_routes),
            "files_with_api_routes": len(files_with_api_routes),
            "inconsistent_candidate_count": len(inconsistent_candidates),
            "required_envelope_keys": sorted(REQUIRED_ENVELOPE_KEYS),
        },
        "inconsistent_candidates": sorted(inconsistent_candidates),
        "rows": rows,
        "note": "schema-aware envelope audit based on local _ok/_fail or delegated envelope helpers",
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    if status == "PASS":
        print(
            "[verify.contract.envelope_consistency_guard] PASS "
            f"files_with_routes={payload['summary']['files_with_routes']} "
            f"candidates={payload['summary']['inconsistent_candidate_count']}"
        )
        return 0

    print(
        "[verify.contract.envelope_consistency_guard] FAIL "
        f"files_with_routes={payload['summary']['files_with_routes']} "
        f"candidates={payload['summary']['inconsistent_candidate_count']}"
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
