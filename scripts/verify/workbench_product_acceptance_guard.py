#!/usr/bin/env python3
from __future__ import annotations

import importlib
import sys
import types
from datetime import datetime
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
HOME_BUILDER = ROOT / "addons/smart_core/core/workspace_home_contract_builder.py"
HOME_VIEW = ROOT / "frontend/apps/web/src/views/HomeView.vue"

MAIN_ZONE_KEYS = ["hero", "today_focus", "analysis", "quick_entries"]
DIAGNOSTIC_TERMS = ("result" + "_summary", "active" + "_filters")


def _fail(errors: list[str]) -> int:
    print("[workbench_product_acceptance_guard] FAIL")
    for err in errors:
        print(f"- {err}")
    return 1


def _ensure_odoo_namespace() -> None:
    addons_path = str(ROOT / "addons")
    smart_core_path = str(ROOT / "addons/smart_core")
    core_path = str(ROOT / "addons/smart_core/core")
    odoo_mod = sys.modules.get("odoo")
    if odoo_mod is None:
        odoo_mod = types.ModuleType("odoo")
        odoo_mod.__path__ = []  # type: ignore[attr-defined]
        sys.modules["odoo"] = odoo_mod

    class _Datetime:
        @staticmethod
        def now():
            return datetime.now()

    class _Fields:
        Datetime = _Datetime

    odoo_mod.fields = _Fields  # type: ignore[attr-defined]
    for module_name, module_path in (
        ("odoo.addons", addons_path),
        ("odoo.addons.smart_core", smart_core_path),
        ("odoo.addons.smart_core.core", core_path),
    ):
        mod = sys.modules.get(module_name)
        if mod is None:
            mod = types.ModuleType(module_name)
            mod.__path__ = [module_path]  # type: ignore[attr-defined]
            sys.modules[module_name] = mod
        elif hasattr(mod, "__path__") and module_path not in mod.__path__:  # type: ignore[attr-defined]
            mod.__path__.append(module_path)  # type: ignore[attr-defined]
    importlib.import_module("odoo.addons.smart_core.core.orchestration_semantics")


def _load_builder():
    _ensure_odoo_namespace()
    spec = spec_from_file_location("workspace_home_contract_builder_product_guard", HOME_BUILDER)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load workspace home builder")
    mod = module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _sample_data() -> dict[str, Any]:
    return {
        "role_surface": {"role_code": "pm"},
        "capabilities": [
            {"key": "project.dashboard.enter", "state": "READY", "ui_label": "进入项目驾驶舱", "default_payload": {"route": "/s/project.management"}},
            {"key": "contract.review", "state": "READY", "ui_label": "处理合同审批", "default_payload": {"route": "/s/contracts.list"}},
            {"key": "risk.review", "state": "READY", "ui_label": "处理风险事项", "default_payload": {"route": "/s/risk.center"}},
            {"key": "cost.track", "state": "READY", "ui_label": "查看成本执行", "default_payload": {"route": "/s/cost.project_boq"}},
        ],
        "scenes": [
            {"key": "project.management"},
            {"key": "contracts.list"},
            {"key": "risk.center"},
            {"key": "cost.project_boq"},
        ],
        "today_actions": [
            {"title": "待审批付款申请", "description": "有付款申请需要审批", "scene_key": "finance.payment", "route": "/s/finance.payment", "status": "urgent", "count": 2},
            {"title": "待处理合同异常", "description": "合同执行存在异常", "scene_key": "contracts.list", "route": "/s/contracts.list", "status": "urgent", "count": 1},
            {"title": "待跟进风险事项", "description": "风险事项需要分派", "scene_key": "risk.center", "route": "/s/risk.center", "status": "normal", "count": 3},
        ],
        "risk_actions": [
            {"title": "高风险项目需处理", "description": "进入风险中心处理", "scene_key": "risk.center", "route": "/s/risk.center", "status": "urgent", "count": 1},
        ],
    }


def _text(value: Any) -> str:
    return str(value or "").strip()


def _has_navigation(row: dict[str, Any]) -> bool:
    return bool(_text(row.get("route")) or _text(row.get("scene_key")) or int(row.get("action_id") or 0) > 0 or int(row.get("menu_id") or 0) > 0)


def _validate_contract(contract: dict[str, Any], errors: list[str]) -> None:
    protocol = contract.get("contract_protocol") if isinstance(contract.get("contract_protocol"), dict) else {}
    if protocol.get("primary") != "page_orchestration_v1":
        errors.append("contract_protocol.primary must be page_orchestration_v1")
    legacy = protocol.get("legacy") if isinstance(protocol.get("legacy"), dict) else {}
    if legacy.get("key") != "page_orchestration" or legacy.get("status") != "compatibility":
        errors.append("contract_protocol.legacy must declare page_orchestration compatibility")

    orchestration = contract.get("page_orchestration_v1") if isinstance(contract.get("page_orchestration_v1"), dict) else {}
    if orchestration.get("contract_version") != "page_orchestration_v1":
        errors.append("page_orchestration_v1.contract_version must be page_orchestration_v1")
    zones = orchestration.get("zones") if isinstance(orchestration.get("zones"), list) else []
    zone_keys = [_text(zone.get("key")) for zone in zones if isinstance(zone, dict)]
    if set(zone_keys) != set(MAIN_ZONE_KEYS):
        errors.append(f"main zones must be exactly {MAIN_ZONE_KEYS}, got {zone_keys}")
    priority = {
        _text(zone.get("key")): int(zone.get("priority") or 0)
        for zone in zones
        if isinstance(zone, dict)
    }
    if not priority:
        errors.append("page_orchestration_v1.zones must include prioritized main zones")
    elif priority.get("today_focus", 0) <= max(priority.get(key, 0) for key in priority if key != "today_focus"):
        errors.append("today_focus must have the highest first-screen priority")
    if priority and priority.get("hero", 999) >= priority.get("today_focus", 0):
        errors.append("hero must be lower priority than today_focus")

    today_actions = contract.get("today_actions") if isinstance(contract.get("today_actions"), list) else []
    if len(today_actions) < 3:
        errors.append("today_actions must contain at least 3 actionable business rows")
    for idx, row in enumerate(today_actions[:3]):
        if not isinstance(row, dict) or not _has_navigation(row):
            errors.append(f"today_actions[{idx}] must include scene/route/action/menu navigation")
        if _text(row.get("source")) != "business":
            errors.append(f"today_actions[{idx}] must prefer business source")
    risk = contract.get("risk") if isinstance(contract.get("risk"), dict) else {}
    risk_actions = risk.get("actions") if isinstance(risk.get("actions"), list) else []
    if not any(isinstance(row, dict) and _has_navigation(row) for row in risk_actions):
        errors.append("risk.actions must include at least one executable action")

    metrics = contract.get("metrics") if isinstance(contract.get("metrics"), list) else []
    platform_metrics = contract.get("platform_metrics") if isinstance(contract.get("platform_metrics"), list) else []
    if not platform_metrics:
        errors.append("platform_metrics must be present outside main business metrics")
    for row in metrics:
        if isinstance(row, dict) and _text(row.get("source")) == "platform":
            errors.append("business metrics must not include platform capability counts")


def _validate_frontend(errors: list[str]) -> None:
    text = HOME_VIEW.read_text(encoding="utf-8", errors="ignore")
    for term in DIAGNOSTIC_TERMS:
        if term in text:
            errors.append(f"HomeView user surface must not contain diagnostic term: {term}")
    required = ["<ContractRoleHome />", "components/role-home/ContractRoleHome.vue"]
    for token in required:
        if token not in text:
            errors.append(f"HomeView missing product surface token: {token}")


def main() -> int:
    if not HOME_BUILDER.is_file():
        return _fail([f"missing file: {HOME_BUILDER.relative_to(ROOT).as_posix()}"])
    if not HOME_VIEW.is_file():
        return _fail([f"missing file: {HOME_VIEW.relative_to(ROOT).as_posix()}"])
    try:
        builder = _load_builder()
        contract = builder.build_workspace_home_contract(_sample_data())
    except Exception as exc:
        return _fail([f"build workspace home contract failed: {exc}"])

    errors: list[str] = []
    if not isinstance(contract, dict):
        errors.append("builder output must be object")
    else:
        _validate_contract(contract, errors)
    _validate_frontend(errors)
    if errors:
        return _fail(errors)
    print("[workbench_product_acceptance_guard] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
