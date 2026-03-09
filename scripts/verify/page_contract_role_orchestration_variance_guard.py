#!/usr/bin/env python3
from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys
from types import ModuleType
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
BUILDER = ROOT / "addons/smart_core/core/page_contracts_builder.py"


def _fail(errors: list[str]) -> int:
    print("[page_contract_role_orchestration_variance_guard] FAIL")
    for err in errors:
        print(f"- {err}")
    return 1


def _load_builder_module(path: Path) -> ModuleType:
    spec = spec_from_file_location("page_contracts_builder_role_variance_guard", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load module spec: {path}")
    mod = module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _build_payload(builder_mod: ModuleType, role_code: str) -> dict[str, Any]:
    data = {"role_surface": {"role_code": role_code}}
    payload = builder_mod.build_page_contracts(data)
    return payload if isinstance(payload, dict) else {}


def _page_sections(payload: dict[str, Any], page_key: str) -> dict[str, bool]:
    pages = payload.get("pages") if isinstance(payload.get("pages"), dict) else {}
    page = pages.get(page_key) if isinstance(pages.get(page_key), dict) else {}
    sections = page.get("sections") if isinstance(page.get("sections"), list) else []
    result: dict[str, bool] = {}
    for section in sections:
        if not isinstance(section, dict):
            continue
        key = str(section.get("key") or "").strip()
        if not key:
            continue
        result[key] = bool(section.get("enabled") is True)
    return result


def _find_block(payload: dict[str, Any], page_key: str, section_key: str) -> dict[str, Any]:
    pages = payload.get("pages") if isinstance(payload.get("pages"), dict) else {}
    page = pages.get(page_key) if isinstance(pages.get(page_key), dict) else {}
    orch = page.get("page_orchestration_v1") if isinstance(page.get("page_orchestration_v1"), dict) else {}
    zones = orch.get("zones") if isinstance(orch.get("zones"), list) else []
    for zone in zones:
        if not isinstance(zone, dict):
            continue
        blocks = zone.get("blocks") if isinstance(zone.get("blocks"), list) else []
        for block in blocks:
            if not isinstance(block, dict):
                continue
            if str(block.get("section_key") or "").strip() == section_key:
                return block
    return {}


def main() -> int:
    if not BUILDER.is_file():
        return _fail([f"missing file: {BUILDER}"])

    try:
        builder_mod = _load_builder_module(BUILDER)
    except Exception as exc:  # pragma: no cover
        return _fail([f"load builder failed: {exc}"])

    if not hasattr(builder_mod, "build_page_contracts"):
        return _fail(["build_page_contracts not found in builder module"])

    pm = _build_payload(builder_mod, "pm")
    finance = _build_payload(builder_mod, "finance")
    owner = _build_payload(builder_mod, "owner")

    errors: list[str] = []

    pm_usage = _page_sections(pm, "usage_analytics")
    if pm_usage.get("tables_role_user") is not False:
        errors.append("pm: usage_analytics.tables_role_user must be disabled")

    finance_action = _page_sections(finance, "action")
    if finance_action.get("group_view") is not False:
        errors.append("finance: action.group_view must be disabled")

    owner_workbench = _page_sections(owner, "workbench")
    if owner_workbench.get("hud_details") is not False:
        errors.append("owner: workbench.hud_details must be disabled")

    owner_action = _page_sections(owner, "action")
    if owner_action.get("advanced_view") is not False:
        errors.append("owner: action.advanced_view must be disabled")

    owner_block = _find_block(owner, "workbench", "hud_details")
    if str(owner_block.get("progress") or "") != "pending":
        errors.append("owner: workbench.hud_details orchestration block progress must be pending")

    pm_block = _find_block(pm, "workbench", "hud_details")
    if str(pm_block.get("progress") or "") != "running":
        errors.append("pm: workbench.hud_details orchestration block progress must be running")

    if errors:
        return _fail(errors)

    print("[page_contract_role_orchestration_variance_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
