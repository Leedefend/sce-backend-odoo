#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import ast
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
CONTROLLERS_ROOT = ROOT / "addons/smart_construction_core/controllers"
ARTIFACT_JSON = ROOT / "artifacts" / "controller_delegate_guard.json"
ALLOWLIST = {
    "frontend_api.py",
    "scene_template_controller.py",
    "pack_controller.py",
}
ENVELOPE_KEYS = {"ok", "data", "meta", "code", "error", "status"}
RUNTIME_SHAPE_KEYS = {"scenes", "capabilities"}


def _iter_controller_files():
    if not CONTROLLERS_ROOT.is_dir():
        return
    for path in CONTROLLERS_ROOT.rglob("*.py"):
        if path.name == "__init__.py":
            continue
        yield path


def _is_route_method(fn: ast.FunctionDef) -> bool:
    for deco in fn.decorator_list:
        if isinstance(deco, ast.Call):
            node = deco.func
            if isinstance(node, ast.Attribute) and node.attr == "route":
                return True
        if isinstance(deco, ast.Attribute) and deco.attr == "route":
            return True
    return False


def _dict_keys(node: ast.Dict) -> set[str]:
    out: set[str] = set()
    for key in node.keys:
        if isinstance(key, ast.Constant) and isinstance(key.value, str):
            out.add(str(key.value))
    return out


def _route_return_violations(path: Path, text: str) -> list[str]:
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return []

    rel = path.relative_to(ROOT).as_posix()
    violations: list[str] = []
    for node in tree.body:
        if not isinstance(node, ast.ClassDef):
            continue
        for fn in node.body:
            if not isinstance(fn, ast.FunctionDef) or not _is_route_method(fn):
                continue
            for sub in ast.walk(fn):
                if not isinstance(sub, ast.Return) or not isinstance(sub.value, ast.Dict):
                    continue
                keys = _dict_keys(sub.value)
                bad = sorted((keys & ENVELOPE_KEYS) | (keys & RUNTIME_SHAPE_KEYS))
                if not bad:
                    continue
                violations.append(
                    f"{rel}:{sub.lineno}: route method {fn.name} returns raw dict with restricted keys: {','.join(bad)}"
                )
    return violations


def main() -> int:
    if not CONTROLLERS_ROOT.is_dir():
        print("[controller_delegate_guard] FAIL")
        print(f"missing dir: {CONTROLLERS_ROOT.relative_to(ROOT).as_posix()}")
        return 1

    violations: list[str] = []
    for path in _iter_controller_files():
        if path.name in ALLOWLIST:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        violations.extend(_route_return_violations(path, text))

    report = {
        "ok": not violations,
        "summary": {
            "controller_root": CONTROLLERS_ROOT.relative_to(ROOT).as_posix(),
            "allowlist_size": len(ALLOWLIST),
            "violation_count": len(violations),
        },
        "violations": violations,
    }
    ARTIFACT_JSON.parent.mkdir(parents=True, exist_ok=True)
    ARTIFACT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(str(ARTIFACT_JSON))
    if violations:
        print("[controller_delegate_guard] FAIL")
        for item in violations:
            print(item)
        return 1

    print("[controller_delegate_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
