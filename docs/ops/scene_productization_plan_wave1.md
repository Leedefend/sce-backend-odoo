# Scene Productization Plan · Wave 1

## 背景

- 当前大量场景属于“已注册可路由”，并不等于“已产品化可交付”。
- Wave 1 目标：只推进主线 `12~20` 个场景到 `R2/R3`，其余保持 `R0/R1`。

## 目标与边界

- 目标：建立成熟度分层治理并完成主线样板升级。
- 范围：项目主线、合同/成本主线、资金/审批主线。
- 不做：全量 100+ 场景一次性 profile 化。

## 主线清单

### 项目主线
- `projects.intake`
- `projects.list`
- `project.management`
- `projects.ledger`

### 合同/成本主线
- `contract.center`
- `contracts.workspace`
- `cost.cost_compare`
- `cost.project_cost_ledger`
- `cost.analysis`

### 资金/审批主线
- `finance.center`
- `finance.workspace`
- `finance.payment_requests`
- `finance.settlement_orders`

## 里程碑（7天快启）

- Day 1：完成 inventory 全量登记与 R0~R3 分级。
- Day 2：锁定主线场景、owner、next_action。
- Day 3：完成 `projects.intake` 正式 profile。
- Day 4：完成项目主线组联动（`projects.list/project.management/projects.ledger`）。
- Day 5：推进 `contract.center/cost.analysis/finance.workspace` 模板化。
- Day 6：输出覆盖率看板（按域的 R0~R3 分布）。
- Day 7：冻结规则上线（新增 scene 先入 inventory）。

## 执行进展

- Day 1：已完成（inventory 建表 + R0~R3 分级）。
- Day 2：已完成（主线圈定 + owner/next_action 明确）。
- Day 3：已完成（`projects.intake` 已补正式 profile，进入 R2）。
- Day 4：已完成（`projects.list/project.management/projects.ledger` 已统一主线 profile 联动）。
- Day 5：已完成（`contract.center/cost.analysis/finance.workspace` 已完成模板化并进入 R2）。
- Day 6：已完成（已生成覆盖率看板 `docs/ops/audit/scene_coverage_dashboard.md`）。
- Day 7：已完成（新增 `scene_inventory_freeze_guard`，冻结“新增 scene 先入 inventory”规则）。

## 阶段结果

- `R2+` 场景已达成 `12+`（当前覆盖率看板为准）。
- `R3` 场景已达成 `4+`（项目/成本/资金主线样板）。
- 迭代深化：`projects.list/projects.ledger/contract.center/finance.center` 已升至 `R3`。
- 继续迭代：`contracts.workspace/cost.cost_compare/cost.project_cost_ledger/finance.payment_requests/finance.settlement_orders` 已升至 `R3`。

## 交付物

- `docs/ops/scene_inventory_matrix_latest.md`
- `docs/ops/scene_templates/dashboard.md`
- `docs/ops/scene_templates/workspace.md`
- `docs/ops/scene_templates/form_list.md`
- `scripts/verify/scene_maturity_guard.py`
- `scripts/verify/scene_coverage_dashboard_report.py`
- `scripts/verify/scene_inventory_freeze_guard.py`
- `docs/ops/audit/scene_coverage_dashboard.md`

## 验收标准

- 主线场景 `R2+` 数量 >= 12。
- 至少 4 个场景达到 `R3`。
- `scene_maturity_guard` 在 CI/本地前置可运行。
