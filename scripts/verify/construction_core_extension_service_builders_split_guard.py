#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CORE_EXTENSION = ROOT / "addons/smart_construction_core/core_extension.py"
SERVICE_BUILDERS = ROOT / "addons/smart_construction_core/core_extension_service_builders.py"
CI = ROOT / "make/ci.mk"

MAX_CORE_EXTENSION_LINES = 2065
MAX_SERVICE_BUILDERS_LINES = 110


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore") if path.is_file() else ""


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _install_service_stubs() -> None:
    for name in [
        "odoo",
        "odoo.addons",
        "odoo.addons.smart_construction_core",
        "odoo.addons.smart_construction_core.services",
        "odoo.addons.smart_construction_core.services.insight",
        "odoo.addons.smart_construction_scene",
        "odoo.addons.smart_construction_scene.services",
    ]:
        sys.modules.setdefault(name, types.ModuleType(name))

    def install_class(module_name: str, class_name: str, methods: dict[str, object] | None = None) -> type:
        module = types.ModuleType(module_name)
        methods = dict(methods or {})

        def __init__(self, env=None):
            self.env = env

        attrs = {"__init__": __init__, **methods}
        cls = type(class_name, (), attrs)
        setattr(module, class_name, cls)
        sys.modules[module_name] = module
        return cls

    install_class("odoo.addons.smart_construction_scene.services.scene_package_service", "ScenePackageService")
    install_class("odoo.addons.smart_construction_scene.services.scene_governance_service", "SceneGovernanceService")
    install_class(
        "odoo.addons.smart_construction_core.services.lifecycle_capability_service",
        "LifecycleCapabilityService",
        {"describe_project": lambda self, project: {"project": project}},
    )
    install_class(
        "odoo.addons.smart_construction_core.services.portal_dashboard_service",
        "PortalDashboardService",
        {"build_dashboard": lambda self: {"dashboard": True}},
    )
    install_class(
        "odoo.addons.smart_construction_core.services.capability_matrix_service",
        "CapabilityMatrixService",
        {"build_matrix": lambda self: {"matrix": True}},
    )
    install_class(
        "odoo.addons.smart_construction_core.services.insight.project_insight_service",
        "ProjectInsightService",
        {"get_insight": lambda self, record, scene: {"record": record, "scene": scene}},
    )
    install_class(
        "odoo.addons.smart_construction_core.services.portal_execute_button_service",
        "PortalExecuteButtonService",
        {"build_contract": lambda self, model, res_id, method: {"model": model, "res_id": res_id, "method": method}},
    )
    for module_name, class_name in [
        ("odoo.addons.smart_construction_core.services.project_execution_service", "ProjectExecutionService"),
        ("odoo.addons.smart_construction_core.services.project_dashboard_service", "ProjectDashboardService"),
        ("odoo.addons.smart_construction_core.services.project_plan_bootstrap_service", "ProjectPlanBootstrapService"),
        ("odoo.addons.smart_construction_core.services.cost_tracking_service", "CostTrackingService"),
        ("odoo.addons.smart_construction_core.services.payment_slice_service", "PaymentSliceService"),
        ("odoo.addons.smart_construction_core.services.settlement_slice_service", "SettlementSliceService"),
    ]:
        install_class(module_name, class_name)


def main() -> int:
    errors: list[str] = []
    core_text = _read(CORE_EXTENSION)
    service_text = _read(SERVICE_BUILDERS)
    ci_text = _read(CI)

    if not core_text:
        errors.append(f"missing core extension file: {CORE_EXTENSION.relative_to(ROOT)}")
    if not service_text:
        errors.append(f"missing service builder module: {SERVICE_BUILDERS.relative_to(ROOT)}")

    if core_text:
        line_count = len(core_text.splitlines())
        if line_count > MAX_CORE_EXTENSION_LINES:
            errors.append(f"core_extension.py line budget exceeded: {line_count} > {MAX_CORE_EXTENSION_LINES}")
        for token in [
            "core_extension_service_builders as _service_builders",
            "return _service_builders.scene_package_service_class()",
            "return _service_builders.build_portal_dashboard(env)",
            "return _service_builders.build_project_execution_service(env)",
            "return _service_builders.build_settlement_slice_service(env)",
        ]:
            if token not in core_text:
                errors.append(f"core_extension.py missing service builder split token: {token}")

    if service_text:
        line_count = len(service_text.splitlines())
        if line_count > MAX_SERVICE_BUILDERS_LINES:
            errors.append(f"service builder module line budget exceeded: {line_count} > {MAX_SERVICE_BUILDERS_LINES}")
        for token in [
            "def scene_package_service_class(",
            "def scene_governance_service_class(",
            "def describe_project_capabilities(",
            "def build_portal_dashboard(",
            "def build_capability_matrix(",
            "def build_portal_execute_button_contract(",
            "def build_project_execution_service(",
            "def build_settlement_slice_service(",
            "PortalExecuteButtonService(env).build_contract(",
        ]:
            if token not in service_text:
                errors.append(f"service builder module missing token: {token}")
        for forbidden in ("env[", ".search(", ".write(", ".create(", ".unlink(", "registry[", "register_", "requests.", "commit("):
            if forbidden in service_text:
                errors.append(f"service builder module must not own ORM/registry side effects; forbidden token: {forbidden}")

    if "python3 scripts/verify/construction_core_extension_service_builders_split_guard.py" not in ci_text:
        errors.append("ci.local.quick must run construction_core_extension_service_builders_split_guard.py")

    if not errors:
        _install_service_stubs()
        builders = _load(SERVICE_BUILDERS, "construction_core_extension_service_builders_under_guard")
        if builders.scene_package_service_class().__name__ != "ScenePackageService":
            errors.append("service builders must preserve scene package service class hook")
        if builders.build_portal_dashboard({"env": True}) != {"dashboard": True}:
            errors.append("service builders must preserve portal dashboard builder")
        if builders.build_capability_matrix({"env": True}) != {"matrix": True}:
            errors.append("service builders must preserve capability matrix builder")
        if builders.get_project_insight({"env": True}, "record-1", "scene-1") != {"record": "record-1", "scene": "scene-1"}:
            errors.append("service builders must preserve project insight delegation")
        contract = builders.build_portal_execute_button_contract({"env": True}, "m", 7, "run")
        if contract != {"model": "m", "res_id": 7, "method": "run"}:
            errors.append("service builders must preserve execute button contract builder")
        if builders.build_settlement_slice_service({"env": True}).__class__.__name__ != "SettlementSliceService":
            errors.append("service builders must preserve settlement slice service builder")

    if errors:
        print("[construction_core_extension_service_builders_split_guard] FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("[construction_core_extension_service_builders_split_guard] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
