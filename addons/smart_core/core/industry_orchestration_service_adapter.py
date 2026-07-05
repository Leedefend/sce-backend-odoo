# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo.addons.smart_core.utils.extension_hooks import call_extension_hook_first


SOURCE_KIND = "industry_orchestration_adapter"
SOURCE_AUTHORITIES = (
    "smart_core.extension_hooks",
    "odoo.orm",
)
ADAPTER_LAYER = "industry_orchestration_adapter"
NO_BUSINESS_FACT_AUTHORITY = True


def source_authority_contract():
    return {
        "kind": SOURCE_KIND,
        "authorities": list(SOURCE_AUTHORITIES),
        "projection_only": True,
        "no_business_fact_authority": NO_BUSINESS_FACT_AUTHORITY,
        "adapter_layer": ADAPTER_LAYER,
        "runtime_carrier": "scene_runtime_service",
    }


def _require_service(hook_name: str, value):
    if value is None:
        raise RuntimeError(f"missing extension hook result: {hook_name}")
    return value


def _resolve_service_with_fallback(env, hook_name: str, fallback_builder_name: str):
    result = call_extension_hook_first(env, hook_name, env)
    if result is not None:
        return result
    return _require_service(hook_name, result)


class _FallbackCostTrackingService:
    SOURCE_KIND = "cost_tracking_missing_extension_degraded_projection"
    SOURCE_AUTHORITIES = ("extension_service_registry",)
    NO_BUSINESS_FACT_AUTHORITY = True

    def __init__(self, env):
        self.env = env

    @classmethod
    def source_authority_contract(cls):
        return {
            "kind": cls.SOURCE_KIND,
            "authorities": list(cls.SOURCE_AUTHORITIES),
            "projection_only": True,
            "no_business_fact_authority": cls.NO_BUSINESS_FACT_AUTHORITY,
            "degraded": True,
            "reason_code": "MISSING_EXTENSION_SERVICE",
            "runtime_carrier": "scene_entry_and_block_contract",
        }

    def resolve_project_with_diagnostics(self, project_id):
        pid = int(project_id or 0)
        project = {
            "id": pid,
            "name": "",
            "project_code": "",
        }
        return project, {"fallback": True, "reason": "MISSING_EXTENSION_SERVICE"}

    def project_payload(self, project):
        if isinstance(project, dict):
            return {
                "id": int(project.get("id") or 0),
                "name": str(project.get("name") or ""),
                "project_code": str(project.get("project_code") or ""),
                "manager_name": "",
                "stage_name": "",
                "cost_record_count": "",
                "cost_total_amount": "",
            }
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
            "message": "行业场景扩展服务未安装，已返回降级契约。",
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
