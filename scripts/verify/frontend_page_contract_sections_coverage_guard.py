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
    spec = spec_from_file_location("page_contracts_builder_coverage_guard", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load module spec: {path}")
    mod = module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _fail(errors: list[str]) -> int:
    print("[frontend_page_contract_sections_coverage_guard] FAIL")
    for err in errors:
        print(f"- {err}")
    return 1


def _find_page_consumers() -> dict[str, list[Path]]:
    consumers: dict[str, list[Path]] = {}
    for view in sorted(VIEWS_DIR.glob("*.vue")):
        text = _read(view)
        if not text:
            continue
        # Keep parsing simple and deterministic: explicit single-quoted usage.
        marker = "usePageContract('"
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


def main() -> int:
    errors: list[str] = []
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
        return _fail(["page contracts missing pages object"])

    page_sections: dict[str, list[dict[str, Any]]] = {}
    for page_key, page_obj in pages.items():
        if not isinstance(page_obj, dict):
            continue
        sections = page_obj.get("sections")
        if isinstance(sections, list) and sections:
            normalized: list[dict[str, Any]] = []
            for sec in sections:
                if isinstance(sec, dict):
                    normalized.append(sec)
            if normalized:
                page_sections[str(page_key)] = normalized

    if not page_sections:
        return _fail(["no sections pages found in page_contracts_builder"])

    consumers = _find_page_consumers()

    checked_pages = 0
    checked_sections = 0
    for page_key, sections in sorted(page_sections.items()):
        consumer_files = consumers.get(page_key) or []
        if not consumer_files:
            errors.append(f"page '{page_key}' has sections but no frontend usePageContract consumer")
            continue
        checked_pages += 1

        consumer_texts = {f: _read(f) for f in consumer_files}
        for sec in sections:
            key = sec.get("key")
            if not isinstance(key, str) or not key.strip():
                continue
            checked_sections += 1
            enabled_token = f"pageSectionEnabled('{key}'"
            if not any(enabled_token in txt for txt in consumer_texts.values()):
                labels = ", ".join(f.relative_to(ROOT).as_posix() for f in consumer_files)
                errors.append(f"page '{page_key}' section '{key}' not consumed via {enabled_token} in: {labels}")

            tag = sec.get("tag")
            if tag == "details":
                open_token = f"pageSectionOpenDefault('{key}'"
                if not any(open_token in txt for txt in consumer_texts.values()):
                    labels = ", ".join(f.relative_to(ROOT).as_posix() for f in consumer_files)
                    errors.append(
                        f"page '{page_key}' details section '{key}' missing open-default consumption {open_token} in: {labels}"
                    )

    if errors:
        return _fail(errors)

    print(
        "[frontend_page_contract_sections_coverage_guard] PASS "
        f"(checked_pages={checked_pages}, checked_sections={checked_sections})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
