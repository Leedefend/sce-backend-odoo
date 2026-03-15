#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BOUNDARY_DOC = ROOT / "docs" / "architecture" / "native_contract_driven_scene_orchestrator_boundary_and_industry_composition_v1.md"
IO_DOC = ROOT / "docs" / "architecture" / "scene_orchestrator_io_contract_and_industry_interface_spec_v1.md"


def _assert(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def main() -> int:
    errors: list[str] = []
    for path in (BOUNDARY_DOC, IO_DOC):
        if not path.is_file():
            errors.append(f"missing file: {path}")
    if errors:
        print("[scene_orchestrator_industry_interface_guard] FAIL")
        for item in errors:
            print(f" - {item}")
        return 1

    boundary_text = BOUNDARY_DOC.read_text(encoding="utf-8")
    io_text = IO_DOC.read_text(encoding="utf-8")

    for token in (
        "Profile + Policy + Provider",
        "原生契约",
        "Scene-ready Contract",
        "行业层禁止",
    ):
        _assert(token in boundary_text, f"boundary doc missing token: {token}", errors)

    for token in (
        "输入契约（Input Contract）",
        "输出契约（Output Contract）",
        "Scene Profile Schema",
        "Policy Schema",
        "Provider Interface",
        "Merge 优先级规则",
    ):
        _assert(token in io_text, f"io spec missing token: {token}", errors)

    if errors:
        print("[scene_orchestrator_industry_interface_guard] FAIL")
        for item in errors:
            print(f" - {item}")
        return 1

    print("[scene_orchestrator_industry_interface_guard] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

