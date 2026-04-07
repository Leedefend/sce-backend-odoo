# ITER-2026-04-07-1297 Report

## Summary of change
- 执行“支付/结算最小办理验收”专项（不进入审批深链，不改后端财务语义）。
- 新增脚本：`scripts/verify/native_business_fact_payment_settlement_operability_verify.py`。

## Verification result
- PASS: `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-07-1297.yaml`
- PASS: `DB_NAME=sc_prod_fresh_1292_b E2E_BASE_URL=http://localhost:18079 ROLE_OWNER_LOGIN=wutao ROLE_OWNER_PASSWORD=demo ROLE_FINANCE_LOGIN=shuiwujingbanren ROLE_FINANCE_PASSWORD=demo ROLE_OUTSIDER_PASSWORD=demo python3 scripts/verify/native_business_fact_payment_settlement_operability_verify.py`
  - 关键输出：`finance_settlement_authorized=1 project_id=19 payment_id=7 settlement_id=7 outsider_payment_count=0 outsider_settlement_count=0`

## Operability closure evidence
- finance 授权成员可创建并编辑 `payment.request`。
- finance 授权成员可创建并编辑 `sc.settlement.order`。
- 两类对象均满足 `project_id/company_id` 锚点一致性。
- outsider 对 payment/settlement 默认不可见且不可写。

## Risk analysis
- 结论：`PASS`
- 风险状态：本轮为 verify 证据收敛，无新增权限面或财务语义变更。

## Rollback suggestion
- `git restore scripts/verify/native_business_fact_payment_settlement_operability_verify.py`
- `git restore docs/ops/project_org_isolation_acceptance_v1.md`

## Next suggestion
- 当前“原生最小办理闭环”已覆盖 project/task/budget/cost/payment/settlement；下一轮可只做你指定的新主题。
