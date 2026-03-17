#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BUILDER_PATH = ROOT / "addons" / "smart_core" / "core" / "scene_ready_contract_builder.py"


def _assert(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def main() -> int:
    errors: list[str] = []
    if not BUILDER_PATH.is_file():
        errors.append(f"missing file: {BUILDER_PATH}")
    if errors:
        print("[scene_ready_scene_type_consumption_metrics_guard] FAIL")
        for item in errors:
            print(f" - {item}")
        return 1

    builder_text = BUILDER_PATH.read_text(encoding="utf-8")
    for token in (
        "_scene_type_consumption_metrics",
        '"scene_type_consumption_metrics": _scene_type_consumption_metrics(entries)',
        '"base_fact_consumption_rate"',
        '"surface_nonempty_rate"',
    ):
        _assert(token in builder_text, f"scene_ready builder missing metrics token: {token}", errors)

    for token in (
        '"base_fact_hits"',
        '"base_fact_consumption_rate"',
        '"surface_nonempty_hits"',
        '"surface_nonempty_rate"',
        '"scene_count"',
        '"search"',
        '"workflow"',
        '"validation"',
        '"action_surface"',
    ):
        _assert(token in builder_text, f"scene_ready metrics definition missing token: {token}", errors)

    if errors:
        print("[scene_ready_scene_type_consumption_metrics_guard] FAIL")
        for item in errors:
            print(f" - {item}")
        return 1

    print("[scene_ready_scene_type_consumption_metrics_guard] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
