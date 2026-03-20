#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
BASELINE = ROOT / "scripts" / "verify" / "baselines" / "backend_contract_closure_snapshot.json"
ARTIFACT = ROOT / "artifacts" / "backend" / "backend_contract_closure_snapshot.json"

META_INTENT_HANDLER = ROOT / "addons" / "smart_core" / "handlers" / "meta_intent_catalog.py"
SCENE_GOV_BUILDER = ROOT / "addons" / "smart_core" / "core" / "scene_governance_payload_builder.py"


def _load_ast(path: Path) -> ast.AST:
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def _dict_keys(node: ast.Dict) -> list[str]:
    out: list[str] = []
    for key in node.keys:
        if isinstance(key, ast.Constant) and isinstance(key.value, str):
            out.append(str(key.value))
    return out


def _extract_meta_intent_payload_keys() -> list[str]:
    tree = _load_ast(META_INTENT_HANDLER)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "handle":
            for stmt in ast.walk(node):
                if isinstance(stmt, ast.Return) and isinstance(stmt.value, ast.Tuple) and stmt.value.elts:
                    first = stmt.value.elts[0]
                    if isinstance(first, ast.Dict):
                        return sorted(_dict_keys(first))
    return []


def _extract_scene_governance_keys() -> list[str]:
    tree = _load_ast(SCENE_GOV_BUILDER)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "build_scene_governance_payload_v1":
            for stmt in ast.walk(node):
                if isinstance(stmt, ast.Return) and isinstance(stmt.value, ast.Dict):
                    return sorted(_dict_keys(stmt.value))
    return []


def _load_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def _save_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _current_snapshot() -> dict[str, Any]:
    return {
        "meta_intent_catalog": {
            "payload_keys": _extract_meta_intent_payload_keys(),
        },
        "scene_governance_v1": {
            "payload_keys": _extract_scene_governance_keys(),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Backend contract closure snapshot baseline guard")
    parser.add_argument("--update-baseline", action="store_true", help="Overwrite baseline with current snapshot")
    args = parser.parse_args()

    current = _current_snapshot()
    _save_json(ARTIFACT, current)

    if args.update_baseline:
        _save_json(BASELINE, current)
        print("[backend_contract_closure_snapshot_guard] UPDATED")
        print(f"baseline={BASELINE.relative_to(ROOT).as_posix()}")
        return 0

    baseline = _load_json(BASELINE)
    if not baseline:
        print("[backend_contract_closure_snapshot_guard] FAIL")
        print(f"missing_or_invalid_baseline={BASELINE.relative_to(ROOT).as_posix()}")
        return 2

    if baseline != current:
        print("[backend_contract_closure_snapshot_guard] FAIL")
        print("baseline and current snapshot mismatch")
        print(f"artifact={ARTIFACT.relative_to(ROOT).as_posix()}")
        return 2

    print("[backend_contract_closure_snapshot_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())

