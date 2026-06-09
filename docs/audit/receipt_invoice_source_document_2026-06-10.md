# Receipt Invoice Source Document 2026-06-10

## Scope

专项补齐正式业务模型 `sc.receipt.invoice.line.source_document_no`。

覆盖菜单：

- 智慧施工管理平台 / 财务中心 / 发票台账 / 收款发票

## Root Cause

历史收款发票明细迁移时保留了发票登记编号 `invoice_document_no`，但没有把父级收入申请中的来源业务单号写入 `source_document_no`。

父级 `payment_request.note` 已稳定携带 `document_no=...`，且本批 4454 条收款发票明细均可由父级收入申请取到来源业务单号。

## Backfill

```text
RECEIPT_INVOICE_SOURCE_DOCUMENT_BACKFILL: {"after_missing_source_document_no": 0, "before_missing_source_document_no": 4454, "candidate_rows": 4454, "operation": "receipt_invoice_source_document_backfill", "status": "PASS", "updated_rows": 4454}
```

说明：

- 只补空的 `source_document_no`。
- 来源限定为父级 `payment_request.note` 中的 `document_no=...`。
- 不使用发票登记编号替代来源业务单号，避免混淆正式业务语义。
- 不改用户已确认菜单体系。

## Audit

```text
RECEIPT_INVOICE_SOURCE_DOCUMENT_AUDIT: {"audit": "receipt_invoice_source_document_audit", "failures": [], "mismatched_parent_document": 0, "missing_source_document_no": 0, "missing_with_parent_document": 0, "parent_document_available": 4454, "status": "PASS", "total": 4454}
```

## Release Gate

```text
FORMAL_BUSINESS_RELEASE_GATE_RESULT: PASS db=sc_demo started_at=2026-06-10T00:49:20+08:00 finished_at=2026-06-10T00:51:36+08:00
```

关键数据对齐结果：

- 用户确认正式菜单：`62`
- 检查记录：`256844`
- 检查字段：`862`
- 不一致字段：`0`
- 只读来源字段未承接：`0`

## Visible Matrix

修复前：

- `issue_count`: `20`
- 需要模型专项业务值门：`5`
- 涉及：`sc.receipt.invoice.line.source_document_no`

修复后：

- `issue_count`: `20`
- 需要模型专项业务值门：`4`
- `sc.receipt.invoice.line.source_document_no` 已退出模型专项业务字段缺口
- `收款发票台账` 剩余 warning 仅为 `source_created_by/source_created_at` 来源元数据

## Remaining Model-Specific Business Gaps

- `sc.settlement.order`: `contract_id`, `legacy_contract_no`, `contract_subject`, `settlement_period_start`, `settlement_period_end`, `engineering_address`, `planned_settlement_date`
- `project.material.plan`: `legacy_visible_10`
- `sc.construction.diary`: `legacy_visible_07`, `legacy_visible_08`
- `sc.material.rfq`: `due_date`, `purchase_request_id`, `source_material_plan_id`

## Policy

- 不改用户已确认菜单体系。
- 不覆盖用户已验收列表值。
- 不制造源数据不存在的业务事实。
- 只承接父级收入申请中已经存在且可审计的来源业务单号。
