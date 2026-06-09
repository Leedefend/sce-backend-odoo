# Core Document Processing Gate 2026-06-09

## Scope

专项验证用户确认后的正式业务单据能按真实办理动作闭环运行。

覆盖：

- 结算单：草稿、提交、统一审批通过、办结、取消
- 付款/收款申请：提交、统一审批通过、自动生成资金流水、办结
- 费用与保证金单据：费用报销、付款还保证金、付款保证金退回、扣款实缴退回、还款登记
- 材料入库：提交、确认入库、取消、重置草稿

## Command

```bash
DB_NAME=sc_demo scripts/ops/validate_core_document_processing_gate.sh
```

## Policy

- 仅允许在非生产环境运行，脚本调用 `guard_prod_forbid`。
- 只创建专项审计数据并调用正式模型动作。
- 不修改用户已确认菜单体系，不覆盖用户可见列表数据，不改历史迁移数据。

## Result

```text
CORE_DOCUMENT_PROCESSING_GATE: {"audit": "core_document_processing_gate", "failures": [], "flows": {"expense_claims": {"claims": {"cancel": 271752, "deduction_refund": 271750, "deposit_pay": 271748, "deposit_refund": 271749, "expense": 271747, "project_company_repay": 271751}, "payments": {"deduction_refund": 35867, "deposit_pay": 35865, "deposit_refund": 35866, "expense": 35864, "project_company_repay": 35868}}, "material_inbound": {"cancel_inbound": 13649, "inbound": 13648}, "settlement_payment": {"cancel_settlement": 2802, "payment": 35863, "settlement": 2801}}, "status": "PASS"}
```
