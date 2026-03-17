#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
COMPILER_PATH = ROOT / "addons" / "smart_core" / "core" / "scene_dsl_compiler.py"


def _assert(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def main() -> int:
    errors: list[str] = []
    if not COMPILER_PATH.is_file():
        errors.append(f"missing file: {COMPILER_PATH}")
    if errors:
        print("[scene_orchestrator_input_schema_guard] FAIL")
        for item in errors:
            print(f" - {item}")
        return 1

    text = COMPILER_PATH.read_text(encoding="utf-8")
    for symbol in (
        "class CompileContext",
        "scene_key: str",
        "ui_base_contract: Dict[str, Any]",
        "provider_registry: Dict[str, Any]",
        "parse_scene_dsl",
        "grammar_validate",
        "semantic_validate",
        "context_bind",
        "generate_surfaces",
    ):
        _assert(symbol in text, f"missing input-schema symbol: {symbol}", errors)

    for fact_key in (
        'ctx.ui_base_contract.get("search")',
        'ctx.ui_base_contract.get("permissions")',
        'ctx.ui_base_contract.get("workflow")',
    ):
        _assert(fact_key in text, f"missing base fact consume key: {fact_key}", errors)

    if errors:
        print("[scene_orchestrator_input_schema_guard] FAIL")
        for item in errors:
            print(f" - {item}")
        return 1

    print("[scene_orchestrator_input_schema_guard] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

