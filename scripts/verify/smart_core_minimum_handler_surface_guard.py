#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import ast
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
HANDLERS_DIR = ROOT / "addons" / "smart_core" / "handlers"
SYSTEM_INIT_HANDLER = HANDLERS_DIR / "system_init.py"
CONSTRUCTION_EXTENSION = ROOT / "addons" / "smart_construction_core" / "core_extension.py"
OUT_JSON = ROOT / "artifacts" / "backend" / "smart_core_minimum_handler_surface_guard.json"
OUT_MD = ROOT / "docs" / "ops" / "audit" / "smart_core_minimum_handler_surface_guard.md"

APP_SHELL_OWNERSHIP_DOCS = [
    ROOT / "docs" / "audit" / "boundary" / "core_extension_platform_intent_owner_mapping.md",
    ROOT / "docs" / "audit" / "boundary" / "duplicate_orchestration_surface.md",
    ROOT / "docs" / "audit" / "boundary" / "duplicate_registry_surface.md",
    ROOT / "docs" / "audit" / "boundary" / "duplicate_source_conflict_table.md",
    ROOT / "docs" / "audit" / "boundary" / "handler_inventory.md",
    ROOT / "docs" / "audit" / "boundary" / "intent_semantic_classification.md",
    ROOT / "docs" / "audit" / "boundary" / "registry_ownership_audit.md",
    ROOT / "docs" / "ops" / "audit" / "intent_capability_matrix.md",
    ROOT / "docs" / "ops" / "audit" / "intent_layered_catalog.md",
    ROOT / "docs" / "ops" / "audit" / "intent_orphan_report.md",
    ROOT / "docs" / "ops" / "audit" / "intent_permission_matrix.md",
]

REQUIRED_INTENTS = {
    "login",
    "auth.logout",
    "system.init",
    "app.catalog",
    "app.nav",
    "app.open",
    "ui.contract",
    "meta.describe_model",
    "permission.check",
}

REQUIRED_ALIASES = {
    "auth.login",
    "app.init",
    "bootstrap",
}

FORBIDDEN_CONSTRUCTION_APP_SHELL_TOKENS = {
    "AppCatalogHandler",
    "AppNavHandler",
    "AppOpenHandler",
    '"app.catalog"',
    '"app.nav"',
    '"app.open"',
}

FORBIDDEN_APP_SHELL_DOC_PATTERNS = {
    "smart_construction_core.handlers.app_catalog",
    "smart_construction_core.handlers.app_nav",
    "smart_construction_core.handlers.app_open",
    "addons/smart_construction_core/handlers/app_catalog.py",
    "addons/smart_construction_core/handlers/app_nav.py",
    "addons/smart_construction_core/handlers/app_open.py",
    'registry["app.catalog"] = AppCatalogHandler',
    'registry["app.nav"] = AppNavHandler',
    'registry["app.open"] = AppOpenHandler',
}


def _literal_str(node: ast.AST | None) -> str:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return str(node.value).strip()
    return ""


def _literal_str_list(node: ast.AST | None) -> list[str]:
    if not isinstance(node, (ast.List, ast.Tuple)):
        return []
    values: list[str] = []
    for item in node.elts:
        text = _literal_str(item)
        if text:
            values.append(text)
    return values


def _extract_from_file(path: Path) -> dict[str, Any]:
    payload: dict[str, Any] = {"intents": set(), "aliases": set(), "errors": []}
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except Exception as exc:
        payload["errors"].append(f"parse_error:{path.name}:{exc}")
        return payload

    class_names: set[str] = set()
    for node in tree.body:
        if not isinstance(node, ast.ClassDef):
            continue
        class_names.add(node.name)
        for stmt in node.body:
            if not isinstance(stmt, ast.Assign) or len(stmt.targets) != 1:
                continue
            target = stmt.targets[0]
            if not isinstance(target, ast.Name):
                continue
            if target.id == "INTENT_TYPE":
                intent = _literal_str(stmt.value)
                if intent:
                    payload["intents"].add(intent)
            if target.id == "ALIASES":
                for alias in _literal_str_list(stmt.value):
                    payload["aliases"].add(alias)

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if not isinstance(node.func, ast.Attribute):
            continue
        if node.func.attr != "setdefault" or not node.args:
            continue
        alias = _literal_str(node.args[0])
        if alias:
            payload["aliases"].add(alias)

    return payload


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def main() -> int:
    intents: set[str] = set()
    aliases: set[str] = set()
    parse_errors: list[str] = []

    for file in sorted(HANDLERS_DIR.glob("*.py")):
        if file.name.startswith("__"):
            continue
        extracted = _extract_from_file(file)
        intents.update(extracted["intents"])
        aliases.update(extracted["aliases"])
        parse_errors.extend(extracted["errors"])

    missing_intents = sorted(REQUIRED_INTENTS - intents)
    missing_aliases = sorted(REQUIRED_ALIASES - aliases)
    boundary_errors: list[str] = []
    system_init_text = SYSTEM_INIT_HANDLER.read_text(encoding="utf-8", errors="ignore")
    if "if delivery_nav and not platform_minimum_surface_mode:" not in system_init_text:
        boundary_errors.append("system.init must not promote delivery nav over platform minimum surface nav")
    construction_extension_text = CONSTRUCTION_EXTENSION.read_text(encoding="utf-8", errors="ignore")
    for token in sorted(FORBIDDEN_CONSTRUCTION_APP_SHELL_TOKENS):
        if token in construction_extension_text:
            boundary_errors.append(
                f"construction core_extension must not contribute smart_core app shell token: {token}"
            )
    for doc_path in APP_SHELL_OWNERSHIP_DOCS:
        doc_text = doc_path.read_text(encoding="utf-8", errors="ignore")
        for pattern in sorted(FORBIDDEN_APP_SHELL_DOC_PATTERNS):
            if pattern in doc_text:
                boundary_errors.append(
                    f"{doc_path.relative_to(ROOT)} still documents construction app shell ownership: {pattern}"
                )

    report = {
        "status": "PASS" if not (missing_intents or missing_aliases or parse_errors or boundary_errors) else "FAIL",
        "required_intents": sorted(REQUIRED_INTENTS),
        "required_aliases": sorted(REQUIRED_ALIASES),
        "found_intents": sorted(intents),
        "found_aliases": sorted(aliases),
        "missing_intents": missing_intents,
        "missing_aliases": missing_aliases,
        "parse_errors": parse_errors,
        "boundary_errors": boundary_errors,
    }
    _write(OUT_JSON, json.dumps(report, ensure_ascii=False, indent=2) + "\n")

    lines = [
        "# Smart Core Minimum Handler Surface Guard",
        "",
        f"- status: {report['status']}",
        f"- missing_intents: {', '.join(missing_intents) if missing_intents else '(none)'}",
        f"- missing_aliases: {', '.join(missing_aliases) if missing_aliases else '(none)'}",
        f"- parse_errors: {', '.join(parse_errors) if parse_errors else '(none)'}",
        f"- boundary_errors: {', '.join(boundary_errors) if boundary_errors else '(none)'}",
        "",
        "## Required Intents",
        *[f"- {item}" for item in report["required_intents"]],
        "",
        "## Required Aliases",
        *[f"- {item}" for item in report["required_aliases"]],
    ]
    _write(OUT_MD, "\n".join(lines) + "\n")

    if report["status"] != "PASS":
        print("[smart_core_minimum_handler_surface_guard] FAIL")
        return 1
    print("[smart_core_minimum_handler_surface_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
