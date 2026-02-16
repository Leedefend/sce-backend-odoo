#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import ast
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
MODELS_ROOT = ROOT / "addons/smart_construction_core/models"
FORBIDDEN_IMPORT_PREFIXES = (
    "odoo.addons.smart_construction_scene.scene_registry",
    "odoo.addons.smart_core.core.scene_provider",
    "odoo.addons.smart_core.utils.contract_governance",
)


def _iter_model_files():
    if not MODELS_ROOT.is_dir():
        return
    for path in MODELS_ROOT.rglob("*.py"):
        yield path


def _forbidden_import_hits(text: str) -> set[str]:
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return set()
    hits: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            mod = str(node.module or "")
            for prefix in FORBIDDEN_IMPORT_PREFIXES:
                if mod == prefix or mod.startswith(f"{prefix}."):
                    hits.add(prefix)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                mod = str(alias.name or "")
                for prefix in FORBIDDEN_IMPORT_PREFIXES:
                    if mod == prefix or mod.startswith(f"{prefix}."):
                        hits.add(prefix)
    return hits


def main() -> int:
    violations: list[str] = []
    if not MODELS_ROOT.is_dir():
        print("[model_ui_dependency_guard] FAIL")
        print(f"missing dir: {MODELS_ROOT.relative_to(ROOT).as_posix()}")
        return 1
    for path in _iter_model_files():
        text = path.read_text(encoding="utf-8", errors="ignore")
        rel = path.relative_to(ROOT).as_posix()
        for hit in sorted(_forbidden_import_hits(text)):
            violations.append(f"{rel}: forbidden model-layer UI dependency import: {hit}")

    if violations:
        print("[model_ui_dependency_guard] FAIL")
        for item in violations:
            print(item)
        return 1

    print("[model_ui_dependency_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
