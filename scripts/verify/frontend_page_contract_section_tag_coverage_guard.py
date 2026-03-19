#!/usr/bin/env python3
from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys
from types import ModuleType
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
VIEWS_DIR = ROOT / "frontend/apps/web/src/views"
PAGE_CONTRACTS_BUILDER = ROOT / "addons/smart_core/core/page_contracts_builder.py"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore") if path.is_file() else ""


def _load_builder_module(path: Path) -> ModuleType:
    spec = spec_from_file_location("page_contracts_builder_tag_guard", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load module spec: {path}")
    mod = module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _find_page_consumers() -> dict[str, list[Path]]:
    consumers: dict[str, list[Path]] = {}
    marker = "usePageContract('"
    for view in sorted(VIEWS_DIR.glob("*.vue")):
        text = _read(view)
        if not text:
            continue
        start = 0
        while True:
            idx = text.find(marker, start)
            if idx < 0:
                break
            key_start = idx + len(marker)
            key_end = text.find("'", key_start)
            if key_end > key_start:
                page_key = text[key_start:key_end].strip()
                if page_key:
                    consumers.setdefault(page_key, []).append(view)
            start = key_start
    return consumers


def _fail(errors: list[str]) -> int:
    print("[frontend_page_contract_section_tag_coverage_guard] FAIL")
    for err in errors:
        print(f"- {err}")
    return 1


def main() -> int:
    if not PAGE_CONTRACTS_BUILDER.is_file():
        return _fail([f"missing file: {PAGE_CONTRACTS_BUILDER.relative_to(ROOT).as_posix()}"])

    try:
        builder_mod = _load_builder_module(PAGE_CONTRACTS_BUILDER)
    except Exception as exc:  # pragma: no cover
        return _fail([f"load builder failed: {exc}"])

    if not hasattr(builder_mod, "build_page_contracts"):
        return _fail(["build_page_contracts not found in page_contracts_builder.py"])

    payload = builder_mod.build_page_contracts({})
    pages = payload.get("pages") if isinstance(payload, dict) else None
    if not isinstance(pages, dict) or not pages:
        return _fail(["page contracts payload missing pages object"])

    consumers = _find_page_consumers()
    errors: list[str] = []
    checked_pages = 0
    checked_sections = 0
    for page_key, page_obj in sorted(pages.items()):
        if not isinstance(page_obj, dict):
            continue
        sections = page_obj.get("sections")
        if not isinstance(sections, list) or not sections:
            continue
        page_key = str(page_key)
        consumer_files = consumers.get(page_key) or []
        if not consumer_files:
            errors.append(f"page '{page_key}' has sections but no frontend usePageContract consumer")
            continue
        checked_pages += 1

        consumer_texts = {f: _read(f) for f in consumer_files}
        for sec in sections:
            if not isinstance(sec, dict):
                continue
            key = sec.get("key")
            tag = sec.get("tag")
            if not isinstance(key, str) or not key.strip() or not isinstance(tag, str) or not tag.strip():
                continue
            checked_sections += 1
            token = f"pageSectionTagIs('{key}', '{tag}')"
            alt_token = f"isSectionVisible('{key}',"
            if page_key == "action":
                matched = any((token in txt) or (alt_token in txt) for txt in consumer_texts.values())
            else:
                matched = any(token in txt for txt in consumer_texts.values())
            if not matched:
                labels = ", ".join(f.relative_to(ROOT).as_posix() for f in consumer_files)
                errors.append(f"page '{page_key}' section '{key}' tag '{tag}' missing token {token} in: {labels}")

    if errors:
        return _fail(errors)

    print(
        "[frontend_page_contract_section_tag_coverage_guard] PASS "
        f"(checked_pages={checked_pages}, checked_sections={checked_sections})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
