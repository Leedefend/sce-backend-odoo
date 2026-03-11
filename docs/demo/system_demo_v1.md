# SCEMS v1.0 系统演示脚本

## 1. 演示目标
在 10~15 分钟内展示 v1 核心业务闭环：

`登录 -> 我的工作 -> 项目台账 -> 项目管理控制台 -> 合同/成本/资金 -> 风险提醒`

## 2. 演示前准备
- 环境：`dev` 或 `test`
- 数据库：包含演示数据（建议 `sc_demo`）
- 验证账号：`sc_fx_pm` / `sc_fx_finance` / `sc_fx_executive`

## 3. 演示步骤

### Step 1 登录系统
- 使用项目经理账号登录。
- 展示工作台首页与主导航。

### Step 2 进入“我的工作”
- 打开 `my_work.workspace`。
- 展示待办、我的项目、快捷入口、风险摘要。

### Step 3 打开“项目台账”
- 打开 `projects.ledger`。
- 执行筛选/搜索，定位目标项目。

### Step 4 进入“项目管理控制台”
- 通过台账跳转到 `project.management`。
- 展示 7 个 dashboard blocks：
  - Header
  - Metrics
  - Progress
  - Contract
  - Cost
  - Finance
  - Risk

### Step 5 展示业务工作台
- 依次展示：
  - `contracts.workspace`
  - `cost.analysis`
  - `finance.workspace`

### Step 6 展示风险与权限差异
- 切换管理层查看账号，展示只读视角。
- 说明未授权能力的降级/拒绝行为。

## 4. 演示验收口径
- 页面可打开且无阻断错误。
- 关键路径可闭环完成。
- 角色差异符合权限设计。

