# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo.addons.smart_core.core.extension_loader import call_extension_hook_first


def _require_service(hook_name: str, value):
    if value is None:
        raise RuntimeError(f"missing extension hook result: {hook_name}")
    return value


def build_project_execution_service(env):
    result = call_extension_hook_first(
        env,
        "smart_core_build_project_execution_service",
        env,
    )
    return _require_service("smart_core_build_project_execution_service", result)


def build_project_dashboard_service(env):
    result = call_extension_hook_first(
        env,
        "smart_core_build_project_dashboard_service",
        env,
    )
    return _require_service("smart_core_build_project_dashboard_service", result)


def build_project_plan_bootstrap_service(env):
    result = call_extension_hook_first(
        env,
        "smart_core_build_project_plan_bootstrap_service",
        env,
    )
    return _require_service("smart_core_build_project_plan_bootstrap_service", result)


def build_cost_tracking_service(env):
    result = call_extension_hook_first(
        env,
        "smart_core_build_cost_tracking_service",
        env,
    )
    return _require_service("smart_core_build_cost_tracking_service", result)


def build_payment_slice_service(env):
    result = call_extension_hook_first(
        env,
        "smart_core_build_payment_slice_service",
        env,
    )
    return _require_service("smart_core_build_payment_slice_service", result)


def build_settlement_slice_service(env):
    result = call_extension_hook_first(
        env,
        "smart_core_build_settlement_slice_service",
        env,
    )
    return _require_service("smart_core_build_settlement_slice_service", result)
