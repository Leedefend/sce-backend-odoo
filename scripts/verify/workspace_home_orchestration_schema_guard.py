#!/usr/bin/env python3
from __future__ import annotations

from datetime import datetime
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys
import types
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
HOME_BUILDER = ROOT / "addons/smart_core/core/workspace_home_contract_builder.py"

REQUIRED_BLOCK_TYPES = {
    "hero_metric",
    "metric_row",
    "todo_list",
    "alert_panel",
    "progress_summary",
    "entry_grid",
    "accordion_group",
    "record_summary",
    "activity_feed",
}
REQUIRED_TONES = {"success", "warning", "danger", "info", "neutral"}
REQUIRED_PROGRESS = {"overdue", "blocked", "pending", "running", "completed"}
ALLOWED_DATA_SOURCE_TYPES = {"static", "scene_context", "api.data", "computed", "capability_registry", "role_profile", "mixed"}
ALLOWED_ACTION_INTENTS = {"ui.contract", "api.data", "execute_button", "file.download"}
ALLOWED_ACTION_TARGET_KINDS = {"scene.key", "page.refresh", "menu.first_reachable", "route.path"}
ALLOWED_PAGE_TYPES = {"workspace", "dashboard", "list", "detail", "approval", "monitor", "report", "entry_hub"}
ALLOWED_LAYOUT_MODES = {"dashboard", "two_column", "single_flow", "focus_task", "monitoring", "entry_grid"}
ALLOWED_PRIORITY_MODELS = {"role_first", "risk_first", "task_first", "metric_first"}
ALLOWED_ZONE_TYPES = {"hero", "primary", "secondary", "supporting", "sidebar", "footer"}
ALLOWED_ZONE_DISPLAY_MODES = {"stack", "grid", "carousel", "tabs", "accordion", "flow"}
BLOCK_PAYLOAD_KEYS = {
    "hero_metric": {"main_value_field", "label_field", "trend_field", "status_field", "click_action"},
    "metric_row": {"items", "show_trend"},
    "todo_list": {"item_layout", "fields", "max_items", "sort_by"},
    "alert_panel": {"alert_level_field", "title_field", "desc_field", "group_by", "max_items", "show_counts"},
    "progress_summary": {"bars", "show_percentage", "show_target"},
    "entry_grid": {"entry_source", "group_key", "layout", "show_icon", "show_hint", "entry_action_intent"},
    "accordion_group": {"mode"},
    "record_summary": {"tag", "enabled", "open", "style_variant"},
    "activity_feed": {"stream"},
}
COMMON_PAYLOAD_KEYS = {"tag", "enabled", "open"}
FORBIDDEN_LAYOUT_KEYS = {"left", "top", "width", "height", "x", "y", "color", "background", "font_size"}


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
    print("[workspace_home_orchestration_schema_guard] FAIL")
    for err in errors:
        print(f"- {err}")
    return 1


def _stub_odoo_module() -> None:
    if "odoo" in sys.modules:
        return
    odoo_mod = types.ModuleType("odoo")

    class _Datetime:
        @staticmethod
        def now():
            return datetime.now()

    class _Fields:
        Datetime = _Datetime

    odoo_mod.fields = _Fields  # type: ignore[attr-defined]
    sys.modules["odoo"] = odoo_mod


def _load_builder():
    _stub_odoo_module()
    spec = spec_from_file_location("workspace_home_contract_builder_guard", HOME_BUILDER)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load module spec")
    mod = module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _sample_data(role_code: str) -> dict[str, Any]:
    return {
        "capabilities": [
            {"key": "a", "state": "READY", "ui_label": "A", "default_payload": {"route": "/s/projects.list"}},
            {"key": "b", "state": "LOCKED", "ui_label": "B", "reason_code": "PERMISSION_DENIED", "reason": "deny"},
            {"key": "c", "state": "PREVIEW", "ui_label": "C"},
        ],
        "scenes": [{"key": "projects.list"}, {"key": "projects.ledger"}],
        "nav": [{"key": "menu:1"}],
        "role_surface": {"role_code": role_code},
    }


def _as_set_list(value: Any) -> set[str]:
    if not isinstance(value, list):
        return set()
    return {str(item).strip() for item in value if str(item).strip()}


def _validate_contract(contract: dict[str, Any], role_code: str, errors: list[str]) -> None:
    protocol = contract.get("semantic_protocol")
    if not isinstance(protocol, dict):
        errors.append(f"{role_code}: missing semantic_protocol object")
        return

    block_types = _as_set_list(protocol.get("block_types"))
    tones = _as_set_list(protocol.get("state_tones"))
    progress = _as_set_list(protocol.get("progress_states"))

    if block_types != REQUIRED_BLOCK_TYPES:
        errors.append(f"{role_code}: block_types mismatch expected={sorted(REQUIRED_BLOCK_TYPES)} got={sorted(block_types)}")
    if tones != REQUIRED_TONES:
        errors.append(f"{role_code}: state_tones mismatch expected={sorted(REQUIRED_TONES)} got={sorted(tones)}")
    if progress != REQUIRED_PROGRESS:
        errors.append(f"{role_code}: progress_states mismatch expected={sorted(REQUIRED_PROGRESS)} got={sorted(progress)}")

    orchestration_v1 = contract.get("page_orchestration_v1")
    if not isinstance(orchestration_v1, dict):
        errors.append(f"{role_code}: missing page_orchestration_v1 object")
        return

    page = orchestration_v1.get("page")
    zones = orchestration_v1.get("zones")
    data_sources = orchestration_v1.get("data_sources")
    state_schema = orchestration_v1.get("state_schema")
    action_schema = orchestration_v1.get("action_schema")
    render_hints = orchestration_v1.get("render_hints")
    meta = orchestration_v1.get("meta")
    if not isinstance(page, dict):
        errors.append(f"{role_code}: page_orchestration_v1.page must be object")
    if isinstance(page, dict):
        if _as_set_list(page.get("audience")) == set():
            errors.append(f"{role_code}: page_orchestration_v1.page.audience must be non-empty")
        page_type = str(page.get("page_type") or "").strip()
        layout_mode = str(page.get("layout_mode") or "").strip()
        priority_model = str(page.get("priority_model") or "").strip()
        if page_type not in ALLOWED_PAGE_TYPES:
            errors.append(f"{role_code}: page.page_type invalid: {page_type}")
        if layout_mode not in ALLOWED_LAYOUT_MODES:
            errors.append(f"{role_code}: page.layout_mode invalid: {layout_mode}")
        if priority_model not in ALLOWED_PRIORITY_MODELS:
            errors.append(f"{role_code}: page.priority_model invalid: {priority_model}")
        header = page.get("header")
        if header is not None and not isinstance(header, dict):
            errors.append(f"{role_code}: page.header must be object when present")
        if isinstance(header, dict):
            badges = header.get("badges")
            if badges is not None and not isinstance(badges, list):
                errors.append(f"{role_code}: page.header.badges must be list when present")
            if isinstance(badges, list):
                for badge_idx, badge in enumerate(badges):
                    bprefix = f"{role_code}: page.header.badges[{badge_idx}]"
                    if not isinstance(badge, dict):
                        errors.append(f"{bprefix} must be object")
                        continue
                    tone = str(badge.get("tone") or "").strip()
                    if tone and tone not in REQUIRED_TONES:
                        errors.append(f"{bprefix}.tone invalid: {tone}")
    if not isinstance(zones, list) or not zones:
        errors.append(f"{role_code}: page_orchestration_v1.zones must be non-empty list")
        return
    if not isinstance(data_sources, dict) or not data_sources:
        errors.append(f"{role_code}: page_orchestration_v1.data_sources must be non-empty object")
        data_sources = {}
    else:
        for ds_key, ds in data_sources.items():
            dprefix = f"{role_code}: data_sources.{ds_key}"
            if not isinstance(ds, dict):
                errors.append(f"{dprefix} must be object")
                continue
            source_type = str(ds.get("source_type") or "").strip()
            provider = str(ds.get("provider") or "").strip()
            if source_type not in ALLOWED_DATA_SOURCE_TYPES:
                errors.append(f"{dprefix}.source_type invalid: {source_type}")
            if not provider:
                errors.append(f"{dprefix}.provider must be non-empty")
            section_keys = ds.get("section_keys")
            if not isinstance(section_keys, list) or not [str(item).strip() for item in section_keys if str(item).strip()]:
                errors.append(f"{dprefix}.section_keys must be non-empty list")
            if source_type in {"computed", "scene_context", "capability_registry", "static"} and not provider.startswith("workspace."):
                errors.append(f"{dprefix}.provider must start with workspace.")
    if not isinstance(state_schema, dict):
        errors.append(f"{role_code}: page_orchestration_v1.state_schema must be object")
    else:
        tone_keys = _as_set_list(list((state_schema.get("tones") or {}).keys()))
        business_state_keys = _as_set_list(list((state_schema.get("business_states") or {}).keys()))
        if tone_keys != REQUIRED_TONES:
            errors.append(f"{role_code}: state_schema.tones mismatch expected={sorted(REQUIRED_TONES)} got={sorted(tone_keys)}")
        if business_state_keys != REQUIRED_PROGRESS:
            errors.append(
                f"{role_code}: state_schema.business_states mismatch expected={sorted(REQUIRED_PROGRESS)} got={sorted(business_state_keys)}"
            )
    action_registry = action_schema.get("actions") if isinstance(action_schema, dict) and isinstance(action_schema.get("actions"), dict) else {}
    if not isinstance(action_registry, dict):
        errors.append(f"{role_code}: page_orchestration_v1.action_schema.actions must be object")
        action_registry = {}
    if not isinstance(render_hints, dict):
        errors.append(f"{role_code}: page_orchestration_v1.render_hints must be object")
    if not isinstance(meta, dict):
        errors.append(f"{role_code}: page_orchestration_v1.meta must be object")

    seen_keys: set[str] = set()
    for zone_idx, zone in enumerate(zones):
        zprefix = f"{role_code}: zones[{zone_idx}]"
        if not isinstance(zone, dict):
            errors.append(f"{zprefix} must be object")
            continue
        zone_type = str(zone.get("zone_type") or "").strip()
        display_mode = str(zone.get("display_mode") or "").strip()
        if zone_type not in {"hero", "primary", "secondary", "supporting", "sidebar", "footer"}:
            errors.append(f"{zprefix}.zone_type invalid: {zone_type}")
        if display_mode not in ALLOWED_ZONE_DISPLAY_MODES:
            errors.append(f"{zprefix}.display_mode invalid: {display_mode}")
        zone_blocks = zone.get("blocks")
        if not isinstance(zone_blocks, list) or not zone_blocks:
            errors.append(f"{zprefix}.blocks must be non-empty list")
            continue
        for block_idx, block in enumerate(zone_blocks):
            prefix = f"{zprefix}.blocks[{block_idx}]"
            if not isinstance(block, dict):
                errors.append(f"{prefix} must be object")
                continue
            key = str(block.get("key") or "").strip()
            block_type = str(block.get("block_type") or "").strip()
            tone = str(block.get("tone") or "").strip()
            prog = str(block.get("progress") or "").strip()
            section_key = str(block.get("section_key") or "").strip()
            if not key:
                errors.append(f"{prefix}.key required")
            elif key in seen_keys:
                errors.append(f"{prefix}.key duplicate: {key}")
            else:
                seen_keys.add(key)
            if block_type not in REQUIRED_BLOCK_TYPES:
                errors.append(f"{prefix}.block_type invalid: {block_type}")
            if tone not in REQUIRED_TONES:
                errors.append(f"{prefix}.tone invalid: {tone}")
            if prog not in REQUIRED_PROGRESS:
                errors.append(f"{prefix}.progress invalid: {prog}")
            if not section_key:
                errors.append(f"{prefix}.section_key required")
            data_source = str(block.get("data_source") or "").strip()
            if not data_source:
                errors.append(f"{prefix}.data_source required")
            elif data_source not in data_sources:
                errors.append(f"{prefix}.data_source missing in data_sources: {data_source}")
            else:
                ds = data_sources.get(data_source)
                if isinstance(ds, dict):
                    section_keys = [str(item).strip() for item in (ds.get("section_keys") if isinstance(ds.get("section_keys"), list) else []) if str(item).strip()]
                    if section_keys and section_key not in section_keys:
                        errors.append(f"{prefix}.section_key not declared in data_sources.{data_source}.section_keys")
            visibility = block.get("visibility")
            if not isinstance(visibility, dict):
                errors.append(f"{prefix}.visibility must be object")
            elif not isinstance(visibility.get("roles"), list):
                errors.append(f"{prefix}.visibility.roles must be list")
            actions = block.get("actions")
            if actions is not None and not isinstance(actions, list):
                errors.append(f"{prefix}.actions must be list when present")
            payload = block.get("payload")
            if payload is not None and not isinstance(payload, dict):
                errors.append(f"{prefix}.payload must be object when present")
            if isinstance(payload, dict):
                allowed_keys = BLOCK_PAYLOAD_KEYS.get(block_type, set()) | COMMON_PAYLOAD_KEYS
                unexpected = sorted(set(str(key) for key in payload.keys()) - allowed_keys)
                if unexpected:
                    errors.append(f"{prefix}.payload unexpected keys for block_type={block_type}: {', '.join(unexpected)}")
            if isinstance(actions, list):
                for action_idx, action in enumerate(actions):
                    aprefix = f"{prefix}.actions[{action_idx}]"
                    if not isinstance(action, dict):
                        errors.append(f"{aprefix} must be object")
                        continue
                    action_key = str(action.get("key") or "").strip()
                    if not action_key:
                        errors.append(f"{aprefix}.key required")
                        continue
                    if action_key not in action_registry:
                        errors.append(f"{aprefix}.key not declared in action_schema.actions: {action_key}")

    if isinstance(page, dict):
        global_actions = page.get("global_actions")
        if global_actions is not None and not isinstance(global_actions, list):
            errors.append(f"{role_code}: page.global_actions must be list when present")
        if isinstance(global_actions, list):
            for action_idx, action in enumerate(global_actions):
                aprefix = f"{role_code}: page.global_actions[{action_idx}]"
                if not isinstance(action, dict):
                    errors.append(f"{aprefix} must be object")
                    continue
                action_key = str(action.get("key") or "").strip()
                intent = str(action.get("intent") or "").strip()
                if not action_key:
                    errors.append(f"{aprefix}.key required")
                    continue
                if action_key not in action_registry:
                    errors.append(f"{aprefix}.key not declared in action_schema.actions: {action_key}")
                    continue
                schema_intent = str((action_registry.get(action_key) or {}).get("intent") or "").strip()
                if intent and schema_intent and intent != schema_intent:
                    errors.append(f"{aprefix}.intent mismatch with action_schema: {intent} != {schema_intent}")

    for action_key, action in action_registry.items():
        aprefix = f"{role_code}: action_schema.actions.{action_key}"
        if not isinstance(action, dict):
            errors.append(f"{aprefix} must be object")
            continue
        intent = str(action.get("intent") or "").strip()
        target = action.get("target")
        visibility = action.get("visibility")
        if intent not in ALLOWED_ACTION_INTENTS:
            errors.append(f"{aprefix}.intent invalid: {intent}")
        if not isinstance(target, dict):
            errors.append(f"{aprefix}.target must be object")
            continue
        if not isinstance(visibility, dict):
            errors.append(f"{aprefix}.visibility must be object")
        else:
            if not isinstance(visibility.get("roles"), list):
                errors.append(f"{aprefix}.visibility.roles must be list")
            if not isinstance(visibility.get("capabilities"), list):
                errors.append(f"{aprefix}.visibility.capabilities must be list")
        kind = str(target.get("kind") or "").strip()
        if kind not in ALLOWED_ACTION_TARGET_KINDS:
            errors.append(f"{aprefix}.target.kind invalid: {kind}")
        if kind == "scene.key":
            scene_key = str(target.get("scene_key") or "").strip()
            if not scene_key:
                errors.append(f"{aprefix}.target.scene_key required when kind=scene.key")
        if kind == "route.path":
            path = str(target.get("path") or "").strip()
            if not path.startswith("/"):
                errors.append(f"{aprefix}.target.path must be absolute when kind=route.path")

    orchestration_legacy = contract.get("page_orchestration")
    if not isinstance(orchestration_legacy, dict):
        errors.append(f"{role_code}: missing legacy page_orchestration object")

    _scan_forbidden_layout_keys(page, f"{role_code}: page", errors)
    _scan_forbidden_layout_keys(zones, f"{role_code}: zones", errors)
    _scan_forbidden_layout_keys(orchestration_v1.get("render_hints"), f"{role_code}: render_hints", errors)


def main() -> int:
    if not HOME_BUILDER.is_file():
        return _fail([f"missing file: {HOME_BUILDER.relative_to(ROOT).as_posix()}"])
    try:
        builder = _load_builder()
    except Exception as exc:  # pragma: no cover
        return _fail([f"load builder failed: {exc}"])

    if not hasattr(builder, "build_workspace_home_contract"):
        return _fail(["build_workspace_home_contract not found"])

    errors: list[str] = []
    contracts: dict[str, dict[str, Any]] = {}
    for role in ("pm", "finance", "owner"):
        payload = builder.build_workspace_home_contract(_sample_data(role))
        if not isinstance(payload, dict):
            errors.append(f"{role}: builder output must be object")
            continue
        contracts[role] = payload
        _validate_contract(payload, role, errors)

    if len(contracts) == 3:
        pm_focus = contracts["pm"].get("role_variant", {}).get("focus")
        finance_focus = contracts["finance"].get("role_variant", {}).get("focus")
        owner_focus = contracts["owner"].get("role_variant", {}).get("focus")
        if pm_focus == finance_focus == owner_focus:
            errors.append("role_variant.focus must differ across pm/finance/owner for heterogeneous layout")

        priority_models = {
            role: str(((contracts[role].get("page_orchestration_v1") or {}).get("page") or {}).get("priority_model") or "").strip()
            for role in ("pm", "finance", "owner")
        }
        if len(set(priority_models.values())) < 2:
            errors.append("page.priority_model should vary across roles (pm/finance/owner)")

        def _zone_order(role: str) -> list[str]:
            orch = contracts[role].get("page_orchestration_v1") if isinstance(contracts[role].get("page_orchestration_v1"), dict) else {}
            zones = orch.get("zones") if isinstance(orch.get("zones"), list) else []
            normalized: list[tuple[int, str]] = []
            for zone in zones:
                if not isinstance(zone, dict):
                    continue
                key = str(zone.get("key") or "").strip()
                priority = int(zone.get("priority") or 0)
                if key:
                    normalized.append((priority, key))
            normalized.sort(key=lambda item: item[0], reverse=True)
            return [key for _, key in normalized]

        pm_order = _zone_order("pm")
        finance_order = _zone_order("finance")
        owner_order = _zone_order("owner")
        if pm_order == finance_order == owner_order:
            errors.append("zone priority order should vary across pm/finance/owner for heterogeneous same-page layout")

    if errors:
        return _fail(errors)

    print("[workspace_home_orchestration_schema_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
