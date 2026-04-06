# -*- coding: utf-8 -*-
import logging
from typing import Any, Dict, List

from odoo.exceptions import AccessError

_logger = logging.getLogger(__name__)


SERVER_ACTION_WINDOW_MAP = {
    "smart_construction_core.action_exec_structure_entry": "smart_construction_core.action_exec_structure_wbs",
}

FILE_UPLOAD_ALLOWED_MODELS = ["project.project", "project.task"]
FILE_DOWNLOAD_ALLOWED_MODELS = ["project.project", "project.task"]
API_DATA_WRITE_ALLOWLIST = {
    "project.project": ["name", "description", "date_start"],
    "project.task": ["name", "description", "date_deadline", "project_id"],
}
API_DATA_UNLINK_ALLOWED_MODELS = [
    "project.task",
    "res.company",
    "hr.department",
    "res.users",
]

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
        item = dict(row)
        item.setdefault("key", key)
        item.setdefault("source_module", "smart_construction_core")
        item.setdefault("owner_module", "smart_construction_core")
        item.setdefault("status", "active")
        out.append(item)
    return out


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
    return dict(CREATE_FIELD_FALLBACKS.get(str(model_name or ""), {}))


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
