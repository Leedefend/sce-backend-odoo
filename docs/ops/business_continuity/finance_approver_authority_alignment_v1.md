# Finance Approver Authority Alignment v1

## 目的

对齐原生付款审批权限与自定义 intent 审批权限。

## 修改

`smart_construction_custom.group_sc_role_payment_manager` 增加继承：

- `smart_construction_core.group_sc_cap_finance_manager`
- `smart_core.group_smart_core_finance_approver`

同步更新 `ScSecurityPolicy.apply_role_matrix()`，保证运行时角色矩阵补齐同一条继承关系。

## 边界

- 未修改 ACL CSV。
- 未修改 record rules。
- 未修改付款、结算、会计业务逻辑。
- 未修改前端。
- 仅做 additive role inheritance。

## 验证

- `validate_task`: PASS
- `py_compile security_policy.py`: PASS
- `role_matrix_groups.xml` XML parse: PASS
- rollback-only authority inheritance check: PASS
  - 对齐前 canonical approver users: `0`
  - 临时继承后 canonical approver users: `8`
- rollback-only daily no-contract payment E2E: PASS_WITH_RISK
  - 付款从 draft 走到 done。
  - 生成 `payment.ledger`。
  - 无合同、无结算单保持成立。
  - rollback 后付款、台账、附件均无残留。

## 新发现风险

权限对齐后，E2E 继续推进到邮件作者校验：

`message_post` 要求当前操作者存在 sender email。

当前付款审批角色用户没有个人邮箱：

- 示例操作者：`wutao`
- user email: empty
- partner email: empty

在 rollback 事务内临时补齐操作者邮箱后，完整付款链路通过。

## 判断

本批解决 authority-surface gap。

下一批应处理 sender email/business user master-data gap：

- 确认客户用户邮箱是否应从旧系统同步。
- 或提供系统级 no-reply author fallback。
- 该问题属于用户主数据/邮件运行事实，不属于付款业务规则。
