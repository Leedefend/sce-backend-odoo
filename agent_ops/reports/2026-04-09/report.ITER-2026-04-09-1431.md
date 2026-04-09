# ITER-2026-04-09-1431 Report

## Batch
- Batch: `1/1`
- Mode: `scan`

## Architecture declaration
- Layer Target: `Governance role-based fact scan`
- Module: `customer mainline lifecycle parity evidence`
- Module Ownership: `verify runtime`
- Kernel or Scenario: `scenario`
- Reason: 按用户要求执行角色并行采样，覆盖项目主线与全流程可见入口。

## Evidence artifacts
- 并行角色主线采样：`artifacts/playwright/iter-2026-04-09-1431/parallel_role_lifecycle_scan.json`
- 原生/自定义全流程入口对照：`artifacts/playwright/iter-2026-04-09-1431/lifecycle_menu_visibility_compare.json`
- 汇总矩阵：`artifacts/playwright/iter-2026-04-09-1431/scan_summary_matrix.json`

## Raw scan coverage
- 并行角色：`admin` / `sc_fx_pm` / `sc_fx_executive`
- 主线场景：`projects.intake` / `projects.list` / `projects.ledger` / `project.dashboard` / `project.management`
- 采样维度：
  - 入口可见性（native menus vs custom scenes）
  - 页面结构（view_mode / views / view_keys / list_columns_count）
  - 数据样本（list/search_read sample_count）
  - 操作可用性（read/write/create/unlink）

## Scan candidates (no root-cause conclusion in this stage)
- C1: 三角色在主线场景均可登录并可达核心项目场景。
- C2: `project.management` 在 custom scene target 中仍为 route-only（无 action_id）。
- C3: 主线 sampled actions 上 custom `view_mode` 为空，而 native `view_mode` 均有明确值。
- C4: 主线 sampled actions 上三角色 custom/native 权限布尔值一致（均可操作）。
- C5: 全流程入口维度中，native 菜单命中明显多于 custom scene（见 `scan_summary_matrix.json`）。

## Verification result
- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-09-1431.yaml` ✅

## Risk analysis
- 结论：`PASS`
- 风险级别：low
- 风险说明：本批仅采样，不做分层归因结论。

## Rollback suggestion
- `git restore agent_ops/reports/2026-04-09/report.ITER-2026-04-09-1431.md`
- `git restore agent_ops/state/task_results/ITER-2026-04-09-1431.json`
- `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`

## Next suggestion
- 进入 `screen` 批次，对 C1~C5 结合 1428/1430 证据做分层分类并形成执行计划。
