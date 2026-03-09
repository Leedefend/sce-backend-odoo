#!/usr/bin/env python3
from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys
from types import ModuleType
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
BUILDER = ROOT / "addons/smart_core/core/page_contracts_builder.py"
SEMANTICS = ROOT / "addons/smart_core/core/orchestration_semantics.py"
SECTIONS_OPTIONAL_PAGES = {"home"}

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
def _load_semantics(path: Path) -> dict[str, Any]:
    spec = spec_from_file_location("orchestration_semantics_guard_page_contract", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load module spec: {path}")
    mod = module_from_spec(spec)
    spec.loader.exec_module(mod)
    return {
        "BLOCK_TYPES": set(getattr(mod, "BLOCK_TYPES", ()) or ()),
        "STATE_TONES": set(getattr(mod, "STATE_TONES", ()) or ()),
        "PROGRESS_STATES": set(getattr(mod, "PROGRESS_STATES", ()) or ()),
        "PAGE_TYPES": set(getattr(mod, "PAGE_TYPES", ()) or ()),
        "LAYOUT_MODES": set(getattr(mod, "LAYOUT_MODES", ()) or ()),
        "PRIORITY_MODELS": set(getattr(mod, "PRIORITY_MODELS", ()) or ()),
        "ZONE_TYPES": set(getattr(mod, "ZONE_TYPES", ()) or ()),
        "ZONE_DISPLAY_MODES": set(getattr(mod, "ZONE_DISPLAY_MODES", ()) or ()),
        "DATA_SOURCE_TYPES": set(getattr(mod, "DATA_SOURCE_TYPES", ()) or ()),
        "BLOCK_PAYLOAD_KEYS": dict(getattr(mod, "BLOCK_PAYLOAD_KEYS", {}) or {}),
        "COMMON_PAYLOAD_KEYS": set(getattr(mod, "COMMON_PAYLOAD_KEYS", set()) or set()),
        "FORBIDDEN_LAYOUT_KEYS": set(getattr(mod, "FORBIDDEN_LAYOUT_KEYS", set()) or set()),
    }


_SEM = _load_semantics(SEMANTICS)
ALLOWED_BLOCK_TYPES = _SEM["BLOCK_TYPES"]
ALLOWED_TONES = _SEM["STATE_TONES"]
ALLOWED_PROGRESS = _SEM["PROGRESS_STATES"]
ALLOWED_DATA_SOURCE_TYPES = _SEM["DATA_SOURCE_TYPES"]
ALLOWED_PAGE_TYPES = _SEM["PAGE_TYPES"]
ALLOWED_LAYOUT_MODES = _SEM["LAYOUT_MODES"]
ALLOWED_PRIORITY_MODELS = _SEM["PRIORITY_MODELS"]
ALLOWED_ZONE_TYPES = _SEM["ZONE_TYPES"]
ALLOWED_ZONE_DISPLAY_MODES = _SEM["ZONE_DISPLAY_MODES"]
BLOCK_PAYLOAD_KEYS = _SEM["BLOCK_PAYLOAD_KEYS"]
COMMON_PAYLOAD_KEYS = _SEM["COMMON_PAYLOAD_KEYS"]
FORBIDDEN_LAYOUT_KEYS = _SEM["FORBIDDEN_LAYOUT_KEYS"]


def _scan_forbidden_layout_keys(value: Any, prefix: str, errors: list[str]) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            key_text = str(key).strip().lower()
            next_prefix = f"{prefix}.{key}" if prefix else str(key)
            if key_text in FORBIDDEN_LAYOUT_KEYS:
                errors.append(f"{next_prefix} uses forbidden pixel/layout key: {key}")
            _scan_forbidden_layout_keys(child, next_prefix, errors)
    elif isinstance(value, list):
        for idx, item in enumerate(value):
            _scan_forbidden_layout_keys(item, f"{prefix}[{idx}]", errors)


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
        if page_key in SECTIONS_OPTIONAL_PAGES:
            return
        errors.append(f"pages.{page_key}.sections must be non-empty list")

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
    else:
        if not isinstance(page.get("audience"), list) or not page.get("audience"):
            errors.append(f"pages.{page_key}.page_orchestration_v1.page.audience must be non-empty list")
        page_type = str(page.get("page_type") or "").strip()
        layout_mode = str(page.get("layout_mode") or "").strip()
        priority_model = str(page.get("priority_model") or "").strip()
        if page_type not in ALLOWED_PAGE_TYPES:
            errors.append(f"pages.{page_key}.page.page_type invalid: {page_type}")
        if layout_mode not in ALLOWED_LAYOUT_MODES:
            errors.append(f"pages.{page_key}.page.layout_mode invalid: {layout_mode}")
        if priority_model not in ALLOWED_PRIORITY_MODELS:
            errors.append(f"pages.{page_key}.page.priority_model invalid: {priority_model}")
        header = page.get("header")
        if header is not None and not isinstance(header, dict):
            errors.append(f"pages.{page_key}.page.header must be object when present")
        if isinstance(header, dict):
            badges = header.get("badges")
            if badges is not None and not isinstance(badges, list):
                errors.append(f"pages.{page_key}.page.header.badges must be list when present")
            if isinstance(badges, list):
                for idx, badge in enumerate(badges):
                    bprefix = f"pages.{page_key}.page.header.badges[{idx}]"
                    if not isinstance(badge, dict):
                        errors.append(f"{bprefix} must be object")
                        continue
                    tone = str(badge.get("tone") or "").strip()
                    if tone and tone not in ALLOWED_TONES:
                        errors.append(f"{bprefix}.tone invalid: {tone}")

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
    action_schema = orch.get("action_schema")
    action_registry = action_schema.get("actions") if isinstance(action_schema, dict) and isinstance(action_schema.get("actions"), dict) else {}
    if not isinstance(action_registry, dict):
        errors.append(f"pages.{page_key}.action_schema.actions must be object")
        action_registry = {}
    global_actions = page.get("global_actions") if isinstance(page, dict) else None
    if global_actions is not None and not isinstance(global_actions, list):
        errors.append(f"pages.{page_key}.page.global_actions must be list when present")
    if isinstance(global_actions, list):
        for aidx, action in enumerate(global_actions):
            aprefix = f"pages.{page_key}.page.global_actions[{aidx}]"
            if not isinstance(action, dict):
                errors.append(f"{aprefix} must be object")
                continue
            action_key = str(action.get("key") or "").strip()
            if not action_key:
                errors.append(f"{aprefix}.key must be non-empty")
                continue
            if action_key not in action_registry:
                errors.append(f"{aprefix}.key not declared in action_schema.actions: {action_key}")

    data_sources = orch.get("data_sources")
    if not isinstance(data_sources, dict) or not data_sources:
        errors.append(f"pages.{page_key}.page_orchestration_v1.data_sources must be non-empty object")
        data_sources = {}
    else:
        for ds_key, ds in data_sources.items():
            dprefix = f"pages.{page_key}.page_orchestration_v1.data_sources.{ds_key}"
            if not isinstance(ds, dict):
                errors.append(f"{dprefix} must be object")
                continue
            source_type = str(ds.get("source_type") or "").strip()
            provider = str(ds.get("provider") or "").strip()
            section_keys = ds.get("section_keys")
            if source_type not in ALLOWED_DATA_SOURCE_TYPES:
                errors.append(f"{dprefix}.source_type invalid: {source_type}")
            if not provider:
                errors.append(f"{dprefix}.provider must be non-empty string")
            if not isinstance(section_keys, list) or not [str(item).strip() for item in section_keys if str(item).strip()]:
                errors.append(f"{dprefix}.section_keys must be non-empty list")
            if source_type == "api.data":
                intent = str(ds.get("intent") or "").strip()
                model = str(ds.get("model") or "").strip()
                if intent != "api.data":
                    errors.append(f"{dprefix}.intent must be api.data when source_type=api.data")
                if not model:
                    errors.append(f"{dprefix}.model required when source_type=api.data")
                params = ds.get("params")
                if params is not None and not isinstance(params, dict):
                    errors.append(f"{dprefix}.params must be object when present")
            if source_type == "capability_registry":
                group_key = str(ds.get("group_key") or "").strip()
                if group_key and not group_key.replace("_", "").isalnum():
                    errors.append(f"{dprefix}.group_key invalid: {group_key}")
            if source_type == "scene_context":
                section_key = str(ds.get("section_key") or "").strip()
                ds_page_key = str(ds.get("page_key") or "").strip()
                if not section_key:
                    errors.append(f"{dprefix}.section_key required when source_type=scene_context")
                if ds_page_key != page_key:
                    errors.append(f"{dprefix}.page_key must equal page key ({page_key}) when source_type=scene_context")

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
    block_data_sources: set[str] = set()
    for zidx, zone in enumerate(zones):
        prefix = f"pages.{page_key}.page_orchestration_v1.zones[{zidx}]"
        if not isinstance(zone, dict):
            errors.append(f"{prefix} must be object")
            continue
        zone_type = str(zone.get("zone_type") or "").strip()
        display_mode = str(zone.get("display_mode") or "").strip()
        if zone_type not in ALLOWED_ZONE_TYPES:
            errors.append(f"{prefix}.zone_type invalid: {zone_type}")
        if display_mode not in ALLOWED_ZONE_DISPLAY_MODES:
            errors.append(f"{prefix}.display_mode invalid: {display_mode}")
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
            data_source = str(block.get("data_source") or "").strip()
            if block_type not in ALLOWED_BLOCK_TYPES:
                errors.append(f"{bprefix}.block_type invalid: {block_type}")
            if tone not in ALLOWED_TONES:
                errors.append(f"{bprefix}.tone invalid: {tone}")
            if progress not in ALLOWED_PROGRESS:
                errors.append(f"{bprefix}.progress invalid: {progress}")
            if not section_key:
                errors.append(f"{bprefix}.section_key must be non-empty")
                continue
            if not data_source:
                errors.append(f"{bprefix}.data_source must be non-empty")
            else:
                block_data_sources.add(data_source)
                if data_source not in data_sources:
                    errors.append(f"{bprefix}.data_source not found in data_sources: {data_source}")
                else:
                    ds = data_sources.get(data_source)
                    if isinstance(ds, dict):
                        ds_section_keys = [str(item).strip() for item in (ds.get("section_keys") if isinstance(ds.get("section_keys"), list) else []) if str(item).strip()]
                        if ds_section_keys and "_all" not in ds_section_keys and section_key not in ds_section_keys:
                            errors.append(f"{bprefix}.section_key not declared in data_sources.{data_source}.section_keys")
                        if str(ds.get("source_type") or "").strip() == "scene_context":
                            ds_section_key = str(ds.get("section_key") or "").strip()
                            if ds_section_key and ds_section_key != section_key:
                                errors.append(
                                    f"{bprefix}.section_key mismatch with data_sources.{data_source}.section_key: {section_key} != {ds_section_key}"
                                )
            actions = block.get("actions")
            if actions is not None and not isinstance(actions, list):
                errors.append(f"{bprefix}.actions must be list when present")
            payload = block.get("payload")
            if payload is not None and not isinstance(payload, dict):
                errors.append(f"{bprefix}.payload must be object when present")
            if isinstance(payload, dict):
                allowed_keys = BLOCK_PAYLOAD_KEYS.get(block_type, set()) | COMMON_PAYLOAD_KEYS
                unexpected = sorted(set(str(key) for key in payload.keys()) - allowed_keys)
                if unexpected:
                    errors.append(f"{bprefix}.payload unexpected keys for block_type={block_type}: {', '.join(unexpected)}")
            if isinstance(actions, list):
                for aidx, action in enumerate(actions):
                    aprefix = f"{bprefix}.actions[{aidx}]"
                    if not isinstance(action, dict):
                        errors.append(f"{aprefix} must be object")
                        continue
                    action_key = str(action.get("key") or "").strip()
                    if not action_key:
                        errors.append(f"{aprefix}.key must be non-empty")
                        continue
                    if action_key not in action_registry:
                        errors.append(f"{aprefix}.key not declared in action_schema.actions: {action_key}")
            block_section_keys.add(section_key)

    if section_keys != block_section_keys:
        missing_in_blocks = sorted(section_keys - block_section_keys)
        extra_in_blocks = sorted(block_section_keys - section_keys)
        if missing_in_blocks:
            errors.append(f"pages.{page_key}: sections missing in orchestration blocks: {', '.join(missing_in_blocks)}")
        if extra_in_blocks:
            errors.append(f"pages.{page_key}: orchestration blocks contain unknown sections: {', '.join(extra_in_blocks)}")
    if data_sources:
        unused_data_sources = sorted(set(data_sources.keys()) - block_data_sources - {"ds_sections"})
        if unused_data_sources:
            errors.append(f"pages.{page_key}: data_sources unused by blocks: {', '.join(unused_data_sources)}")

    _scan_forbidden_layout_keys(page, f"pages.{page_key}.page", errors)
    _scan_forbidden_layout_keys(zones, f"pages.{page_key}.zones", errors)
    _scan_forbidden_layout_keys(orch.get("render_hints"), f"pages.{page_key}.render_hints", errors)


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
