# ITER-2026-04-09-1430 Report

## Batch
- Batch: `1/1`
- Mode: `screen`

## Architecture declaration
- Layer Target: `Governance root-cause classification`
- Module: `role-mainline parity gap judgement`
- Module Ownership: `verify runtime`
- Kernel or Scenario: `scenario`
- Reason: 按用户要求，先完成完整事实判断，再安排下一步执行。

## Evidence baseline
- 主线角色扫描（校准版）：`artifacts/playwright/iter-2026-04-09-1429/role_mainline_full_scan_v2.json`
- 交互差异证据：`artifacts/playwright/iter-2026-04-09-1428/interaction_matrix_action26.json`
- 分类矩阵：`artifacts/playwright/iter-2026-04-09-1430/classification_matrix.json`

## Fact judgement (by requested layers)
- 业务事实层模型（data/model）
  - 事实：`projects.list/ledger/intake/dashboard` 在 custom/native 均指向 `project.project`，首屏样本量一致（20）。
  - 判断：当前样本下**不是主根因**。

- 权限与定义层（permission/definition）
  - 事实：三角色（admin/pm/executive）在 sampled actions 上 custom/native 的 `read/write/create/unlink` 均为 `true`。
  - 判断：当前样本下**不是主根因**。

- 平台解释层契约承载（contract carrying）
  - 事实：custom `ui.contract(action_open)` 的 `head.view_mode` 持续为 `null`，native action 明确给出 `view_mode`（如 `list,kanban,form` / `form`）。
  - 判断：**存在真实承载不足**，会削弱前端对“主视图顺序与能力口径”的忠实对齐。

- 前端消费岔路（frontend consumption）
  - 事实：1428 交互证据中，native 搜索 `67->7`，custom `40->40`；native `group.available=false`，custom `group.available=true`。
  - 判断：**存在真实消费侧偏差**（输入控件存在但过滤未等价绑定、分组入口暴露口径与原生样本不一致）。

## Consolidated truth
- 与事实最一致的根因排序：
  1. `platform_contract_carrying_insufficient`（view_mode 等关键编排语义未完整承载）
  2. `frontend_consumption_branch`（搜索/分组交互绑定与原生口径不等价）
  3. `business_fact_or_permission`（本轮证据不支持其为主根因）

## Execution-ready next plan
- P0（先修）平台契约承载补齐
  - 为 action_open 输出稳定 `view_mode` 与主视图优先级（tree/form/kanban 顺序语义）。
- P1（并行或紧随）前端消费收敛
  - 搜索控件仅绑定当前列表过滤主链；
  - 分组入口严格按契约/原生可用性显隐。
- P2（收口验证）
  - 角色维度（admin/pm/executive）+ 主线场景全链路回归一次，避免每次小改都跑全链路。

## Verification result
- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-09-1430.yaml` ✅

## Risk analysis
- 结论：`PASS_WITH_RISK`
- 风险级别：medium
- 风险说明：若先改前端不补齐契约承载，后续仍会出现“页面看起来接近但交互不等价”的重复偏差。

## Rollback suggestion
- `git restore agent_ops/reports/2026-04-09/report.ITER-2026-04-09-1430.md`
- `git restore agent_ops/state/task_results/ITER-2026-04-09-1430.json`
- `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`

## Next suggestion
- 进入实现批：先做契约承载（P0），再做前端消费（P1），批末一次性做角色主线全链路验证（P2）。
