# ITER-2026-03-31-391 Report

## Summary

- Audited whether the current `工作台` should still be treated as a direct rendering of the native `portal.dashboard` fact anchor.
- Confirmed that the native portal dashboard fact anchor still exists and remains narrow and stable.
- Confirmed that the current custom `工作台` has evolved into a broader product orchestration surface rather than a direct native fact rendering.

## Changed Files

- `agent_ops/tasks/ITER-2026-03-31-391.yaml`
- `agent_ops/reports/2026-03-31/report.ITER-2026-03-31-391.md`
- `agent_ops/state/task_results/ITER-2026-03-31-391.json`
- `docs/ops/iterations/delivery_context_switch_log_v1.md`

## Verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-31-391.yaml` -> PASS

## Audit Basis

### Native Fact Anchor Still Exists

- `addons/smart_construction_core/controllers/portal_dashboard_controller.py`
  - `/api/contract/portal_dashboard` still serves `PortalDashboardService.build_dashboard()`
- `addons/smart_construction_core/services/portal_dashboard_service.py`
  - the native dashboard remains a fixed five-entry registry:
    - `project_work`
    - `contract_work`
    - `cost_work`
    - `finance_work`
    - `capability_matrix`

This means the original native fact anchor still exists and has not been removed.

### Scene Layer Still Publishes A Dashboard-Oriented Fact Shape

- `addons/smart_construction_scene/data/sc_scene_layout.xml`
  - `portal.dashboard` still declares:
    - workspace page type
    - `overview / focus_actions / alerts` zones
    - computed providers `portal.dashboard.summary` and `portal.dashboard.alerts`

This means the scene layer still recognizes `portal.dashboard` as a dashboard-oriented fact surface.

### Current Custom `工作台` Is Product-Orchestrated

- `frontend/apps/web/src/views/HomeView.vue`
  - binds `:contract=\"homeOrchestrationContract\"`
  - derives entries from `session.scenes`
  - derives cards from `session.capabilityGroups`
  - loads `workspace.home` / `portal.dashboard` on demand through the unified orchestration path
  - renders a broader workspace/home product surface instead of directly mirroring the five-entry native dashboard registry

This means the current custom `工作台` is no longer a narrow frontend rendering of the native portal dashboard facts.

## Classification Decision

### `工作台`: Product Orchestration Surface

The current `工作台` should be formally classified as a product-level orchestration surface.

It is not accurate anymore to treat it as a direct rendering of the native `portal.dashboard` fact anchor, because:

- its entry set is built from orchestrated scene/session state
- its layout is driven by orchestration contracts
- its capability grouping is broader than the native five-entry registry

## Consistency Decision

The remaining `工作台` topic is therefore not an active fact-consistency defect.

It is a classification / ownership clarification:

- native `portal.dashboard` remains a valid fact anchor
- custom `工作台` remains a valid product surface
- the two should not be described as the same frontend rendering artifact

## Main Conclusion

- The explicit consistency-repair line opened by ITER-2026-03-31-388 is now closed.
- `能力矩阵` route drift has already been repaired in `389/390`.
- `工作台` should now be treated as a formally reclassified product orchestration surface rather than as a broken direct native-dashboard rendering.

## Risk Analysis

- Risk remained low because this batch was audit-only.
- No code changes were made.
- The remaining follow-up, if any, is governance wording / ownership clarification rather than implementation repair.

## Rollback

- `git restore agent_ops/tasks/ITER-2026-03-31-391.yaml`
- `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`
- `git restore agent_ops/reports/2026-03-31/report.ITER-2026-03-31-391.md`
- `git restore agent_ops/state/task_results/ITER-2026-03-31-391.json`

## Next Suggestion

- Close the current fact-to-custom consistency line.
- If another batch is needed, open it as a governance wording / ownership objective rather than a repair objective.
