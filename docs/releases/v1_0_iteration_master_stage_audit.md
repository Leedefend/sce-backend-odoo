# v1.0 产品表达层迭代 · 大阶段复核清单

## 复核方法

- 以 Task Pack 01–11 为主线逐项核对；
- 以“文档产物 + 代码落点 + verify 结果”为三类证据；
- 输出状态：`已完成` / `已完成（含后续收口）` / `待收口`。

## 第 1 批复核（Task Pack 01/02/03）

### Task Pack 01：冻结范围

- 状态：`已完成`
- 证据：
  - `docs/releases/v1_0_iteration_round_1_scope.md`
  - `docs/releases/v1_0_iteration_round_1_scope.en.md`

### Task Pack 02：页面模式规范

- 状态：`已完成`
- 证据：
  - `docs/product/page_mode_spec_v1.md`
  - `docs/product/page_mode_spec_v1.en.md`
  - `frontend/apps/web/src/app/pageMode.ts`

### Task Pack 03：页面骨架规范与收敛

- 状态：`已完成（含后续收口）`
- 证据：
  - `docs/product/page_shell_guideline_v1.md`
  - `docs/product/page_shell_guideline_v1.en.md`
  - `frontend/apps/web/src/pages/ListPage.vue`
  - `frontend/apps/web/src/components/page/PageHeader.vue`
  - `frontend/apps/web/src/components/page/PageToolbar.vue`

## 第 2 批复核（Task Pack 04/05/06）

### Task Pack 04：`project.management`

- 状态：`已完成`
- 证据：
  - `frontend/apps/web/src/views/ProjectManagementDashboardView.vue`
  - `frontend/apps/web/src/components/page/ZoneRenderer.vue`
  - `verify.project.dashboard.contract` 已通过

### Task Pack 05：`projects.ledger`

- 状态：`已完成`
- 证据：
  - `frontend/apps/web/src/views/ActionView.vue`（总览层）
  - `docs/product/projects_ledger_information_structure_v1.md`
  - `docs/product/projects_ledger_information_structure_v1.en.md`

### Task Pack 06：`projects.list`

- 状态：`已完成（含后续收口）`
- 证据：
  - `addons/smart_construction_scene/data/sc_scene_list_profile.xml`
  - `frontend/apps/web/src/pages/ListPage.vue`
  - `frontend/apps/web/src/utils/semantic.ts`

## 第 3 批复核（Task Pack 07/08/09）

### Task Pack 07：三列表页收敛

- 状态：`已完成（含 round2/round3 收口）`
- 证据：
  - `docs/product/list_pages_convergence_v1.md`
  - `docs/product/list_pages_convergence_v1.en.md`
  - `frontend/apps/web/src/views/ActionView.vue`
  - `frontend/apps/web/src/pages/ListPage.vue`

### Task Pack 08：字段语义中文化

- 状态：`已完成（含 round3 补强）`
- 证据：
  - `docs/product/field_semantic_mapping_v1.md`
  - `docs/product/field_semantic_mapping_v1.en.md`
  - `frontend/apps/web/src/utils/display.ts`
  - `frontend/apps/web/src/utils/semantic.ts`

### Task Pack 09：演示数据补齐

- 状态：`已完成`
- 证据：
  - `docs/demo/demo_data_round_1_plan.md`
  - `docs/demo/demo_data_round_1_plan.en.md`
  - `addons/smart_construction_demo/data/base/25_project_tasks.xml`
  - `addons/smart_construction_demo/__manifest__.py`

## 第 4 批复核（Task Pack 10/11）

### Task Pack 10：产品表达验证清单

- 状态：`已完成`
- 证据：
  - `docs/releases/v1_0_iteration_round_1_checklist.md`
  - `docs/releases/v1_0_iteration_round_1_checklist.en.md`

### Task Pack 11：最小回归验证

- 状态：`已完成（prod-sim 已跑通）`
- 证据：
  - `docs/releases/v1_0_iteration_round_1_regression_report.md`
  - `docs/releases/v1_0_iteration_round_1_regression_report.en.md`
  - `docs/releases/v1_0_iteration_round_3_task_12_report.md`
  - `make ENV=test ENV_FILE=.env.prod.sim verify.phase_next.evidence.bundle` 已通过

## 缺口清单（当前）

- `待收口`：等待“本次大阶段登录验证”反馈后，做最后一轮 UI 细节与文案阈值修正；
- `无结构性缺口`：Task Pack 01–11 主体已落地并有证据。

## 下一动作

1. 你完成大阶段登录验证后给我统一反馈；
2. 我按反馈生成 `v1_0_iteration_round_4_feedback_closure.md`；
3. 执行同一套最小回归并产出最终收口报告。
