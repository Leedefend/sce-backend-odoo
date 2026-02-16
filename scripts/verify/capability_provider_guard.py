#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import ast
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
BASELINE_JSON = ROOT / "scripts/verify/baselines/capability_provider_guard.json"
ADDONS_ROOT = ROOT / "addons"


def _imports_module(file_text: str, module_name: str) -> bool:
    try:
        tree = ast.parse(file_text)
    except SyntaxError:
        return False
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == module_name:
            return True
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == module_name:
                    return True
    return False


def _imports_forbidden_prefix(file_text: str, forbidden_prefixes: tuple[str, ...]) -> bool:
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


def _load_policy() -> tuple[Path, str, set[str], tuple[str, ...], tuple[str, ...]]:
    payload = json.loads(BASELINE_JSON.read_text(encoding="utf-8"))
    provider_file = ROOT / str(payload.get("provider_file") or "").strip()
    provider_module = str(payload.get("provider_module") or "").strip()
    allowed_importers = {
        str(item or "").strip()
        for item in (payload.get("allowed_importers") if isinstance(payload.get("allowed_importers"), list) else [])
        if str(item or "").strip()
    }
    required_symbols = tuple(
        str(item or "").strip()
        for item in (payload.get("required_symbols") if isinstance(payload.get("required_symbols"), list) else [])
        if str(item or "").strip()
    )
    forbidden_prefixes = tuple(
        str(item or "").strip()
        for item in (
            payload.get("forbidden_provider_import_prefixes")
            if isinstance(payload.get("forbidden_provider_import_prefixes"), list)
            else []
        )
        if str(item or "").strip()
    )
    if not provider_file.as_posix().strip() or not provider_module:
        raise RuntimeError("invalid provider policy: provider_file/provider_module required")
    if not allowed_importers:
        raise RuntimeError("invalid provider policy: allowed_importers required")
    if not required_symbols:
        raise RuntimeError("invalid provider policy: required_symbols required")
    return provider_file, provider_module, allowed_importers, required_symbols, forbidden_prefixes


def main() -> int:
    try:
        provider_file, provider_module, allowed_importers, required_symbols, forbidden_prefixes = _load_policy()
    except Exception as exc:
        print("[capability_provider_guard] FAIL")
        print(f"failed to load policy: {exc}")
        return 1

    violations: list[str] = []
    if not provider_file.is_file():
        violations.append(f"missing file: {provider_file.relative_to(ROOT).as_posix()}")
    else:
        provider_text = provider_file.read_text(encoding="utf-8", errors="ignore")
        for symbol in required_symbols:
            if f"def {symbol}(" not in provider_text:
                violations.append(f"missing provider symbol: {symbol}")
        if forbidden_prefixes and _imports_forbidden_prefix(provider_text, forbidden_prefixes):
            violations.append("capability_provider must not import smart_construction_* modules")

    provider_rel = provider_file.relative_to(ROOT).as_posix()
    for path in ADDONS_ROOT.rglob("*.py"):
        rel = path.relative_to(ROOT).as_posix()
        if rel == provider_rel:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        if _imports_module(text, provider_module) and rel not in allowed_importers:
            violations.append(f"{rel}: capability_provider import is restricted to {sorted(allowed_importers)}")

    if violations:
        print("[capability_provider_guard] FAIL")
        for item in violations:
            print(item)
        return 1

    print("[capability_provider_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
