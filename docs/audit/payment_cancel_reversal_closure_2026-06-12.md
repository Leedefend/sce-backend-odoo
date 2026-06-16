# 付款取消与撤销办理闭环口径

日期：2026-06-12

## 业务边界

- 付款/收款申请取消只适用于尚未形成付款或资金台账的申请。
- 已完成申请不能直接取消，避免申请状态与 `payment.ledger`、`sc.treasury.ledger` 现金事实断裂。
- 已付款执行的撤销应从 `sc.payment.execution` 发起，由业务动作删除对应付款台账，并把付款申请退回已批准状态。
- 已收款入账当前不做简单取消；后续应按收款冲销、红冲或更正办理沉淀独立流程。
- 取消和撤销都必须写审计事件，不能通过直接写 `state` 绕过状态机。

## 办理规则

- `payment.request.action_cancel`
  - 允许取消未完成且未生成台账的付款/收款申请。
  - 取消后状态为 `cancel`。
  - 写入 `payment_cancelled` 审计事件。
- `payment.request.action_cancel`
  - 阻断 `done` 或 `cancel` 状态。
  - 阻断已存在 `payment.ledger` 或未作废 `sc.treasury.ledger` 的申请。
- `sc.payment.execution.action_cancel`
  - 草稿或已确认付款执行可取消。
  - 已付款执行通过撤销链路处理。
- `sc.payment.execution._reverse_paid_execution`
  - 删除对应 `payment.ledger`。
  - 将 `payment.request` 从 `done` 退回 `approved`。
  - 写入 `payment_reversed` 审计事件。

## 验收证据

- 已批准未入账申请可取消，且不会生成付款台账。
- 已完成付款申请直接取消被阻断。
- 已付款执行取消后，付款台账清零，付款申请退回已批准。
- 财务办理 HTTP 表面仍可打开付款申请、付款执行、收款、费用、保证金、扣款和往来入口。
- 项目资金事实摘要保持一致，取消/撤销规则不改变历史已确认资金事实。

## 本轮验收命令

- `DB_NAME=sc_demo scripts/ops/validate_finance_handling_evidence.sh`
- `DB_NAME=sc_demo make verify.finance_handling.http_surface.smoke`
- `DB_NAME=sc_demo make verify.finance_business_project.summary.audit`
