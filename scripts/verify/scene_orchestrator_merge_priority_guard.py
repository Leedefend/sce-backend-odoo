#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
IO_SPEC = ROOT / "docs" / "architecture" / "scene_orchestrator_io_contract_and_industry_interface_spec_v1.md"
COMPILER = ROOT / "addons" / "smart_core" / "core" / "scene_dsl_compiler.py"


def _assert(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def main() -> int:
    errors: list[str] = []
    for path in (IO_SPEC, COMPILER):
        if not path.is_file():
            errors.append(f"missing file: {path}")
    if errors:
        print("[scene_orchestrator_merge_priority_guard] FAIL")
        for item in errors:
            print(f" - {item}")
        return 1

    io_text = IO_SPEC.read_text(encoding="utf-8")
    compiler_text = COMPILER.read_text(encoding="utf-8")

    priority_tokens = (
        "平台默认规则（Platform Default）",
        "原生能力事实（Base Fact）",
        "行业 Profile",
        "行业 Policy",
        "Provider 运行时增强",
        "权限与治理裁决（最终裁决层）",
    )
    for token in priority_tokens:
        _assert(token in io_text, f"io spec missing priority token: {token}", errors)

    order_tokens = (
        "Profile Apply",
        "Policy Apply",
        "Provider Merge",
        "Permission/Workflow Gate",
    )
    for token in order_tokens:
        _assert(token in io_text, f"io spec missing execution order token: {token}", errors)

    _assert("compile_pipeline" in compiler_text, "compiler missing compile_pipeline trace", errors)
    _assert("compile_verdict" in compiler_text, "compiler missing compile_verdict", errors)
    _assert("semantic_validate" in compiler_text, "compiler missing semantic validation stage", errors)

    if errors:
        print("[scene_orchestrator_merge_priority_guard] FAIL")
        for item in errors:
            print(f" - {item}")
        return 1

    print("[scene_orchestrator_merge_priority_guard] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

