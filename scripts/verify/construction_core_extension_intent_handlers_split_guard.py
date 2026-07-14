#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CORE_EXTENSION = ROOT / "addons/smart_construction_core/core_extension.py"
INTENT_HANDLERS = ROOT / "addons/smart_construction_core/core_extension_intent_handlers.py"
CI = ROOT / "make/ci.mk"

MAX_CORE_EXTENSION_LINES = 2243
MAX_INTENT_HANDLER_LINES = 210

HANDLER_MODULES = {
    "odoo.addons.smart_construction_core.handlers.system_ping_construction": ["SystemPingConstructionHandler"],
    "odoo.addons.smart_construction_core.handlers.capability_describe": ["CapabilityDescribeHandler"],
    "odoo.addons.smart_construction_core.handlers.my_work_summary": ["MyWorkSummaryHandler"],
    "odoo.addons.smart_construction_core.handlers.my_work_complete": ["MyWorkCompleteHandler", "MyWorkCompleteBatchHandler"],
    "odoo.addons.smart_construction_core.handlers.telemetry_track": ["TelemetryTrackHandler"],
    "odoo.addons.smart_construction_core.handlers.capability_visibility_report": ["CapabilityVisibilityReportHandler"],
    "odoo.addons.smart_construction_core.handlers.approval_policy_configuration": [
        "ApprovalPolicyConfigGetHandler",
        "ApprovalPolicyConfigSetHandler",
        "ApprovalPolicyStepsSetHandler",
    ],
    "odoo.addons.smart_construction_core.handlers.payment_request_approval": [
        "PaymentRequestApproveHandler",
        "PaymentRequestDoneHandler",
        "PaymentRequestRejectHandler",
        "PaymentRequestSubmitHandler",
    ],
    "odoo.addons.smart_construction_core.handlers.payment_request_available_actions": ["PaymentRequestAvailableActionsHandler"],
    "odoo.addons.smart_construction_core.handlers.payment_request_execute": ["PaymentRequestExecuteHandler"],
    "odoo.addons.smart_construction_core.handlers.project_dashboard": ["ProjectDashboardHandler"],
    "odoo.addons.smart_construction_core.handlers.risk_action_execute": ["RiskActionExecuteHandler"],
    "odoo.addons.smart_construction_core.handlers.project_initiation_enter": ["ProjectInitiationEnterHandler"],
    "odoo.addons.smart_construction_core.handlers.project_dashboard_open": ["ProjectDashboardOpenHandler"],
    "odoo.addons.smart_construction_core.handlers.project_dashboard_enter": ["ProjectDashboardEnterHandler"],
    "odoo.addons.smart_construction_core.handlers.project_entry_context_resolve": ["ProjectEntryContextResolveHandler"],
    "odoo.addons.smart_construction_core.handlers.project_entry_context_options": ["ProjectEntryContextOptionsHandler"],
    "odoo.addons.smart_construction_core.handlers.business_evidence_trace": ["BusinessEvidenceTraceHandler"],
    "odoo.addons.smart_construction_core.handlers.project_dashboard_block_fetch": ["ProjectDashboardBlockFetchHandler"],
    "odoo.addons.smart_construction_core.handlers.project_plan_bootstrap_enter": ["ProjectPlanBootstrapEnterHandler"],
    "odoo.addons.smart_construction_core.handlers.project_plan_bootstrap_block_fetch": ["ProjectPlanBootstrapBlockFetchHandler"],
    "odoo.addons.smart_construction_core.handlers.project_execution_enter": ["ProjectExecutionEnterHandler"],
    "odoo.addons.smart_construction_core.handlers.project_execution_block_fetch": ["ProjectExecutionBlockFetchHandler"],
    "odoo.addons.smart_construction_core.handlers.project_execution_advance": ["ProjectExecutionAdvanceHandler"],
    "odoo.addons.smart_construction_core.handlers.project_connection_transition": ["ProjectConnectionTransitionHandler"],
    "odoo.addons.smart_construction_core.handlers.cost_tracking_enter": ["CostTrackingEnterHandler"],
    "odoo.addons.smart_construction_core.handlers.cost_tracking_block_fetch": ["CostTrackingBlockFetchHandler"],
    "odoo.addons.smart_construction_core.handlers.cost_tracking_record_create": ["CostTrackingRecordCreateHandler"],
    "odoo.addons.smart_construction_core.handlers.payment_slice_enter": ["PaymentSliceEnterHandler"],
    "odoo.addons.smart_construction_core.handlers.payment_slice_block_fetch": ["PaymentSliceBlockFetchHandler"],
    "odoo.addons.smart_construction_core.handlers.payment_slice_record_create": ["PaymentSliceRecordCreateHandler"],
    "odoo.addons.smart_construction_core.handlers.settlement_slice_enter": ["SettlementSliceEnterHandler"],
    "odoo.addons.smart_construction_core.handlers.settlement_slice_block_fetch": ["SettlementSliceBlockFetchHandler"],
    "odoo.addons.smart_construction_core.handlers.workspace_home_enter": ["WorkspaceHomeEnterHandler"],
    "odoo.addons.smart_construction_core.handlers.dashboard_company_enter": ["DashboardCompanyEnterHandler"],
}


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore") if path.is_file() else ""


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _install_stubs() -> None:
    for name in [
        "odoo",
        "odoo.addons",
        "odoo.addons.smart_core",
        "odoo.addons.smart_core.utils",
        "odoo.addons.smart_construction_core",
        "odoo.addons.smart_construction_core.handlers",
    ]:
        sys.modules.setdefault(name, types.ModuleType(name))
    boundary = types.ModuleType("odoo.addons.smart_core.utils.backend_contract_boundaries")
    boundary.APPROVAL_POLICY_INTENTS = {
        "config_get": "approval.policy.config.get",
        "config_set": "approval.policy.config.set",
        "steps_set": "approval.policy.steps.set",
    }
    sys.modules["odoo.addons.smart_core.utils.backend_contract_boundaries"] = boundary
    for module_name, class_names in HANDLER_MODULES.items():
        module = types.ModuleType(module_name)
        for class_name in class_names:
            setattr(module, class_name, type(class_name, (), {}))
        sys.modules[module_name] = module


def main() -> int:
    errors: list[str] = []
    core_text = _read(CORE_EXTENSION)
    handler_text = _read(INTENT_HANDLERS)
    ci_text = _read(CI)

    if not core_text:
        errors.append(f"missing core extension file: {CORE_EXTENSION.relative_to(ROOT)}")
    if not handler_text:
        errors.append(f"missing intent handler module: {INTENT_HANDLERS.relative_to(ROOT)}")

    if core_text:
        line_count = len(core_text.splitlines())
        if line_count > MAX_CORE_EXTENSION_LINES:
            errors.append(f"core_extension.py line budget exceeded: {line_count} > {MAX_CORE_EXTENSION_LINES}")
        for token in [
            "core_extension_intent_handlers as _intent_handlers",
            "return _intent_handlers.get_intent_handler_contributions()",
            "def smart_core_register(registry):",
            "registry[intent_name] = handler",
        ]:
            if token not in core_text:
                errors.append(f"core_extension.py missing intent handler split token: {token}")
        if "APPROVAL_POLICY_INTENTS" in core_text:
            errors.append("core_extension.py should not keep approval policy intent constants after handler extraction")

    if handler_text:
        line_count = len(handler_text.splitlines())
        if line_count > MAX_INTENT_HANDLER_LINES:
            errors.append(f"intent handler module line budget exceeded: {line_count} > {MAX_INTENT_HANDLER_LINES}")
        for token in [
            "def get_intent_handler_contributions(",
            "APPROVAL_POLICY_INTENTS[\"config_get\"]",
            "\"project.entry.context.options\"",
            "\"cost.tracking.record.create\"",
            "\"workspace.home.enter\"",
            "\"source_module\": \"smart_construction_core\"",
            "\"domain\": \"construction\"",
        ]:
            if token not in handler_text:
                errors.append(f"intent handler module missing token: {token}")
        for forbidden in ("env[", ".search(", ".write(", ".create(", ".unlink(", "registry[", "register_", "requests.", "commit("):
            if forbidden in handler_text:
                errors.append(f"intent handler module must not own env/registry side effects; forbidden token: {forbidden}")

    if "python3 scripts/verify/construction_core_extension_intent_handlers_split_guard.py" not in ci_text:
        errors.append("ci.local.quick must run construction_core_extension_intent_handlers_split_guard.py")

    if not errors:
        _install_stubs()
        handlers = _load(INTENT_HANDLERS, "construction_core_extension_intent_handlers_under_guard")
        contributions = handlers.get_intent_handler_contributions()
        by_intent = {row.get("intent"): row for row in contributions if isinstance(row, dict)}
        for intent in [
            "system.ping.construction",
            "approval.policy.config.get",
            "approval.policy.config.set",
            "approval.policy.steps.set",
            "project.entry.context.options",
            "cost.tracking.record.create",
            "workspace.home.enter",
        ]:
            if intent not in by_intent:
                errors.append(f"intent handler mapping missing intent: {intent}")
        if not all(row.get("source_module") == "smart_construction_core" for row in by_intent.values()):
            errors.append("intent handler contributions must preserve source_module")
        if not all(row.get("domain") == "construction" for row in by_intent.values()):
            errors.append("intent handler contributions must preserve construction domain")
        if not all(row.get("handler") is not None for row in by_intent.values()):
            errors.append("intent handler contributions must skip missing handlers")

    if errors:
        print("[construction_core_extension_intent_handlers_split_guard] FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("[construction_core_extension_intent_handlers_split_guard] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
