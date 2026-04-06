#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path
import sys
from typing import Any, Dict, List


ROOT = Path(__file__).resolve().parents[2]
BASELINE = ROOT / "scripts" / "verify" / "baselines" / "native_capability_projection_snapshot.json"
ARTIFACT = ROOT / "artifacts" / "backend" / "native_capability_projection_snapshot.json"

NATIVE_DIR = ROOT / "addons" / "smart_core" / "app_config_engine" / "capability" / "native"
SERVICE = NATIVE_DIR / "native_projection_service.py"
SCHEMA = ROOT / "addons" / "smart_core" / "app_config_engine" / "capability" / "schema" / "capability_schema.py"


def _load_ast(path: Path) -> ast.AST:
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def _load_json(path: Path) -> Dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _save_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _extract_projection_calls() -> List[str]:
    tree = _load_ast(SERVICE)
    calls: List[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef) or node.name != "load_native_capability_rows":
            continue
        for stmt in node.body:
            call_name = ""
            if isinstance(stmt, ast.Try):
                for try_stmt in stmt.body:
                    if not isinstance(try_stmt, ast.Expr) or not isinstance(try_stmt.value, ast.Call):
                        continue
                    call = try_stmt.value
                    if not isinstance(call.func, ast.Attribute) or call.func.attr != "extend":
                        continue
                    if not call.args:
                        continue
                    first_arg = call.args[0]
                    if isinstance(first_arg, ast.Call) and isinstance(first_arg.func, ast.Name):
                        call_name = first_arg.func.id
                        break
                if call_name:
                    calls.append(call_name)
    return calls


def _extract_schema_native_types() -> List[str]:
    tree = _load_ast(SCHEMA)
    out: List[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        if not any(isinstance(target, ast.Name) and target.id == "ALLOWED_TYPES" for target in node.targets):
            continue
        if not isinstance(node.value, ast.Set):
            continue
        for element in node.value.elts:
            if isinstance(element, ast.Constant) and isinstance(element.value, str):
                value = str(element.value)
                if value.startswith("native_"):
                    out.append(value)
    return sorted(set(out))


def _extract_adapter_declared_types() -> Dict[str, List[str]]:
    out: Dict[str, List[str]] = {}
    for path in sorted(NATIVE_DIR.glob("*_adapter.py")):
        text = path.read_text(encoding="utf-8", errors="ignore")
        declared: List[str] = []
        for marker in (
            "native_menu_entry",
            "native_window_action",
            "native_model_access",
            "native_server_action",
            "native_report_action",
            "native_view_binding",
        ):
            if f'"type": "{marker}"' in text:
                declared.append(marker)
        out[path.name] = sorted(declared)
    return out


def _current_snapshot() -> Dict[str, Any]:
    return {
        "native_types_in_schema": _extract_schema_native_types(),
        "projection_calls": _extract_projection_calls(),
        "adapter_files": sorted([path.name for path in NATIVE_DIR.glob("*_adapter.py")]),
        "adapter_declared_native_types": _extract_adapter_declared_types(),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Native capability projection snapshot guard")
    parser.add_argument("--update-baseline", action="store_true", help="Overwrite baseline with current snapshot")
    args = parser.parse_args()

    current = _current_snapshot()
    _save_json(ARTIFACT, current)

    if args.update_baseline:
        _save_json(BASELINE, current)
        print("[native_capability_projection_snapshot_guard] UPDATED")
        print(f"baseline={BASELINE.relative_to(ROOT).as_posix()}")
        return 0

    baseline = _load_json(BASELINE)
    if not baseline:
        print("[native_capability_projection_snapshot_guard] FAIL")
        print(f"missing_or_invalid_baseline={BASELINE.relative_to(ROOT).as_posix()}")
        return 2

    if baseline != current:
        print("[native_capability_projection_snapshot_guard] FAIL")
        print("baseline and current snapshot mismatch")
        print(f"artifact={ARTIFACT.relative_to(ROOT).as_posix()}")
        return 2

    print("[native_capability_projection_snapshot_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())

