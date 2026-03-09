#!/usr/bin/env python3
from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import re
import sys
from types import ModuleType
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
BUILDER = ROOT / "addons/smart_core/core/page_contracts_builder.py"
ALLOWED_SOURCE_TYPES = {"static", "scene_context", "api.data", "computed", "capability_registry", "role_profile", "mixed"}


def _fail(errors: list[str]) -> int:
    print("[page_contract_data_source_semantics_guard] FAIL")
    for err in errors:
        print(f"- {err}")
    return 1


def _load_builder(path: Path) -> ModuleType:
    spec = spec_from_file_location("page_contract_data_source_semantics_guard", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load module spec: {path}")
    mod = module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _expected_ds_key(section_key: str) -> str:
    token = re.sub(r"[^a-z0-9_]+", "_", str(section_key or "").strip().lower())
    token = re.sub(r"_+", "_", token).strip("_")
    if not token:
        token = "section"
    return f"ds_section_{token}"


def _validate_page(page_key: str, page_obj: dict[str, Any], errors: list[str]) -> None:
    orch = page_obj.get("page_orchestration_v1") if isinstance(page_obj.get("page_orchestration_v1"), dict) else {}
    if not orch:
        return

    data_sources = orch.get("data_sources") if isinstance(orch.get("data_sources"), dict) else {}
    if not data_sources:
        errors.append(f"pages.{page_key}.page_orchestration_v1.data_sources must be non-empty object")
        return

    ds_sections = data_sources.get("ds_sections")
    if not isinstance(ds_sections, dict):
        errors.append(f"pages.{page_key}.data_sources.ds_sections must exist")
    else:
        if str(ds_sections.get("source_type") or "").strip() != "static":
            errors.append(f"pages.{page_key}.data_sources.ds_sections.source_type must be static")
        if str(ds_sections.get("provider") or "").strip() != "page_contract.sections":
            errors.append(f"pages.{page_key}.data_sources.ds_sections.provider must be page_contract.sections")
        section_keys = ds_sections.get("section_keys")
        normalized = [str(item).strip() for item in section_keys] if isinstance(section_keys, list) else []
        if "_all" not in normalized:
            errors.append(f"pages.{page_key}.data_sources.ds_sections.section_keys must include _all")

    for ds_key, ds in data_sources.items():
        prefix = f"pages.{page_key}.data_sources.{ds_key}"
        if not isinstance(ds, dict):
            errors.append(f"{prefix} must be object")
            continue
        source_type = str(ds.get("source_type") or "").strip()
        provider = str(ds.get("provider") or "").strip()
        section_keys = ds.get("section_keys")
        if source_type not in ALLOWED_SOURCE_TYPES:
            errors.append(f"{prefix}.source_type invalid: {source_type}")
        if not provider:
            errors.append(f"{prefix}.provider must be non-empty")
        if not isinstance(section_keys, list) or not [str(item).strip() for item in section_keys if str(item).strip()]:
            errors.append(f"{prefix}.section_keys must be non-empty list")
        if source_type == "api.data":
            intent = str(ds.get("intent") or "").strip()
            model = str(ds.get("model") or "").strip()
            if intent != "api.data":
                errors.append(f"{prefix}.intent must be api.data when source_type=api.data")
            if not model:
                errors.append(f"{prefix}.model required when source_type=api.data")
            params = ds.get("params")
            if params is not None and not isinstance(params, dict):
                errors.append(f"{prefix}.params must be object when present")

    zones = orch.get("zones") if isinstance(orch.get("zones"), list) else []
    for zone_idx, zone in enumerate(zones):
        if not isinstance(zone, dict):
            continue
        blocks = zone.get("blocks") if isinstance(zone.get("blocks"), list) else []
        for block_idx, block in enumerate(blocks):
            if not isinstance(block, dict):
                continue
            prefix = f"pages.{page_key}.zones[{zone_idx}].blocks[{block_idx}]"
            section_key = str(block.get("section_key") or "").strip()
            data_source = str(block.get("data_source") or "").strip()
            if not section_key:
                errors.append(f"{prefix}.section_key must be non-empty")
                continue
            expected_key = _expected_ds_key(section_key)
            if data_source != expected_key:
                errors.append(f"{prefix}.data_source must be {expected_key}, got {data_source or '<empty>'}")
                continue
            ds = data_sources.get(data_source)
            if not isinstance(ds, dict):
                errors.append(f"{prefix}.data_source missing in data_sources: {data_source}")
                continue
            if str(ds.get("source_type") or "").strip() != "scene_context":
                errors.append(f"{prefix}.data_source.source_type must be scene_context")
            if str(ds.get("provider") or "").strip() != "page_contract.section":
                errors.append(f"{prefix}.data_source.provider must be page_contract.section")
            if str(ds.get("page_key") or "").strip() != page_key:
                errors.append(f"{prefix}.data_source.page_key must be {page_key}")
            if str(ds.get("section_key") or "").strip() != section_key:
                errors.append(f"{prefix}.data_source.section_key must match block.section_key")
            ds_section_keys = [str(item).strip() for item in (ds.get("section_keys") if isinstance(ds.get("section_keys"), list) else []) if str(item).strip()]
            if section_key not in ds_section_keys:
                errors.append(f"{prefix}.data_source.section_keys must contain block.section_key")


def main() -> int:
    if not BUILDER.is_file():
        return _fail([f"missing file: {BUILDER}"])
    try:
        mod = _load_builder(BUILDER)
    except Exception as exc:  # pragma: no cover
        return _fail([f"load builder failed: {exc}"])
    if not hasattr(mod, "build_page_contracts"):
        return _fail(["build_page_contracts not found in builder module"])

    payload = mod.build_page_contracts({})
    pages = payload.get("pages") if isinstance(payload, dict) else None
    if not isinstance(pages, dict) or not pages:
        return _fail(["page contracts payload missing pages object"])

    errors: list[str] = []
    checked = 0
    for page_key, page_obj in pages.items():
        if not isinstance(page_obj, dict):
            errors.append(f"pages.{page_key} must be object")
            continue
        if not isinstance(page_obj.get("page_orchestration_v1"), dict):
            continue
        checked += 1
        _validate_page(str(page_key), page_obj, errors)

    if checked == 0:
        errors.append("no page_orchestration_v1 payload found")
    if errors:
        return _fail(errors)
    print(f"[page_contract_data_source_semantics_guard] PASS (checked_pages={checked})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
