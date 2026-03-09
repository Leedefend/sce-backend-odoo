#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
REGISTRY = ROOT / "frontend/apps/web/src/app/pageBlockRegistry.ts"
BLOCK_RENDERER = ROOT / "frontend/apps/web/src/components/page/BlockRenderer.vue"
HOME_BUILDER = ROOT / "addons/smart_core/core/workspace_home_contract_builder.py"
PAGE_BUILDER = ROOT / "addons/smart_core/core/page_contracts_builder.py"

REQUIRED_BLOCK_TYPES = {
    "metric_row",
    "todo_list",
    "alert_panel",
    "entry_grid",
    "record_summary",
    "progress_summary",
    "activity_feed",
    "accordion_group",
}


def _fail(errors: list[str]) -> int:
    print("[frontend_page_block_registry_guard] FAIL")
    for err in errors:
        print(f"- {err}")
    return 1


def _extract_block_types(text: str) -> set[str]:
    return {m.group(1) for m in re.finditer(r'"block_type"\s*:\s*"([a-zA-Z0-9_]+)"', text)}

def _extract_registry_keys(text: str) -> set[str]:
    quoted = {m.group(1) for m in re.finditer(r"(?:'|\")([a-zA-Z0-9_]+)(?:'|\")\s*:", text)}
    bare = {m.group(1) for m in re.finditer(r"\b([a-zA-Z_][a-zA-Z0-9_]*)\b\s*:", text)}
    return quoted | bare


def main() -> int:
    errors: list[str] = []
    if not REGISTRY.is_file():
        errors.append(f"missing file: {REGISTRY.relative_to(ROOT).as_posix()}")
    if not BLOCK_RENDERER.is_file():
        errors.append(f"missing file: {BLOCK_RENDERER.relative_to(ROOT).as_posix()}")
    if errors:
        return _fail(errors)

    registry_text = REGISTRY.read_text(encoding="utf-8", errors="ignore")
    renderer_text = BLOCK_RENDERER.read_text(encoding="utf-8", errors="ignore")
    home_text = HOME_BUILDER.read_text(encoding="utf-8", errors="ignore") if HOME_BUILDER.is_file() else ""
    page_text = PAGE_BUILDER.read_text(encoding="utf-8", errors="ignore") if PAGE_BUILDER.is_file() else ""

    registry_keys = _extract_registry_keys(registry_text)
    for block_type in sorted(REQUIRED_BLOCK_TYPES):
        if block_type not in registry_keys:
            errors.append(f"registry missing required block type: {block_type}")

    backend_types = _extract_block_types(home_text) | _extract_block_types(page_text)
    if backend_types:
        missing = sorted(bt for bt in backend_types if bt not in registry_keys)
        if missing and "未支持的区块类型" not in renderer_text:
            errors.append("block renderer must provide fallback UI for unregistered backend block types")

    if "resolveBlockComponent" not in renderer_text:
        errors.append("BlockRenderer must consume resolveBlockComponent")

    if errors:
        return _fail(errors)

    print("[frontend_page_block_registry_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
