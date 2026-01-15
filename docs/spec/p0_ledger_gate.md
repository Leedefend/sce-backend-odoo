# P0 Ledger Gate v0_1

## 1. 术语与对象
- payment.request: 付款/收款申请。
- sc.settlement.order: 结算单。
- payment.ledger: 付款台账记录。

## 2. Ledger 生成触发点
- 入口方法（模型层）：payment.ledger.create。
- 可选入口：payment.request action_approve / action_on_tier_approved（仅触发，不应绕过 ledger.create 的校验）。

## 3. 前置条件
- payment.request.state == approved。
- payment.request.settlement_id.state in (approve, done)。
- payment.ledger.amount > 0。
- payment.ledger 累计金额不得超过 payment.request.amount。

## 4. 幂等与重复生成规则
- 同一 payment.request 仅允许一条 payment.ledger（唯一约束：payment_request_id）。
- 重复触发时应返回已存在记录或抛出可解释错误。

## 5. 失败策略
- 校验失败时抛出 UserError/ValidationError，阻断写入。
- 不写 silent ignore（避免漏账）。

## 6. 权限模型
- finance_user/finance_manager 可创建 ledger。
- finance_read 仅可读。
- 其它角色禁止 create/write/unlink。

## 7. 测试矩阵
- 正向：
  - test_p0_ledger_gate.test_create_ledger_from_approved_payment
  - test_p0_ledger_gate.test_ledger_idempotent_per_request
  - test_p0_ledger_gate.test_ledger_amount_matches_request
- 反向：
  - test_p0_ledger_gate.test_block_when_settlement_not_approved
  - test_p0_ledger_gate.test_block_unauthorized_create
  - test_p0_ledger_gate.test_block_overpay
