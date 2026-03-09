#!/usr/bin/env python3
from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys
from types import ModuleType
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
BUILDER = ROOT / "addons/smart_core/core/page_contracts_builder.py"
ALLOWED_TAGS = {"header", "section", "details", "div"}
SECTIONS_OPTIONAL_PAGES = {"home"}


def _fail(errors: list[str]) -> int:
    print("[page_contract_sections_schema_guard] FAIL")
    for err in errors:
        print(f"- {err}")
    return 1


def _load_builder_module(path: Path) -> ModuleType:
    spec = spec_from_file_location("page_contracts_builder_guard", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load module spec: {path}")
    mod = module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _validate_page_sections(page_key: str, sections: Any, errors: list[str]) -> None:
    if not isinstance(sections, list) or not sections:
        errors.append(f"pages.{page_key}.sections must be non-empty list")
        return

    seen_keys: set[str] = set()
    seen_orders: set[int] = set()
    prev_order = 0

    for idx, section in enumerate(sections):
        prefix = f"pages.{page_key}.sections[{idx}]"
        if not isinstance(section, dict):
            errors.append(f"{prefix} must be object")
            continue

        key = section.get("key")
        if not isinstance(key, str) or not key.strip():
            errors.append(f"{prefix}.key must be non-empty string")
        elif key in seen_keys:
            errors.append(f"{prefix}.key duplicate: {key}")
        else:
            seen_keys.add(key)

        enabled = section.get("enabled")
        if not isinstance(enabled, bool):
            errors.append(f"{prefix}.enabled must be bool")

        order = section.get("order")
        if not isinstance(order, int) or order <= 0:
            errors.append(f"{prefix}.order must be positive int")
        else:
            if order in seen_orders:
                errors.append(f"{prefix}.order duplicate: {order}")
            seen_orders.add(order)
            if order <= prev_order:
                errors.append(f"{prefix}.order must be strictly increasing (prev={prev_order}, cur={order})")
            prev_order = order

        tag = section.get("tag")
        if not isinstance(tag, str) or tag not in ALLOWED_TAGS:
            errors.append(f"{prefix}.tag must be one of {sorted(ALLOWED_TAGS)}")
        elif tag == "details":
            if "open" not in section:
                errors.append(f"{prefix}.open is required when tag=details")
            elif not isinstance(section.get("open"), bool):
                errors.append(f"{prefix}.open must be bool when tag=details")
        elif "open" in section and not isinstance(section.get("open"), bool):
            errors.append(f"{prefix}.open must be bool when present")

    if seen_orders and seen_orders != set(range(1, len(sections) + 1)):
        errors.append(
            f"pages.{page_key}.sections.order must be contiguous from 1..{len(sections)} "
            f"(got={sorted(seen_orders)})"
        )


def main() -> int:
    if not BUILDER.is_file():
        return _fail([f"missing file: {BUILDER}"])

    try:
        builder_mod = _load_builder_module(BUILDER)
    except Exception as exc:  # pragma: no cover
        return _fail([f"load builder failed: {exc}"])

    if not hasattr(builder_mod, "build_page_contracts"):
        return _fail(["build_page_contracts not found in builder module"])

    data = builder_mod.build_page_contracts({})
    pages = data.get("pages") if isinstance(data, dict) else None
    if not isinstance(pages, dict) or not pages:
        return _fail(["page contracts payload missing pages object"])

    errors: list[str] = []
    checked = 0
    for page_key, page_obj in pages.items():
        if not isinstance(page_obj, dict):
            errors.append(f"pages.{page_key} must be object")
            continue
        if str(page_key) in SECTIONS_OPTIONAL_PAGES and "sections" not in page_obj:
            continue
        checked += 1
        _validate_page_sections(str(page_key), page_obj.get("sections"), errors)

    if checked == 0:
        errors.append("no page sections found to validate")

    if errors:
        return _fail(errors)

    print(f"[page_contract_sections_schema_guard] PASS (checked_pages={checked})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
