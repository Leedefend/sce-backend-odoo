# -*- coding: utf-8 -*-
import logging

from odoo.addons.smart_core.utils.backend_contract_boundaries import APPROVAL_POLICY_INTENTS

_logger = logging.getLogger(__name__)


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
        from odoo.addons.smart_construction_core.handlers.telemetry_track import (
            TelemetryTrackHandler,
        )
        from odoo.addons.smart_construction_core.handlers.capability_visibility_report import (
            CapabilityVisibilityReportHandler,
        )
        from odoo.addons.smart_construction_core.handlers.approval_policy_configuration import (
            ApprovalPolicyConfigGetHandler,
            ApprovalPolicyConfigSetHandler,
            ApprovalPolicyStepsSetHandler,
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
        try:
            from odoo.addons.smart_construction_core.handlers.project_execution_advance import (
                ProjectExecutionAdvanceHandler,
            )
        except Exception as exc:
            ProjectExecutionAdvanceHandler = None
            _logger.warning("[get_intent_handler_contributions] skip project_execution_advance: %s", exc)
        from odoo.addons.smart_construction_core.handlers.project_connection_transition import (
            ProjectConnectionTransitionHandler,
        )
        from odoo.addons.smart_construction_core.handlers.cost_tracking_enter import (
            CostTrackingEnterHandler,
        )
        from odoo.addons.smart_construction_core.handlers.cost_tracking_block_fetch import (
            CostTrackingBlockFetchHandler,
        )
        try:
            from odoo.addons.smart_construction_core.handlers.cost_tracking_record_create import (
                CostTrackingRecordCreateHandler,
            )
        except Exception as exc:
            CostTrackingRecordCreateHandler = None
            _logger.warning("[get_intent_handler_contributions] skip cost_tracking_record_create: %s", exc)
        try:
            from odoo.addons.smart_construction_core.handlers.payment_slice_enter import (
                PaymentSliceEnterHandler,
            )
        except Exception as exc:
            PaymentSliceEnterHandler = None
            _logger.warning("[get_intent_handler_contributions] skip payment_slice_enter: %s", exc)
        try:
            from odoo.addons.smart_construction_core.handlers.payment_slice_block_fetch import (
                PaymentSliceBlockFetchHandler,
            )
        except Exception as exc:
            PaymentSliceBlockFetchHandler = None
            _logger.warning("[get_intent_handler_contributions] skip payment_slice_block_fetch: %s", exc)
        try:
            from odoo.addons.smart_construction_core.handlers.payment_slice_record_create import (
                PaymentSliceRecordCreateHandler,
            )
        except Exception as exc:
            PaymentSliceRecordCreateHandler = None
            _logger.warning("[get_intent_handler_contributions] skip payment_slice_record_create: %s", exc)
        try:
            from odoo.addons.smart_construction_core.handlers.settlement_slice_enter import (
                SettlementSliceEnterHandler,
            )
        except Exception as exc:
            SettlementSliceEnterHandler = None
            _logger.warning("[get_intent_handler_contributions] skip settlement_slice_enter: %s", exc)
        try:
            from odoo.addons.smart_construction_core.handlers.settlement_slice_block_fetch import (
                SettlementSliceBlockFetchHandler,
            )
        except Exception as exc:
            SettlementSliceBlockFetchHandler = None
            _logger.warning("[get_intent_handler_contributions] skip settlement_slice_block_fetch: %s", exc)
        from odoo.addons.smart_construction_core.handlers.workspace_home_enter import (
            WorkspaceHomeEnterHandler,
        )
        from odoo.addons.smart_construction_core.handlers.dashboard_company_enter import (
            DashboardCompanyEnterHandler,
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
        ("telemetry.track", TelemetryTrackHandler),
        ("capability.visibility.report", CapabilityVisibilityReportHandler),
        (APPROVAL_POLICY_INTENTS["config_get"], ApprovalPolicyConfigGetHandler),
        (APPROVAL_POLICY_INTENTS["config_set"], ApprovalPolicyConfigSetHandler),
        (APPROVAL_POLICY_INTENTS["steps_set"], ApprovalPolicyStepsSetHandler),
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
        ("workspace.home.enter", WorkspaceHomeEnterHandler),
        ("dashboard.company.enter", DashboardCompanyEnterHandler),
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
        if handler is not None
    ]

