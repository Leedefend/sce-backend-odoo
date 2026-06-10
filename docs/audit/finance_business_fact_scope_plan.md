# 财务中心业务事实口径整合计划

## 目标

财务中心历史数据不能继续按旧菜单细项直接进入正式办理口径。正式办理应围绕业务事实统一，旧菜单只保留为来源追溯与用户验收证据。

本专题将财务事实收敛为五个正式口径：

| 正式口径 | 承载事实 | 业务定位 |
| --- | --- | --- |
| 工程款到账清算 | 到款确认表 | 工程款到账后，拆分到账、代扣代缴、拨付、留存 |
| 扣款代缴与退回 | 扣款实缴登记、扣款实缴退回 | 管理费、税费、风险责任金等扣出、实缴、退回、未退 |
| 税务抵扣 | 抵扣登记 | 发票认证抵扣与税负，不作为现金流 |
| 自筹垫资与退回 | 自筹收入、自筹退回 | 项目垫资权益、退回、未退余额 |
| 保证金支出与退回 | 自筹保证金、付款保证金、保证金退回 | 投标/履约保证金资金来源、支出、退回、在外 |

## 当前审计结论

审计命令：

```bash
DB_NAME=sc_demo MIGRATION_ARTIFACT_ROOT=artifacts/migration make verify.finance_business_fact.scope.audit
```

当前数据规模：

| 事实类 | 数量 | 金额口径 |
| --- | ---: | ---: |
| 到款确认表 | 5205 | 本期收款约 45.05 亿，代扣代缴约 2.08 亿，拨付约 43.23 亿 |
| 扣款实缴登记 | 13264 | 正式菜单来源口径 `online_old_scbs:T_KK_SJDJB:list897` |
| 扣款实缴退回 | 1800 | 正式菜单来源口径 `online_old_scbs:T_KK_SJTHB:list898` |
| 抵扣登记 | 10231 | 抵扣税额约 1.14 亿 |
| 自筹收入/退回 | 6699 | 自筹收入约 4.46 亿，退回约 1.45 亿，未退约 3.01 亿 |
| 投标保证金 | 7439 | 支出约 3.48 亿，退回约 3.01 亿，在外约 4712 万 |

## 口径风险

自筹数据存在必须先定政策的来源口径风险：

- `income` 与 `income_visible` 金额接近，存在近似重复事实族。
- `refund_visible` 有记录数但退回金额为 0，余额计算不能直接使用该族。

因此，自筹余额不能简单对所有 `sc.legacy.self.funding.fact` 行求和。正式办理口径必须明确：

- 收入使用 `income` 还是 `income_visible`。
- 退回使用 `refund`，还是需要证明 `refund_visible` 与 `refund` 的对应关系。
- 用户可见菜单与余额计算口径要分开治理：可见菜单保留验收一致性，余额口径使用可证明金额来源。

## 正式办理设计

后续正式能力建议分三层落地：

1. **事实层**
   - 已新增统一财务业务事实投影 `sc.finance.business.fact`，按五个正式口径归类。
   - 保留 `source_model/source_res_id/legacy_record_id/source_menu_hint`。
   - 不直接修改用户已验收菜单。
   - 不挂正式菜单，仅作为后台审计与后续办理模型的数据底座。

2. **办理层**
   - 工程款到账清算：到账确认、扣款拆分、拨付确认。
   - 扣款代缴与退回：扣款确认、实缴、退回、未退余额。
   - 税务抵扣：认证抵扣、转出、未抵扣。
   - 自筹垫资：垫入、退回、核销、未退余额。
   - 保证金：缴纳、退回、在外、资金来源。

3. **看板层**
   - 已新增项目财务业务事实汇总 `sc.finance.business.project.summary`，按项目和业务域归集。
   - 项目资金余额。
   - 公司与项目结算。
   - 项目扣款清算。
   - 自筹垫资余额。
   - 保证金在外余额。
   - 税务抵扣台账。

## 边界

- `sc.treasury.ledger` 继续承载付款/收款申请形成的资金台账，不强行承接税务抵扣或历史扣款清算。
- 到款确认、扣款清算、自筹、保证金需要进入统一财务事实视图，但不能混同为同一种资金往来。
- 税务抵扣是税务权益事实，不应计入现金流余额。

## 已落地事实投影

审计命令：

```bash
DB_NAME=sc_demo MIGRATION_ARTIFACT_ROOT=artifacts/migration make verify.finance_business_fact.projection.audit
```

`sc.finance.business.fact` 的余额策略：

| 业务域 | 来源 | 正式余额策略 |
| --- | --- | --- |
| 到款确认 | `sc.legacy.fund.confirmation.document` | `arrival_gross` 计入正式余额，同时保留代扣代缴、拨付金额 |
| 扣款实缴 | `sc.expense.claim` / `online_old_scbs:T_KK_SJDJB:list897` | `deduction_paid` 计入正式余额 |
| 扣款退回 | `sc.expense.claim` / `online_old_scbs:T_KK_SJTHB:list898` | `deduction_refund` 以负向余额影响计入 |
| 抵扣登记 | `sc.tax.deduction.registration` | `tax_deducted` 保留税务事实，`balance_effect=0` |
| 自筹收入/退回 | `sc.legacy.self.funding.fact` | `income/refund` 计入正式余额，`income_visible/refund_visible` 仅作可见参考且 `balance_effect=0` |
| 保证金 | `tender.guarantee` | `out/return` 分别以正负余额影响计入 |

这个投影解决的是“用户验收数据如何成为后续办理模型的事实底座”。它不是最终办理单据，也不替代用户已确认的正式菜单。

## 已落地项目汇总

审计命令：

```bash
DB_NAME=sc_demo MIGRATION_ARTIFACT_ROOT=artifacts/migration make verify.finance_business_project.summary.audit
```

`sc.finance.business.project.summary` 从 `sc.finance.business.fact` 汇总，不直接重读旧表。它的职责是：

- 按项目、业务域汇总事实明细数量。
- 汇总正式余额影响、现金流入、现金流出、扣款、拨付、税额。
- 单独给出扣款净额、自筹正式余额、保证金在外余额。
- 自筹可见参考金额保留为参考指标，不计入 `self_funding_balance`。
- 税务抵扣保留抵扣金额和抵扣税额，`balance_effect` 仍为 0。

这个汇总层用于后续业务办理口径和看板，不发布为正式业务菜单。

## 已落地项目资金综合口径

审计命令：

```bash
DB_NAME=sc_demo MIGRATION_ARTIFACT_ROOT=artifacts/migration make verify.finance_project_capital.position.audit
```

已新增只读投影 `sc.finance.project.capital.position`，按项目合并两类已审计汇总：

- `sc.finance.business.project.summary`：到款、扣款、抵扣、自筹、保证金五类财务业务事实。
- `sc.interfund.movement.project.summary`：公司与项目、项目与项目、项目与承包人之间的资金往来事实。

该综合口径的职责是：

- 给出项目层面的财务余额影响、现金流入、现金流出、现金净额。
- 给出项目资金往来流入、流出、净流入、项目内调拨。
- 保留到款、扣款、自筹、保证金、公司借还、承包人借还等关键拆分指标。
- 形成 `combined_balance_effect` 和 `combined_cash_net_amount`，用于后续项目资金占用、垫资、借还款和清分分析。

边界：

- 不新增正式菜单，不改变用户已确认菜单。
- 不回写来源单据，不替代到款、扣款、保证金、账户往来等业务表。
- 不把税务抵扣计入现金净额；抵扣仍作为税务权益事实保留。
- `combined_balance_effect` 是分析口径，不等同于会计科目余额或银行账户余额。

## 已落地项目往来对象口径

审计命令：

```bash
DB_NAME=sc_demo MIGRATION_ARTIFACT_ROOT=artifacts/migration make verify.finance_project_counterparty.position.audit
```

已新增只读投影 `sc.finance.project.counterparty.position`，在项目资金综合口径基础上进一步按“对方对象”归集：

- 财务业务事实：按项目与往来单位/人员归集，缺失对象时保留为未识别对象。
- 缺失项目的财务业务事实：保留为未关联项目，不强行挂到错误项目。
- 公司与项目借还：对方对象归为公司。
- 项目与项目调拨：来源项目和目标项目分别以对方项目归集。
- 项目与承包人借还：对方对象归为往来单位/人员。
- 同项目账户调拨：对方对象归为项目内部账户，只计内部调拨，不形成净流入。

该层用于回答“项目资金和谁发生关系、综合影响是多少”。它不新增正式菜单，不修改用户已确认列表，也不替代来源业务单据。

## 已落地往来对象综合口径

审计命令：

```bash
DB_NAME=sc_demo MIGRATION_ARTIFACT_ROOT=artifacts/migration make verify.finance_counterparty.position_summary.audit
```

已新增只读投影 `sc.finance.counterparty.position.summary`，从 `sc.finance.project.counterparty.position` 跨项目归集到对象层面：

- 按公司、项目、往来单位/人员、项目内部、未识别对象汇总。
- 保留涉及项目数、财务事实明细数、资金往来明细数和综合明细数。
- 汇总财务余额影响、财务现金净额、资金往来净流入、综合余额影响和综合现金净额。
- 给出正向余额、负向余额、已平衡三个方向，便于后续清收、清付、核对和补录对象。

该层用于回答“同一个对方对象跨所有项目总体和我们是什么资金关系”。它不新增正式菜单，不改变用户已确认菜单体系。

## 往来对象识别质量门禁

审计命令：

```bash
DB_NAME=sc_demo MIGRATION_ARTIFACT_ROOT=artifacts/migration make verify.finance_counterparty.identity_quality.audit
```

该审计固定以下约束：

- 禁止出现 `unknown / 公司`，避免把缺失承包人名称的资金事实误导为公司往来。
- 项目与承包人借还缺失承包人名称时，统一归为 `往来单位/人员 / 未识别承包人`。
- 未识别对象只允许使用 `未识别对象` 这一口径。
- 资金往来事实必须全部进入项目视角透视，不能有遗漏。
- 财务事实缺失往来对象时，必须落入已解释的来源类型：扣款清分、保证金无投标业主、到款确认无建设单位、税务非现金事实、自筹旧数据缺稳定对象。

当前已知待后续业务补强的对象缺口：

- 扣款实缴/退回大量旧数据只有税金、管理费等清分说明，没有稳定客户/供应商对象，暂按未识别对象保留。
- 部分投标保证金只关联投标记录但投标业主缺失，保留为未识别对象。
- 部分到款确认来源没有建设单位名称，保留为未识别对象。
- `未识别承包人` 是明确的承包人类事实缺口，不再混入公司口径。

## 专题总门禁

完整资金事实与资金往来专题收口审计命令：

```bash
DB_NAME=sc_demo MIGRATION_ARTIFACT_ROOT=artifacts/migration make verify.finance_interfund.position.all
```

该总门禁串联以下检查：

- 资金事实投影静态守卫：只读 SQL 视图、无菜单入口、权限只读。
- 财务业务事实来源范围审计。
- 财务业务事实投影闭合审计。
- 财务业务项目汇总审计。
- 资金往来事实审计。
- 资金往来项目视角汇总审计。
- 项目资金综合口径审计。
- 项目往来对象口径审计。
- 往来对象综合口径审计。
- 往来对象识别质量门禁。
- 资金事实专题汇总报告。

该总门禁只读校验，不写业务数据，不发布菜单。

静态守卫可单独执行：

```bash
make verify.finance_interfund.projection.static_guard
```

汇总报告可单独生成：

```bash
DB_NAME=sc_demo MIGRATION_ARTIFACT_ROOT=artifacts/migration make verify.finance_interfund.position.bundle_summary
```

当前汇总报告核心口径：

- 财务事实 44,638 条，并贯通到项目汇总、项目资金综合、项目对象、对象汇总四层。
- 资金往来事实 1,938 条，项目视角展开为 1,950 条，并贯通到项目资金综合、项目对象、对象汇总三层。
- 项目资金综合口径 660 行。
- 项目往来对象口径 6,706 行。
- 往来对象综合口径 4,258 行。
- 综合余额影响 5,050,079,658.45。
- 综合现金净额 4,955,828,907.27。
