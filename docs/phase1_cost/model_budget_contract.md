# Phase-1 成本域模型说明：预算 / 合同

## 1. project.budget

- 模块：`smart_construction_core`
- 表名：`project_budget`
- 用途：项目级预算版本管理，定义目标收入 / 成本基线。

### 1.1 关键字段

| 字段名              | 类型        | 说明 |
|---------------------|------------|------|
| `name`              | Char       | 预算名称 |
| `project_id`        | Many2one   | 关联项目 `project.project` |
| `version_code`      | Char       | 版本号（如 v001） |
| `is_current`        | Boolean    | 是否当前生效版本 |
| `amount_cost_target`    | Monetary | 目标成本合计（汇总行） |
| `amount_revenue_target` | Monetary | 目标收入合计（汇总行） |

> 唯一约束：同一项目 + 版本号唯一。

---

## 2. project.budget.boq.line

- 表名：`project_budget_boq_line`
- 用途：按 BOQ 清单维度拆分预算量价，后续可与合同 / 实际成本对比。

### 2.1 关键字段

| 字段名         | 类型      | 说明 |
|----------------|-----------|------|
| `budget_id`    | Many2one  | 预算头 `project.budget` |
| `boq_line_id`  | Many2one  | 清单行 `project.boq.line` |
| `wbs_id`       | Many2one  | 关联 WBS `project.wbs`（如有） |
| `budget_qty`   | Float     | 预算工程量 |
| `budget_price` | Monetary  | 预算单价 |
| `budget_amount`| Monetary  | 预算合价 = qty * price |

---

## 3. project.contract

- 模块：`smart_construction_core`
- 表名：`project_contract`

### 3.1 关键字段

| 字段名              | 类型      | 说明 |
|---------------------|-----------|------|
| `name`              | Char      | 合同名称 |
| `code`              | Char      | 合同编号 |
| `project_id`        | Many2one  | 所属项目 |
| `partner_id`        | Many2one  | 合同相对方 |
| `company_id`        | Many2one  | 公司 |
| `contract_type`     | Selection | 收入 / 分包 / 采购等 |
| `state`             | Selection | 草稿 / 已生效 / 执行中 / 已关闭 / 已取消 |
| `currency_id`       | Many2one  | 币种 |
| `amount_total`      | Monetary  | 合同金额汇总（由行汇总） |

---

## 4. project.contract.line

| 字段名             | 类型      | 说明 |
|--------------------|-----------|------|
| `contract_id`      | Many2one  | 合同头 |
| `boq_line_id`      | Many2one  | 清单行 |
| `wbs_id`           | Many2one  | WBS |
| `qty`              | Float     | 合同工程量 |
| `price`            | Monetary  | 合同单价 |
| `amount`           | Monetary  | 合同合价 |
| `cost_split_key`   | Selection | 成本分摊规则（预留） |

> 更详细的字段说明，可在后续开发中持续补充本文件。  
> 推荐：每次新增字段时顺手更新这里，避免“代码有字段、文档没说明”的现象。
