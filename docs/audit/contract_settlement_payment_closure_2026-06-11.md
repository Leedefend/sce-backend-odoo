# Contract Settlement Payment Closure - 2026-06-11

## Scope

本矩阵承接总计划 Phase 4。材料域已进入后续计划，本轮转向合同与结算域能力闭环：支出合同登记后，结算单走正式提交和审批，付款申请走提交、审批和完成，付款台账和合同对账能解释结算余额；收入合同登记后，收款申请、收款登记、资金台账和销项发票登记能解释合同执行。

当前不扩展报表，先保证用户可以办理：

- 合同登记
- 结算申报
- 结算审批
- 付款申请
- 付款审批
- 付款完成
- 收款申请
- 收款登记
- 销项开票登记
- 合同维度追溯

## User Data Reading

用户画像中合同与结算域约 48,755 条记录，并且与付款、收款、发票、成本、账户资金等高体量域强相关。产品设计不能把合同只当筛选字段；合同必须成为结算、收付款、开票和成本沉淀的业务锚点。

设计判断：

- 收入合同、支出合同是用户认知清晰的业务类别，入口可以整合，但类别不能丢。
- 结算单必须保留合同、项目、往来单位、币种、结算类型和明细合同的一致性。
- 付款申请必须受已批准结算、合同方向、项目、往来单位和结算余额约束。
- 历史结算和直营验收来源不伪造合同；有正式合同来源的结算必须承接合同快照。
- 合同/结算/付款分类后续进入 `sc.business.category` 和行业模板，当前 action/context/表单分组只是过渡呈现方式。

## Entry Matrix

| 用户入口 | 正式模型 | 当前办理动作 | 下游事实 | 当前结论 | 下一步 |
| --- | --- | --- | --- | --- | --- |
| 支出合同 | `construction.contract` | 保存、提交、审批/确认 | 结算、付款、合同对账 | 可作为付款类合同锚点 | 补合同类别与业务分类字典绑定 |
| 支出结算 | `sc.settlement.order` | 保存、提交、统一审批通过、完成、取消 | 付款申请、合同对账 | 已有合同/项目/往来单位/采购依据/结算余额约束 | 扩展收入结算和多来源结算归集 |
| 付款申请 | `payment.request` | 保存、提交、统一审批通过、完成 | `payment.ledger` | 已受结算状态、合同方向、结算余额和资金基准约束 | 补合同发票、成本、账户维度追溯 |
| 收款申请 | `payment.request` | 保存、提交、统一审批通过、收款登记后完成 | `sc.treasury.ledger` | 收入合同方向、项目、往来单位、合同关系可追溯 | 补收入结算和回款余额策略 |
| 收款登记 | `sc.receipt.income` | 保存、确认、登记收款 | 收款申请完成、资金台账 | 已要求收款申请、合同、往来单位、收款账户，并能自动完成收款申请 | 沉淀工程进度款、残余收款等分类策略 |
| 销项发票登记 | `sc.invoice.registration` | 保存、确认、登记 | 合同执行开票金额 | 已校验项目、合同、往来单位，登记后进入合同开票金额 | 补开票申请、红冲、收款关联余额策略 |
| 合同对账 | `sc.contract.recon.summary` | 按合同汇总结算与付款 | 余额解释 | 可解释结算总额、付款总额和差额 | 后续再接开票、收款和成本口径 |

## Current Gate

```text
DB_NAME=sc_demo scripts/ops/validate_business_category_dictionary.sh
BUSINESS_CATEGORY_DICTIONARY_AUDIT: status=PASS
category_count=48
contract categories: contract.income, contract.expense, settlement.income, settlement.expense

DB_NAME=sc_demo scripts/ops/validate_contract_settlement_payment_closure.sh
CONTRACT_SETTLEMENT_PAYMENT_CLOSURE_AUDIT: status=PASS
evidence: contract=12581, settlement=3133, payment_request=36713, settlement_total=1200.0, payment_total=450.0, delta=750.0, payment_ledger_count=1

DB_NAME=sc_demo scripts/ops/validate_income_contract_receipt_invoice_closure.sh
INCOME_CONTRACT_RECEIPT_INVOICE_CLOSURE_AUDIT: status=PASS
evidence: contract=12582, receipt_request=36714, receipt_income=351134, treasury_ledger=293722, invoice=775051, receipt_amount=800.0, invoice_total=872.0, contract_received_amount=800.0, contract_invoice_amount=872.0
```

门禁覆盖：

- `sc.business.category` 已覆盖合同域四类办理：收入合同、支出合同、收入合同结算、支出合同结算。
- 合同域分类已绑定目标 action、正式模型、默认值、入口 domain、必填字段和下游台账策略。
- 新建支出合同、项目、往来单位和资金基准。
- 新建带采购依据的结算单和结算明细。
- 结算单通过 `action_submit` 进入提交状态，通过统一审批回调进入已批准。
- 付款申请通过 `action_submit`、统一审批回调和 `action_done` 完成付款。
- `payment.ledger` 写入付款事实。
- `sc.contract.recon.summary` 能解释结算总额、付款总额和差额。
- 已有关联已批准/已完成付款时，直接写结算单 `state=cancel` 被 `P0_SETTLEMENT_CANCEL_BLOCKED` 拦截。
- 新建收入合同、收款申请、收款登记和销项发票登记。
- 收款申请通过 `action_submit` 和统一审批回调进入已批准。
- 收款登记通过 `action_confirm` 和 `action_received` 完成，自动生成 `sc.treasury.ledger` 并完成收款申请。
- 销项发票通过 `action_confirm` 和 `action_register` 完成登记。
- `construction.contract` 执行金额能反映本轮收款金额和销项开票金额。

## Boundary Rules

- 支出合同对应付款申请，收入合同对应收款申请；合同方向不一致必须阻断。
- 结算单审批必须通过正式动作，不能用直接写状态替代办理路径。
- 结算单取消必须检查已批准、已完成或已付款申请，不能绕过动作保护。
- 付款申请完成前必须可追溯到合同、结算、项目、往来单位和付款台账。
- 收款申请完成前必须可追溯到收入合同、项目、往来单位、收款登记和资金台账。
- 销项发票登记必须校验项目、合同和往来单位一致性；登记后进入合同开票执行口径。
- 合同对账是办理结果解释，不替代合同、结算、付款入口。
- 菜单可以整合到合同/结算域，但收入合同、支出合同、收入结算、支出结算、付款申请和收款申请必须按业务类别清晰切分。
- 合同分类、结算分类和收付款分类后续必须沉淀到可维护业务分类字典，支持行业模板默认值和客户覆盖。

## Next Gates

- 收入合同 -> 收款申请 -> 收款台账 -> 开票/结算追溯的分类策略字典化。
- 合同 -> 发票登记/开票申请 -> 收付款/结算一致性，补开票余额、回款余额和红冲策略。
- 多来源结算归集：采购、材料、劳务、分包、直营验收来源的统一结算解释。
- 合同余额、结算余额、发票余额、收付款余额的统一字段和硬阻断策略。
- 合同/结算分类进入 `sc.business.category`，并绑定默认必填字段、附件策略、审批策略和下游台账策略。
