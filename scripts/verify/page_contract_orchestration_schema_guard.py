#!/usr/bin/env python3
from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys
from types import ModuleType
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
BUILDER = ROOT / "addons/smart_core/core/page_contracts_builder.py"

REQUIRED_TOP_LEVEL = {
    "contract_version",
    "scene_key",
    "page",
    "zones",
    "data_sources",
    "state_schema",
    "action_schema",
    "render_hints",
    "meta",
}
ALLOWED_BLOCK_TYPES = {
    "hero_metric",
    "kpi_row",
    "todo_list",
    "alert_panel",
    "progress_group",
    "quick_entry_grid",
    "fold_section",
    "record_summary",
    "activity_feed",
}
ALLOWED_TONES = {"success", "warning", "danger", "info", "neutral"}
ALLOWED_PROGRESS = {"overdue", "blocked", "pending", "running", "completed"}


def _fail(errors: list[str]) -> int:
    print("[page_contract_orchestration_schema_guard] FAIL")
    for err in errors:
        print(f"- {err}")
    return 1


def _load_builder_module(path: Path) -> ModuleType:
    spec = spec_from_file_location("page_contracts_builder_orchestration_guard", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load module spec: {path}")
    mod = module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _validate_page(page_key: str, page_obj: dict[str, Any], errors: list[str]) -> None:
    sections = page_obj.get("sections") if isinstance(page_obj.get("sections"), list) else []
    if not sections:
        return

    orch = page_obj.get("page_orchestration_v1")
    if not isinstance(orch, dict):
        errors.append(f"pages.{page_key}.page_orchestration_v1 must be object")
        return

    missing_top = sorted(REQUIRED_TOP_LEVEL - set(orch.keys()))
    if missing_top:
        errors.append(f"pages.{page_key}.page_orchestration_v1 missing keys: {', '.join(missing_top)}")

    if str(orch.get("contract_version") or "") != "page_orchestration_v1":
        errors.append(f"pages.{page_key}.page_orchestration_v1.contract_version must be page_orchestration_v1")
    page = orch.get("page")
    if not isinstance(page, dict):
        errors.append(f"pages.{page_key}.page_orchestration_v1.page must be object")
    elif not isinstance(page.get("audience"), list) or not page.get("audience"):
        errors.append(f"pages.{page_key}.page_orchestration_v1.page.audience must be non-empty list")

    state_schema = orch.get("state_schema")
    if not isinstance(state_schema, dict):
        errors.append(f"pages.{page_key}.page_orchestration_v1.state_schema must be object")
    else:
        tones = state_schema.get("tones")
        progress = state_schema.get("business_states")
        tone_keys = set(tones.keys()) if isinstance(tones, dict) else set()
        progress_keys = set(progress.keys()) if isinstance(progress, dict) else set()
        if tone_keys != ALLOWED_TONES:
            errors.append(f"pages.{page_key}.state_schema.tones mismatch expected={sorted(ALLOWED_TONES)} got={sorted(tone_keys)}")
        if progress_keys != ALLOWED_PROGRESS:
            errors.append(
                f"pages.{page_key}.state_schema.business_states mismatch expected={sorted(ALLOWED_PROGRESS)} got={sorted(progress_keys)}"
            )

    zones = orch.get("zones")
    if not isinstance(zones, list) or not zones:
        errors.append(f"pages.{page_key}.page_orchestration_v1.zones must be non-empty list")
        return

    section_keys: set[str] = set()
    for section in sections:
        if not isinstance(section, dict):
            continue
        key = str(section.get("key") or "").strip()
        if key:
            section_keys.add(key)

    block_section_keys: set[str] = set()
    for zidx, zone in enumerate(zones):
        prefix = f"pages.{page_key}.page_orchestration_v1.zones[{zidx}]"
        if not isinstance(zone, dict):
            errors.append(f"{prefix} must be object")
            continue
        if not isinstance(zone.get("blocks"), list):
            errors.append(f"{prefix}.blocks must be list")
            continue
        for bidx, block in enumerate(zone.get("blocks") or []):
            bprefix = f"{prefix}.blocks[{bidx}]"
            if not isinstance(block, dict):
                errors.append(f"{bprefix} must be object")
                continue
            block_type = str(block.get("block_type") or "").strip()
            tone = str(block.get("tone") or "").strip()
            progress = str(block.get("progress") or "").strip()
            section_key = str(block.get("section_key") or "").strip()
            if block_type not in ALLOWED_BLOCK_TYPES:
                errors.append(f"{bprefix}.block_type invalid: {block_type}")
            if tone not in ALLOWED_TONES:
                errors.append(f"{bprefix}.tone invalid: {tone}")
            if progress not in ALLOWED_PROGRESS:
                errors.append(f"{bprefix}.progress invalid: {progress}")
            if not section_key:
                errors.append(f"{bprefix}.section_key must be non-empty")
                continue
            block_section_keys.add(section_key)

    if section_keys != block_section_keys:
        missing_in_blocks = sorted(section_keys - block_section_keys)
        extra_in_blocks = sorted(block_section_keys - section_keys)
        if missing_in_blocks:
            errors.append(f"pages.{page_key}: sections missing in orchestration blocks: {', '.join(missing_in_blocks)}")
        if extra_in_blocks:
            errors.append(f"pages.{page_key}: orchestration blocks contain unknown sections: {', '.join(extra_in_blocks)}")


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
        if "sections" not in page_obj:
            continue
        checked += 1
        _validate_page(str(page_key), page_obj, errors)

    if checked == 0:
        errors.append("no page sections found to validate")

    if errors:
        return _fail(errors)

    print(f"[page_contract_orchestration_schema_guard] PASS (checked_pages={checked})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
