# Handler Inventory (Phase B-1 / Scan)

- Stage: `scan` (fact-only; no ownership conclusion)
- Scope: `addons/smart_construction_core/handlers/**/*.py`, `addons/smart_construction_core/core_extension.py`
- handler_class_count: `43`
- core_extension_registry_bindings: `42`

## Core Extension Registry Bindings

| Intent Name | Handler Class | Handler File | Handler INTENT_TYPE |
|---|---|---|---|
| `system.ping.construction` | `SystemPingConstructionHandler` | `addons/smart_construction_core/handlers/system_ping_construction.py` | `system.ping.construction` |
| `capability.describe` | `CapabilityDescribeHandler` | `addons/smart_construction_core/handlers/capability_describe.py` | `capability.describe` |
| `my.work.summary` | `MyWorkSummaryHandler` | `addons/smart_construction_core/handlers/my_work_summary.py` | `my.work.summary` |
| `my.work.complete` | `MyWorkCompleteHandler` | `addons/smart_construction_core/handlers/my_work_complete.py` | `my.work.complete` |
| `my.work.complete_batch` | `MyWorkCompleteBatchHandler` | `addons/smart_construction_core/handlers/my_work_complete.py` | `my.work.complete_batch` |
| `usage.track` | `UsageTrackHandler` | `addons/smart_construction_core/handlers/usage_track.py` | `usage.track` |
| `telemetry.track` | `TelemetryTrackHandler` | `addons/smart_construction_core/handlers/telemetry_track.py` | `telemetry.track` |
| `usage.report` | `UsageReportHandler` | `addons/smart_construction_core/handlers/usage_report.py` | `usage.report` |
| `usage.export.csv` | `UsageExportCsvHandler` | `addons/smart_construction_core/handlers/usage_export_csv.py` | `usage.export.csv` |
| `capability.visibility.report` | `CapabilityVisibilityReportHandler` | `addons/smart_construction_core/handlers/capability_visibility_report.py` | `capability.visibility.report` |
| `payment.request.submit` | `PaymentRequestSubmitHandler` | `addons/smart_construction_core/handlers/payment_request_approval.py` | `payment.request.submit` |
| `payment.request.approve` | `PaymentRequestApproveHandler` | `addons/smart_construction_core/handlers/payment_request_approval.py` | `payment.request.approve` |
| `payment.request.reject` | `PaymentRequestRejectHandler` | `addons/smart_construction_core/handlers/payment_request_approval.py` | `payment.request.reject` |
| `payment.request.done` | `PaymentRequestDoneHandler` | `addons/smart_construction_core/handlers/payment_request_approval.py` | `payment.request.done` |
| `payment.request.available_actions` | `PaymentRequestAvailableActionsHandler` | `addons/smart_construction_core/handlers/payment_request_available_actions.py` | `payment.request.available_actions` |
| `payment.request.execute` | `PaymentRequestExecuteHandler` | `addons/smart_construction_core/handlers/payment_request_execute.py` | `payment.request.execute` |
| `project.dashboard` | `ProjectDashboardHandler` | `addons/smart_construction_core/handlers/project_dashboard.py` | `project.dashboard` |
| `project.dashboard.open` | `ProjectDashboardOpenHandler` | `addons/smart_construction_core/handlers/project_dashboard_open.py` | `project.dashboard.open` |
| `project.dashboard.enter` | `ProjectDashboardEnterHandler` | `addons/smart_construction_core/handlers/project_dashboard_enter.py` | `project.dashboard.enter` |
| `project.entry.context.resolve` | `ProjectEntryContextResolveHandler` | `addons/smart_construction_core/handlers/project_entry_context_resolve.py` | `project.entry.context.resolve` |
| `project.entry.context.options` | `ProjectEntryContextOptionsHandler` | `addons/smart_construction_core/handlers/project_entry_context_options.py` | `project.entry.context.options` |
| `business.evidence.trace` | `BusinessEvidenceTraceHandler` | `addons/smart_construction_core/handlers/business_evidence_trace.py` | `business.evidence.trace` |
| `project.dashboard.block.fetch` | `ProjectDashboardBlockFetchHandler` | `addons/smart_construction_core/handlers/project_dashboard_block_fetch.py` | `project.dashboard.block.fetch` |
| `project.plan_bootstrap.enter` | `ProjectPlanBootstrapEnterHandler` | `addons/smart_construction_core/handlers/project_plan_bootstrap_enter.py` | `project.plan_bootstrap.enter` |
| `project.plan_bootstrap.block.fetch` | `ProjectPlanBootstrapBlockFetchHandler` | `addons/smart_construction_core/handlers/project_plan_bootstrap_block_fetch.py` | `project.plan_bootstrap.block.fetch` |
| `project.execution.enter` | `ProjectExecutionEnterHandler` | `addons/smart_construction_core/handlers/project_execution_enter.py` | `project.execution.enter` |
| `project.execution.block.fetch` | `ProjectExecutionBlockFetchHandler` | `addons/smart_construction_core/handlers/project_execution_block_fetch.py` | `project.execution.block.fetch` |
| `project.execution.advance` | `ProjectExecutionAdvanceHandler` | `addons/smart_construction_core/handlers/project_execution_advance.py` | `project.execution.advance` |
| `project.connection.transition` | `ProjectConnectionTransitionHandler` | `addons/smart_construction_core/handlers/project_connection_transition.py` | `project.connection.transition` |
| `cost.tracking.enter` | `CostTrackingEnterHandler` | `addons/smart_construction_core/handlers/cost_tracking_enter.py` | `cost.tracking.enter` |
| `cost.tracking.block.fetch` | `CostTrackingBlockFetchHandler` | `addons/smart_construction_core/handlers/cost_tracking_block_fetch.py` | `cost.tracking.block.fetch` |
| `cost.tracking.record.create` | `CostTrackingRecordCreateHandler` | `addons/smart_construction_core/handlers/cost_tracking_record_create.py` | `cost.tracking.record.create` |
| `payment.enter` | `PaymentSliceEnterHandler` | `addons/smart_construction_core/handlers/payment_slice_enter.py` | `payment.enter` |
| `payment.block.fetch` | `PaymentSliceBlockFetchHandler` | `addons/smart_construction_core/handlers/payment_slice_block_fetch.py` | `payment.block.fetch` |
| `payment.record.create` | `PaymentSliceRecordCreateHandler` | `addons/smart_construction_core/handlers/payment_slice_record_create.py` | `payment.record.create` |
| `settlement.enter` | `SettlementSliceEnterHandler` | `addons/smart_construction_core/handlers/settlement_slice_enter.py` | `settlement.enter` |
| `settlement.block.fetch` | `SettlementSliceBlockFetchHandler` | `addons/smart_construction_core/handlers/settlement_slice_block_fetch.py` | `settlement.block.fetch` |
| `project.initiation.enter` | `ProjectInitiationEnterHandler` | `addons/smart_construction_core/handlers/project_initiation_enter.py` | `project.initiation.enter` |
| `risk.action.execute` | `RiskActionExecuteHandler` | `addons/smart_construction_core/handlers/risk_action_execute.py` | `risk.action.execute` |
| `app.catalog` | `AppCatalogHandler` | `addons/smart_construction_core/handlers/app_catalog.py` | `app.catalog` |
| `app.nav` | `AppNavHandler` | `addons/smart_construction_core/handlers/app_nav.py` | `app.nav` |
| `app.open` | `AppOpenHandler` | `addons/smart_construction_core/handlers/app_open.py` | `app.open` |

## Handler Class Inventory

| Handler File | Handler Class | INTENT_TYPE | Has Handle | Service Imports | Semantic Signals |
|---|---|---|---|---|---|
| `addons/smart_construction_core/handlers/app_catalog.py` | `AppCatalogHandler` | `app.catalog` | `yes` | `none` | `catalog, scene` |
| `addons/smart_construction_core/handlers/app_nav.py` | `AppNavHandler` | `app.nav` | `yes` | `none` | `app.nav` |
| `addons/smart_construction_core/handlers/app_open.py` | `AppOpenHandler` | `app.open` | `yes` | `odoo.addons.smart_core.app_config_engine.services.contract_service, odoo.addons.smart_core.app_config_engine.services.dispatchers.action_dispatcher` | `app.open` |
| `addons/smart_construction_core/handlers/business_evidence_trace.py` | `BusinessEvidenceTraceHandler` | `business.evidence.trace` | `yes` | `odoo.addons.smart_construction_core.services.evidence_chain_service` | `none` |
| `addons/smart_construction_core/handlers/capability_describe.py` | `CapabilityDescribeHandler` | `capability.describe` | `yes` | `none` | `capability` |
| `addons/smart_construction_core/handlers/capability_visibility_report.py` | `CapabilityVisibilityReportHandler` | `capability.visibility.report` | `yes` | `none` | `capability` |
| `addons/smart_construction_core/handlers/cost_tracking_block_fetch.py` | `CostTrackingBlockFetchHandler` | `cost.tracking.block.fetch` | `yes` | `odoo.addons.smart_construction_core.services.project_context_contract` | `block.fetch` |
| `addons/smart_construction_core/handlers/cost_tracking_enter.py` | `CostTrackingEnterHandler` | `cost.tracking.enter` | `yes` | `odoo.addons.smart_construction_core.services.project_context_contract, odoo.addons.smart_construction_scene.services.project_management_entry_target` | `capability, scene` |
| `addons/smart_construction_core/handlers/cost_tracking_record_create.py` | `CostTrackingRecordCreateHandler` | `cost.tracking.record.create` | `yes` | `odoo.addons.smart_construction_core.services.cost_tracking_service` | `none` |
| `addons/smart_construction_core/handlers/my_work_complete.py` | `MyWorkCompleteBatchHandler` | `my.work.complete_batch` | `yes` | `none` | `none` |
| `addons/smart_construction_core/handlers/my_work_complete.py` | `MyWorkCompleteHandler` | `my.work.complete` | `yes` | `none` | `none` |
| `addons/smart_construction_core/handlers/my_work_summary.py` | `MyWorkSummaryHandler` | `my.work.summary` | `yes` | `odoo.addons.smart_construction_core.services.my_work_aggregate_service, odoo.addons.smart_construction_core.services.project_execution_item_projection_service, odoo.addons.smart_construction_scene.services.my_work_scene_targets` | `scene` |
| `addons/smart_construction_core/handlers/payment_request_approval.py` | `PaymentRequestApproveHandler` | `payment.request.approve` | `no` | `none` | `none` |
| `addons/smart_construction_core/handlers/payment_request_approval.py` | `PaymentRequestDoneHandler` | `payment.request.done` | `no` | `none` | `none` |
| `addons/smart_construction_core/handlers/payment_request_approval.py` | `PaymentRequestRejectHandler` | `payment.request.reject` | `no` | `none` | `none` |
| `addons/smart_construction_core/handlers/payment_request_approval.py` | `PaymentRequestSubmitHandler` | `payment.request.submit` | `no` | `none` | `none` |
| `addons/smart_construction_core/handlers/payment_request_approval.py` | `_BasePaymentApprovalHandler` | `n/a` | `yes` | `none` | `none` |
| `addons/smart_construction_core/handlers/payment_request_available_actions.py` | `PaymentRequestAvailableActionsHandler` | `payment.request.available_actions` | `yes` | `none` | `none` |
| `addons/smart_construction_core/handlers/payment_request_execute.py` | `PaymentRequestExecuteHandler` | `payment.request.execute` | `yes` | `none` | `none` |
| `addons/smart_construction_core/handlers/payment_slice_block_fetch.py` | `PaymentSliceBlockFetchHandler` | `payment.block.fetch` | `yes` | `odoo.addons.smart_construction_core.services.project_context_contract` | `block.fetch` |
| `addons/smart_construction_core/handlers/payment_slice_enter.py` | `PaymentSliceEnterHandler` | `payment.enter` | `yes` | `odoo.addons.smart_construction_core.services.project_context_contract, odoo.addons.smart_construction_scene.services.project_management_entry_target` | `capability, scene` |
| `addons/smart_construction_core/handlers/payment_slice_record_create.py` | `PaymentSliceRecordCreateHandler` | `payment.record.create` | `yes` | `odoo.addons.smart_construction_core.services.payment_slice_service` | `none` |
| `addons/smart_construction_core/handlers/project_connection_transition.py` | `ProjectConnectionTransitionHandler` | `project.connection.transition` | `yes` | `none` | `none` |
| `addons/smart_construction_core/handlers/project_dashboard.py` | `ProjectDashboardHandler` | `project.dashboard` | `yes` | `none` | `none` |
| `addons/smart_construction_core/handlers/project_dashboard_block_fetch.py` | `ProjectDashboardBlockFetchHandler` | `project.dashboard.block.fetch` | `yes` | `odoo.addons.smart_construction_core.services.project_context_contract` | `block.fetch, scene` |
| `addons/smart_construction_core/handlers/project_dashboard_enter.py` | `ProjectDashboardEnterHandler` | `project.dashboard.enter` | `yes` | `odoo.addons.smart_construction_core.services.project_context_contract, odoo.addons.smart_construction_scene.services.project_management_entry_target` | `capability, scene` |
| `addons/smart_construction_core/handlers/project_dashboard_open.py` | `ProjectDashboardOpenHandler` | `project.dashboard.open` | `yes` | `none` | `none` |
| `addons/smart_construction_core/handlers/project_entry_context_options.py` | `ProjectEntryContextOptionsHandler` | `project.entry.context.options` | `yes` | `odoo.addons.smart_construction_core.services.project_entry_context_service` | `none` |
| `addons/smart_construction_core/handlers/project_entry_context_resolve.py` | `ProjectEntryContextResolveHandler` | `project.entry.context.resolve` | `yes` | `odoo.addons.smart_construction_core.services.project_entry_context_service` | `none` |
| `addons/smart_construction_core/handlers/project_execution_advance.py` | `ProjectExecutionAdvanceHandler` | `project.execution.advance` | `yes` | `odoo.addons.smart_construction_core.services.project_execution_consistency_guard, odoo.addons.smart_construction_core.services.project_execution_hint_service, odoo.addons.smart_construction_core.services.project_execution_post_transition_service, odoo.addons.smart_construction_core.services.project_execution_precheck_service, odoo.addons.smart_construction_core.services.project_execution_project_lookup_service, odoo.addons.smart_construction_core.services.project_execution_request_service, odoo.addons.smart_construction_core.services.project_execution_response_builder, odoo.addons.smart_construction_core.services.project_execution_state_machine, odoo.addons.smart_construction_core.services.project_execution_task_transition_service, odoo.addons.smart_construction_core.services.project_execution_transition_service` | `block.fetch, telemetry` |
| `addons/smart_construction_core/handlers/project_execution_block_fetch.py` | `ProjectExecutionBlockFetchHandler` | `project.execution.block.fetch` | `yes` | `odoo.addons.smart_construction_core.services.project_context_contract` | `block.fetch, scene` |
| `addons/smart_construction_core/handlers/project_execution_enter.py` | `ProjectExecutionEnterHandler` | `project.execution.enter` | `yes` | `odoo.addons.smart_construction_core.services.project_context_contract, odoo.addons.smart_construction_scene.services.project_management_entry_target` | `capability, scene` |
| `addons/smart_construction_core/handlers/project_initiation_enter.py` | `ProjectInitiationEnterHandler` | `project.initiation.enter` | `yes` | `odoo.addons.smart_construction_core.services.project_creation_service` | `scene` |
| `addons/smart_construction_core/handlers/project_plan_bootstrap_block_fetch.py` | `ProjectPlanBootstrapBlockFetchHandler` | `project.plan_bootstrap.block.fetch` | `yes` | `none` | `block.fetch, scene` |
| `addons/smart_construction_core/handlers/project_plan_bootstrap_enter.py` | `ProjectPlanBootstrapEnterHandler` | `project.plan_bootstrap.enter` | `yes` | `odoo.addons.smart_construction_scene.services.project_management_entry_target` | `capability, scene` |
| `addons/smart_construction_core/handlers/risk_action_execute.py` | `RiskActionExecuteHandler` | `risk.action.execute` | `yes` | `none` | `none` |
| `addons/smart_construction_core/handlers/settlement_slice_block_fetch.py` | `SettlementSliceBlockFetchHandler` | `settlement.block.fetch` | `yes` | `odoo.addons.smart_construction_core.services.project_context_contract` | `block.fetch` |
| `addons/smart_construction_core/handlers/settlement_slice_enter.py` | `SettlementSliceEnterHandler` | `settlement.enter` | `yes` | `odoo.addons.smart_construction_core.services.project_context_contract, odoo.addons.smart_construction_scene.services.project_management_entry_target` | `capability, scene` |
| `addons/smart_construction_core/handlers/system_ping_construction.py` | `SystemPingConstructionHandler` | `system.ping.construction` | `yes` | `none` | `none` |
| `addons/smart_construction_core/handlers/telemetry_track.py` | `TelemetryTrackHandler` | `telemetry.track` | `yes` | `none` | `telemetry` |
| `addons/smart_construction_core/handlers/usage_export_csv.py` | `UsageExportCsvHandler` | `usage.export.csv` | `yes` | `none` | `capability, usage` |
| `addons/smart_construction_core/handlers/usage_report.py` | `UsageReportHandler` | `usage.report` | `yes` | `none` | `capability, scene, usage` |
| `addons/smart_construction_core/handlers/usage_track.py` | `UsageTrackHandler` | `usage.track` | `yes` | `none` | `capability, scene, usage` |

## Core Extension Cross-Module Hooks (Evidence)

- `addons/smart_construction_core/core_extension.py:464` → `smart_core_list_capabilities_for_user`
- `addons/smart_construction_core/core_extension.py:478` → `smart_core_capability_groups`
- `addons/smart_construction_core/core_extension.py:487` → `smart_core_scene_package_service_class`
- `addons/smart_construction_core/core_extension.py:496` → `smart_core_scene_governance_service_class`
- `addons/smart_construction_core/core_extension.py:505` → `smart_core_load_scene_configs`
- `addons/smart_construction_core/core_extension.py:516` → `smart_core_has_db_scenes`

## Scan Notes

- This artifact inventories registration and semantic signals only.
- Intent ownership classification and registry-boundary judgment are deferred to next stage.
