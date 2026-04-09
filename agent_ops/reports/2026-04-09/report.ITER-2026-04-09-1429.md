# ITER-2026-04-09-1429 Report

## Batch
- Batch: `1/1`
- Mode: `scan`

## Architecture declaration
- Layer Target: `Governance runtime fact scan`
- Module: `role-based tri-view parity evidence`
- Module Ownership: `verify runtime`
- Kernel or Scenario: `scenario`
- Reason: 按用户要求，以真实角色与核心主线页面采集入口可见性/结构/数据/操作事实证据。

## Evidence artifact
- `artifacts/playwright/iter-2026-04-09-1429/role_mainline_full_scan.json`

## Raw scan coverage
- 角色登录：`admin` / `sc_fx_pm` / `sc_fx_executive`（custom/native 均登录成功）
- 主线场景：`projects.list` / `projects.ledger` / `projects.intake` / `project.dashboard` / `project.management`
- 采样动作：`484` / `531` / `538` / `520`
- 采样维度：
  - 入口可见性：scene presence + target(action/menu/route)
  - 页面结构：native action view_mode/views 与 custom view_keys/list_columns_count
  - 数据：custom api.data 首屏样本量 与 native search_read 首屏样本量
  - 操作：custom permissions.effective.rights 与 native check_access_rights

## Candidate findings (scan only, no conclusion)
- C1: 三个角色在 custom `app.init.nav` 中 `named_nav_nodes=0`，但核心 scene 均存在。
- C2: `project.management` 场景在 scene target 中无 `action_id`（route-only）。
- C3: custom 侧 action_open 返回 `view_mode=null`，native 侧对应 action 的 `view_mode` 完整存在。
- C4: 同一 action 的 custom/native 首屏样本首条 `id` 不同（custom 多为 `1`，native 多为 `21`）。
- C5: 三角色在 sampled actions 上 read/write/create/unlink 全为 `true`。

## Verification result
- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-09-1429.yaml` ✅

## Risk analysis
- 结论：`PASS`
- 风险级别：low
- 风险说明：本批仅完成事实采集，不做归因结论；需下一批 `screen` 分类根因。

## Rollback suggestion
- `git restore agent_ops/reports/2026-04-09/report.ITER-2026-04-09-1429.md`
- `git restore agent_ops/state/task_results/ITER-2026-04-09-1429.json`
- `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`

## Next suggestion
- 立即进入 `screen` 批次，对 C1~C5 进行层级归因：业务事实层 / 权限定义 / 平台契约承载 / 前端消费岔路。
