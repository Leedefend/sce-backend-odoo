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

        if task_rows:
            data["task_items"] = task_rows
        if payment_rows:
            data["payment_requests"] = payment_rows
        if risk_rows:
            data["risk_actions"] = risk_rows
        if project_rows:
            data["project_actions"] = project_rows

        module_facts["workspace_business_source"] = {
            "task_items": len(task_rows),
            "payment_requests": len(payment_rows),
            "risk_actions": len(risk_rows),
            "project_actions": len(project_rows),
        }

        providers = data.get("role_surface_override_providers")
        if not isinstance(providers, dict):
            providers = {}
        providers["smart_construction_core"] = {
            "enabled": True,
            "priority": 100,
            "root_xmlids": ["smart_construction_core.menu_sc_root"],
            "scene_codes": ["portal.dashboard", "project.management", "projects.list", "projects.intake"],
            "role_surface_overrides": ROLE_SURFACE_OVERRIDES,
        }
        data["role_surface_override_providers"] = providers

        ext_facts["smart_construction_core"] = module_facts
        data["ext_facts"] = ext_facts
    except Exception as exc:
        _logger.warning("[smart_core_extend_system_init] failed: %s", exc)
