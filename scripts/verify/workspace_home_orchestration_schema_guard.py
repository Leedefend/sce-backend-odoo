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
    "kpi_row",
    "todo_list",
    "alert_panel",
    "progress_group",
    "quick_entry_grid",
    "fold_section",
    "record_summary",
    "activity_feed",
}
REQUIRED_TONES = {"success", "warning", "danger", "info", "neutral"}
REQUIRED_PROGRESS = {"overdue", "blocked", "pending", "running", "completed"}


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

    orchestration = contract.get("page_orchestration")
    if not isinstance(orchestration, dict):
        errors.append(f"{role_code}: missing page_orchestration object")
        return

    page = orchestration.get("page")
    zones = orchestration.get("zones")
    blocks = orchestration.get("blocks")
    role_layout = orchestration.get("role_layout")
    if not isinstance(page, dict):
        errors.append(f"{role_code}: page_orchestration.page must be object")
    if not isinstance(zones, list) or not zones:
        errors.append(f"{role_code}: page_orchestration.zones must be non-empty list")
    if not isinstance(blocks, list) or not blocks:
        errors.append(f"{role_code}: page_orchestration.blocks must be non-empty list")
        return
    if not isinstance(role_layout, dict):
        errors.append(f"{role_code}: page_orchestration.role_layout must be object")

    seen_keys: set[str] = set()
    for idx, block in enumerate(blocks):
        prefix = f"{role_code}: blocks[{idx}]"
        if not isinstance(block, dict):
            errors.append(f"{prefix} must be object")
            continue
        key = str(block.get("key") or "").strip()
        block_type = str(block.get("type") or "").strip()
        tone = str(block.get("tone") or "").strip()
        prog = str(block.get("progress") or "").strip()
        zone = str(block.get("zone") or "").strip()
        if not key:
            errors.append(f"{prefix}.key required")
        elif key in seen_keys:
            errors.append(f"{prefix}.key duplicate: {key}")
        else:
            seen_keys.add(key)
        if block_type not in REQUIRED_BLOCK_TYPES:
            errors.append(f"{prefix}.type invalid: {block_type}")
        if tone not in REQUIRED_TONES:
            errors.append(f"{prefix}.tone invalid: {tone}")
        if prog not in REQUIRED_PROGRESS:
            errors.append(f"{prefix}.progress invalid: {prog}")
        if zone not in {"primary", "analysis", "support"}:
            errors.append(f"{prefix}.zone invalid: {zone}")


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

    if errors:
        return _fail(errors)

    print("[workspace_home_orchestration_schema_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
