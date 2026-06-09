# Operation Strategy And Contract Surface 2026-06-10

## Scope

专项补齐正式业务模型中的经营方式和合同编号可见承接字段。

覆盖模型：

- `sc.general.contract`
- `sc.fund.account`
- `sc.treasury.reconciliation`

## Root Cause

项目主数据 `project.project.operation_strategy` 已完整，但部分正式模型上的存储型 related 字段没有刷新，导致列表/矩阵看到经营方式为空。

一般合同还存在 `contract_no` 为空但 `document_no` 有值的历史合同，影响合同编号检索。

## Backfill

```text
OPERATION_STRATEGY_CONTRACT_SURFACE_BACKFILL: {"contract_no_updated": 38, "remaining": {"sc_fund_account_no_strategy": 1, "sc_general_contract_no_contract_no": 0, "sc_general_contract_no_strategy": 0, "sc_treasury_reconciliation_no_strategy": 0}, "status": "PASS", "strategy_updates": {"sc_fund_account": {"before_mismatch": 161, "updated": 161}, "sc_general_contract": {"before_mismatch": 335, "updated": 335}, "sc_treasury_reconciliation": {"before_mismatch": 19806, "updated": 19806}}}
```

说明：

- `sc_fund_account_no_strategy = 1` 是无项目账户，不属于项目经营方式错配。
- 一般合同空 `contract_no` 使用 `document_no` 兜底，未伪造不存在的合同编号。

## Audit

```text
OPERATION_STRATEGY_CONTRACT_SURFACE_AUDIT: {"failures": [], "general_contract_no": {"missing_contract_no": 0, "missing_contract_no_with_document_no": 0, "total": 1065}, "status": "PASS", "strategy": {"sc.fund.account": {"missing_with_project": 0, "no_project": 1, "total": 165}, "sc.general.contract": {"missing_with_project": 0, "no_project": 0, "total": 1065}, "sc.treasury.reconciliation": {"missing_with_project": 0, "no_project": 0, "total": 20060}}}
```

## Release Gate

```text
FORMAL_BUSINESS_RELEASE_GATE_RESULT: PASS db=sc_demo started_at=2026-06-10T00:33:04+08:00 finished_at=2026-06-10T00:35:19+08:00
```

关键数据对齐结果：

- 用户确认正式菜单：`62`
- 检查记录：`256844`
- 检查字段：`862`
- 不一致字段：`0`
- 只读来源字段未承接：`0`

## Visible Matrix

修复前：

- `issue_count`: `22`
- 需要模型专项业务值门：`8`
- 涉及：`sc.general.contract`, `sc.fund.account`, `sc.treasury.reconciliation`

修复后：

- `issue_count`: `20`
- 需要模型专项业务值门：`5`
- `sc.general.contract`, `sc.fund.account`, `sc.treasury.reconciliation` 已退出业务字段缺口

## Policy

- 不改用户已确认菜单体系。
- 不覆盖用户已验收列表值。
- 不制造源数据不存在的业务事实。
- 只刷新可由项目主数据稳定推导的经营方式，以及可由审批编号兜底的一般合同编号。
