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
BASELINE = ROOT / "scripts" / "verify" / "baselines" / "runtime_exposure_projection_schema_snapshot.json"
ARTIFACT = ROOT / "artifacts" / "backend" / "runtime_exposure_projection_schema_snapshot.json"

LIST_PROJECTION = ROOT / "addons" / "smart_core" / "app_config_engine" / "capability" / "projection" / "capability_list_projection.py"
WORKSPACE_PROJECTION = ROOT / "addons" / "smart_core" / "app_config_engine" / "capability" / "projection" / "workspace_projection.py"


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


def _extract_append_dict_keys(path: Path, function_name: str, list_name: str) -> List[str]:
    tree = _load_ast(path)
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef) or node.name != function_name:
            continue
        keys: set[str] = set()
        for call in ast.walk(node):
            if not isinstance(call, ast.Call):
                continue
            if not isinstance(call.func, ast.Attribute):
                continue
            if call.func.attr != "append":
                continue
            if not isinstance(call.func.value, ast.Name) or call.func.value.id != list_name:
                continue
            if not call.args:
                continue
            payload = call.args[0]
            if isinstance(payload, ast.Dict):
                for key_node in payload.keys:
                    if isinstance(key_node, ast.Constant) and isinstance(key_node.value, str):
                        keys.add(str(key_node.value))
        return sorted(keys)
    return []


def _current_snapshot() -> Dict[str, Any]:
    list_keys = _extract_append_dict_keys(
        LIST_PROJECTION,
        function_name="build_capability_list_projection",
        list_name="out",
    )
    workspace_keys = _extract_append_dict_keys(
        WORKSPACE_PROJECTION,
        function_name="build_workspace_projection",
        list_name="tiles",
    )
    return {
        "capability_list_projection_fields": list_keys,
        "workspace_projection_fields": workspace_keys,
        "required_runtime_exposure_fields": ["primary_intent", "runtime_target"],
    }


def _has_required_fields(snapshot: Dict[str, Any]) -> bool:
    required = set(snapshot.get("required_runtime_exposure_fields") or [])
    list_fields = set(snapshot.get("capability_list_projection_fields") or [])
    workspace_fields = set(snapshot.get("workspace_projection_fields") or [])
    return required.issubset(list_fields) and required.issubset(workspace_fields)


def main() -> int:
    parser = argparse.ArgumentParser(description="Runtime exposure projection schema snapshot guard")
    parser.add_argument("--update-baseline", action="store_true", help="Overwrite baseline with current snapshot")
    args = parser.parse_args()

    current = _current_snapshot()
    _save_json(ARTIFACT, current)

    if not _has_required_fields(current):
        print("[runtime_exposure_projection_schema_snapshot_guard] FAIL")
        print("required runtime exposure fields missing in current projection snapshot")
        return 2

    if args.update_baseline:
        _save_json(BASELINE, current)
        print("[runtime_exposure_projection_schema_snapshot_guard] UPDATED")
        print(f"baseline={BASELINE.relative_to(ROOT).as_posix()}")
        return 0

    baseline = _load_json(BASELINE)
    if not baseline:
        print("[runtime_exposure_projection_schema_snapshot_guard] FAIL")
        print(f"missing_or_invalid_baseline={BASELINE.relative_to(ROOT).as_posix()}")
        return 2

    if baseline != current:
        print("[runtime_exposure_projection_schema_snapshot_guard] FAIL")
        print("baseline and current snapshot mismatch")
        print(f"artifact={ARTIFACT.relative_to(ROOT).as_posix()}")
        return 2

    print("[runtime_exposure_projection_schema_snapshot_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())

