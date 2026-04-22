# Intent Semantic Classification (Phase B-2 / Screen)

- Stage: `screen` (classification from existing inventory only)
- Input: `docs/audit/boundary/handler_inventory.md`

## Category Summary

- `业务意图`: `32`
- `平台意图`: `4`
- `观测意图`: `4`
- `运营治理意图`: `0`
- `场景运行时意图`: `3`

| Intent | Handler Class | Handler File | Category | Signal Evidence |
|---|---|---|---|---|
| `business.evidence.trace` | `BusinessEvidenceTraceHandler` | `addons/smart_construction_core/handlers/business_evidence_trace.py` | 业务意图 | `none` |
| `cost.tracking.block.fetch` | `CostTrackingBlockFetchHandler` | `addons/smart_construction_core/handlers/cost_tracking_block_fetch.py` | 业务意图 | `block.fetch` |
| `cost.tracking.enter` | `CostTrackingEnterHandler` | `addons/smart_construction_core/handlers/cost_tracking_enter.py` | 业务意图 | `capability, scene` |
| `cost.tracking.record.create` | `CostTrackingRecordCreateHandler` | `addons/smart_construction_core/handlers/cost_tracking_record_create.py` | 业务意图 | `none` |
| `my.work.complete` | `MyWorkCompleteHandler` | `addons/smart_construction_core/handlers/my_work_complete.py` | 业务意图 | `none` |
| `my.work.complete_batch` | `MyWorkCompleteBatchHandler` | `addons/smart_construction_core/handlers/my_work_complete.py` | 业务意图 | `none` |
| `n/a` | `_BasePaymentApprovalHandler` | `addons/smart_construction_core/handlers/payment_request_approval.py` | 业务意图 | `none` |
| `payment.block.fetch` | `PaymentSliceBlockFetchHandler` | `addons/smart_construction_core/handlers/payment_slice_block_fetch.py` | 业务意图 | `block.fetch` |
| `payment.enter` | `PaymentSliceEnterHandler` | `addons/smart_construction_core/handlers/payment_slice_enter.py` | 业务意图 | `capability, scene` |
| `payment.record.create` | `PaymentSliceRecordCreateHandler` | `addons/smart_construction_core/handlers/payment_slice_record_create.py` | 业务意图 | `none` |
| `payment.request.approve` | `PaymentRequestApproveHandler` | `addons/smart_construction_core/handlers/payment_request_approval.py` | 业务意图 | `none` |
| `payment.request.available_actions` | `PaymentRequestAvailableActionsHandler` | `addons/smart_construction_core/handlers/payment_request_available_actions.py` | 业务意图 | `none` |
| `payment.request.done` | `PaymentRequestDoneHandler` | `addons/smart_construction_core/handlers/payment_request_approval.py` | 业务意图 | `none` |
| `payment.request.execute` | `PaymentRequestExecuteHandler` | `addons/smart_construction_core/handlers/payment_request_execute.py` | 业务意图 | `none` |
| `payment.request.reject` | `PaymentRequestRejectHandler` | `addons/smart_construction_core/handlers/payment_request_approval.py` | 业务意图 | `none` |
| `payment.request.submit` | `PaymentRequestSubmitHandler` | `addons/smart_construction_core/handlers/payment_request_approval.py` | 业务意图 | `none` |
| `project.connection.transition` | `ProjectConnectionTransitionHandler` | `addons/smart_construction_core/handlers/project_connection_transition.py` | 业务意图 | `none` |
| `project.dashboard` | `ProjectDashboardHandler` | `addons/smart_construction_core/handlers/project_dashboard.py` | 业务意图 | `none` |
| `project.dashboard.block.fetch` | `ProjectDashboardBlockFetchHandler` | `addons/smart_construction_core/handlers/project_dashboard_block_fetch.py` | 业务意图 | `block.fetch, scene` |
| `project.dashboard.enter` | `ProjectDashboardEnterHandler` | `addons/smart_construction_core/handlers/project_dashboard_enter.py` | 业务意图 | `capability, scene` |
| `project.dashboard.open` | `ProjectDashboardOpenHandler` | `addons/smart_construction_core/handlers/project_dashboard_open.py` | 业务意图 | `none` |
| `project.entry.context.options` | `ProjectEntryContextOptionsHandler` | `addons/smart_construction_core/handlers/project_entry_context_options.py` | 业务意图 | `none` |
| `project.entry.context.resolve` | `ProjectEntryContextResolveHandler` | `addons/smart_construction_core/handlers/project_entry_context_resolve.py` | 业务意图 | `none` |
| `project.execution.advance` | `ProjectExecutionAdvanceHandler` | `addons/smart_construction_core/handlers/project_execution_advance.py` | 业务意图 | `block.fetch, telemetry` |
| `project.execution.block.fetch` | `ProjectExecutionBlockFetchHandler` | `addons/smart_construction_core/handlers/project_execution_block_fetch.py` | 业务意图 | `block.fetch, scene` |
| `project.execution.enter` | `ProjectExecutionEnterHandler` | `addons/smart_construction_core/handlers/project_execution_enter.py` | 业务意图 | `capability, scene` |
| `project.initiation.enter` | `ProjectInitiationEnterHandler` | `addons/smart_construction_core/handlers/project_initiation_enter.py` | 业务意图 | `scene` |
| `project.plan_bootstrap.block.fetch` | `ProjectPlanBootstrapBlockFetchHandler` | `addons/smart_construction_core/handlers/project_plan_bootstrap_block_fetch.py` | 业务意图 | `block.fetch, scene` |
| `project.plan_bootstrap.enter` | `ProjectPlanBootstrapEnterHandler` | `addons/smart_construction_core/handlers/project_plan_bootstrap_enter.py` | 业务意图 | `capability, scene` |
| `risk.action.execute` | `RiskActionExecuteHandler` | `addons/smart_construction_core/handlers/risk_action_execute.py` | 业务意图 | `none` |
| `settlement.block.fetch` | `SettlementSliceBlockFetchHandler` | `addons/smart_construction_core/handlers/settlement_slice_block_fetch.py` | 业务意图 | `block.fetch` |
| `settlement.enter` | `SettlementSliceEnterHandler` | `addons/smart_construction_core/handlers/settlement_slice_enter.py` | 业务意图 | `capability, scene` |
| `capability.describe` | `CapabilityDescribeHandler` | `addons/smart_construction_core/handlers/capability_describe.py` | 场景运行时意图 | `capability` |
| `capability.visibility.report` | `CapabilityVisibilityReportHandler` | `addons/smart_construction_core/handlers/capability_visibility_report.py` | 场景运行时意图 | `capability` |
| `my.work.summary` | `MyWorkSummaryHandler` | `addons/smart_construction_core/handlers/my_work_summary.py` | 场景运行时意图 | `scene` |
| `app.catalog` | `AppCatalogHandler` | `addons/smart_construction_core/handlers/app_catalog.py` | 平台意图 | `catalog, scene` |
| `app.nav` | `AppNavHandler` | `addons/smart_construction_core/handlers/app_nav.py` | 平台意图 | `app.nav` |
| `app.open` | `AppOpenHandler` | `addons/smart_construction_core/handlers/app_open.py` | 平台意图 | `app.open` |
| `system.ping.construction` | `SystemPingConstructionHandler` | `addons/smart_construction_core/handlers/system_ping_construction.py` | 平台意图 | `none` |
| `telemetry.track` | `TelemetryTrackHandler` | `addons/smart_construction_core/handlers/telemetry_track.py` | 观测意图 | `telemetry` |
| `usage.export.csv` | `UsageExportCsvHandler` | `addons/smart_construction_core/handlers/usage_export_csv.py` | 观测意图 | `capability, usage` |
| `usage.report` | `UsageReportHandler` | `addons/smart_construction_core/handlers/usage_report.py` | 观测意图 | `capability, scene, usage` |
| `usage.track` | `UsageTrackHandler` | `addons/smart_construction_core/handlers/usage_track.py` | 观测意图 | `capability, scene, usage` |

## Screening Notes

- This output is semantic grouping only, not ownership final judgment.
- Registry ownership conclusion is deferred to Phase B-3 audit batch.
