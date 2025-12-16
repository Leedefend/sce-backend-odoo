# 指标口径定义 v1

面向经营主线的关键指标口径表，注明来源模型/字段与包含/排除规则。

| 指标 | 定义 | 来源模型/字段 | 状态/过滤 | 备注 |
| --- | --- | --- | --- | --- |
| 合同额（收入/支出） | 合同金额（含税，按合同类型区分收/支） | construction.contract.amount_total | type in ('in','out') | 权威来源：合同 |
| 预算额（目标成本/收入） | 项目预算的目标金额 | project.budget.amount_cost_target / amount_revenue_target | is_active=True | 预算版本化；兼容 project.budget.line 仍存在 |
| 预算行金额 | 预算行的金额/工程量 | project.budget.line.budget_amount / budget_qty / budget_price | - | 预算与 BOQ 关联 |
| 成本域分摊金额 | 预算 BOQ 行到成本科目的分摊 | project.budget.cost.alloc.amount | - | 与成本科目/项目维度关联 |
| 采购已下单 | 已确认采购/分包金额 | purchase.order.amount_total | state in ('purchase','done') | 项目维度 |
| 已结算金额 | 结算单金额 | sc.settlement.order.amount_total | state in ('approve','done') | 项目/合同/供应商维度 |
| 已付累计 | 结算单已付金额累计 | sc.settlement.order.amount_paid | 付款申请 state in ('submit','approve','approved','done') | compute_sudo，排除当前付款自统计 |
| 可付余额 | 结算金额 - 已付累计 | sc.settlement.order.amount_payable | 同上 | 权威可付口径，超付门禁使用 |
| 付款申请金额 | 付款申请的金额 | payment.request.amount | type='pay'; state varies | 门禁/审批口径使用 |
| 已支付金额 | 已通过审批/完成的付款金额 | payment.request.amount | type='pay'; state in ('submit','approve','approved','done') | 口径与 amount_paid 一致 |
| 收入申请金额 | 收款申请金额 | payment.request.amount | type='receive' | 收入侧 |
| 资金流水金额 | 资金台账中的金额 | treasury_ledger.amount | state posted/approved | 投影，幂等写入 |
| 现金需求（应付余额汇总） | 可付余额的汇总 | 聚合 sc.settlement.order.amount_payable | amount_payable>0 | 用于现金流计划 |
| 3WAY 完整性 | 采购/结算/付款关键关联完整 | validator SC.VAL.3WAY.001 | - | 校验项，非金额 |
| 公司一致性 | 采购/结算/付款公司一致 | validator SC.VAL.COMP.001 | - | 校验项 |
| 项目必填 | 关键单据必须挂项目 | validator SC.VAL.PROJ.001 | - | 校验项 |
| 金额数量合理性 | 关键字段不为负数 | validator SC.VAL.AMT.001 | - | 校验项 |
| 付款不可超付 | 付款不得超过结算可付余额 | validator SC.VAL.PAY.001 + 按钮门禁 | scope 支持 | 校验项 |

说明：
- 付款/结算口径使用的状态集合：`('submit','approve','approved','done')`，可在后续版本根据业务调整。
- 可付余额与超付门禁保持同一计算逻辑，避免 UI 与门禁口径不一致。***
