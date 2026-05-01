# Current Project Scope Contract Matrix v1

## Purpose

当前项目上下文不是前端筛选条件，而是平台级访问契约。用户一旦选择当前项目，所有项目承载业务能力必须由后端统一执行项目域限制；前端只负责透传 `current_project_id` 并按后端契约渲染结果。

## Contract Boundary

Layer Target: Platform project scope contract enforcement

Module:
- `addons/smart_core`: context contract, intent data access, record-bound platform intents
- `addons/smart_construction_core`: project-scoped business aggregations and execution projections
- `frontend/apps/web`: context propagation only

Reason: 项目级隔离属于契约体系边界，不能只在项目列表、合同列表等单页局部实现。

## Contract Invariants

1. `system.init.project_context` is the only shell source for current project selection.
2. Frontend must propagate `current_project_id` through the intent envelope and `params.context`.
3. Backend must enforce scope for project-bearing models:
   - `project.project`: `id = current_project_id`
   - models with `project_id -> project.project`: `project_id = current_project_id`
   - models with `project_ids -> project.project`: `project_ids in [current_project_id]`
4. Models without project relation are public/shared for this contract and must not be filtered by guessing.
5. Record-bound write/read side-effect intents must reject out-of-scope records with `PROJECT_SCOPE_DENIED`.
6. Aggregation/workbench/domain services that bypass `api.data` must explicitly consume current project context or be classified as public configuration.
7. Any covered intent must be runtime-registerable. If `core_extension.get_intent_handler_contributions()` skips a handler because its service modules are missing, the contract is not covered even if the handler file still exists.

## Coverage Matrix

| Area | Intent / Entry | Scope Requirement | Current Status | Evidence / Owner |
| --- | --- | --- | --- | --- |
| Startup contract | `system.init` / `app.init` | emit `project_context`, echo selected project | Covered | `addons/smart_core/handlers/system_init.py` |
| Project selector search | `project.context.search` | public selector, no selected-project self-filter | Covered | `addons/smart_core/handlers/project_context.py` |
| Frontend propagation | all non-bootstrap intents | inject `current_project_id` into envelope and params context | Covered | `frontend/apps/web/src/api/intents.ts` |
| Generic list/read/count/export/create/write | `api.data` | apply model-derived project domain or deny out-of-scope mutation | Covered | `addons/smart_core/handlers/api_data.py` |
| Dedicated write API | `api.data.create` / `api.data.write` | check existing record scope; prevent project move; default project on create when allowed | Covered | `addons/smart_core/handlers/api_data_write.py` |
| Batch mutation | `api.data.batch` | reject mixed/out-of-scope record sets | Covered | `addons/smart_core/handlers/api_data_batch.py` |
| Delete mutation | `api.data.unlink` | reject out-of-scope record sets before unlink | Covered | `addons/smart_core/handlers/api_data_unlink.py` |
| Button side effects | `execute_button` | reject out-of-scope target record before object/action method | Covered | `addons/smart_core/handlers/execute_button.py` |
| Onchange roundtrip | `api.onchange` | when editing existing record, reject out-of-scope record before onchange | Covered | `addons/smart_core/handlers/api_onchange.py` |
| Chatter write | `chatter.post` | reject out-of-scope target record before message post | Covered | `addons/smart_core/handlers/chatter_post.py` |
| Chatter activity write | `chatter.activity.schedule` | reject out-of-scope target record before activity create | Covered | `addons/smart_core/handlers/chatter_activity_schedule.py` |
| Chatter timeline read | `chatter.timeline` | reject out-of-scope target record before loading messages/attachments/audit | Covered | `addons/smart_core/handlers/chatter_timeline.py` |
| File upload | `file.upload` | reject out-of-scope target record before attachment create | Covered | `addons/smart_core/handlers/file_upload.py` |
| File download | `file.download` | reject out-of-scope attachment business record before returning data | Covered | `addons/smart_core/handlers/file_download.py` |
| My work aggregation | `my.work.summary` | filter project-bearing rows and recompute counts after scope | Covered | `addons/smart_construction_core/handlers/my_work_summary.py` |
| Execution projection | `ProjectExecutionItemProjectionService` | project-scoped system items when current project exists | Covered | `addons/smart_construction_core/services/project_execution_item_projection_service.py` |
| Execution runtime services | `project.execution.enter` / `project.execution.block.fetch` / `project.execution.advance` | execution builders and advance services must exist and import cleanly before registry contribution | Covered with runtime import guard | `addons/smart_construction_core/services/project_execution_*` |
| Project dashboard/slices | `project.*.enter`, `*.block.fetch`, `payment.enter`, `payment.block.fetch`, `payment.record.create`, `settlement.enter`, `settlement.block.fetch`, `cost.tracking.enter`, `cost.tracking.block.fetch`, `cost.tracking.record.create` | reject explicit `project_id` mismatch with current project; runtime service dependencies must import cleanly | Covered with runtime import guard | `addons/smart_construction_core/handlers/*enter.py`, `addons/smart_construction_core/services/*_builders` |
| Business approval/actions | `payment.request.*`, `risk.action.execute`, `project.execution.advance` | must guard target record through domain service or record-bound scope check | Covered for record/project mismatch guard; still requires live state-path acceptance | Domain handlers own business transition semantics |
| Public configuration | `app.nav`, `app.catalog`, `ui.contract`, `meta.*`, `scene.*`, `user.view.preference.*`, `search.favorite.set` | no project filtering unless returning project-bearing records | Exempt / Context-transparent | Platform configuration, preferences, and contracts |
| Telemetry / usage | `usage.*`, `telemetry.track` | no project filtering for audit counters unless rows are project-bearing | Exempt / Observability | Runtime telemetry |

## Mandatory Review Rule

Any new intent must be classified into one of these categories before merge:

- `project_scoped_data`: generic data access or business rows with project relation
- `record_bound_side_effect`: operates on `model/res_id` and must call record scope guard
- `project_explicit_scene`: receives `project_id` and must reject mismatch with current project
- `public_configuration`: does not expose project-bearing business data
- `observability`: telemetry/audit only

Unclassified intent = contract architecture gap.

## Registry Rule

For extension-provided intents, coverage requires all three layers:

1. Handler file contains the scope guard.
2. Handler dependencies exist and import cleanly.
3. `core_extension.get_intent_handler_contributions()` contributes the intent to the platform registry.

If any layer fails, the runtime result can degrade to `Unknown intent`, which is an architecture coverage failure rather than a successful project-scope denial.

## Known Follow-Up

Domain-specific business transition intents now have project mismatch guards, but each transition still requires live state-path acceptance with valid business records. That acceptance must verify business state semantics and approval handoff, not just the project scope boundary.
