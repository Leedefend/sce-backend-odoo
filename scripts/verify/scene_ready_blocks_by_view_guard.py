#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BUILDER_PATH = ROOT / "addons" / "smart_core" / "core" / "scene_ready_contract_builder.py"
SYSTEM_INIT_MIN_PATH = ROOT / "addons" / "smart_core" / "core" / "system_init_payload_builder.py"
WEB_RESOLVER_PATH = ROOT / "frontend" / "apps" / "web" / "src" / "app" / "resolvers" / "sceneReadyResolver.ts"


def _assert(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore") if path.is_file() else ""


def main() -> int:
    errors: list[str] = []
    builder_text = _read(BUILDER_PATH)
    system_init_text = _read(SYSTEM_INIT_MIN_PATH)
    web_resolver_text = _read(WEB_RESOLVER_PATH)

    _assert(builder_text != "", f"missing file: {BUILDER_PATH}", errors)
    _assert(system_init_text != "", f"missing file: {SYSTEM_INIT_MIN_PATH}", errors)
    _assert(web_resolver_text != "", f"missing file: {WEB_RESOLVER_PATH}", errors)
    if errors:
        print("[scene_ready_blocks_by_view_guard] FAIL")
        for item in errors:
            print(f" - {item}")
        return 1

    for token in (
        'for mode in ("form", "list", "kanban")',
        'compiled["scene_blocks_by_view"] = scene_blocks_by_view',
        "_build_scene_blocks(compiled, scene_type_override=mode)",
        "_enforce_native_view_block_structure(",
    ):
        _assert(token in builder_text, f"scene_ready builder missing token: {token}", errors)

    _assert('"scene_blocks_by_view"' in system_init_text, "system_init minimal payload missing scene_blocks_by_view retention", errors)

    for token in (
        "const blocksByView = asDict(row.scene_blocks_by_view);",
        "const directViewBlocks = Array.isArray(viewBlocks) ? viewBlocks : [];",
        "resolveSceneReadyBlocks(entry, 'form')",
        "resolveSceneReadyBlocks(entry, 'list')",
        "resolveSceneReadyBlocks(entry, mode)",
    ):
        _assert(token in web_resolver_text, f"web resolver missing direct scene_blocks_by_view consumption token: {token}", errors)

    _assert("synthesizeFormSceneBlocks" not in web_resolver_text, "web resolver still contains local form scene block synthesis", errors)

    if errors:
        print("[scene_ready_blocks_by_view_guard] FAIL")
        for item in errors:
            print(f" - {item}")
        return 1

    print("[scene_ready_blocks_by_view_guard] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
