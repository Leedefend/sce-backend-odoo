# -*- coding: utf-8 -*-
import logging
from typing import Any, Dict, List

from odoo.exceptions import AccessError

_logger = logging.getLogger(__name__)


ROLE_SURFACE_OVERRIDES = {
    "owner": {
        "landing_scene_candidates": ["projects.list", "projects.intake"],
        "menu_xmlids": [
            "smart_construction_core.menu_sc_project_center",
            "smart_construction_core.menu_sc_contract_center",
        ],
    },
    "pm": {
        "landing_scene_candidates": ["portal.dashboard", "projects.ledger", "projects.list", "projects.intake"],
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
        "landing_scene_candidates": ["portal.dashboard", "project.management", "projects.list", "projects.ledger", "projects.intake"],
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
    "smart_construction_core.menu_sc_project_initiation": "projects.intake",
    "smart_construction_core.menu_sc_project_project": "projects.ledger",
    "smart_construction_core.menu_sc_project_management_scene": "project.management",
    "smart_construction_core.menu_sc_project_cost_code": "config.project_cost_code",
    "smart_construction_core.menu_sc_root": "projects.list",
    "smart_construction_core.menu_sc_project_dashboard": "projects.dashboard",
    "smart_construction_demo.menu_sc_project_dashboard_showcase": "projects.dashboard_showcase",
    "smart_construction_core.menu_sc_dictionary": "data.dictionary",
    "smart_construction_core.menu_payment_request": "finance.payment_requests",
    "smart_construction_portal.menu_sc_portal_lifecycle": "portal.lifecycle",
    "smart_construction_portal.menu_sc_portal_capability_matrix": "portal.capability_matrix",
    "smart_construction_portal.menu_sc_portal_dashboard": "portal.dashboard",
}

NAV_ACTION_SCENE_MAP = {
    "smart_construction_demo.action_sc_project_list_showcase": "projects.list",
    "smart_construction_core.action_project_initiation": "projects.intake",
    "smart_construction_core.action_sc_project_kanban_lifecycle": "projects.ledger",
    "smart_construction_core.action_sc_project_list": "projects.list",
    "smart_construction_core.action_project_dashboard": "projects.dashboard",
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


INDUSTRY_CREATE_FIELD_FALLBACKS = {
    "project.project": {
        "selection_defaults": {
            "privacy_visibility": "followers",
            "rating_status": "stage",
            "last_update_status": "to_define",
            "rating_status_period": "monthly",
        }
    }
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


def _step_status_label(status: str) -> str:
    key = str(status or "").strip().lower()
    if key == "active":
        return "进行中"
    if key in {"done", "completed"}:
        return "已完成"
    if key in {"pending", "todo", "planned"}:
        return "待开始"
    return "后端未提供步骤状态标签"


def _build_enterprise_enablement_contract(env, user) -> Dict[str, Any]:
    company = getattr(user, "company_id", None)
    company_id = int(getattr(company, "id", 0) or 0)
    company_name = str(getattr(company, "name", "") or "").strip()
    steps = [
        {
            "key": "enterprise_company",
            "label": "企业信息",
            "status": "active" if company_id else "pending",
            "status_label": _step_status_label("active" if company_id else "pending"),
            "entry_xmlid": "smart_enterprise_base.action_enterprise_company",
            "action_xmlid": "smart_enterprise_base.action_enterprise_company",
            "next_hint": "请先补齐企业基础信息。",
            "target": {"action_id": 0, "menu_id": 0, "route": ""},
        },
        {
            "key": "enterprise_department",
            "label": "组织结构",
            "status": "pending",
            "status_label": _step_status_label("pending"),
            "entry_xmlid": "smart_enterprise_base.action_enterprise_department",
            "action_xmlid": "smart_enterprise_base.action_enterprise_department",
            "next_hint": "请补齐部门与岗位结构。",
            "target": {"action_id": 0, "menu_id": 0, "route": ""},
        },
        {
            "key": "enterprise_user",
            "label": "用户设置",
            "status": "pending",
            "status_label": _step_status_label("pending"),
            "entry_xmlid": "smart_enterprise_base.action_enterprise_user",
            "action_xmlid": "smart_enterprise_base.action_enterprise_user",
            "next_hint": "请完成用户、角色和账号初始化。",
            "target": {"action_id": 0, "menu_id": 0, "route": ""},
        },
    ]
    return {
        "mainline": {
            "version": "v1",
            "phase": "sprint1" if company_id else "bootstrap",
            "theme": "enterprise_enablement",
            "entry_root_xmlid": "smart_enterprise_base.menu_enterprise_base_root",
            "current_company_id": company_id,
            "current_company_name": company_name,
            "primary_action": steps[0].get("target") or {},
            "steps": steps,
        }
    }


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
                    "count": 1,
                    "source_detail": "factual_record",
                }
            )
    return result


def smart_core_identity_profile(env):
    return {
        "role_surface_map": ROLE_SURFACE_OVERRIDES,
        "role_groups_explicit": ROLE_GROUPS_EXPLICIT,
        "role_groups_capability_fallback": ROLE_GROUPS_CAPABILITY_FALLBACK,
        "role_precedence": ROLE_PRECEDENCE,
    }


def smart_core_nav_scene_maps(env):
    return {
        "menu_scene_map": dict(NAV_MENU_SCENE_MAP),
        "action_xmlid_scene_map": dict(NAV_ACTION_SCENE_MAP),
        "model_view_scene_map": dict(NAV_MODEL_VIEW_SCENE_MAP),
    }


def smart_core_critical_scene_target_overrides(env):
    return set(CRITICAL_SCENE_TARGET_OVERRIDES)


def smart_core_critical_scene_target_route_overrides(env):
    return dict(CRITICAL_SCENE_TARGET_ROUTE_OVERRIDES)


def get_server_action_window_map_contributions(env):
    return dict(SERVER_ACTION_WINDOW_MAP)


def get_file_upload_allowed_model_contributions(env):
    return list(FILE_UPLOAD_ALLOWED_MODELS)


def get_file_download_allowed_model_contributions(env):
    return list(FILE_DOWNLOAD_ALLOWED_MODELS)


def get_api_data_write_allowlist_contributions(env):
    return {
        str(model_name): list(field_names)
        for model_name, field_names in API_DATA_WRITE_ALLOWLIST.items()
    }


def get_api_data_unlink_allowed_model_contributions(env):
    return list(API_DATA_UNLINK_ALLOWED_MODELS)


def get_model_code_mapping_contributions(env):
    return dict(MODEL_CODE_MAPPING)


def _build_role_entry_contract_rows(env) -> List[Dict[str, Any]]:
    rows = _safe_search_read(
        env,
        "sc.dictionary",
        domain=[("type", "=", "role_entry"), ("active", "=", True)],
        fields=["code", "name", "scope_type", "scope_ref", "value_json", "sequence"],
        limit=200,
    )
    grouped: Dict[str, List[Dict[str, Any]]] = {}
    for row in rows:
        scope_type = _as_text(row.get("scope_type")) or "global"
        scope_ref = _as_text(row.get("scope_ref"))
        role_code = ""
        if scope_type == "role":
            role_code = scope_ref
        elif scope_type in {"global", "company"}:
            role_code = "__global__"
        if not role_code:
            continue

        value_json = row.get("value_json") if isinstance(row.get("value_json"), dict) else {}
        entry_key = (
            _as_text(row.get("code"))
            or _as_text(value_json.get("entry_key"))
            or _as_text(row.get("name"))
        )
        if not entry_key:
            continue

        entry_type = _as_text(value_json.get("entry_type")) or "menu"
        is_enabled = value_json.get("is_enabled")
        if isinstance(is_enabled, bool):
            enabled = is_enabled
        else:
            enabled = True
        sequence = int(row.get("sequence") or 10)

        grouped.setdefault(role_code, []).append(
            {
                "entry_key": entry_key,
                "entry_type": entry_type,
                "is_enabled": enabled,
                "sequence": sequence,
            }
        )

    contract_rows: List[Dict[str, Any]] = []
    for role_code, entries in grouped.items():
        sorted_entries = sorted(
            entries,
            key=lambda item: (
                int(item.get("sequence") or 10),
                str(item.get("entry_key") or ""),
            ),
        )
        contract_rows.append(
            {
                "role_code": role_code,
                "entries": sorted_entries,
            }
        )

    return sorted(contract_rows, key=lambda item: str(item.get("role_code") or ""))


def _build_home_block_contract_rows(env) -> List[Dict[str, Any]]:
    rows = _safe_search_read(
        env,
        "sc.dictionary",
        domain=[("type", "=", "home_block"), ("active", "=", True)],
        fields=["code", "name", "scope_type", "scope_ref", "value_json", "sequence"],
        limit=200,
    )
    grouped: Dict[str, List[Dict[str, Any]]] = {}
    for row in rows:
        scope_type = _as_text(row.get("scope_type")) or "global"
        scope_ref = _as_text(row.get("scope_ref"))
        role_code = ""
        if scope_type == "role":
            role_code = scope_ref
        elif scope_type == "global":
            role_code = "__global__"
        if not role_code:
            continue

        value_json = row.get("value_json") if isinstance(row.get("value_json"), dict) else {}
        block_key = (
            _as_text(row.get("code"))
            or _as_text(value_json.get("block_key"))
            or _as_text(row.get("name"))
        )
        if not block_key:
            continue

        is_enabled = value_json.get("is_enabled")
        if isinstance(is_enabled, bool):
            enabled = is_enabled
        else:
            enabled = True
        if not enabled:
            continue

        sequence = int(row.get("sequence") or 10)
        grouped.setdefault(role_code, []).append(
            {
                "block_key": block_key,
                "sequence": sequence,
            }
        )

    contract_rows: List[Dict[str, Any]] = []
    for role_code, blocks in grouped.items():
        sorted_blocks = sorted(
            blocks,
            key=lambda item: (
                int(item.get("sequence") or 10),
                str(item.get("block_key") or ""),
            ),
        )
        contract_rows.append(
            {
                "role_code": role_code,
                "blocks": [str(item.get("block_key") or "") for item in sorted_blocks if str(item.get("block_key") or "")],
            }
        )

    return sorted(contract_rows, key=lambda item: str(item.get("role_code") or ""))


def get_intent_handler_contributions():
    """Return construction intent handler contributions for platform loader."""
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
        from odoo.addons.smart_construction_core.handlers.project_entry_context_resolve import (
            ProjectEntryContextResolveHandler,
        )
        from odoo.addons.smart_construction_core.handlers.project_entry_context_options import (
            ProjectEntryContextOptionsHandler,
        )
        from odoo.addons.smart_construction_core.handlers.business_evidence_trace import (
            BusinessEvidenceTraceHandler,
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
        from odoo.addons.smart_construction_core.handlers.project_execution_advance import (
            ProjectExecutionAdvanceHandler,
        )
        from odoo.addons.smart_construction_core.handlers.project_connection_transition import (
            ProjectConnectionTransitionHandler,
        )
        from odoo.addons.smart_construction_core.handlers.cost_tracking_enter import (
            CostTrackingEnterHandler,
        )
        from odoo.addons.smart_construction_core.handlers.cost_tracking_block_fetch import (
            CostTrackingBlockFetchHandler,
        )
        from odoo.addons.smart_construction_core.handlers.cost_tracking_record_create import (
            CostTrackingRecordCreateHandler,
        )
        from odoo.addons.smart_construction_core.handlers.payment_slice_enter import (
            PaymentSliceEnterHandler,
        )
        from odoo.addons.smart_construction_core.handlers.payment_slice_block_fetch import (
            PaymentSliceBlockFetchHandler,
        )
        from odoo.addons.smart_construction_core.handlers.payment_slice_record_create import (
            PaymentSliceRecordCreateHandler,
        )
        from odoo.addons.smart_construction_core.handlers.settlement_slice_enter import (
            SettlementSliceEnterHandler,
        )
        from odoo.addons.smart_construction_core.handlers.settlement_slice_block_fetch import (
            SettlementSliceBlockFetchHandler,
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
        _logger.warning("[get_intent_handler_contributions] import handler failed: %s", e)
        return []

    mapping = [
        ("system.ping.construction", SystemPingConstructionHandler),
        ("capability.describe", CapabilityDescribeHandler),
        ("my.work.summary", MyWorkSummaryHandler),
        ("my.work.complete", MyWorkCompleteHandler),
        ("my.work.complete_batch", MyWorkCompleteBatchHandler),
        ("usage.track", UsageTrackHandler),
        ("telemetry.track", TelemetryTrackHandler),
        ("usage.report", UsageReportHandler),
        ("usage.export.csv", UsageExportCsvHandler),
        ("capability.visibility.report", CapabilityVisibilityReportHandler),
        ("payment.request.submit", PaymentRequestSubmitHandler),
        ("payment.request.approve", PaymentRequestApproveHandler),
        ("payment.request.reject", PaymentRequestRejectHandler),
        ("payment.request.done", PaymentRequestDoneHandler),
        ("payment.request.available_actions", PaymentRequestAvailableActionsHandler),
        ("payment.request.execute", PaymentRequestExecuteHandler),
        ("project.dashboard", ProjectDashboardHandler),
        ("project.dashboard.open", ProjectDashboardOpenHandler),
        ("project.dashboard.enter", ProjectDashboardEnterHandler),
        ("project.entry.context.resolve", ProjectEntryContextResolveHandler),
        ("project.entry.context.options", ProjectEntryContextOptionsHandler),
        ("business.evidence.trace", BusinessEvidenceTraceHandler),
        ("project.dashboard.block.fetch", ProjectDashboardBlockFetchHandler),
        ("project.plan_bootstrap.enter", ProjectPlanBootstrapEnterHandler),
        ("project.plan_bootstrap.block.fetch", ProjectPlanBootstrapBlockFetchHandler),
        ("project.execution.enter", ProjectExecutionEnterHandler),
        ("project.execution.block.fetch", ProjectExecutionBlockFetchHandler),
        ("project.execution.advance", ProjectExecutionAdvanceHandler),
        ("project.connection.transition", ProjectConnectionTransitionHandler),
        ("cost.tracking.enter", CostTrackingEnterHandler),
        ("cost.tracking.block.fetch", CostTrackingBlockFetchHandler),
        ("cost.tracking.record.create", CostTrackingRecordCreateHandler),
        ("payment.enter", PaymentSliceEnterHandler),
        ("payment.block.fetch", PaymentSliceBlockFetchHandler),
        ("payment.record.create", PaymentSliceRecordCreateHandler),
        ("settlement.enter", SettlementSliceEnterHandler),
        ("settlement.block.fetch", SettlementSliceBlockFetchHandler),
        ("project.initiation.enter", ProjectInitiationEnterHandler),
        ("risk.action.execute", RiskActionExecuteHandler),
        ("app.catalog", AppCatalogHandler),
        ("app.nav", AppNavHandler),
        ("app.open", AppOpenHandler),
    ]
    return [
        {
            "intent": intent,
            "handler": handler,
            "source_module": "smart_construction_core",
            "domain": "construction",
            "status": "active",
        }
        for intent, handler in mapping
    ]


def get_capability_contributions(env, user):
    try:
        from odoo.addons.smart_construction_core.services.capability_registry import (
            list_capabilities_for_user as registry_list_capabilities_for_user,
        )
    except Exception:
        return []
    try:
        capabilities = registry_list_capabilities_for_user(env, user)
    except Exception:
        return []
    if not isinstance(capabilities, list) or not capabilities:
        return []

    out = []
    for row in capabilities:
        if not isinstance(row, dict):
            continue
        key = str(row.get("key") or "").strip()
        if not key:
            continue
        identity_name = str(row.get("name") or row.get("ui_label") or key).strip() or key
        group_key = str(row.get("group_key") or "others").strip() or "others"
        intent_name = str(row.get("intent") or "ui.contract").strip() or "ui.contract"
        entry_target = row.get("entry_target") if isinstance(row.get("entry_target"), dict) else {}
        entry_scene_key = str(entry_target.get("scene_key") or "").strip()
        item = {
            "key": key,
            "name": identity_name,
            "domain": str(key.split(".")[0] if "." in key else "construction").strip() or "construction",
            "type": "entry",
            "source_module": "smart_construction_core",
            "owner_module": "smart_core",
            "status": str(row.get("status") or "ga").strip().lower() or "ga",
            "group_key": group_key,
            "group_label": str(row.get("group_label") or "").strip(),
            "group_icon": str(row.get("group_icon") or "").strip(),
            "group_sequence": int(row.get("group_sequence") or 0),
            "ui_label": str(row.get("ui_label") or identity_name).strip(),
            "ui_hint": str(row.get("ui_hint") or "").strip(),
            "intent": intent_name,
            "required_roles": [str(x).strip() for x in (row.get("required_roles") or []) if str(x).strip()],
            "required_groups": [str(x).strip() for x in (row.get("required_groups") or []) if str(x).strip()],
            "entry_target": dict(entry_target),
            "sequence": int(row.get("sequence") or 0),
            "tags": list(row.get("tags") or []),
            "identity": {
                "key": key,
                "name": identity_name,
                "domain": str(key.split(".")[0] if "." in key else "construction").strip() or "construction",
                "type": "entry",
                "version": "v1",
            },
            "ownership": {
                "owner_module": "smart_core",
                "source_module": "smart_construction_core",
                "source_kind": "industry_contribution",
            },
            "ui": {
                "label": str(row.get("ui_label") or identity_name).strip(),
                "hint": str(row.get("ui_hint") or "").strip(),
                "group_key": group_key,
                "icon": str(row.get("group_icon") or "").strip(),
                "sequence": int(row.get("sequence") or 0),
                "tags": list(row.get("tags") or []),
            },
            "binding": {
                "scene": {
                    "entry_scene_key": entry_scene_key,
                    "target_mode": str(entry_target.get("target_mode") or "scene").strip() or "scene",
                },
                "intent": {
                    "primary_intent": intent_name,
                },
                "contract": {
                    "subject": "scene",
                    "contract_type": "entry_contract",
                    "contract_version": "v1",
                },
                "exposure": {
                    "group_key": group_key,
                },
            },
            "permission": {
                "required_roles": [str(x).strip() for x in (row.get("required_roles") or []) if str(x).strip()],
                "required_groups": [str(x).strip() for x in (row.get("required_groups") or []) if str(x).strip()],
                "access_mode": "execute",
                "data_scope": "user_env",
            },
            "release": {
                "tier": "standard",
                "slice": "",
                "exposure_mode": "default",
                "approval_required": False,
                "feature_flag": "",
            },
            "lifecycle": {
                "status": str(row.get("status") or "ga").strip().lower() or "ga",
                "deprecated": False,
                "replacement_key": "",
                "introduced_in": "",
                "sunset_after": "",
            },
            "runtime": {
                "supports_entry": True,
                "supports_execute": False,
                "supports_batch": False,
                "safe_fallback": "workspace.home",
            },
            "audit": {
                "audit_enabled": True,
                "policy_trace_enabled": True,
                "owner_trace": "smart_construction_core.get_capability_contributions",
            },
        }
        out.append(item)
    return out


def get_capability_contributions_with_timings(env, user):
    try:
        from odoo.addons.smart_construction_core.services.capability_registry import (
            list_capabilities_for_user_with_timings as registry_list_capabilities_for_user_with_timings,
        )
    except Exception:
        return [], {}
    try:
        capabilities, timings_ms = registry_list_capabilities_for_user_with_timings(env, user)
    except Exception:
        return [], {}
    if not isinstance(capabilities, list) or not capabilities:
        return [], timings_ms if isinstance(timings_ms, dict) else {}

    out = []
    for row in capabilities:
        if not isinstance(row, dict):
            continue
        key = str(row.get("key") or "").strip()
        if not key:
            continue
        identity_name = str(row.get("name") or row.get("ui_label") or key).strip() or key
        group_key = str(row.get("group_key") or "others").strip() or "others"
        intent_name = str(row.get("intent") or "ui.contract").strip() or "ui.contract"
        entry_target = row.get("entry_target") if isinstance(row.get("entry_target"), dict) else {}
        entry_scene_key = str(entry_target.get("scene_key") or "").strip()
        item = {
            "key": key,
            "name": identity_name,
            "domain": str(key.split(".")[0] if "." in key else "construction").strip() or "construction",
            "type": "entry",
            "source_module": "smart_construction_core",
            "owner_module": "smart_core",
            "status": str(row.get("status") or "ga").strip().lower() or "ga",
            "group_key": group_key,
            "group_label": str(row.get("group_label") or "").strip(),
            "group_icon": str(row.get("group_icon") or "").strip(),
            "group_sequence": int(row.get("group_sequence") or 0),
            "ui_label": str(row.get("ui_label") or identity_name).strip(),
            "ui_hint": str(row.get("ui_hint") or "").strip(),
            "intent": intent_name,
            "required_roles": [str(x).strip() for x in (row.get("required_roles") or []) if str(x).strip()],
            "required_groups": [str(x).strip() for x in (row.get("required_groups") or []) if str(x).strip()],
            "entry_target": dict(entry_target),
            "sequence": int(row.get("sequence") or 0),
            "tags": list(row.get("tags") or []),
            "identity": {
                "key": key,
                "name": identity_name,
                "domain": str(key.split(".")[0] if "." in key else "construction").strip() or "construction",
                "type": "entry",
                "version": "v1",
            },
            "ownership": {
                "owner_module": "smart_core",
                "source_module": "smart_construction_core",
                "source_kind": "industry_contribution",
            },
            "ui": {
                "label": str(row.get("ui_label") or identity_name).strip(),
                "hint": str(row.get("ui_hint") or "").strip(),
                "group_key": group_key,
                "icon": str(row.get("group_icon") or "").strip(),
                "sequence": int(row.get("sequence") or 0),
                "tags": list(row.get("tags") or []),
            },
            "binding": {
                "scene": {
                    "entry_scene_key": entry_scene_key,
                    "target_mode": str(entry_target.get("target_mode") or "scene").strip() or "scene",
                },
                "intent": {
                    "primary_intent": intent_name,
                },
                "contract": {
                    "subject": "scene",
                    "contract_type": "entry_contract",
                    "contract_version": "v1",
                },
                "exposure": {
                    "group_key": group_key,
                },
            },
            "permission": {
                "required_roles": [str(x).strip() for x in (row.get("required_roles") or []) if str(x).strip()],
                "required_groups": [str(x).strip() for x in (row.get("required_groups") or []) if str(x).strip()],
                "access_mode": "execute",
                "data_scope": "user_env",
            },
            "release": {
                "tier": "standard",
                "slice": "",
                "exposure_mode": "default",
                "approval_required": False,
                "feature_flag": "",
            },
            "lifecycle": {
                "status": str(row.get("status") or "ga").strip().lower() or "ga",
                "deprecated": False,
                "replacement_key": "",
                "introduced_in": "",
                "sunset_after": "",
            },
            "runtime": {
                "supports_entry": True,
                "supports_execute": False,
                "supports_batch": False,
                "safe_fallback": "workspace.home",
            },
            "audit": {
                "audit_enabled": True,
                "policy_trace_enabled": True,
                "owner_trace": "smart_construction_core.get_capability_contributions",
            },
        }
        out.append(item)
    return out, timings_ms if isinstance(timings_ms, dict) else {}


def get_capability_group_contributions(env):
    del env
    try:
        from odoo.addons.smart_construction_core.services.capability_registry import CAPABILITY_GROUPS
    except Exception:
        return []
    out = []
    for item in CAPABILITY_GROUPS:
        if not isinstance(item, dict):
            continue
        row = dict(item)
        row.setdefault("source_module", "smart_construction_core")
        out.append(row)
    return out


def get_create_field_fallback_contributions(env, model_name):
    del env
    return dict(INDUSTRY_CREATE_FIELD_FALLBACKS.get(str(model_name or ""), {}))


def get_system_init_fact_contributions(env, user, context=None):
    """Return construction system.init facts contribution payload."""
    del context
    try:
        Entitlement = env.get("sc.entitlement")
        Usage = env.get("sc.usage.counter")
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

        role_entries = _build_role_entry_contract_rows(env)
        if role_entries:
            module_facts["role_entries"] = role_entries

        home_blocks = _build_home_block_contract_rows(env)
        if home_blocks:
            module_facts["home_blocks"] = home_blocks

        enterprise_enablement = _build_enterprise_enablement_contract(env, user)
        if enterprise_enablement:
            module_facts["enterprise_enablement"] = enterprise_enablement

        return {
            "module": "smart_construction_core",
            "facts": module_facts,
            "collections": module_facts.get("workspace_collections") or {},
            "meta": {
                "source": "smart_construction_core",
                "status": "active",
            },
        }
    except Exception as exc:
        _logger.warning("[get_system_init_fact_contributions] failed: %s", exc)
        return None


def smart_core_extend_system_init(data, env, user):
    """Legacy hook shim: write construction facts only under data['ext_facts']."""
    if not isinstance(data, dict):
        return data

    contribution = get_system_init_fact_contributions(env, user)
    ext_facts = data.get("ext_facts")
    if not isinstance(ext_facts, dict):
        ext_facts = {}
    if isinstance(contribution, dict):
        module_key = str(contribution.get("module") or "smart_construction_core").strip() or "smart_construction_core"
        facts_payload = contribution.get("facts") if isinstance(contribution.get("facts"), dict) else {}
        ext_facts[module_key] = dict(facts_payload)
    data["ext_facts"] = ext_facts
    return data


def smart_core_describe_project_capabilities(env, project):
    from odoo.addons.smart_construction_core.services.lifecycle_capability_service import (
        LifecycleCapabilityService,
    )

    return LifecycleCapabilityService(env).describe_project(project)


def smart_core_build_portal_dashboard(env):
    from odoo.addons.smart_construction_core.services.portal_dashboard_service import (
        PortalDashboardService,
    )

    return PortalDashboardService(env).build_dashboard()


def smart_core_build_capability_matrix(env):
    from odoo.addons.smart_construction_core.services.capability_matrix_service import (
        CapabilityMatrixService,
    )

    return CapabilityMatrixService(env).build_matrix()


def smart_core_get_project_insight(env, record, scene):
    from odoo.addons.smart_construction_core.services.insight.project_insight_service import (
        ProjectInsightService,
    )

    return ProjectInsightService(env).get_insight(record, scene=scene)


def smart_core_build_portal_execute_button_contract(env, model, res_id, method):
    from odoo.addons.smart_construction_core.services.portal_execute_button_service import (
        PortalExecuteButtonService,
    )

    return PortalExecuteButtonService(env).build_contract(
        model=model,
        res_id=res_id,
        method=method,
    )


def smart_core_build_project_execution_service(env):
    from odoo.addons.smart_construction_core.services.project_execution_service import (
        ProjectExecutionService,
    )

    return ProjectExecutionService(env)


def smart_core_build_project_dashboard_service(env):
    from odoo.addons.smart_construction_core.services.project_dashboard_service import (
        ProjectDashboardService,
    )

    return ProjectDashboardService(env)


def smart_core_build_project_plan_bootstrap_service(env):
    from odoo.addons.smart_construction_core.services.project_plan_bootstrap_service import (
        ProjectPlanBootstrapService,
    )

    return ProjectPlanBootstrapService(env)


def smart_core_build_cost_tracking_service(env):
    from odoo.addons.smart_construction_core.services.cost_tracking_service import (
        CostTrackingService,
    )

    return CostTrackingService(env)


def smart_core_build_payment_slice_service(env):
    from odoo.addons.smart_construction_core.services.payment_slice_service import (
        PaymentSliceService,
    )

    return PaymentSliceService(env)


def smart_core_build_settlement_slice_service(env):
    from odoo.addons.smart_construction_core.services.settlement_slice_service import (
        SettlementSliceService,
    )

    return SettlementSliceService(env)
