# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase, tagged

from odoo.addons.smart_construction_core.handlers.app_catalog import (
    APP_DELIVERY_FALLBACK_META,
    APP_DELIVERY_SOURCE_AUTHORITY,
)
from odoo.addons.smart_construction_core.handlers.business_evidence_trace import BusinessEvidenceTraceHandler
from odoo.addons.smart_construction_core.handlers.capability_describe import CapabilityDescribeHandler
from odoo.addons.smart_construction_core.handlers.cost_tracking_block_fetch import CostTrackingBlockFetchHandler
from odoo.addons.smart_construction_core.handlers.cost_tracking_enter import CostTrackingEnterHandler
from odoo.addons.smart_construction_core.handlers.cost_tracking_record_create import CostTrackingRecordCreateHandler
from odoo.addons.smart_construction_core.handlers.dashboard_company_enter import DashboardCompanyEnterHandler
from odoo.addons.smart_construction_core.handlers.project_connection_transition import ProjectConnectionTransitionHandler
from odoo.addons.smart_construction_core.handlers.my_work_summary import MyWorkSummaryHandler
from odoo.addons.smart_construction_core.handlers.my_work_complete import MyWorkCompleteBatchHandler, MyWorkCompleteHandler
from odoo.addons.smart_construction_core.handlers.payment_request_approval import PaymentRequestApproveHandler
from odoo.addons.smart_construction_core.handlers.payment_request_available_actions import PaymentRequestAvailableActionsHandler
from odoo.addons.smart_construction_core.handlers.payment_slice_block_fetch import PaymentSliceBlockFetchHandler
from odoo.addons.smart_construction_core.handlers.payment_slice_enter import PaymentSliceEnterHandler
from odoo.addons.smart_construction_core.handlers.payment_slice_record_create import PaymentSliceRecordCreateHandler
from odoo.addons.smart_construction_core.handlers.project_entry_context_options import ProjectEntryContextOptionsHandler
from odoo.addons.smart_construction_core.handlers.project_entry_context_resolve import ProjectEntryContextResolveHandler
from odoo.addons.smart_construction_core.handlers.project_execution_advance import ProjectExecutionAdvanceHandler
from odoo.addons.smart_construction_core.handlers.project_execution_block_fetch import ProjectExecutionBlockFetchHandler
from odoo.addons.smart_construction_core.handlers.project_execution_enter import ProjectExecutionEnterHandler
from odoo.addons.smart_construction_core.handlers.project_initiation_enter import ProjectInitiationEnterHandler
from odoo.addons.smart_construction_core.handlers.project_plan_bootstrap_block_fetch import (
    ProjectPlanBootstrapBlockFetchHandler,
)
from odoo.addons.smart_construction_core.handlers.project_plan_bootstrap_enter import ProjectPlanBootstrapEnterHandler
from odoo.addons.smart_construction_core.handlers.risk_action_execute import RiskActionExecuteHandler
from odoo.addons.smart_construction_core.handlers.settlement_slice_block_fetch import SettlementSliceBlockFetchHandler
from odoo.addons.smart_construction_core.handlers.settlement_slice_enter import SettlementSliceEnterHandler
from odoo.addons.smart_construction_core.handlers.telemetry_track import TelemetryTrackHandler
from odoo.addons.smart_construction_core.handlers.workspace_home_enter import WorkspaceHomeEnterHandler
from odoo.addons.smart_construction_core.services.dashboard_contract_builder import DashboardContractBuilder
from odoo.addons.smart_construction_core.services.cost_tracking_service import CostTrackingService
from odoo.addons.smart_construction_core.services.payment_slice_service import PaymentSliceService
from odoo.addons.smart_construction_core.services.project_creation_service import ProjectCreationService
from odoo.addons.smart_construction_core.services.project_execution_service import ProjectExecutionService
from odoo.addons.smart_construction_core.services.project_dashboard_builders.base import BaseProjectBlockBuilder
from odoo.addons.smart_construction_core.services.project_dashboard_service import ProjectDashboardService
from odoo.addons.smart_construction_core.services.project_plan_bootstrap_service import ProjectPlanBootstrapService
from odoo.addons.smart_construction_core.services.settlement_slice_service import SettlementSliceService
from odoo.addons.smart_construction_core.services.workspace_contract_builder import WorkspaceContractBuilder


@tagged("post_install", "-at_install", "sc_native_alignment")
class TestConstructionOdooNativeAlignmentBoundaries(TransactionCase):
    def test_approval_policy_runtime_authority_is_tier_validation(self):
        policy_model = self.env["sc.approval.policy"]

        self.assertEqual(policy_model._runtime_authority, "base_tier_validation")
        self.assertEqual(policy_model.runtime_authority(), "base_tier_validation")

    def test_legacy_workflow_runtime_is_disabled_by_default(self):
        workflow = self.env["sc.workflow.instance"]

        self.assertFalse(workflow._legacy_runtime_enabled())

    def test_my_work_declares_mail_activity_as_primary_todo_authority(self):
        handler = MyWorkSummaryHandler(self.env, payload={})
        contract = handler._source_authority_contract()

        self.assertEqual(contract.get("primary_todo"), "mail.activity")
        self.assertIn("mail.activity", (contract.get("section_authorities") or {}).get("todo") or [])
        self.assertEqual((contract.get("section_semantics") or {}).get("mentions"), "collaboration_signal")
        self.assertIn("sc.workflow.workitem", contract.get("historical_todo_authorities") or [])

    def test_dashboard_services_declare_business_fact_sources(self):
        self.assertEqual(ProjectDashboardService.SOURCE_KIND, "project_dashboard_business_fact_projection")
        self.assertIn("project.project", ProjectDashboardService.SOURCE_AUTHORITIES)
        self.assertIn("odoo.read_group", ProjectDashboardService.SOURCE_AUTHORITIES)
        self.assertEqual(DashboardContractBuilder.SOURCE_KIND, "company_dashboard_business_fact_projection")
        self.assertIn("payment.request", DashboardContractBuilder.SOURCE_AUTHORITIES)
        source = BaseProjectBlockBuilder(self.env)._source_authority_contract()
        self.assertTrue(source.get("projection_only"))
        self.assertIn("odoo.orm", source.get("authorities") or [])

    def test_scene_slice_services_declare_business_fact_sources(self):
        expectations = [
            (PaymentSliceService, "payment_slice_business_fact_projection", "payment.request"),
            (CostTrackingService, "cost_tracking_business_fact_projection", "project.cost.ledger"),
            (SettlementSliceService, "settlement_slice_business_fact_projection", "payment.ledger"),
            (ProjectExecutionService, "project_execution_business_fact_projection", "project.task"),
            (ProjectPlanBootstrapService, "project_plan_bootstrap_business_fact_projection", "project.task"),
        ]
        for service, kind, authority in expectations:
            with self.subTest(service=service.__name__):
                source = service.source_authority_contract()
                self.assertEqual(source.get("kind"), kind)
                self.assertTrue(source.get("projection_only"))
                self.assertEqual(source.get("runtime_carrier"), "scene_entry_and_block_contract")
                self.assertIn(authority, source.get("authorities") or [])
                self.assertIn("odoo.orm", source.get("authorities") or [])

    def test_scene_entry_and_block_intents_are_covered_by_native_alignment_tests(self):
        expectations = {
            "cost.tracking.block.fetch": CostTrackingBlockFetchHandler,
            "cost.tracking.enter": CostTrackingEnterHandler,
            "cost.tracking.record.create": CostTrackingRecordCreateHandler,
            "dashboard.company.enter": DashboardCompanyEnterHandler,
            "payment.block.fetch": PaymentSliceBlockFetchHandler,
            "payment.enter": PaymentSliceEnterHandler,
            "payment.record.create": PaymentSliceRecordCreateHandler,
            "project.entry.context.options": ProjectEntryContextOptionsHandler,
            "project.entry.context.resolve": ProjectEntryContextResolveHandler,
            "project.execution.block.fetch": ProjectExecutionBlockFetchHandler,
            "project.execution.enter": ProjectExecutionEnterHandler,
            "project.initiation.enter": ProjectInitiationEnterHandler,
            "project.plan_bootstrap.block.fetch": ProjectPlanBootstrapBlockFetchHandler,
            "project.plan_bootstrap.enter": ProjectPlanBootstrapEnterHandler,
            "settlement.block.fetch": SettlementSliceBlockFetchHandler,
            "settlement.enter": SettlementSliceEnterHandler,
            "workspace.home.enter": WorkspaceHomeEnterHandler,
        }

        for intent, handler_cls in expectations.items():
            with self.subTest(intent=intent):
                self.assertEqual(handler_cls.INTENT_TYPE, intent)

    def test_project_initiation_uses_odoo_orm_write_authority(self):
        source = ProjectCreationService.source_authority_contract()

        self.assertEqual(source.get("kind"), "project_initiation_odoo_orm_write_proxy")
        self.assertFalse(source.get("projection_only"))
        self.assertEqual(source.get("runtime_authority"), "odoo.orm")
        self.assertEqual(source.get("write_authority"), "project.project.create")
        self.assertIn("project.project", source.get("authorities") or [])
        self.assertIn("ir.model.access", source.get("authorities") or [])

    def test_runtime_write_intents_declare_odoo_authorities(self):
        payment_write = PaymentSliceService.write_source_authority_contract()
        cost_write = CostTrackingService.write_source_authority_contract()
        approval = PaymentRequestApproveHandler.source_authority_contract()

        self.assertEqual(payment_write.get("write_authority"), "payment.request.create")
        self.assertIn("payment.request", payment_write.get("authorities") or [])
        self.assertEqual(cost_write.get("write_authority"), "account.move.create")
        self.assertIn("account.move", cost_write.get("authorities") or [])
        self.assertEqual(approval.get("kind"), "payment_request_odoo_model_method_proxy")
        self.assertIn("tier.review", approval.get("authorities") or [])

    def test_runtime_action_projections_and_mutations_declare_authorities(self):
        self.assertEqual(PaymentRequestAvailableActionsHandler.SOURCE_AUTHORITY.get("kind"), "payment_request_action_availability_projection")
        self.assertTrue(PaymentRequestAvailableActionsHandler.SOURCE_AUTHORITY.get("projection_only"))
        self.assertIn("payment.request", PaymentRequestAvailableActionsHandler.SOURCE_AUTHORITY.get("authorities") or [])
        self.assertEqual(ProjectExecutionAdvanceHandler.SOURCE_AUTHORITY.get("runtime_authority"), "project.execution.state_transition")
        self.assertIn("project.task", ProjectExecutionAdvanceHandler.SOURCE_AUTHORITY.get("authorities") or [])
        self.assertEqual(RiskActionExecuteHandler.SOURCE_AUTHORITY.get("write_authority"), "project.risk.action.create/write")
        self.assertIn("project.risk.action", RiskActionExecuteHandler.SOURCE_AUTHORITY.get("authorities") or [])
        self.assertEqual(MyWorkCompleteHandler.SOURCE_AUTHORITY.get("runtime_authority"), "mail.activity.action_feedback")
        self.assertEqual(MyWorkCompleteBatchHandler.SOURCE_AUTHORITY.get("idempotency_authority"), "sc.audit.log")

    def test_workspace_home_is_native_capability_projection(self):
        source = WorkspaceContractBuilder.source_authority_contract()

        self.assertEqual(source.get("kind"), "workspace_home_odoo_native_capability_projection")
        self.assertTrue(source.get("projection_only"))
        self.assertTrue(source.get("no_business_fact_authority"))
        self.assertIn("ir.actions", source.get("authorities") or [])
        self.assertIn("project.project", source.get("authorities") or [])

    def test_delivery_and_observability_handlers_do_not_claim_business_fact_authority(self):
        self.assertTrue(APP_DELIVERY_SOURCE_AUTHORITY.get("delivery_only"))
        self.assertTrue(APP_DELIVERY_SOURCE_AUTHORITY.get("no_business_fact_authority"))
        self.assertTrue(APP_DELIVERY_FALLBACK_META.get("fallback"))
        self.assertEqual(APP_DELIVERY_FALLBACK_META.get("fallback_kind"), "delivery_navigation_fallback")
        self.assertTrue(APP_DELIVERY_FALLBACK_META.get("no_business_fact_authority"))
        self.assertEqual(CapabilityDescribeHandler.SOURCE_AUTHORITY.get("kind"), "capability_delivery_projection")
        self.assertTrue(CapabilityDescribeHandler.SOURCE_AUTHORITY.get("no_business_fact_authority"))
        self.assertTrue(TelemetryTrackHandler.SOURCE_AUTHORITY.get("observability_only"))

    def test_evidence_and_project_context_handlers_declare_projection_or_transition_authorities(self):
        self.assertEqual(BusinessEvidenceTraceHandler.SOURCE_AUTHORITY.get("kind"), "business_evidence_trace_projection")
        self.assertTrue(BusinessEvidenceTraceHandler.SOURCE_AUTHORITY.get("projection_only"))
        self.assertIn("sc.evidence.timeline.service", BusinessEvidenceTraceHandler.SOURCE_AUTHORITY.get("authorities") or [])
        self.assertEqual(ProjectConnectionTransitionHandler.SOURCE_AUTHORITY.get("runtime_authority"), "project.project.action_set_lifecycle_state")
        self.assertFalse(ProjectConnectionTransitionHandler.SOURCE_AUTHORITY.get("projection_only"))
        self.assertIn("project.project", ProjectConnectionTransitionHandler.SOURCE_AUTHORITY.get("authorities") or [])

    def test_scene_orchestration_is_delivery_only(self):
        scene_source = self.env["sc.scene"].source_authority_contract()
        cap_source = self.env["sc.capability"].source_authority_contract()

        self.assertEqual(scene_source.get("kind"), "scene_delivery_orchestration")
        self.assertTrue(scene_source.get("delivery_only"))
        self.assertTrue(scene_source.get("no_business_fact_authority"))
        self.assertIn("ir.actions", scene_source.get("authorities") or [])
        self.assertEqual(cap_source.get("kind"), "scene_delivery_capability_catalog")
        self.assertIn("res.groups", cap_source.get("authorities") or [])
