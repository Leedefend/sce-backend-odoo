#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import ast
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
ADAPTER_FILE = ROOT / "addons" / "smart_core" / "core" / "industry_runtime_service_adapter.py"
PROVIDER_FILE = ROOT / "addons" / "smart_construction_core" / "core_extension.py"
ARTIFACT_JSON = ROOT / "artifacts" / "adapter_protocol_hook_guard.json"


def _parse_module(path: Path):
    text = path.read_text(encoding="utf-8", errors="ignore")
    return ast.parse(text)


def _adapter_required_hooks(tree: ast.AST) -> set[str]:
    hooks: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if not isinstance(node.func, ast.Name) or node.func.id != "call_extension_hook_first":
            continue
        if len(node.args) < 2:
            continue
        hook_arg = node.args[1]
        if isinstance(hook_arg, ast.Constant) and isinstance(hook_arg.value, str):
            hooks.add(hook_arg.value)
    return hooks


def _provider_hook_defs(tree: ast.AST) -> set[str]:
    defs: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            defs.add(node.name)
    return defs


def main() -> int:
    adapter_tree = _parse_module(ADAPTER_FILE)
    provider_tree = _parse_module(PROVIDER_FILE)

    required = _adapter_required_hooks(adapter_tree)
    provided = _provider_hook_defs(provider_tree)
    missing = sorted(hook for hook in required if hook not in provided)

    report = {
        "ok": not missing,
        "summary": {
            "adapter_file": ADAPTER_FILE.relative_to(ROOT).as_posix(),
            "provider_file": PROVIDER_FILE.relative_to(ROOT).as_posix(),
            "required_hook_count": len(required),
            "provided_hook_count": len(provided),
            "missing_hook_count": len(missing),
        },
        "required_hooks": sorted(required),
        "missing_hooks": missing,
    }
    ARTIFACT_JSON.parent.mkdir(parents=True, exist_ok=True)
    ARTIFACT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(str(ARTIFACT_JSON))

    if missing:
        print("[adapter_protocol_hook_guard] FAIL")
        for hook in missing:
            print(f"missing hook: {hook}")
        return 1

    print("[adapter_protocol_hook_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
