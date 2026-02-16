#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import ast
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
PROVIDER = ROOT / "addons/smart_core/core/scene_provider.py"
ADDONS_ROOT = ROOT / "addons"
BASELINE_JSON = ROOT / "scripts/verify/baselines/scene_provider_guard.json"

PROVIDER_MODULE = "odoo.addons.smart_core.core.scene_provider"


def _imports_scene_provider(file_text: str) -> bool:
    try:
        tree = ast.parse(file_text)
    except SyntaxError:
        return False
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == PROVIDER_MODULE:
            return True
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == PROVIDER_MODULE:
                    return True
    return False


def _imports_forbidden_provider_module(file_text: str, forbidden_prefixes: tuple[str, ...]) -> bool:
    try:
        tree = ast.parse(file_text)
    except SyntaxError:
        return False
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            mod = str(node.module or "")
            for prefix in forbidden_prefixes:
                if mod == prefix or mod.startswith(f"{prefix}."):
                    return True
        elif isinstance(node, ast.Import):
            for alias in node.names:
                mod = str(alias.name or "")
                for prefix in forbidden_prefixes:
                    if mod == prefix or mod.startswith(f"{prefix}."):
                        return True
    return False


def _load_policy() -> tuple[set[str], tuple[str, ...], tuple[str, ...]]:
    payload = {}
    if BASELINE_JSON.is_file():
        payload = json.loads(BASELINE_JSON.read_text(encoding="utf-8"))

    allowed_raw = payload.get("allowed_importers") if isinstance(payload, dict) else None
    symbols_raw = payload.get("required_symbols") if isinstance(payload, dict) else None
    forbidden_raw = payload.get("forbidden_provider_import_prefixes") if isinstance(payload, dict) else None

    allowed_importers = {
        str(item or "").strip()
        for item in (allowed_raw if isinstance(allowed_raw, list) else [])
        if str(item or "").strip()
    }
    required_symbols = tuple(
        str(item or "").strip()
        for item in (symbols_raw if isinstance(symbols_raw, list) else [])
        if str(item or "").strip()
    )
    forbidden_prefixes = tuple(
        str(item or "").strip()
        for item in (forbidden_raw if isinstance(forbidden_raw, list) else [])
        if str(item or "").strip()
    )
    if not allowed_importers:
        raise RuntimeError("scene provider policy missing allowed_importers")
    if not required_symbols:
        raise RuntimeError("scene provider policy missing required_symbols")
    if not forbidden_prefixes:
        raise RuntimeError("scene provider policy missing forbidden_provider_import_prefixes")
    return allowed_importers, required_symbols, forbidden_prefixes


def main() -> int:
    try:
        allowed_importers, required_symbols, forbidden_prefixes = _load_policy()
    except Exception as exc:
        print("[scene_provider_guard] FAIL")
        print(f"failed to load policy: {exc}")
        return 1

    if not PROVIDER.is_file():
        print("[scene_provider_guard] FAIL")
        print(f"missing file: {PROVIDER.as_posix()}")
        return 1

    text = PROVIDER.read_text(encoding="utf-8", errors="ignore")
    violations: list[str] = []

    for symbol in required_symbols:
        if f"def {symbol}(" not in text:
            violations.append(f"missing provider symbol: {symbol}")

    if _imports_forbidden_provider_module(text, forbidden_prefixes):
        violations.append("scene_provider must not import smart_construction_* business/demo/seed modules")

    for path in ADDONS_ROOT.rglob("*.py"):
        rel = path.relative_to(ROOT).as_posix()
        if rel == PROVIDER.relative_to(ROOT).as_posix():
            continue
        file_text = path.read_text(encoding="utf-8", errors="ignore")
        if _imports_scene_provider(file_text) and rel not in allowed_importers:
            violations.append(
                f"{rel}: scene_provider import is restricted to {sorted(allowed_importers)}"
            )

    if violations:
        print("[scene_provider_guard] FAIL")
        for item in violations:
            print(item)
        return 1

    print("[scene_provider_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
