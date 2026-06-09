# Settlement Contract Surface 2026-06-10

## Scope

专项补齐并固化 `sc.settlement.order` 的合同/结算字段承接规则。

覆盖字段：

- `contract_id`
- `legacy_contract_no`
- `contract_subject`
- `engineering_address`
- `settlement_period_start`
- `settlement_period_end`
- `planned_settlement_date`

## Root Cause

收入/支出合同结算投影已能进入正式 `sc.settlement.order`，但部分合同快照字段没有沉入结算单，导致通用结算列表矩阵仍把合同编号、合同名称、工程地址等字段判为业务值缺口。

直营验收来源的结算单多数没有正式合同关系，不能为消除空值而伪造合同。该类数据已经由用户确认结算可见字段门禁单独覆盖。

## Backfill

```text
SETTLEMENT_CONTRACT_SURFACE_BACKFILL: {"operation": "settlement_contract_surface_backfill", "settlement_count": 2747, "status": "PASS", "updated_by_source": {"construction.contract.expense:settlement_surface": 118, "construction.contract.income:settlement_surface": 36, "sc.legacy.direct.acceptance.fact": 110, "sc.legacy.direct.acceptance.fact:direct_engineering_settlement_order": 37}, "updated_fields": {"contract_subject": 37, "engineering_address": 16, "legacy_contract_no": 176, "settlement_period_end": 88, "settlement_period_start": 88}, "updated_rows": 301}
```

说明：

- 合同来源结算：从关联 `construction.contract` 补齐合同编号、合同名称和有来源的工程地址。
- 直营工程结算：从验收字段 `legacy_visible_13` 补合同名称，从 `legacy_visible_15` 补工程地址。
- 结算起止日期：只解析明确日期区间文本。
- `planned_settlement_date` 未回填；当前旧源没有独立计划结算日期，不能用单据日期替代。

## Audit

```text
SETTLEMENT_CONTRACT_SURFACE_AUDIT: {"audit": "settlement_contract_surface_audit", "contract_backed_missing_count": 0, "direct_engineering_missing_count": 0, "status": "PASS", "total": 2747}
```

关键结论：

- 合同来源结算：`154` 条合同快照缺口清零。
- 直营工程结算：`37` 条合同名称/工程地址可承接缺口清零。
- 直营验收来源无合同记录保留源范围说明，不伪造正式合同。

## Release Gate

```text
FORMAL_BUSINESS_RELEASE_GATE_RESULT: PASS db=sc_demo started_at=2026-06-10T01:06:52+08:00 finished_at=2026-06-10T01:09:10+08:00
```

关键数据对齐结果：

- 用户确认正式菜单：`62`
- 检查记录：`256844`
- 检查字段：`862`
- 不一致字段：`0`
- 只读来源字段未承接：`0`

## Visible Matrix Classification

修复前：

- 需要模型专项业务值门：`4`
- 涉及：`sc.settlement.order`

修复后：

- `sc.settlement.order` 进入 `covered_by_settlement_contract_surface_gate`
- 需要模型专项业务值门：`3`

剩余模型级业务字段缺口：

- `project.material.plan`: `legacy_visible_10`
- `sc.construction.diary`: `legacy_visible_07`, `legacy_visible_08`
- `sc.material.rfq`: `due_date`, `purchase_request_id`, `source_material_plan_id`

## Policy

- 不改用户已确认菜单体系。
- 不覆盖用户已验收列表值。
- 不制造源数据不存在的合同或计划日期。
- 对有正式合同来源的结算单强制承接合同快照。
- 对直营验收来源的结算单保留用户确认可见字段门禁作为承接依据。
