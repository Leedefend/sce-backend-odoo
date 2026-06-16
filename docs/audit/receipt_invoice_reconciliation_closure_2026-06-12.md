# 收款发票核销办理闭环口径

日期：2026-06-12

## 业务边界

- 收款发票明细 `sc.receipt.invoice.line` 用于表达收款申请与销项发票之间的核销关系。
- 收款申请、收款登记和销项开票仍是独立办理事实：
  - `payment.request(type=receive)` 表达收款申请。
  - `sc.receipt.income` 表达项目收款登记，完成后进入 `sc.treasury.ledger`。
  - `sc.invoice.registration(direction=output)` 表达销项开票登记。
- 核销明细不直接生成现金流，不能替代收款登记或资金台账。
- 核销金额约束只作用于新系统办理明细；历史导入批次保持锁定追溯，不 retroactive 改写旧口径。

## 用户数据依据

- 当前本地用户库共有 4454 条 `sc.receipt.invoice.line`，全部来自历史批次 `history_continuity_receipt_invoice_line_v1`。
- 历史数据中存在旧口径例外：
  - 1 条明细本次收款金额超过发票金额。
  - 19 个收款申请的明细本次收款合计超过申请金额。
- 因此本轮不批量修正历史事实，只对新发生办理建立防超额门禁。

## 办理规则

- 新系统核销明细填写 `current_receipt_amount` 时，金额必须为合理正向核销金额。
- 单条明细的本次收款金额不能超过该行发票金额。
- 同一收款申请下，填写了本次收款金额的明细合计不能超过收款申请金额。
- 历史导入批次 `import_batch` 不触发新规则，用于保持用户旧系统验收口径。

## 验收证据

- 合法收款发票明细可创建。
- 本次收款金额超过发票金额会被阻断。
- 同一收款申请下本次收款合计超过申请金额会被阻断。
- 原收入合同 -> 收款申请 -> 收款登记 -> 资金台账 -> 销项开票 -> 合同累计链路保持通过。

## 本轮验收命令

- `DB_NAME=sc_demo scripts/ops/validate_income_contract_receipt_invoice_closure.sh`
- `DB_NAME=sc_demo scripts/ops/validate_invoice_tax_downstream_traceability.sh`
- `DB_NAME=sc_demo make verify.finance_handling.http_surface.smoke`
- `DB_NAME=sc_demo make verify.finance_business_project.summary.audit`
