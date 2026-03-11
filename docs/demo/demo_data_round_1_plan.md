# 演示数据 Round 1 方案

## 1. 目标页面

确保以下页面具备可读数据：

- `project.management`
- `projects.ledger`
- `projects.list`
- `task.center`
- `risk.center`
- `cost.project_boq`

## 2. 补数策略

- 不做大规模脏造数；
- 优先复用现有 demo 数据文件与场景文件；
- 只补“能打通展示链路”的最小数据。

## 3. 补数内容

1. 项目任务（`project.task`）
   - 为 `sc_demo_project_001` 增加最小任务集，覆盖在办/完成/受阻。
2. 合同与付款
   - 启用 `s10_contract_payment` 场景中的合同与付款申请示例。
3. 工程量清单
   - 继续使用 `s00_min_path/10_project_boq.xml` 已有样本。
4. 项目关联
   - 继续使用 `s00_min_path/20_project_links.xml` 保持最小业务关联。

## 4. 涉及模型与数据文件

- 模型：`project.project`、`project.task`、`construction.contract`、`payment.request`、`project.boq.line`
- 文件：
  - `addons/smart_construction_demo/data/base/25_project_tasks.xml`（新增）
  - `addons/smart_construction_demo/data/scenario/s10_contract_payment/10_contracts.xml`（纳入 manifest）
  - `addons/smart_construction_demo/data/scenario/s10_contract_payment/20_payment_requests.xml`（纳入 manifest）

## 5. 验证页面

- 驾驶舱指标区和风险区不再空壳；
- 台账和列表可展示状态、负责人、金额；
- 任务中心可展示任务记录；
- 风险工作台可展示与付款申请相关信号；
- 工程量清单可展示 BOQ 行。
