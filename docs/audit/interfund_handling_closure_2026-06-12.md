# 往来借还款办理闭环口径

日期：2026-06-12

## 用户数据边界

- 旧系统没有统一“往来款”概念，当前产品口径按公司、项目、承包人三主体重新归类。
- 纳入往来办理闭环的事实：
  - 项目借公司款：`company_to_project_borrow`
  - 项目还公司款：`project_to_company_repay`
  - 承包人借项目款：`project_to_contractor_borrow`
  - 承包人还项目款：`contractor_to_project_repay`
  - 项目间账户调拨：`project_to_project_transfer`
- 不纳入往来责任事实的输入：
  - 资金日报：作为用户日报型台账/余额快照，不作为往来责任发生事实。
  - 同项目账户调拨：现金流净影响为 0，不形成外部应收应还责任。
  - 余额校准：只影响账户状态，不直接形成对方资金责任。

## 办理规则

- 往来借还款和经营收付款申请彻底分开，不关联 `payment.request`，不写 `payment.ledger`。
- 往来现金流进入 `sc.treasury.ledger`，通过 `source_model/source_res_id` 追溯原始办理单据。
- 新系统借款办理完成前必须选择具体字典分类：
  - `finance.loan.contractor_project_borrow`
  - `finance.loan.project_borrow_company`
- 泛化的 `finance.loan.borrowing` 只作为借款申请入口/聚合入口，不允许直接完成入账；完成入账必须落到具体动作域。
- 历史迁移数据可以保留文本识别证据，但交付口径以 `business_category_id.code` 为长期锚点。

## 当前本地验证结论

- `sc.interfund.movement.fact` 覆盖 1543 条往来事实，全部高置信，无重复来源。
- 应进入资金台账的 1171 条往来现金流均已有 `sc.treasury.ledger` 来源追溯。
- 资金日报没有漏入往来事实。
- 旧“承包人借项目款”入口中存在按用途分流到项目借公司款的记录，不能用旧菜单名直接作为长期分类基线；必须继续以可维护业务分类字典承接。

## 本轮验收命令

- `DB_NAME=sc_demo make verify.finance_interfund_category.handling_policy.audit`
- `DB_NAME=sc_demo make verify.interfund_movement.fact.audit`
- `DB_NAME=sc_demo make verify.interfund_treasury_ledger.backfill_readiness.audit`
