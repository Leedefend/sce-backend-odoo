# Workbench 可见性诊断报告（v1）

## 背景
- 现象：`sc_fx_pm` 在工作台的 `today_factual_rate` 显著低于 `finance/owner`。
- 目标：确认根因是权限策略、数据归属，还是前端渲染问题。

## 事实采样
- 运行环境：`sc_prod_sim`（prod-sim）。
- 诊断入口：`app.init` 返回的 `workspace_home.diagnostics.extraction_stats` 与 `ext_facts.smart_construction_core.workspace_business_source`。
- 对比账号：`sc_fx_pm` / `sc_fx_finance` / `sc_fx_executive`。

关键观测（修复前）：
- `sc_fx_pm`：`task_items=0, payment_requests=0, risk_actions=2`
- `sc_fx_finance`：`task_items=0, payment_requests>0, risk_actions=2`
- `sc_fx_executive`：`task_items=0, payment_requests>0, risk_actions=2`

结论：PM 缺少可见的真实动作源，问题不在前端展示层。

## 根因分析

### 1) 权限侧（设计内）
- PM fixture 账号不具备财务能力组，`payment.request` 对 PM 不可见属于权限设计结果。
- finance/owner 具备财务能力，能看到付款申请真实记录。

### 2) 归属侧（demo 数据）
- demo 项目与任务归属偏向系统用户/演示管理员，未对 PM 角色形成稳定“可见任务池”。
- 导致 PM 在 `today_actions` 真实记录来源不足，只能依赖风险项与模板项。

### 3) 非根因项
- 前端样式/布局不是本问题根因。
- 命中率统计逻辑本身无误，问题是数据源可见性。

## 修复策略（已执行）

### A. 不改 ACL 基线
- 保持权限模型不变，不通过放开财务权限来“抬高 PM 指标”。

### B. 增加 PM 可见真实源
- 在 `system_init` 扩展中新增 `project_actions`（基于可见项目生成真实动作）。
- 将 `project_actions` 纳入 `today_actions` 的业务优先来源序列。

### C. 补齐 demo 数据
- 新增 Round 2 demo 数据：任务与付款申请，覆盖项目 001/002。
- 通过模块升级将数据实际加载到 `sc_prod_sim`。

## 修复后结果
- 最新命中率报告：`artifacts/backend/workbench_extraction_hit_rate_report.md`。

结果：
- `pm`: `today_factual_rate` 提升至 `83.33%`
- `finance`: `today_factual_rate` 为 `100%`
- `owner`: `today_factual_rate` 为 `100%`
- 三角色 `risk_factual_rate` 均为 `100%`

## 后续约束
- 后续新增 demo 用户时，必须同步检查“角色可见数据池”是否覆盖任务/风险/付款至少两类。
- 工作台命中率评估必须保留双口径：
  - `business_rate`（语义业务）
  - `factual_rate`（真实记录）

## 一句话结论
- 本次差异的主因是“权限 + 归属导致的可见真实源不足”，已通过“新增 PM 可见项目动作源 + Round 2 demo 补数”完成修复，且未突破权限基线。

