# 保证金办理闭环口径

日期：2026-06-12

## 业务边界

- 保证金办理是项目经营收付款类现金业务，不纳入往来借还款责任域。
- 保证金缴纳、退回必须关联真实 `payment.request`，用于承接用户可见的付款申请、收款申请办理过程。
- 完成后的现金事实进入对应台账：
  - 保证金缴纳写入 `payment.ledger`，同步付款申请完成状态。
  - 保证金退回写入 `sc.treasury.ledger`，同步收款申请完成状态。
- 资金台账通过 `payment_request_id` 和来源单据追溯经营收付款，不复用往来款的无申请办理口径。
- 系统币种口径确定为人民币 CNY；保证金办理不再把币种作为用户选择项。

## 用户数据依据

- 用户历史保证金事实已形成独立业务域，当前摘要口径为：
  - `guarantee_deposit` 共 7439 条。
  - 发生额 648,603,388.91。
  - 未清余额 47,125,375.59。
- 旧数据主要落在投标保证金缴纳、投标保证金退回两个可见办理类别；合同保证金入口保留为标准行业模板能力。
- 保证金分类必须继续字典化，长期锚点为 `sc.business.category.code`，不能依赖旧文本标题推断。

## 办理规则

- `finance.deposit.bid.pay`：投标保证金缴纳，目标模型 `sc.expense.claim`，完成动作 `action_done`。
- `finance.deposit.bid.return`：投标保证金退回，目标模型 `sc.expense.claim`，完成动作 `action_done`。
- `finance.deposit.contract.pay`：合同保证金缴纳，作为行业模板入口保留。
- `finance.deposit.contract.return`：合同保证金退回，作为行业模板入口保留。
- 新系统保证金退回必须受同项目、同往来单位、同保证金类型的已缴未退余额约束。
- 超出可退余额的退回单不得提交、批准或完成；该规则作用在办理链路，不等待报表发现。

## 迭代原则

- 保证金域当前优先闭合办理动作、余额约束、台账追溯；报表继续后置。
- 菜单入口可以整合，但投标保证金、合同保证金等业务类别必须保留为可维护字典分类。
- 用户现有投标保证金数据是一个行业特例，产品实现必须沉淀为可扩展的保证金模板，而不是写死单一客户口径。
- 后续若出现履约保证金、质量保证金等新类型，应先扩展业务分类字典和表单分组，再补办理校验。

## 本轮验收命令

- `DB_NAME=sc_demo make verify.finance_expense_category.handling_policy.audit`
- `DB_NAME=sc_demo make verify.finance_business_project.summary.audit`
- `DB_NAME=sc_demo make verify.finance_handling.http_surface.smoke`
