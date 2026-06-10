# 业务能力产品化专题 - 第一轮实施清单

基线：`docs/product/business_capability_productization_baseline_v1.json`

画像：`artifacts/user_business_data_portrait.sc_demo.json`

门禁：`scripts/verify/user_business_productization_baseline_guard.py`

锁定事实正式模型连续性守卫：`scripts/verify/locked_fact_formal_model_continuity_guard.py`

## 不变边界

1. 用户已验收的正式菜单、列表字段、数据可见面保持锁定。
2. 旧系统入口不直接决定新系统产品入口，只保留来源明细和追溯价值。
3. 新增办理能力必须进入产品化业务入口，不能把临时菜单暴露给用户。
4. 办理入口必须可新增、可保存、可提交/确认/完成，并能回流到汇总视图或来源事实。
5. 附件、历史流程、审批轨迹不能丢失。
6. 用户已验收的历史业务事实数据不得被改写；所有事实画像、候选关系、口径分析只能只读使用。
7. 新系统业务闭环可以基于锁定事实设计归集口径，但归集结果必须通过新办理单据、派生视图或非侵入式映射层承载，不写回锁定事实表。

## 第一轮 P1 范围

### 首轮缺口优先级

报告：`artifacts/p1_business_relationship_gap_report.md`

当前 P1 主模型识别出 18 个存在正式办理关系缺口的模型，总缺口计数 414,726，其中 13 个为 critical。这里的缺口只作为业务闭环设计依据，不代表要改写用户已锁定事实数据。第一批不先做新菜单扩张，先解决新系统办理链路中的关系承载和闭环：

1. 付款与费用：`sc.expense.claim`、`sc.payment.execution`、`payment.request`
2. 税务与发票：`sc.invoice.registration`、`sc.tax.deduction.registration`、`sc.output.invoice.ledger`
3. 预算成本管控：`project.cost.ledger`
4. 收入与收款：`sc.receipt.income`、`sc.receipt.invoice.line`
5. 账户与往来资金：`sc.fund.account.operation`、`sc.financing.loan`
6. 合同与结算：`sc.settlement.order`
7. 项目与主数据：`sc.business.entity`、`project.project`

处理顺序按“合同/项目/往来单位/账户关系口径 -> 新办理动作 -> 派生汇总回流”推进，不能只补列表显示，也不能直接写回锁定事实。

候选规则探针：`artifacts/p1_locked_fact_mapping_candidate_probe.sc_demo.json`

本轮探针结论：

- 可进入新办理归集/非侵入式映射候选：
  - `sc.receipt.income.partner_id`：缺口 8,418，文本/映射匹配 8,418，覆盖率 100%。
  - `sc.invoice.registration.partner_id`：缺口 41,893，匹配 35,473，覆盖率 84.68%。
  - `sc.tax.deduction.registration.partner_id`：缺口 5,202，匹配 4,517，覆盖率 86.83%。
- 可进入人工确认映射候选：
  - `sc.business.entity.partner_id`：缺口 11,070，匹配 7,603，覆盖率 68.68%，需要确认内部核算主体/项目经营载体是否应绑定往来单位。
- 只能人工/规则增强后处理：
  - `sc.expense.claim.partner_id`：覆盖率 17.75%，有来源字段但需要结合扣款/保证金/还款类型进一步拆分。
  - `sc.payment.execution.payment_request_id`：覆盖率 5.97%，需要从付款申请行、历史申请号和实际付款来源建立链路。
  - `sc.fund.account.operation.source_account_id/target_account_id`：覆盖率约 4%，需要先治理账户主数据和历史账户号。
  - `sc.financing.loan.partner_id`：覆盖率 18.42%，需要按借款类型区分公司、承包人和项目载体。
- 暂不能按文本直接建立关系：
  - 合同关系类：`sc.invoice.registration.contract_id`、`sc.receipt.income.contract_id`、`payment.request.contract_id`、`sc.settlement.order.contract_id` 等 exact match 基本为 0，必须从项目、合同台账、结算、付款/收款申请关系推导。
  - `project.cost.ledger.partner_id`：备注字段不适合作为往来单位直接匹配，应从来源单据或成本归集链路补。

### A. 项目经营关系口径

目标：新发生的 P1 办理单据以项目为第一关系口径，并尽量具备往来单位、合同、账户关系。历史锁定事实只用于派生视图和映射建议，不写回。

本轮任务：

- 盘点 P1 主模型的关系缺口。
- 明确新办理单据的关系必填规则、历史事实的只读映射建议和人工确认入口。
- 对历史名称字段保留追溯，但正式办理使用正式主数据字段。

验收：

- 项目、往来单位、合同、账户关系缺口可统计。
- 候选关系只读可审计；任何需要落地的关系必须进入新单据或映射层，不改写锁定事实。

### B. 合同与结算办理

目标：合同成为收款、付款、发票、结算、成本的业务主干。

本轮任务：

- 固化收入合同办理、支出合同办理、收入合同结算、支出合同结算四个入口。
- 结算单合同/往来单位关系缺口分析。
- 合同台账提供收款、付款、发票、结算的汇总关系。

验收：

- 合同记录能进入结算办理。
- 结算记录能反查合同、项目、往来单位。
- 合同台账能解释核心金额来源。

### C. 收入与收款办理

目标：到款确认、工程进度收款、自筹资金都统一到项目收入/收款办理。

本轮任务：

- 以 `sc.receipt.income` 作为项目收款登记主模型。
- 区分正式办理入口和到款/工程进度/自筹来源明细。
- 设计往来单位、合同、收款申请关系在新办理链路和派生汇总中的承载规则。

验收：

- 用户从“项目收款登记”能新增并完成收款业务。
- 历史来源数据仍可追溯到来源明细。
- 收款记录能进入项目资金总览和收入汇总。

### D. 付款与费用办理

目标：付款申请、付款执行、费用/保证金/扣款类事实形成统一付款办理链。

本轮任务：

- 以 `payment.request`、`sc.payment.execution`、`sc.expense.claim` 组成付款办理主链。
- 给 `sc.expense.claim.claim_type` 建立用户可理解的业务入口：费用、保证金、扣款、项目还款。
- 明确费用事实如何沉淀到成本台账。

验收：

- 付款申请能提交、审批、执行。
- 费用/保证金/扣款记录能解释资金流向。
- 付款和费用能关联项目、往来单位、合同、成本。

### E. 税务与发票办理

目标：发票登记、抵扣登记、销项台账统一进项目经营口径。

本轮任务：

- 固化发票登记、抵扣登记、销项发票台账入口。
- 抵扣登记作为非现金税务事实，进入项目经营汇总。
- 发票按项目、合同、往来单位的非侵入式归集规则。

验收：

- 发票/抵扣可办理并保留附件。
- 发票能按项目、合同、往来单位汇总。
- 抵扣金额不被错误计入现金收支。

### F. 资金往来与账户调拨办理

目标：公司与项目、项目与项目、项目与承包人之间的借还/调拨统一办理。

本轮任务：

- 以 `sc.fund.account.operation` 和 `sc.financing.loan` 承接办理入口。
- 资金往来结果回流 `项目资金总览`、`往来对象资金总览`、`项目往来明细`。
- 账户、往来单位、来源项目关系的映射建议和新办理必填规则。

验收：

- 资金往来/账户调拨能新增、确认、完成。
- 汇总视图只作为分析入口，不替代办理入口。
- 用户不需要理解旧表名即可办理业务。

### G. 预算成本管控

目标：成本台账成为付款、材料、分包、劳务、机械、发票的统一成本落点。

本轮任务：

- 成本科目、成本台账、成本期间锁定作为 P1 入口。
- 建立费用/付款/发票到成本台账的派生归集策略。
- 成本期间锁定防止历史数据被办理流误改。

验收：

- 成本台账能按项目、成本科目、往来单位统计。
- 已锁定期间不能被普通办理动作破坏。

### H. 审批附件治理

目标：所有正式办理动作可追溯。

本轮任务：

- 明确 P1 单据附件字段和审批策略。
- 历史附件索引与正式附件关系可查。
- 历史流程作为审计轨迹，不作为新审批流状态。

验收：

- P1 办理入口保存附件。
- 审批动作产生可追溯记录。
- 历史审批事实能在来源明细中查看。

## 第一轮验收组合

必须同时通过：

- `python3 scripts/verify/user_business_productization_baseline_guard.py`
- `python3 -m py_compile scripts/verify/user_business_data_portrait.py scripts/verify/user_business_productization_baseline_guard.py`
- `docker compose exec -T odoo odoo shell -d sc_demo -c /var/lib/odoo/odoo.conf < scripts/verify/locked_fact_formal_model_continuity_guard.py`
- 用户已验收菜单/列表稳定性验收
- P1 办理入口浏览器验收
- P1 主模型关系缺口统计验收
- 锁定事实只读策略验收

当前本地 `sc_demo` 守卫结论：

- `sc.receipt.income`：13,429 条锁定历史事实，非法改 `amount` 被拦截。
- `sc.expense.claim`：65,295 条锁定历史事实，非法改 `amount` 被拦截。
- `sc.invoice.registration`：69,485 条锁定历史事实，非法改 `amount_total` 被拦截。
- `sc.tax.deduction.registration`：5,037 条锁定历史事实，非法改 `invoice_amount_total` 被拦截。
- `sc.payment.execution`：37,716 条锁定历史事实，非法改 `planned_amount` 被拦截。
- `sc.financing.loan`：463 条锁定历史事实，非法改 `amount` 被拦截。
- `payment.request`、`sc.settlement.order`、`sc.fund.account.operation` 已有正式来源载体记录，后续连续办理通过新单据、派生视图或非侵入式映射层承载。

## 第二轮再进入的范围

- 材料采购库存
- 分包劳务机械
- 现场进度质量安全

这三类数据量很大，但第一轮先不混入办理主链重构，避免在财务/合同/成本主干未稳定前扩大风险。
