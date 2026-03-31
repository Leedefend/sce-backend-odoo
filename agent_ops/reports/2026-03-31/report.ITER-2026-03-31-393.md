# ITER-2026-03-31-393 Report

## Summary

- Audited whether the native-to-custom parsing chain still preserves native
  capability intent from `menu / action / view` facts through to custom
  rendering and delivery behavior.
- Avoided using scene-orchestration sufficiency as the primary explanation.
- Classified key custom frontend surfaces by direct native-capability alignment.

## Changed Files

- `agent_ops/tasks/ITER-2026-03-31-393.yaml`
- `agent_ops/reports/2026-03-31/report.ITER-2026-03-31-393.md`
- `agent_ops/state/task_results/ITER-2026-03-31-393.json`
- `docs/ops/iterations/delivery_context_switch_log_v1.md`

## Verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-31-393.yaml` -> PASS

## Audit Rule

This batch answers a narrower question than `392`:

- not "can the page do anything useful"
- but "after native capability facts are parsed into custom frontend behavior,
  are the rendered result and delivery logic still aligned with the native
  capability itself"

The classifications used here are:

- `faithfully_rendered`
- `faithfully_handled`
- `semantically_shifted`

## Surface Results

### 1. `工作台`

Classification: `semantically_shifted`

#### Native Capability Basis

- `addons/smart_construction_core/services/portal_dashboard_service.py`
  defines a narrow five-entry native dashboard registry:
  - `project_work`
  - `contract_work`
  - `cost_work`
  - `finance_work`
  - `capability_matrix`
- `addons/smart_construction_core/controllers/portal_dashboard_controller.py`
  still exposes that native fact contract via `/api/contract/portal_dashboard`

#### Custom Delivery Result

- `frontend/apps/web/src/views/HomeView.vue`
  renders from:
  - `homeOrchestrationContract`
  - `session.scenes`
  - `session.capabilityGroups`
- It does not behave like a direct rendering of the five-entry native dashboard
  registry.

#### Alignment Decision

The custom `工作台` has shifted from the original native capability intent.
It is no longer a faithful frontend rendering of the native portal dashboard
fact; it has become a broader product-level orchestration surface.

### 2. `我的工作`

Classification: `faithfully_handled`

#### Native Capability Basis

- `addons/smart_construction_core/handlers/my_work_summary.py`
  builds the fact surface for `my.work.summary`
- `addons/smart_construction_core/handlers/my_work_complete.py`
  implements:
  - `my.work.complete`
  - `my.work.complete_batch`

#### Custom Delivery Result

- `frontend/apps/web/src/views/MyWorkView.vue`
  uses real summary and completion flows
- `frontend/apps/web/src/api/myWork.ts`
  calls the same native intents directly

#### Alignment Decision

The custom `我的工作` remains closely aligned with the native capability:

- the rendered list is based on native work-item facts
- the delivery logic completes the same native todo items
- the page is not reinterpreting the capability into a different product meaning

This is a faithful handling surface.

### 3. `生命周期驾驶舱`

Classification: `faithfully_handled`

#### Native Capability Basis

- the native capability intent is `project.management`
- `ProjectManagementDashboardView` still loads through the corresponding entry
  and runtime block intent chain

#### Custom Delivery Result

- `frontend/apps/web/src/views/ProjectManagementDashboardView.vue`
  performs:
  - entry loading via native intent chain
  - block refresh via native runtime hints
  - action execution through the same backend intent surface
  - scene reload after action execution

#### Alignment Decision

For the audited non-finance subset, the custom lifecycle dashboard is still
delivering the same native capability intent:

- inspect project state
- execute next-step actions
- submit non-finance operational records such as cost entry

So this surface is best classified as faithfully handled, not semantically
shifted.

### 4. `能力矩阵`

Classification: `faithfully_rendered`

#### Native Capability Basis

- `addons/smart_construction_core/services/capability_matrix_service.py`
  resolves native menu/action capability entries and emits:
  - `target_url`
  - `menu_id`
  - `action_id`
  - allow/deny state

#### Custom Delivery Result

- `frontend/apps/web/src/api/capabilityMatrix.ts`
  consumes the real backend contract
- `frontend/apps/web/src/views/CapabilityMatrixView.vue`
  renders those entries and normalizes native portal anchors into SPA-owned
  routes

#### Alignment Decision

The custom capability-matrix page does not change the underlying capability
meaning. It remains a governance/readability surface that renders native
capability visibility and opens allowed targets.

This is a faithful rendering of the native capability intent.

## Main Conclusion

The native-to-custom parsing chain is mixed:

- `我的工作` = faithful handling
- `生命周期驾驶舱` = faithful handling
- `能力矩阵` = faithful rendering
- `工作台` = semantic shift

So the parsing pipeline is not globally broken, but it is also not globally
uniform. The real alignment issue is concentrated in `工作台`, where custom
delivery has expanded beyond the original native capability definition.

## Risk Analysis

- Risk remained low because this batch was audit-only.
- No implementation files were modified.
- The main follow-up risk is governance wording and ownership clarity around
  `工作台`, not a generic parsing failure across all custom surfaces.

## Rollback

- `git restore agent_ops/tasks/ITER-2026-03-31-393.yaml`
- `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`
- `git restore agent_ops/reports/2026-03-31/report.ITER-2026-03-31-393.md`
- `git restore agent_ops/state/task_results/ITER-2026-03-31-393.json`

## Next Suggestion

- If a follow-up batch is needed, it should focus only on `工作台` native-capability
  alignment rather than reopening the whole custom-frontend chain.
