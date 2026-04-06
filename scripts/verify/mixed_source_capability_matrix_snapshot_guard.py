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
BASELINE = ROOT / "scripts" / "verify" / "baselines" / "mixed_source_capability_matrix_snapshot.json"
ARTIFACT = ROOT / "artifacts" / "backend" / "mixed_source_capability_matrix_snapshot.json"

MATRIX_PROJECTION = ROOT / "addons" / "smart_core" / "app_config_engine" / "capability" / "projection" / "capability_matrix_projection.py"


def _load_ast(path: Path) -> ast.AST:
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def _save_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _load_json(path: Path) -> Dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _extract_return_keys() -> List[str]:
    tree = _load_ast(MATRIX_PROJECTION)
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef) or node.name != "build_capability_matrix_projection":
            continue
        for stmt in ast.walk(node):
            if not isinstance(stmt, ast.Return) or not isinstance(stmt.value, ast.Dict):
                continue
            out: List[str] = []
            for key in stmt.value.keys:
                if isinstance(key, ast.Constant) and isinstance(key.value, str):
                    out.append(str(key.value))
            return sorted(out)
    return []


def _extract_row_keys() -> List[str]:
    tree = _load_ast(MATRIX_PROJECTION)
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef) or node.name != "build_capability_matrix_projection":
            continue
        for call in ast.walk(node):
            if not isinstance(call, ast.Call):
                continue
            if not isinstance(call.func, ast.Attribute) or call.func.attr != "append":
                continue
            if not isinstance(call.func.value, ast.Name) or call.func.value.id != "list_rows":
                continue
            if not call.args or not isinstance(call.args[0], ast.Dict):
                continue
            out: List[str] = []
            for key in call.args[0].keys:
                if isinstance(key, ast.Constant) and isinstance(key.value, str):
                    out.append(str(key.value))
            return sorted(out)
    return []


def _current_snapshot() -> Dict[str, Any]:
    return {
        "matrix_return_keys": _extract_return_keys(),
        "matrix_row_keys": _extract_row_keys(),
        "required_return_keys": ["total", "by_domain", "by_status", "by_tier", "rows"],
        "required_row_keys": ["key", "domain", "status", "tier"],
    }


def _required_ok(snapshot: Dict[str, Any]) -> bool:
    return set(snapshot.get("required_return_keys") or []).issubset(set(snapshot.get("matrix_return_keys") or [])) and set(snapshot.get("required_row_keys") or []).issubset(set(snapshot.get("matrix_row_keys") or []))


def main() -> int:
    parser = argparse.ArgumentParser(description="Mixed-source capability matrix snapshot guard")
    parser.add_argument("--update-baseline", action="store_true", help="Overwrite baseline with current snapshot")
    args = parser.parse_args()

    current = _current_snapshot()
    _save_json(ARTIFACT, current)

    if not _required_ok(current):
        print("[mixed_source_capability_matrix_snapshot_guard] FAIL")
        print("required matrix keys missing")
        return 2

    if args.update_baseline:
        _save_json(BASELINE, current)
        print("[mixed_source_capability_matrix_snapshot_guard] UPDATED")
        print(f"baseline={BASELINE.relative_to(ROOT).as_posix()}")
        return 0

    baseline = _load_json(BASELINE)
    if not baseline:
        print("[mixed_source_capability_matrix_snapshot_guard] FAIL")
        print(f"missing_or_invalid_baseline={BASELINE.relative_to(ROOT).as_posix()}")
        return 2

    if baseline != current:
        print("[mixed_source_capability_matrix_snapshot_guard] FAIL")
        print("baseline and current matrix snapshot mismatch")
        print(f"artifact={ARTIFACT.relative_to(ROOT).as_posix()}")
        return 2

    print("[mixed_source_capability_matrix_snapshot_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())

