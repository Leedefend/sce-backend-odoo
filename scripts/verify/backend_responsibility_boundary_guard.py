#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Guard backend responsibility boundaries for contract delivery.

This is a lightweight source guard. It keeps the recently frozen responsibility
rules executable without trying to replace full architecture review.
"""

from __future__ import annotations

from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "docs" / "architecture" / "backend_contract_layer_responsibility_freeze_v1.md"
CONTRACT_GOVERNANCE = ROOT / "addons" / "smart_core" / "utils" / "contract_governance.py"
HANDLER_DIR = ROOT / "addons" / "smart_core" / "handlers"
FRONTEND_GENERIC_CONSUMERS = [
    ROOT / "frontend" / "apps" / "web" / "src" / "app" / "action_runtime" / "useActionViewActionPresentationRuntime.ts",
    ROOT / "frontend" / "apps" / "web" / "src" / "app" / "action_runtime" / "useActionViewContractShapeRuntime.ts",
    ROOT / "frontend" / "apps" / "web" / "src" / "app" / "runtime" / "detailLayoutRuntime.ts",
]


REQUIRED_DOC_TOKENS = [
    "Business Fact Layer",
    "Native Structure Fact Layer",
    "Contract Assembly Layer",
    "Contract Governance Layer",
    "Handler Delivery Envelope",
    "Frontend Consumer",
    "Responsibility Matrix",
    "Implementation Routing Rule",
    "Contract Governance Special Rule",
    "scene_contract_v1",
    "owner_layer=scene_orchestration",
    "frontend did not add model-specific semantic repair",
]

REQUIRED_GOVERNANCE_TOKENS = [
    "def _ensure_scene_contract_v1_envelope",
    '"contract_version"] = "v1"',
    '"owner_layer", "scene_orchestration"',
    '"scene_contract_supply_owner_layer", "scene_orchestration"',
]

FORBIDDEN_HANDLER_PATTERNS = [
    re.compile(r"def\s+_ensure_project_form_layout_structure\s*\("),
    re.compile(r"form\[\s*[\"']layout[\"']\s*\]\s*="),
    re.compile(r"views\[\s*[\"']form[\"']\s*\]\s*="),
    re.compile(r"data\[\s*[\"']views[\"']\s*\]\s*="),
    re.compile(r"[\"']project_form_sheet[\"']"),
    re.compile(r"[\"']core_group[\"']"),
    re.compile(r"[\"']advanced_group[\"']"),
]

FORBIDDEN_FRONTEND_GENERIC_PATTERNS = [
    re.compile(r"project\.project"),
    re.compile(r"legacy_project_"),
    re.compile(r"owner_layer\s*=\s*[\"']scene_orchestration[\"']"),
]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def _require_tokens(path: Path, tokens: list[str], errors: list[str]) -> None:
    if not path.is_file():
        errors.append(f"missing file: {path.relative_to(ROOT)}")
        return
    text = _read(path)
    for token in tokens:
        if token not in text:
            errors.append(f"{path.relative_to(ROOT)} missing token: {token}")


def _guard_handlers(errors: list[str]) -> None:
    if not HANDLER_DIR.is_dir():
        errors.append(f"missing handler dir: {HANDLER_DIR.relative_to(ROOT)}")
        return
    for path in sorted(HANDLER_DIR.glob("*.py")):
        text = _read(path)
        rel = path.relative_to(ROOT).as_posix()
        for pattern in FORBIDDEN_HANDLER_PATTERNS:
            if pattern.search(text):
                errors.append(f"{rel}: handler must not own layout restructuring pattern `{pattern.pattern}`")


def _guard_frontend_generic_consumers(errors: list[str]) -> None:
    for path in FRONTEND_GENERIC_CONSUMERS:
        if not path.is_file():
            errors.append(f"missing frontend consumer: {path.relative_to(ROOT)}")
            continue
        text = _read(path)
        rel = path.relative_to(ROOT).as_posix()
        for pattern in FORBIDDEN_FRONTEND_GENERIC_PATTERNS:
            if pattern.search(text):
                errors.append(f"{rel}: generic frontend consumer must not contain `{pattern.pattern}`")


def main() -> int:
    errors: list[str] = []
    _require_tokens(DOC, REQUIRED_DOC_TOKENS, errors)
    _require_tokens(CONTRACT_GOVERNANCE, REQUIRED_GOVERNANCE_TOKENS, errors)
    _guard_handlers(errors)
    _guard_frontend_generic_consumers(errors)

    if errors:
        print("[backend_responsibility_boundary_guard] FAIL")
        for error in errors:
            print(error)
        return 1

    print("[backend_responsibility_boundary_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
