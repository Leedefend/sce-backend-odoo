# Demo 数据补齐方案（Round 2）

## 目标
- 为工作台真实业务链路提供可持续演示数据。
- 覆盖任务、付款申请、风险三条主动作来源。
- 保证 `today_actions` / `risk.actions` 在各角色下均有真实记录可读。

## 覆盖范围
- 工作台首页（`portal.dashboard` / workspace home）
- 任务中心（`task.center`）
- 付款申请（`finance.payment_requests`）
- 风险中心（`risk.center`）

## 数据模型与来源
- `project.task`
  - 目标状态：`sc_state in (ready, in_progress)`；兼容 `kanban_state in (normal, blocked)`。
  - 目标数量：每个演示项目至少 3 条任务，覆盖进行中/待处理。
- `payment.request`
  - 目标状态：`draft/submit/approve/approved`。
  - 目标数量：每个演示项目至少 2 条付款申请。
- `project.risk`（或 `project.project.health_state` 回退）
  - 目标状态：`warn/risk`。
  - 目标数量：每个演示项目至少 1 条风险信号。

## 本轮已落地（后端收口）
- `system_init` 扩展点已注入真实业务动作源：
  - `task_items`
  - `payment_requests`
  - `risk_actions`
- 工作台诊断新增双口径：
  - `business_rate`（业务语义）
  - `factual_rate`（真实记录）

## 下一步数据补齐动作
1. 在 `smart_construction_demo` 增加 Round 2 数据文件（建议：`data/scenario/s10_contract_payment/25_workbench_actions.xml`）。
2. 为 `sc_demo_project_001/002` 补任务、付款、风险最小闭环数据。
3. 通过 `make demo.reset` + `make verify.workbench.extraction_hit_rate.report` 复核。

## 验收标准
- `artifacts/backend/workbench_extraction_hit_rate_report.md` 中三角色均有：
  - `today_factual_rate > 0`
  - `risk_factual_rate > 0`
- 工作台首屏“今日行动/风险提醒”存在真实记录，不仅是模板动作。

