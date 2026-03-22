# -*- coding: utf-8 -*-
import logging
from typing import Any, Dict, List

from odoo.exceptions import AccessError

_logger = logging.getLogger(__name__)


ROLE_SURFACE_OVERRIDES = {
    "owner": {
        "landing_scene_candidates": ["projects.list", "project.initiation", "projects.intake"],
        "menu_xmlids": [
            "smart_construction_core.menu_sc_project_center",
            "smart_construction_core.menu_sc_contract_center",
        ],
    },
    "pm": {
        "landing_scene_candidates": ["portal.dashboard", "projects.ledger", "projects.list", "project.initiation", "projects.intake"],
        "menu_xmlids": [
            "smart_construction_core.menu_sc_project_center",
            "smart_construction_core.menu_sc_contract_center",
            "smart_construction_core.menu_sc_cost_center",
        ],
        "menu_blocklist_xmlids": ["smart_construction_core.menu_sc_project_manage"],
    },
    "finance": {
        "landing_scene_candidates": ["finance.payment_requests", "projects.ledger", "projects.list"],
        "menu_xmlids": [
            "smart_construction_core.menu_sc_finance_center",
            "smart_construction_core.menu_sc_settlement_center",
            "smart_construction_core.menu_payment_request",
        ],
    },
    "executive": {
        "landing_scene_candidates": ["portal.dashboard", "project.management", "projects.list", "projects.ledger", "project.initiation", "projects.intake"],
        "menu_xmlids": [
            "smart_construction_core.menu_sc_root",
            "smart_construction_core.menu_sc_projection_root",
            "smart_construction_core.menu_sc_project_center",
        ],
    },
}

ROLE_GROUPS_EXPLICIT = {
    "executive": {
        "smart_construction_custom.group_sc_role_executive",
        "smart_construction_core.group_sc_super_admin",
        "smart_construction_core.group_sc_cap_config_admin",
        "base.group_system",
    },
    "pm": {
        "smart_construction_custom.group_sc_role_pm",
        "smart_construction_custom.group_sc_role_project_manager",
        "smart_construction_custom.group_sc_role_project_user",
        "smart_construction_core.group_sc_role_project_manager",
    },
    "finance": {
        "smart_construction_custom.group_sc_role_finance",
        "smart_construction_custom.group_sc_role_payment_manager",
        "smart_construction_custom.group_sc_role_payment_user",
        "smart_construction_custom.group_sc_role_payment_read",
        "smart_construction_core.group_sc_role_finance_manager",
        "smart_construction_core.group_sc_role_finance_user",
    },
}

ROLE_GROUPS_CAPABILITY_FALLBACK = {
    "pm": {
        "smart_construction_core.group_sc_cap_project_manager",
        "smart_construction_core.group_sc_cap_project_user",
    },
    "finance": {
        "smart_construction_core.group_sc_cap_finance_user",
        "smart_construction_core.group_sc_cap_finance_manager",
    },
}

ROLE_PRECEDENCE = ("executive", "pm", "finance")

NAV_MENU_SCENE_MAP = {
    "smart_construction_demo.menu_sc_project_list_showcase": "projects.list",
    "smart_construction_core.menu_sc_project_initiation": "project.initiation",
    "smart_construction_core.menu_sc_project_project": "projects.ledger",
    "smart_construction_core.menu_sc_project_management_scene": "project.management",
    "smart_construction_core.menu_sc_project_cost_code": "config.project_cost_code",
    "smart_construction_core.menu_sc_root": "projects.list",
    "smart_construction_core.menu_sc_project_dashboard": "project.dashboard",
    "smart_construction_demo.menu_sc_project_dashboard_showcase": "projects.dashboard_showcase",
    "smart_construction_core.menu_sc_dictionary": "data.dictionary",
    "smart_construction_core.menu_payment_request": "finance.payment_requests",
    "smart_construction_portal.menu_sc_portal_lifecycle": "portal.lifecycle",
    "smart_construction_portal.menu_sc_portal_capability_matrix": "portal.capability_matrix",
    "smart_construction_portal.menu_sc_portal_dashboard": "portal.dashboard",
}

NAV_ACTION_SCENE_MAP = {
    "smart_construction_demo.action_sc_project_list_showcase": "projects.list",
    "smart_construction_core.action_project_initiation": "project.initiation",
    "smart_construction_core.action_sc_project_kanban_lifecycle": "projects.ledger",
    "smart_construction_core.action_sc_project_list": "projects.list",
    "smart_construction_core.action_project_dashboard": "project.dashboard",
    "smart_construction_demo.action_project_dashboard_showcase": "projects.dashboard_showcase",
    "smart_construction_core.action_project_dictionary": "data.dictionary",
    "smart_construction_core.action_project_cost_code": "config.project_cost_code",
    "smart_construction_core.action_payment_request": "finance.payment_requests",
    "smart_construction_core.action_payment_request_my": "finance.payment_requests",
    "smart_construction_portal.action_sc_portal_lifecycle": "portal.lifecycle",
    "smart_construction_portal.action_sc_portal_capability_matrix": "portal.capability_matrix",
    "smart_construction_portal.action_sc_portal_dashboard": "portal.dashboard",
}

NAV_MODEL_VIEW_SCENE_MAP = {
    ("project.project", "list"): "projects.list",
    ("project.project", "form"): "projects.intake",
    ("payment.request", "list"): "finance.payment_requests",
    ("payment.request", "form"): "finance.payment_requests",
}

SERVER_ACTION_WINDOW_MAP = {
    "smart_construction_core.action_exec_structure_entry": "smart_construction_core.action_exec_structure_wbs",
}

FILE_UPLOAD_ALLOWED_MODELS = ["project.project", "project.task"]
FILE_DOWNLOAD_ALLOWED_MODELS = ["project.project", "project.task"]
API_DATA_WRITE_ALLOWLIST = {
    "project.project": ["name", "description", "date_start"],
    "project.task": ["name", "description", "date_deadline", "project_id"],
}
API_DATA_UNLINK_ALLOWED_MODELS = ["project.task"]

MODEL_CODE_MAPPING = {
    "project": "project.project",
    "task": "project.task",
}

CREATE_FIELD_FALLBACKS = {
    "project.project": {
        "selection_defaults": {
            "privacy_visibility": "followers",
            "rating_status": "stage",
            "last_update_status": "to_define",
            "rating_status_period": "monthly",
        }
    }
}

SURFACE_NAV_ALLOWLIST = {
    "construction_pm_v1": [
        "project.management",
        "project.dashboard",
        "projects.dashboard",
        "projects.ledger",
        "project.initiation",
        "projects.intake",
        "my_work.workspace",
    ]
}
SURFACE_DEEP_LINK_ALLOWLIST = {
    "construction_pm_v1": [
        "contract.center",
        "cost.budget_alloc",
        "cost.cost_compare",
        "cost.profit_compare",
        "cost.project_boq",
        "cost.project_budget",
        "cost.project_cost_ledger",
        "cost.project_progress",
        "data.dictionary",
        "finance.center",
        "finance.operating_metrics",
        "finance.payment_ledger",
        "finance.payment_requests",
        "finance.settlement_orders",
        "finance.treasury_ledger",
        "config.project_cost_code",
        "risk.monitor",
        "task.center",
    ]
}
SURFACE_POLICY_DEFAULT_NAME = "construction_pm_v1"
SURFACE_POLICY_DEFAULT_FILE = "docs/product/delivery/v1/construction_pm_v1_scene_surface_policy.json"

CRITICAL_SCENE_TARGET_OVERRIDES = {
    "projects.list",
    "projects.detail",
    "projects.intake",
    "projects.ledger",
    "projects.execution",
    "projects.dashboard",
    "project.management",
    "my_work.workspace",
    "portal.dashboard",
    "finance.payment_requests",
}

CRITICAL_SCENE_TARGET_ROUTE_OVERRIDES = {
    "my_work.workspace": "/my-work",
}


def _as_text(value: Any) -> str:
    if isinstance(value, dict):
        for key in ("zh_CN", "en_US"):
            text = str(value.get(key) or "").strip()
            if text:
                return text
        return ""
    return str(value or "").strip()


def _safe_search_read(env, model_name: str, domain: List[Any], fields: List[str], limit: int = 6) -> List[Dict[str, Any]]:
    if model_name not in env:
        return []
    model = env[model_name]
    try:
        return model.search_read(domain, fields=fields, limit=limit, order="write_date desc, id desc")
    except AccessError:
        return []
    except Exception as exc:
        _logger.warning("[smart_core_extend_system_init] search_read failed model=%s error=%s", model_name, exc)
        return []


def _model_has_field(env, model_name: str, field_name: str) -> bool:
    if model_name not in env:
        return False
    return field_name in env[model_name]._fields


def _build_task_action_rows(env, user) -> List[Dict[str, Any]]:
    user_domain = ["|", ("user_id", "=", user.id), ("user_ids", "in", [user.id])]
    rows = _safe_search_read(
        env,
        "project.task",
        domain=[("sc_state", "in", ["draft", "ready", "in_progress"])] + user_domain,
        fields=["id", "name", "project_id", "sc_state", "date_deadline", "user_id", "write_date"],
        limit=6,
    )
    if not rows:
        rows = _safe_search_read(
            env,
            "project.task",
            domain=[("sc_state", "in", ["draft", "ready", "in_progress"])],
            fields=["id", "name", "project_id", "sc_state", "date_deadline", "user_id", "write_date"],
            limit=6,
        )
    if not rows and _model_has_field(env, "project.task", "kanban_state"):
        rows = _safe_search_read(
            env,
            "project.task",
            domain=[("kanban_state", "in", ["normal", "blocked"])] + user_domain,
            fields=["id", "name", "project_id", "kanban_state", "date_deadline", "user_id", "write_date"],
            limit=6,
        )
    if not rows and _model_has_field(env, "project.task", "kanban_state"):
        rows = _safe_search_read(
            env,
            "project.task",
            domain=[("kanban_state", "in", ["normal", "blocked"])],
            fields=["id", "name", "project_id", "kanban_state", "date_deadline", "user_id", "write_date"],
            limit=6,
        )
    result: List[Dict[str, Any]] = []
    for row in rows:
        task_name = _as_text(row.get("name")) or "待办任务"
        state = _as_text(row.get("sc_state") or row.get("kanban_state"))
        status = "urgent" if state == "in_progress" else "normal"
        project_name = ""
        project_raw = row.get("project_id")
        if isinstance(project_raw, list) and len(project_raw) > 1:
            project_name = _as_text(project_raw[1])
        result.append(
            {
                "id": f"task-{row.get('id')}",
                "title": task_name,
                "description": f"项目任务待处理：{project_name}" if project_name else "项目任务待处理",
                "status": status,
                "scene_key": "task.center",
                "route": "/s/task.center",
                "count": 1,
                "source_detail": "factual_record",
                "due_date": row.get("date_deadline"),
            }
        )
    return result


def _build_payment_action_rows(env) -> List[Dict[str, Any]]:
    rows = _safe_search_read(
        env,
        "payment.request",
        domain=[("state", "in", ["draft", "submit", "approve", "approved"])],
        fields=["id", "name", "project_id", "state", "amount", "date_request", "write_date"],
        limit=6,
    )
    result: List[Dict[str, Any]] = []
    for row in rows:
        req_name = _as_text(row.get("name")) or "付款申请"
        amount = row.get("amount") or 0
        project_name = ""
        project_raw = row.get("project_id")
        if isinstance(project_raw, list) and len(project_raw) > 1:
            project_name = _as_text(project_raw[1])
        result.append(
            {
                "id": f"payment-{row.get('id')}",
                "title": f"付款申请待审批 · {req_name}",
                "description": f"{project_name} 申请金额 {amount}" if project_name else f"申请金额 {amount}",
                "status": "urgent",
                "scene_key": "finance.payment_requests",
                "route": "/s/finance.payment_requests",
                "amount": amount,
                "count": 1,
                "source_detail": "factual_record",
                "deadline": row.get("date_request"),
            }
        )
    return result


def _build_risk_action_rows(env) -> List[Dict[str, Any]]:
    actionable_rows = _safe_search_read(
        env,
        "project.risk.action",
        domain=[("state", "in", ["open", "claimed", "escalated"])],
        fields=["id", "name", "state", "risk_level", "project_id", "write_date"],
        limit=6,
    )
    if actionable_rows:
        result: List[Dict[str, Any]] = []
        for row in actionable_rows:
            state = _as_text(row.get("state")).lower()
            status = "urgent" if state in {"open", "escalated"} else "normal"
            title = _as_text(row.get("name")) or "风险事项"
            project_name = ""
            project_raw = row.get("project_id")
            if isinstance(project_raw, list) and len(project_raw) > 1:
                project_name = _as_text(project_raw[1])
            result.append(
                {
                    "id": f"risk-action-{row.get('id')}",
                    "title": f"风险处置 · {title}",
                    "description": f"{project_name} 风险状态：{state}" if project_name else f"风险状态：{state}",
                    "status": status,
                    "scene_key": "risk.center",
                    "route": "/s/risk.center",
                    "count": 1,
                    "risk_action_id": int(row.get("id") or 0),
                    "source_detail": "mutation_record",
                }
            )
        return result

    rows = _safe_search_read(
        env,
        "project.risk",
        domain=[],
        fields=["id", "name", "health_state", "write_date"],
        limit=6,
    )
    if not rows:
        rows = _safe_search_read(
            env,
            "project.project",
            domain=[("health_state", "in", ["risk", "warn"])],
            fields=["id", "name", "health_state", "write_date"],
            limit=6,
        )
    result: List[Dict[str, Any]] = []
    for row in rows:
        health = _as_text(row.get("health_state"))
        status = "urgent" if health == "risk" else "normal"
        title = _as_text(row.get("name")) or "风险事项"
        result.append(
            {
                "id": f"risk-{row.get('id')}",
                "title": f"项目风险预警 · {title}",
                "description": "项目健康状态异常，请优先跟进。",
                "status": status,
                "scene_key": "risk.center",
                "route": "/s/risk.center",
                "count": 1,
                "project_id": int(row.get("id") or 0),
                "name": title,
                "source_detail": "factual_record",
            }
        )
    return result


def _build_project_action_rows(env, user) -> List[Dict[str, Any]]:
    rows = _safe_search_read(
        env,
        "project.project",
        domain=[("active", "=", True)],
        fields=["id", "name", "health_state", "lifecycle_state", "write_date", "user_id", "manager_id"],
        limit=6,
    )
    result: List[Dict[str, Any]] = []
    for row in rows:
        health = _as_text(row.get("health_state"))
        lifecycle = _as_text(row.get("lifecycle_state"))
        title = _as_text(row.get("name")) or "项目事项"
        if health in {"risk", "warn"} or lifecycle in {"draft", "in_progress"}:
            status = "urgent" if health == "risk" else "normal"
            result.append(
                {
                    "id": f"project-{row.get('id')}",
                    "title": f"项目跟进 · {title}",
                    "description": "项目状态需要关注，请进入项目管理跟进。",
                    "status": status,
                    "scene_key": "project.management",
                    "route": "/s/project.management",
                    "count": 1,
                    "source_detail": "factual_record",
                }
            )
    return result


def smart_core_register(registry):
    """
    Register construction demo intent into smart_core registry.
    """
    try:
        from odoo.addons.smart_construction_core.handlers.system_ping_construction import (
            SystemPingConstructionHandler,
        )
        from odoo.addons.smart_construction_core.handlers.capability_describe import (
            CapabilityDescribeHandler,
        )
        from odoo.addons.smart_construction_core.handlers.my_work_summary import (
            MyWorkSummaryHandler,
        )
        from odoo.addons.smart_construction_core.handlers.my_work_complete import (
            MyWorkCompleteHandler,
            MyWorkCompleteBatchHandler,
        )
        from odoo.addons.smart_construction_core.handlers.usage_track import (
            UsageTrackHandler,
        )
        from odoo.addons.smart_construction_core.handlers.telemetry_track import (
            TelemetryTrackHandler,
        )
        from odoo.addons.smart_construction_core.handlers.usage_report import (
            UsageReportHandler,
        )
        from odoo.addons.smart_construction_core.handlers.usage_export_csv import (
            UsageExportCsvHandler,
        )
        from odoo.addons.smart_construction_core.handlers.capability_visibility_report import (
            CapabilityVisibilityReportHandler,
        )
        from odoo.addons.smart_construction_core.handlers.payment_request_approval import (
            PaymentRequestApproveHandler,
            PaymentRequestDoneHandler,
            PaymentRequestRejectHandler,
            PaymentRequestSubmitHandler,
        )
        from odoo.addons.smart_construction_core.handlers.payment_request_available_actions import (
            PaymentRequestAvailableActionsHandler,
        )
        from odoo.addons.smart_construction_core.handlers.payment_request_execute import (
            PaymentRequestExecuteHandler,
        )
        from odoo.addons.smart_construction_core.handlers.project_dashboard import (
            ProjectDashboardHandler,
        )
        from odoo.addons.smart_construction_core.handlers.risk_action_execute import (
            RiskActionExecuteHandler,
        )
        from odoo.addons.smart_construction_core.handlers.project_initiation_enter import (
            ProjectInitiationEnterHandler,
        )
        from odoo.addons.smart_construction_core.handlers.project_dashboard_open import (
            ProjectDashboardOpenHandler,
        )
        from odoo.addons.smart_construction_core.handlers.project_dashboard_enter import (
            ProjectDashboardEnterHandler,
        )
        from odoo.addons.smart_construction_core.handlers.project_dashboard_block_fetch import (
            ProjectDashboardBlockFetchHandler,
        )
        from odoo.addons.smart_construction_core.handlers.project_plan_bootstrap_enter import (
            ProjectPlanBootstrapEnterHandler,
        )
        from odoo.addons.smart_construction_core.handlers.project_plan_bootstrap_block_fetch import (
            ProjectPlanBootstrapBlockFetchHandler,
        )
        from odoo.addons.smart_construction_core.handlers.project_execution_enter import (
            ProjectExecutionEnterHandler,
        )
        from odoo.addons.smart_construction_core.handlers.project_execution_block_fetch import (
            ProjectExecutionBlockFetchHandler,
        )
        from odoo.addons.smart_construction_core.handlers.app_catalog import (
            AppCatalogHandler,
        )
        from odoo.addons.smart_construction_core.handlers.app_nav import (
            AppNavHandler,
        )
        from odoo.addons.smart_construction_core.handlers.app_open import (
            AppOpenHandler,
        )
    except Exception as e:
        _logger.warning("[smart_core_register] import handler failed: %s", e)
        return

    registry["system.ping.construction"] = SystemPingConstructionHandler
    registry["capability.describe"] = CapabilityDescribeHandler
    registry["my.work.summary"] = MyWorkSummaryHandler
    registry["my.work.complete"] = MyWorkCompleteHandler
    registry["my.work.complete_batch"] = MyWorkCompleteBatchHandler
    registry["usage.track"] = UsageTrackHandler
    registry["telemetry.track"] = TelemetryTrackHandler
    registry["usage.report"] = UsageReportHandler
    registry["usage.export.csv"] = UsageExportCsvHandler
    registry["capability.visibility.report"] = CapabilityVisibilityReportHandler
    registry["payment.request.submit"] = PaymentRequestSubmitHandler
    registry["payment.request.approve"] = PaymentRequestApproveHandler
    registry["payment.request.reject"] = PaymentRequestRejectHandler
    registry["payment.request.done"] = PaymentRequestDoneHandler
    registry["payment.request.available_actions"] = PaymentRequestAvailableActionsHandler
    registry["payment.request.execute"] = PaymentRequestExecuteHandler
    registry["project.dashboard"] = ProjectDashboardHandler
    registry["project.dashboard.open"] = ProjectDashboardOpenHandler
    registry["project.dashboard.enter"] = ProjectDashboardEnterHandler
    registry["project.dashboard.block.fetch"] = ProjectDashboardBlockFetchHandler
    registry["project.plan_bootstrap.enter"] = ProjectPlanBootstrapEnterHandler
    registry["project.plan_bootstrap.block.fetch"] = ProjectPlanBootstrapBlockFetchHandler
    registry["project.execution.enter"] = ProjectExecutionEnterHandler
    registry["project.execution.block.fetch"] = ProjectExecutionBlockFetchHandler
    registry["project.initiation.enter"] = ProjectInitiationEnterHandler
    registry["risk.action.execute"] = RiskActionExecuteHandler
    registry["app.catalog"] = AppCatalogHandler
    registry["app.nav"] = AppNavHandler
    registry["app.open"] = AppOpenHandler
    _logger.info("[smart_core_register] registered system.ping.construction")
    _logger.info("[smart_core_register] registered capability.describe")
    _logger.info("[smart_core_register] registered my.work.summary")
    _logger.info("[smart_core_register] registered my.work.complete")
    _logger.info("[smart_core_register] registered my.work.complete_batch")
    _logger.info("[smart_core_register] registered usage.track")
    _logger.info("[smart_core_register] registered telemetry.track")
    _logger.info("[smart_core_register] registered usage.report")
    _logger.info("[smart_core_register] registered usage.export.csv")
    _logger.info("[smart_core_register] registered capability.visibility.report")
    _logger.info("[smart_core_register] registered payment.request.submit")
    _logger.info("[smart_core_register] registered payment.request.approve")
    _logger.info("[smart_core_register] registered payment.request.reject")
    _logger.info("[smart_core_register] registered payment.request.done")
    _logger.info("[smart_core_register] registered payment.request.available_actions")
    _logger.info("[smart_core_register] registered payment.request.execute")
    _logger.info("[smart_core_register] registered project.dashboard")
    _logger.info("[smart_core_register] registered project.dashboard.open")
    _logger.info("[smart_core_register] registered project.dashboard.enter")
    _logger.info("[smart_core_register] registered project.dashboard.block.fetch")
    _logger.info("[smart_core_register] registered project.plan_bootstrap.enter")
    _logger.info("[smart_core_register] registered project.plan_bootstrap.block.fetch")
    _logger.info("[smart_core_register] registered project.execution.enter")
    _logger.info("[smart_core_register] registered project.execution.block.fetch")
    _logger.info("[smart_core_register] registered project.initiation.enter")
    _logger.info("[smart_core_register] registered risk.action.execute")
    _logger.info("[smart_core_register] registered app.catalog")
    _logger.info("[smart_core_register] registered app.nav")
    _logger.info("[smart_core_register] registered app.open")


def smart_core_identity_profile(env):
    del env
    return {
        "role_surface_map": ROLE_SURFACE_OVERRIDES,
        "role_groups_explicit": ROLE_GROUPS_EXPLICIT,
        "role_groups_capability_fallback": ROLE_GROUPS_CAPABILITY_FALLBACK,
        "role_precedence": ROLE_PRECEDENCE,
    }


def smart_core_list_capabilities_for_user(env, user):
    try:
        from odoo.addons.smart_construction_core.services.capability_registry import (
            list_capabilities_for_user as registry_list_capabilities_for_user,
        )
    except Exception:
        return None
    try:
        capabilities = registry_list_capabilities_for_user(env, user)
    except Exception:
        return None
    return capabilities if isinstance(capabilities, list) and capabilities else None


def smart_core_capability_groups(env):
    del env
    try:
        from odoo.addons.smart_construction_core.services.capability_registry import CAPABILITY_GROUPS
    except Exception:
        return None
    return [dict(item) for item in CAPABILITY_GROUPS if isinstance(item, dict)]


def smart_core_nav_scene_maps(env):
    del env
    return {
        "menu_scene_map": NAV_MENU_SCENE_MAP,
        "action_xmlid_scene_map": NAV_ACTION_SCENE_MAP,
        "model_view_scene_map": NAV_MODEL_VIEW_SCENE_MAP,
    }


def smart_core_scene_package_service_class(env):
    del env
    try:
        from odoo.addons.smart_construction_scene.services.scene_package_service import ScenePackageService
    except Exception:
        return None
    return ScenePackageService


def smart_core_scene_governance_service_class(env):
    del env
    try:
        from odoo.addons.smart_construction_scene.services.scene_governance_service import SceneGovernanceService
    except Exception:
        return None
    return SceneGovernanceService


def smart_core_load_scene_configs(env, *, drift=None):
    try:
        from odoo.addons.smart_construction_scene.scene_registry import load_scene_configs
    except Exception:
        return None
    try:
        return load_scene_configs(env, drift=drift)
    except Exception:
        return None


def smart_core_has_db_scenes(env):
    try:
        from odoo.addons.smart_construction_scene.scene_registry import has_db_scenes
    except Exception:
        return None
    try:
        return bool(has_db_scenes(env))
    except Exception:
        return None


def smart_core_get_scene_version(env):
    del env
    try:
        from odoo.addons.smart_construction_scene.scene_registry import get_scene_version
    except Exception:
        return None
    try:
        return get_scene_version()
    except Exception:
        return None


def smart_core_get_schema_version(env):
    del env
    try:
        from odoo.addons.smart_construction_scene.scene_registry import get_schema_version
    except Exception:
        return None
    try:
        return get_schema_version()
    except Exception:
        return None


def smart_core_server_action_window_map(env):
    del env
    return dict(SERVER_ACTION_WINDOW_MAP)


def smart_core_file_upload_allowed_models(env):
    del env
    return list(FILE_UPLOAD_ALLOWED_MODELS)


def smart_core_file_download_allowed_models(env):
    del env
    return list(FILE_DOWNLOAD_ALLOWED_MODELS)


def smart_core_api_data_write_allowlist(env):
    del env
    return {str(model): list(fields) for model, fields in API_DATA_WRITE_ALLOWLIST.items()}


def smart_core_api_data_unlink_allowed_models(env):
    del env
    return list(API_DATA_UNLINK_ALLOWED_MODELS)


def smart_core_model_code_mapping(env):
    del env
    return dict(MODEL_CODE_MAPPING)


def smart_core_create_field_fallbacks(env, model_name):
    del env
    return dict(CREATE_FIELD_FALLBACKS.get(str(model_name or ""), {}))


def smart_core_surface_nav_allowlist(env):
    del env
    return {str(surface): list(codes) for surface, codes in SURFACE_NAV_ALLOWLIST.items()}


def smart_core_surface_deep_link_allowlist(env):
    del env
    return {str(surface): list(codes) for surface, codes in SURFACE_DEEP_LINK_ALLOWLIST.items()}


def smart_core_surface_policy_default_name(env):
    del env
    return SURFACE_POLICY_DEFAULT_NAME


def smart_core_surface_policy_file_default(env):
    del env
    return SURFACE_POLICY_DEFAULT_FILE


def smart_core_critical_scene_target_overrides(env):
    del env
    return list(CRITICAL_SCENE_TARGET_OVERRIDES)


def smart_core_critical_scene_target_route_overrides(env):
    del env
    return dict(CRITICAL_SCENE_TARGET_ROUTE_OVERRIDES)


def smart_core_extend_system_init(data, env, user):
    """
    Enrich smart_core system.init response with construction facts only.
    Contract shape fields (e.g. scenes/capabilities) are owned by smart_core.
    """
    try:
        Entitlement = env.get("sc.entitlement")
        Usage = env.get("sc.usage.counter")
        ext_facts = data.get("ext_facts")
        if not isinstance(ext_facts, dict):
            ext_facts = {}
        module_facts = ext_facts.get("smart_construction_core")
        if not isinstance(module_facts, dict):
            module_facts = {}
        if Entitlement:
            module_facts["entitlements"] = Entitlement.get_payload(user)
        if Usage:
            module_facts["usage"] = Usage.get_usage_map(user.company_id)

        task_rows = _build_task_action_rows(env, user)
        payment_rows = _build_payment_action_rows(env)
        risk_rows = _build_risk_action_rows(env)
        project_rows = _build_project_action_rows(env, user)

        module_facts["workspace_collections"] = {
            "task_items": task_rows,
            "payment_requests": payment_rows,
            "risk_actions": risk_rows,
            "project_actions": project_rows,
        }

        module_facts["workspace_business_source"] = {
            "task_items": len(task_rows),
            "payment_requests": len(payment_rows),
            "risk_actions": len(risk_rows),
            "project_actions": len(project_rows),
        }

        module_facts["role_surface_override_provider"] = {
            "key": "smart_construction_core",
            "enabled": True,
            "priority": 100,
            "domain_key": "construction",
            "root_xmlids": ["smart_construction_core.menu_sc_root"],
            "scene_codes": ["portal.dashboard", "project.management", "projects.list", "projects.intake"],
            "role_surface_overrides": ROLE_SURFACE_OVERRIDES,
        }

        ext_facts["smart_construction_core"] = module_facts
        data["ext_facts"] = ext_facts
    except Exception as exc:
        _logger.warning("[smart_core_extend_system_init] failed: %s", exc)
