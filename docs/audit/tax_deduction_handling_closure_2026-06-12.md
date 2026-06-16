# 税务抵扣办理闭环口径

日期：2026-06-12

## 业务边界

- 税务抵扣登记是税务事实，不是现金收付款事实，不进入 `payment.request`，也不写现金收支台账。
- 抵扣完成后生成 `sc.finance.business.fact`，进入项目资金事实和项目资金总览，用于反映项目税务口径。
- 税务抵扣 `balance_effect` 保持为 0，不能混入到款、付款、往来款或保证金余额。
- 系统币种口径确定为人民币 CNY；税务办理不再把币种作为用户选择项。

## 用户数据依据

- 当前用户本地库 `sc_tax_deduction_registration` 共 10231 条。
- 10231 条均为普通抵扣登记：
  - `is_transfer_out = false`。
  - `withholding_amount = 0`。
  - `business_category_id` 无缺失。
- 当前用户数据没有进项税额转出、扣款抵扣分支；因此本轮不新增用户不可见的办理入口，不改变用户认知。

## 办理规则

- `tax.deduction.registration`：抵扣登记，目标模型 `sc.tax.deduction.registration`，完成动作 `action_deduct`。
- 草稿可确认，确认后可完成抵扣；完成抵扣必须具备发票号码、认证抵扣日期和大于 0 的抵扣税额。
- 抵扣税额不能超过发票税额，抵扣金额不能超过发票不含税金额。
- 财务经理或财务角色才能执行终态抵扣确认。
- 抵扣完成后必须能追溯：
  - 来源登记单。
  - `sc.finance.business.fact` 税务事实。
  - `sc.finance.business.project.summary` 项目税务摘要。
  - `sc.finance.project.capital.position` 项目资金总览。

## 行业模板后续

- 进项税额转出、扣款抵扣不能长期混在 `tax.deduction.registration` 普通抵扣分类中。
- 若后续用户数据或新客户启用这些分支，必须先补独立业务分类字典、入口 domain、默认值、必填字段和办理校验，再允许验收。
- 当前审计已记录分支检查：出现 `is_transfer_out = true` 或 `withholding_amount != 0` 时，如果仍没有独立分类模板，分类绑定审计应失败。

## 本轮验收命令

- `DB_NAME=sc_demo scripts/ops/validate_invoice_tax_category_binding.sh`
- `DB_NAME=sc_demo scripts/ops/validate_invoice_tax_handling_evidence.sh`
- `DB_NAME=sc_demo scripts/ops/validate_invoice_tax_downstream_traceability.sh`
- `DB_NAME=sc_demo make verify.finance_business_project.summary.audit`
