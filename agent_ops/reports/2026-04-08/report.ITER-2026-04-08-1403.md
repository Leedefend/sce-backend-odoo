# ITER-2026-04-08-1403 Report

## Batch
- Batch: `1/1`
- Mode: `scan`

## Summary of change
- 本批仅做差异候选扫描，不做归因裁决与实现。
- 依据：
  - 原生复用规范：`docs/architecture/native_view_reuse_frontend_spec_v1.md:25`
  - 当前 tree/form/kanban 页面与 runtime 入口实现。

## Scan candidates (for screen stage)
- C1 (`tree` 交互层)：`ListPage` 使用自定义 `PageToolbar + batch-bar` 组合，需核对与原生 control panel/列表操作语义映射是否一一对应。证据：
  - `frontend/apps/web/src/pages/ListPage.vue:16`
  - `frontend/apps/web/src/pages/ListPage.vue:85`
- C2 (`tree` 搜索层)：前端存在 contract filters/saved filters/group by 组合消费路径，需核对是否完全受 search view 契约驱动。证据：
  - `frontend/apps/web/src/pages/ListPage.vue:49`
  - 规范约束：`docs/architecture/native_view_reuse_frontend_spec_v1.md:132`
- C3 (`form` 页头动作)：`ContractFormPage` 暴露调试动作（复制/导出契约、重新加载），需筛选其是否应从生产对齐口径剥离。证据：
  - `frontend/apps/web/src/pages/ContractFormPage.vue:32`
  - `frontend/apps/web/src/pages/ContractFormPage.vue:33`
  - `frontend/apps/web/src/pages/ContractFormPage.vue:34`
- C4 (`form` 结构一致性)：虽然 form 支持 header/group/notebook/modifiers/x2many，但需核查是否存在与原生结构顺序冲突的自定义重排。证据：
  - `frontend/apps/web/src/pages/ContractFormPage.vue:2236`
  - `frontend/apps/web/src/pages/ContractFormPage.vue:2315`
  - 规范约束：`docs/architecture/native_view_reuse_frontend_spec_v1.md:26`
- C5 (`kanban` 分栏逻辑)：`KanbanPage` 当前分栏依赖 `statusFields` 推导，需核查与原生 `group_by`/kanban 语义是否一致。证据：
  - `frontend/apps/web/src/pages/KanbanPage.vue:134`
  - `frontend/apps/web/src/pages/KanbanPage.vue:179`
  - `frontend/apps/web/src/app/action_runtime/useActionViewContractShapeRuntime.ts:127`
- C6 (`kanban` 状态渲染)：卡片 tone 使用 `state/stage_id/status` 本地归一，需 screen 判断是否属于合法通用语义消费。证据：
  - `frontend/apps/web/src/pages/KanbanPage.vue:213`
- C7 (`view runtime` 多形态路径)：`ActionView` 存在 list/kanban/advanced_view 多分支，需确认 advanced 分支是否属于原生增强而非结构替代。证据：
  - `frontend/apps/web/src/views/ActionView.vue:302`
  - `frontend/apps/web/src/views/ActionView.vue:393`
- C8 (`parity verification coverage`)：现有 parity 验证脚本仅覆盖 form/tree 的 `ui.contract`，kanban 未纳入同级 parity 检查。证据：
  - `scripts/verify/native_business_admin_config_center_intent_parity_verify.py:105`
  - `scripts/verify/native_business_admin_config_center_intent_parity_verify.py:109`

## Verification result
- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-08-1403.yaml` ✅

## Risk analysis
- 结论：`PASS`
- 风险级别：low
- 说明：本批仅候选扫描，未触发业务行为变更。

## Rollback suggestion
- `git restore agent_ops/tasks/ITER-2026-04-08-1403.yaml`
- `git restore agent_ops/reports/2026-04-08/report.ITER-2026-04-08-1403.md`
- `git restore agent_ops/state/task_results/ITER-2026-04-08-1403.json`
- `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`

## Next iteration suggestion
- 启动 `screen` 阶段：
  - 分类 C1~C8 为 `结构差异 / 交互差异 / 验证覆盖缺口`；
  - 输出 P0（先做）与 P1（后做）实现批次顺序。
