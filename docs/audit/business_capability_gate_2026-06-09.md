# Business Capability Gate 2026-06-09

## Scope

汇总前三轮专项验收，形成一个正式业务办理能力总门禁。

总门禁顺序执行：

- `validate_core_document_processing_gate.sh`
- `validate_business_flow_closure.sh`
- `validate_business_action_coverage.sh`
- `validate_field_operation_actions.sh`

## Command

```bash
DB_NAME=sc_demo scripts/ops/validate_business_capability_gate.sh
```

## Coverage

- 核心单据办理：正式动作提交、审批、办结、取消，覆盖结算、付款、费用报销、保证金、扣款退回、项目还公司款、材料入库
- 核心闭环：合同、结算、付款、材料采购、库存、材料结算
- 财务动作：付款执行、收入、费用支出、发票、抵扣、工资、资金账户
- 施工生产动作：劳务、机械、分包、周转材料、安全、质量

## Policy

- 仅允许在非生产环境运行，脚本调用 `guard_prod_forbid`。
- 任意子验收失败时总门禁失败。
- 脚本只创建专项审计数据并调用正式模型动作，不修改用户已确认菜单体系，不覆盖历史迁移数据。

## Result

```text
BUSINESS_CAPABILITY_GATE_START: db=sc_demo started_at=2026-06-09T21:59:12+08:00
BUSINESS_CAPABILITY_GATE_CHECK_PASS: core_document_processing
BUSINESS_CAPABILITY_GATE_CHECK_PASS: business_flow_closure
BUSINESS_CAPABILITY_GATE_CHECK_PASS: business_action_coverage
BUSINESS_CAPABILITY_GATE_CHECK_PASS: field_operation_actions
BUSINESS_CAPABILITY_GATE_RESULT: PASS db=sc_demo started_at=2026-06-09T23:36:37+08:00 finished_at=2026-06-09T23:37:05+08:00
```
