# -*- coding: utf-8 -*-
from __future__ import annotations

import importlib

from odoo.addons.smart_core.utils.extension_hooks import call_extension_hook_first


def _require_service(hook_name: str, value):
    if value is None:
        raise RuntimeError(f"missing extension hook result: {hook_name}")
    return value


def _resolve_service_with_fallback(env, hook_name: str, fallback_builder_name: str):
    result = call_extension_hook_first(env, hook_name, env)
    if result is not None:
        return result
    try:
        module = importlib.import_module("odoo.addons.smart_construction_core.core_extension")
        fallback_builder = getattr(module, fallback_builder_name, None)
        if callable(fallback_builder):
            result = fallback_builder(env)
    except Exception:
        result = None
    return _require_service(hook_name, result)


class _FallbackCostTrackingService:
    def __init__(self, env):
        self.env = env

    def resolve_project_with_diagnostics(self, project_id):
        pid = int(project_id or 0)
        project = self.env["project.project"].sudo().browse(pid).exists() if pid > 0 else self.env["project.project"]
        return project, {"fallback": True, "reason": "MISSING_EXTENSION_SERVICE"}

    def project_payload(self, project):
        return {
            "id": int(getattr(project, "id", 0) or 0),
            "name": str(getattr(project, "name", "") or ""),
            "project_code": str(getattr(project, "project_code", "") or ""),
            "manager_name": "",
            "stage_name": "",
            "cost_record_count": "",
            "cost_total_amount": "",
        }

    def build_block(self, block_key, project=None, context=None):
        return self.error_block(block_key, "MISSING_EXTENSION_SERVICE")

    def error_block(self, block_key, reason_code):
        return {
            "key": str(block_key or ""),
            "state": "degraded",
            "reason_code": str(reason_code or "UNKNOWN"),
            "message": "成本场景扩展服务未安装，已返回降级契约。",
        }

    def build_summary_rows(self, project):
        return []


def build_project_execution_service(env):
    return _resolve_service_with_fallback(
        env,
        "smart_core_build_project_execution_service",
        "smart_core_build_project_execution_service",
    )


def build_project_dashboard_service(env):
    return _resolve_service_with_fallback(
        env,
        "smart_core_build_project_dashboard_service",
        "smart_core_build_project_dashboard_service",
    )


def build_project_plan_bootstrap_service(env):
    return _resolve_service_with_fallback(
        env,
        "smart_core_build_project_plan_bootstrap_service",
        "smart_core_build_project_plan_bootstrap_service",
    )


def build_cost_tracking_service(env):
    hook_name = "smart_core_build_cost_tracking_service"
    result = call_extension_hook_first(env, hook_name, env)
    if result is not None:
        return result
    try:
        module = importlib.import_module("odoo.addons.smart_construction_core.core_extension")
        fallback_builder = getattr(module, hook_name, None)
        if callable(fallback_builder):
            result = fallback_builder(env)
    except Exception:
        result = None
    return result if result is not None else _FallbackCostTrackingService(env)


def build_payment_slice_service(env):
    return _resolve_service_with_fallback(
        env,
        "smart_core_build_payment_slice_service",
        "smart_core_build_payment_slice_service",
    )


def build_settlement_slice_service(env):
    return _resolve_service_with_fallback(
        env,
        "smart_core_build_settlement_slice_service",
        "smart_core_build_settlement_slice_service",
    )
