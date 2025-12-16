# Operating Line v1

本文定义系统的经营主线（对象流 + 金额口径流），让新人能快速理解“真相来源”与“金额如何流转”。

## 1. 对象流（经营主线）

```mermaid
flowchart LR
    Project[项目<br/>project.project] -->|合同&项目维度| ContractIn[合同-收入<br/>construction.contract(type=in)]
    Project -->|合同&项目维度| ContractOut[合同-支出<br/>construction.contract(type=out)]

    ContractOut -->|采购/分包| PO[purchase.order]
    ContractOut -->|结算关联| Settle[结算单<br/>sc.settlement.order]
    PO -->|关联| Settle

    Settle -->|支撑付款申请| PayReq[付款申请<br/>payment.request(type=pay)]
    PayReq -->|审批通过入账| Ledger[资金台账/收支流水<br/>treasury_ledger]

    %% 预算与成本域
    Project -->|预算版本| Budget[项目预算<br/>project.budget]
    Budget -->|成本域/分摊| CostDomain[成本域/分摊<br/>project.budget.boq.line + alloc]
    PO -->|成本归集| CostDomain
    Settle -->|成本归集| CostDomain

    %% 收入侧（若开启）
    ContractIn -->|收款申请| PayReqIn[收款申请<br/>payment.request(type=receive)]
    PayReqIn -->|收/付流水| Ledger
```

## 2. 金额口径流（核心金额与字段）

```mermaid
flowchart LR
    ContractAmt[合同额<br/>construction.contract.amount_total] --> BudgetAmt[预算额<br/>project.budget.amount_*]
    BudgetAmt --> CommittedPO[已下单/承诺额<br/>purchase.order.amount_total]
    CommittedPO --> Settled[已结算额<br/>sc.settlement.order.amount_total]
    Settled --> Paid[已支付额<br/>payment.request.amount (pay, states in approve/approved/done)]
    Paid --> LedgerAmt[资金流水<br/>treasury_ledger.amount]

    Settled --> Payable[可付余额<br/>sc.settlement.order.amount_payable]
    Payable --> CashNeed[现金需求<br/>Payable 汇总]
```

说明：
- **合同额**：`construction.contract` 里的金额字段（当前模块使用 `amount_total` 口径）。
- **预算额**：`project.budget` 及其行（`project.budget.line`/`project.budget.boq.line`）。兼容模型 `_name = project.budget.line` 仍存在。
- **已结算额**：`sc.settlement.order.amount_total`。
- **已支付额**：`payment.request`（type=pay）在状态集合 `('submit','approve','approved','done')` 的 `amount` 汇总。
- **可付余额**：`sc.settlement.order.amount_payable = amount_total - amount_paid`（amount_paid 同上状态集合，排除当前申请自统计）。
- **资金流水**：`treasury_ledger.amount`（approve/done 时入账，作为投影）。

## 3. 口径说明（要点）

- 事实来源优先级：**结算单** 是付款申请的额度来源，`amount_payable` 是权威可付口径。
- 付款申请门禁：提交/审批时硬校验不可超付；validator 规则 `SC.VAL.PAY.001` 全局体检。
- 兼容模型：`project.budget.line` 作为兼容层继承 `project.budget.boq.line`，避免老库升级失败。
- 投影模型：`treasury_ledger`、`profit_report`、`cost_report` 属于可重算投影，不作为经营事实修改入口。

## 4. 版本约定

- 本文口径为 **v1**，对应当前代码分层：`models/core`, `models/projection`, `models/support`。
- 若后续新增“预占/冻结余额”等，需要在指标定义与金额流中新增节点和口径描述。***
