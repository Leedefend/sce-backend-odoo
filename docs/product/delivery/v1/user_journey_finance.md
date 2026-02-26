# Finance User Journey V1

## Goal
完成付款申请到审批与台账沉淀的闭环。

## Journey Steps
| Step | Entry/Menu | scene_key | intent | Action | Expected Result |
|---|---|---|---|---|---|
| 1 | 付款申请 | `finance.payment_requests` | `ui.contract` | 打开申请列表并选择目标单据 | 单据可读可编辑 |
| 2 | 审批中心 | `finance.center` | `ui.contract` | 进入审批视图查看待办 | 待办审批条目可见 |
| 3 | 审批动作 | `finance.center` | `execute_button` | 提交审批（通过/驳回） | 返回 2xx 或可解释权限拒绝 |
| 4 | 资金台账 | `finance.treasury_ledger` | `ui.contract` | 查看资金侧变更记录 | 资金记录与审批结果一致 |
| 5 | 支付台账 | `finance.payment_ledger` | `ui.contract` | 校验付款执行记录 | 状态可追溯 |
| 6 | 结算单据 | `finance.settlement_orders` | `ui.contract` | 检查结算联动结果 | 形成完整链路 |

## Validation Notes
- 至少验证 1 条审批链路状态变化。
- `execute_button` 不允许未分类 404。

## Demo Data Anchor
- 推荐样例付款申请：`PAYREQ-DEMO-001`（对应 `delivery_minimum_seed.payment_request_id`）。
- 推荐审批角色：`sc_fx_finance`（审批） + `sc_fx_pm`（发起）。
- 若无数据，最小创建步骤：
  - 在 `finance.payment_requests` 创建 1 张付款申请。
  - 在 `finance.center` 完成一次审批动作。
  - 在 `finance.payment_ledger` 与 `finance.treasury_ledger` 校验状态联动。
