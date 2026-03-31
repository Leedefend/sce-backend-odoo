# ITER-2026-03-30-362 Report

## Summary

- Re-anchored the active line from scene cleanup back to industry business-fact usability.
- Audited the currently published `21` preview menus against their real fact chain:
  - `menu`
  - `action`
  - `model`
  - `view`
  - `permission`
  - `data/context prerequisite`
- Collapsed the menu set into three execution-ready classes:
  - `native_usable`: `16`
  - `data_or_context_dependent`: `1`
  - `custom_frontend_required`: `4`

## Changed Files

- `agent_ops/tasks/ITER-2026-03-30-362.yaml`
- `agent_ops/reports/2026-03-30/report.ITER-2026-03-30-362.md`
- `agent_ops/state/task_results/ITER-2026-03-30-362.json`
- `docs/ops/iterations/delivery_context_switch_log_v1.md`

## Verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-30-362.yaml` -> PASS

## Fact Matrix

### A. Native Usable (`16`)

These entries already have a complete original business fact chain:

- concrete `ir.actions.act_window`
- resolvable `res_model`
- concrete view mode and view definition
- PM menu-group match
- PM ACL match

Rows:

- `项目立项`
- `快速创建项目`
- `项目台账（试点）`
- `项目列表（演示）`
- `投标管理`
- `工程资料`
- `工程结构`
- `阶段要求配置`
- `项目驾驶舱` (`action_project_dashboard`)
- `项目驾驶舱（演示）`
- `项目指标`
- `付款/收款申请`
- `结算单`
- `资金台账`
- `付款记录`
- `业务字典`

Interpretation:

- These are already usable through the original model/menu/action/view path.
- Their remaining product work is not “make it reachable”, but only optional data quality, labeling, or custom-frontend takeover decisions.
- Empty demo data may reduce business value on some pages, but does not break their native usability classification.

### B. Data or Context Dependent (`1`)

- `执行结构`
  - menu: `smart_construction_core.menu_sc_project_wbs`
  - action: `smart_construction_core.action_exec_structure_entry`
  - type: `ir.actions.server`
  - prerequisite: a concrete project context is required before the real execution-structure windows become meaningful
  - current native behavior: warns the user and redirects to `项目列表` when project context is missing

Interpretation:

- The fact chain is valid, but usability depends on prior project selection rather than a standalone menu open.
- This is the highest-value native-fact repair target if the next batch wants to improve immediate user success rate.

### C. Custom Frontend Required (`4`)

These entries remain valid publication anchors in the original menu/action system, but their usable surface is no longer the abandoned native frontend.

- `项目驾驶舱`
  - menu: `smart_construction_core.menu_sc_project_management_scene`
  - anchor type: `scene_route_only`
  - current user surface: custom frontend scene `/s/project.management`

- `工作台`
  - action: `smart_construction_portal.action_sc_portal_dashboard`
  - type: `ir.actions.act_url`
  - original URL: `/portal/dashboard`

- `生命周期驾驶舱`
  - action: `smart_construction_portal.action_sc_portal_lifecycle`
  - type: `ir.actions.act_url`
  - original URL: `/portal/lifecycle`

- `能力矩阵`
  - action: `smart_construction_portal.action_sc_portal_capability_matrix`
  - type: `ir.actions.act_url`
  - original URL: `/portal/capability-matrix`

Interpretation:

- Their native fact anchor is valid and should remain published.
- Their user-facing fulfillment belongs to the custom frontend lane, not to the abandoned native portal frontend.
- They should not be treated as native Odoo page defects in future usability repair tasks.

## Risk Analysis

- Risk level remains low because this batch is audit-only.
- The main decision risk was misclassifying scene/portal anchors as broken native business pages.
- That ambiguity is now reduced:
  - native `act_window` pages can be repaired or improved through fact-chain work
  - context-sensitive runtime entries are a separate repair lane
  - portal/scene anchors are custom-frontend fulfillment items, not native frontend bugs

## Rollback

- `git restore agent_ops/tasks/ITER-2026-03-30-362.yaml`
- `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`
- `git restore agent_ops/reports/2026-03-30/report.ITER-2026-03-30-362.md`
- `git restore agent_ops/state/task_results/ITER-2026-03-30-362.json`

## Next Suggestion

- Open the next fact-driven repair batch on the narrowest real usability gap:
  - `执行结构` context bridge and first-success path
- Keep `工作台 / 生命周期驾驶舱 / 能力矩阵 / 项目驾驶舱(scene)` in the custom-frontend fulfillment backlog rather than mixing them back into native fact repair.
