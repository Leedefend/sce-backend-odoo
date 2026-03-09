#!/usr/bin/env python3
from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import re
import sys
from types import ModuleType
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
VIEWS_DIR = ROOT / "frontend/apps/web/src/views"
PAGE_CONTRACTS_BUILDER = ROOT / "addons/smart_core/core/page_contracts_builder.py"

USE_PAGE_CONTRACT_RE = re.compile(r"usePageContract\('([^']+)'\)")
PAGE_TEXT_RE = re.compile(r"pageText\('([^']+)'")
ACTION_TEXT_RE = re.compile(r"actionText\('([^']+)'")


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore") if path.is_file() else ""


def _load_builder_module(path: Path) -> ModuleType:
    spec = spec_from_file_location("page_contracts_builder_text_guard", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load module spec: {path}")
    mod = module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _fail(errors: list[str]) -> int:
    print("[page_contract_text_key_coverage_guard] FAIL")
    for err in errors:
        print(f"- {err}")
    return 1


def _as_key_set(value: Any) -> set[str]:
    if not isinstance(value, dict):
        return set()
    return {str(k).strip() for k in value.keys() if str(k).strip()}


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

    errors: list[str] = []
    checked_pages = 0
    checked_text_keys = 0
    checked_action_keys = 0

    for view in sorted(VIEWS_DIR.glob("*.vue")):
        text = _read(view)
        if not text:
            continue
        match = USE_PAGE_CONTRACT_RE.search(text)
        if not match:
            continue
        page_key = match.group(1).strip()
        if not page_key:
            continue
        page = pages.get(page_key)
        if not isinstance(page, dict):
            errors.append(f"{view.relative_to(ROOT).as_posix()} uses unknown page contract key: {page_key}")
            continue

        text_keys_available = _as_key_set(page.get("texts"))
        action_keys_available = _as_key_set(page.get("actions"))

        used_text_keys = {m.group(1).strip() for m in PAGE_TEXT_RE.finditer(text) if m.group(1).strip()}
        used_action_keys = {m.group(1).strip() for m in ACTION_TEXT_RE.finditer(text) if m.group(1).strip()}
        if not used_text_keys and not used_action_keys:
            continue

        checked_pages += 1
        for key in sorted(used_text_keys):
            checked_text_keys += 1
            if key not in text_keys_available:
                errors.append(
                    f"{view.relative_to(ROOT).as_posix()} uses pageText('{key}') but page_contracts.{page_key}.texts missing key"
                )
        for key in sorted(used_action_keys):
            checked_action_keys += 1
            if key not in action_keys_available:
                errors.append(
                    f"{view.relative_to(ROOT).as_posix()} uses actionText('{key}') but page_contracts.{page_key}.actions missing key"
                )

    if errors:
        return _fail(errors)

    print(
        "[page_contract_text_key_coverage_guard] PASS "
        f"(checked_pages={checked_pages}, text_keys={checked_text_keys}, action_keys={checked_action_keys})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
