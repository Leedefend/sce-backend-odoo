# 业务能力产品化专题 - 第一轮实施清单

基线：`docs/product/business_capability_productization_baseline_v1.json`

画像：`artifacts/user_business_data_portrait.sc_demo.json`

用户确认可见列表业务入口整合计划：`docs/product/user_confirmed_62_business_entry_integration_plan.md`

锁定菜单整合矩阵：`artifacts/user_confirmed_62_business_entry_integration_matrix.md`

客户旧系统在线核实协议属于私有迁移交付物，不进入标准产品仓库。

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
8. 用户在线系统实时可见面是业务口径最高优先级证据。后续每个业务域收口前，必须优先核实旧在线系统和在线开发系统的真实菜单、列表字段、记录数量、表单字段和办理动作；本地 SQL、迁移产物和静态代码只能作为解释与实现证据，不能替代在线可见面。
9. 在线核实默认按业务域增量拉取，只指定当前需要验证的旧系统菜单序号；最终交付收口前才显式运行完整旧新系统实时一致性门禁。
10. 开发服务器未升级当前分支前，不用线上缺模型、缺 action 或旧页面报错判断本地功能完成度；本地先以 `sc_demo` 的模型、菜单、HTTP intent 和业务数据门禁收口，升级后再做在线可见面复核。

## 第一轮 P1 范围

### 用户确认可见列表先行分析

功能完善必须先服从用户确认的锁定可见列表入口。当前基线启用 60 个入口，这些入口不是简单菜单清单，而是用户已验收的业务事实边界。后续办理能力完善不能绕过这套入口体系，也不能因为新增产品化能力改变用户已经确认的菜单和列表数据。

本轮新增只读整合矩阵：

- 脚本：`scripts/verify/user_confirmed_62_business_entry_integration_matrix.py`
- 输出：`artifacts/user_confirmed_62_business_entry_integration_matrix.json`
- 输出：`artifacts/user_confirmed_62_business_entry_integration_matrix.md`

矩阵按锁定基线实际启用入口分类为正式办理入口、主数据入口、来源事实明细、汇总分析入口和配置入口，并给出统一承接口径。后续所有办理能力改造必须从该矩阵进入，不能只按单个模型或单个按钮局部修补。

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
- `sc.settlement.order` 表单以“业务方向、项目与合同、往来单位、结算金额、来源匹配、办理说明”组织字段，列表直接展示办理事项。
- 收入合同结算、支出合同结算保持用户确认的锁定列表口径，运行态仍为 `create=False`；底层正式模型承接新增和后续连续办理能力。
- 直采/方单来源的材料、机械、劳务、分包结算不强行绑定正式合同；优先补齐项目、往来单位和来源可见字段，只有唯一、可审计证据才自动落正式关系。

验收：

- 合同记录能进入结算办理。
- 结算记录能反查合同、项目、往来单位。
- 合同台账能解释核心金额来源。
- `scripts/verify/finance_interfund_handling_entry_audit.py` 必须覆盖结算主模型和收入/支出结算动作，防止 action 模型、默认结算类型和表单语义漂移。
- `scripts/ops/validate_mechanical_settlement_partner.sh` 必须证明机械结算单中旧可见结算单位能唯一匹配的往来单位已经回填；同名重复和旧字段为空保留为人工核对残差。

### C. 收入与收款办理

目标：到款确认、工程进度收款、自筹资金都统一到项目收入/收款办理。

本轮任务：

- 以 `sc.receipt.income` 作为项目收款登记主模型。
- 区分正式办理入口和到款/工程进度/自筹来源明细。
- 设计往来单位、合同、收款申请关系在新办理链路和派生汇总中的承载规则。
- `sc.receipt.income` 表单以“业务方向、项目与往来单位、收款信息、收款账户、收款金额/抵扣与结算、办理说明”组织字段，列表直接展示办理事项。
- “收入”作为可办理入口继续指向 `sc.receipt.income`；“工程进度款收入登记”保持用户确认的锁定列表口径，只作为已验收历史事实可见面，不被改成普通可编辑入口。

验收：

- 用户从“项目收款登记”能新增并完成收款业务。
- 历史来源数据仍可追溯到来源明细。
- 收款记录能进入项目资金总览和收入汇总。
- `scripts/verify/finance_interfund_handling_entry_audit.py` 必须覆盖收款收入主模型，防止 action 模型、默认收入类型和表单语义漂移。

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

本轮已落地的安全关系补强：

- 发票登记往来单位锚点：基于 `legacy_visible_partner_name`、`legacy_partner_name`、`recipient_unit_name` 与 `res.partner.name` 的唯一匹配，并要求发票自身合同/结算往来单位不冲突；已补齐 `sc.invoice.registration.partner_id` 31,967 条。
- 抵扣登记往来单位锚点：基于 `partner_name` 与 `res.partner.name` 的唯一匹配；已补齐 `sc.tax.deduction.registration.partner_id` 4,537 条。
- 只补正式关系字段 `partner_id`，不改写发票金额、税额、历史名称、来源字段和锁定事实口径。
- 验收脚本：`scripts/ops/validate_invoice_tax_partner_anchor.sh`，当前 `sc_demo` 结论为 PASS，发票/抵扣剩余安全候选均为 0；发票合同/结算范围冲突为 0。
- 当前残差：发票仍有 9,926 条无正式往来单位，其中 304 条无可用历史名称，其他为同名重复、无唯一主数据或需要人工/上下文确认；抵扣仍有 665 条无正式往来单位，其中 10 条无可用历史名称。残差不得自动落正式关系，后续进入人工确认或更强上下文规则。

本轮任务：

- 固化发票登记、抵扣登记、销项发票台账入口。
- 抵扣登记作为非现金税务事实，进入项目经营汇总。
- 发票按项目、合同、往来单位的非侵入式归集规则。
- `sc.invoice.registration` 表单以“业务方向、项目与往来单位、发票与税务信息、发票金额与税额、办理说明”组织字段，列表直接展示办理事项。
- `sc.tax.deduction.registration` 表单以“业务方向、项目与往来单位、发票信息、抵扣金额与税额、扣款办理、办理说明”组织字段，区分进项抵扣、扣款抵扣和税额转出。
- 销项开票申请、进项上报、预缴税款、抵扣登记的 action 模型和默认上下文纳入运行时审计；用户确认的锁定列表入口保持原验收口径。

验收：

- 发票/抵扣可办理并保留附件。
- 发票能按项目、合同、往来单位汇总。
- 抵扣金额不被错误计入现金收支。
- `scripts/verify/finance_interfund_handling_entry_audit.py` 必须覆盖发票税务主模型，防止 action 模型、默认业务口径和表单语义漂移。

### F. 资金往来与账户调拨办理

目标：公司与项目、项目与项目、项目与承包人之间的借还/调拨统一办理。

本轮只读审计结论：

- 账户调拨 `sc.fund.account.operation` 已有 395 条 `transfer_between` 记录，转出账户和转入账户均已具备正式账户关系；资金日报 7,453 条已具备日报账户关系，资金日报仍只作为用户日报型台账/余额状态输入，不作为往来责任事实。
- 融资/借款 `sc.financing.loan` 仍有正式往来单位缺口：借款申请 771 条缺 `partner_id`，贷款登记 152 条缺 `partner_id`。
- 只读候选审计：`scripts/ops/validate_interfund_financing_loan_partner_candidate.sh`。当前本地数据中，仅按历史往来方字段可形成 47 条唯一候选，其中借款申请 44 条、贷款登记 3 条；这些候选在完成旧在线系统与在线开发系统可见面核实前不得直接写入。
- 收款人、收款单位、收款账户、贷款账户等字段不能直接定义为借款责任往来方；它们可能只是代收对象或账户对象。此类候选必须进入在线可见面核实或人工确认，避免把收款对象误写成公司-项目/项目-承包人的责任主体。
- 在线增量证据：`ONLINE_VISIBLE_SURFACE_MODE=incremental ONLINE_VISIBLE_SURFACE_SEQS=022,023,027,028,032,037,038 DB_NAME=sc_demo bash scripts/ops/validate_online_visible_surface_verification.sh` 已通过，产物 `artifacts/migration/live_old_system_strict_parity_gate/20260611T132349Z`。旧系统实时记录数：借款申请 37、还款登记 25、承包人还项目款 157、承包人借项目款 166、账户间资金往来 485、项目借公司款登记 164、项目还公司款登记 155。行数据：022/023/027/028 复用前次实时 dump，032/037/038 本次补拉并通过。
- 本地 HTTP 可见面证据：`DB_NAME=sc_demo make verify.company_contractor.responsibility_http.smoke` 已通过，不依赖浏览器下载，覆盖 `system.init` 菜单、`ui.contract.v2` 页面契约、`api.data` 普通列表和按 `responsibility_state` 分组汇总。当前本地余额页 action=995、menu=823、模型 `sc.company.contractor.responsibility.summary`，分组列表总数 1,327、状态分组 3、汇总字段完整。
- 本地增量同步策略已调整为按旧表 + 旧记录号幂等承载，`SCBS55_FINANCING_SURFACE_SEQS=22,23,27,28,37,38 DB_NAME=sc_demo make odoo.shell.exec < scripts/migration/scbs55_financing_loan_surfaces_online_patch.py` 使用本地 artifact 重放后均为 `created=0`、按旧系统行数 `updated`。`verify.interfund_borrow.classification_gap.audit` 已通过，确认旧入口活动记录不重复进入办理列表、往来事实和现金流台账。
- 本地借款分类已从文本推断推进到正式业务分类字段：`sc.financing.loan.business_category_id` 绑定 `sc.business.category`，`finance.loan.contractor_project_borrow` 和 `finance.loan.project_borrow_company` 的入口 domain 已切到 `business_category_id.code`，新建入口通过 `default_business_category_code`/`business_category_code` 自动落类。历史活动借款往来 645 条已全部回填分类，其中 `project_to_contractor_borrow` 89 条、`company_to_project_borrow` 556 条，`classification_confidence=high` 覆盖 645 条。
- 去重后的本地往来借款事实为 645 条，其中旧“承包人借项目款”入口活动数 166 条；旧入口内部当前业务分类为 `project_to_contractor_borrow` 68 条、`company_to_project_borrow` 98 条。该差异不是覆盖缺口，而是旧入口、用途文本和三主体事实分类未完全等价；收口前必须由用户按验收口径确认这些旧入口中“借某项目工程款付材料款/借公司款/项目周转”等记录应归入公司-项目还是项目-承包人。
- 本地资金台账已按当前往来事实口径完成一致性清理：`sc.treasury.ledger._ensure_interfund_ledger` 会按来源幂等刷新金额、方向、币种和状态；`_void_stale_interfund_ledgers` 在模块升级同步中作废不再匹配当前 `sc.interfund.movement.fact` 的历史残留。`verify.interfund_treasury_ledger.backfill_readiness.audit` 通过，期望 1,171 条、已有 1,171 条、缺失 0、意外残留 0。
- 2026-06-11 本地开发库 `sc_demo` 已升级并通过 `COMPOSE_PROJECT_NAME=sc-backend-odoo-dev DB_NAME=sc_demo make verify.finance_interfund.position.all`，结论 `FINANCE_INTERFUND_POSITION_AUDIT_ALL_PASS db=sc_demo`。该结论仅代表本地开发库；开发服务器尚未升级，不能作为用户可见面完成依据。

本轮任务：

- 以 `sc.fund.account.operation` 和 `sc.financing.loan` 承接办理入口。
- 资金往来结果回流 `项目资金总览`、`往来对象资金总览`、`项目与对象资金往来`。
- 账户、往来单位、来源项目关系的映射建议和新办理必填规则。
- `sc.fund.account.operation` 表单以“业务方向、付款与收款、办理说明”组织字段，列表直接展示付款项目、收款项目、调拨金额。
- `sc.financing.loan` 表单以“借款方向、项目与往来单位、办理说明”组织字段，区分承包人借项目款、项目借公司款等办理口径。

验收：

- 资金往来/账户调拨能新增、确认、完成。
- 汇总视图只作为分析入口，不替代办理入口。
- 用户不需要理解旧表名即可办理业务。
- `scripts/verify/finance_interfund_handling_entry_audit.py` 必须通过，防止办理入口 action、默认业务口径和表单方向字段漂移。

### G. 预算成本管控

目标：成本台账成为付款、材料、分包、劳务、机械、发票的统一成本落点。

本轮任务：

- 成本科目、成本台账、成本期间锁定作为 P1 入口。
- 建立费用/付款/发票到成本台账的派生归集策略。
- 成本期间锁定防止历史数据被办理流误改。
- `project.cost.ledger` 正式入口统一发布为“成本归集台账”，表单按“成本归集、项目与成本科目、发生金额、来源追溯、办理说明”组织。
- 成本台账补充 `cost_flow_label`，把采购、入库、付款、费用、发票、抵扣、合同结算等来源转为用户能理解的成本来源口径。

验收：

- 成本台账能按项目、成本科目、往来单位统计。
- 已锁定期间不能被普通办理动作破坏。
- `scripts/verify/finance_interfund_handling_entry_audit.py` 必须覆盖成本归集入口、表单字段和核心分组文案，防止后续功能完善破坏办理口径。

### H. 审批附件治理

目标：所有正式办理动作可追溯。

本轮任务：

- 明确 P1 单据附件字段和审批策略。
- 历史附件索引与正式附件关系可查。
- 历史流程作为审计轨迹，不作为新审批流状态。
- P1 正式办理主链的附件、历史附件引用、状态动作纳入 `finance_interfund_handling_entry_audit.py` 运行态守护。
- 借款、付款申请、付款登记表单补充历史附件引用展示，确保历史依据能从正式办理页追溯。

验收：

- P1 办理入口保存附件。
- 审批动作产生可追溯记录。
- 历史审批事实能在来源明细中查看。
- 审计必须确认 P1 办理模型具备状态字段、附件字段、关键流转动作，且表单中可见附件/历史附件追溯字段。

## 第一轮验收组合

统一门禁：

- `make verify.business_capability.productization_p1 DB_NAME=sc_demo`

该门禁必须同时覆盖：

- 用户确认锁定菜单整合矩阵。
- 旧在线系统与在线开发系统真实用户可见面核实；缓存 dump 只能辅助定位，不能单独作为最终验收依据。
- 用户业务产品化基线。
- 用户已验收菜单/列表稳定性。
- 锁定事实只读和正式模型连续性。
- P1 办理入口 action、表单字段、附件/历史附件和状态动作。
- 锁定事实到正式关系的候选映射阈值。
- 结算、付款申请、付款登记、收款、发票之间的正式关系连续性。
- 新正式办理单据的项目/合同/申请类型范围拦截。
- 项目收付款、借还调拨、项目资金和往来单位资金投影一致性。
- 用户可见历史标签必须全部由正式产品字段承载，行业模块办理边界 `backlog/action_required` 必须保持 0。

必要时可单独拆跑：

- `python3 scripts/verify/user_business_productization_baseline_guard.py`
- `python3 -m py_compile scripts/verify/user_business_data_portrait.py scripts/verify/user_business_productization_baseline_guard.py`
- `DB_NAME=sc_demo make verify.user_data.product_field_coverage.matrix`
- `DB_NAME=sc_demo make verify.industry_module.handling_capability_boundary`
- `DB_NAME=sc_demo bash scripts/ops/odoo_shell_exec.sh < scripts/verify/locked_fact_formal_model_continuity_guard.py`
- `DB_NAME=sc_demo bash scripts/ops/odoo_shell_exec.sh < scripts/verify/p1_formal_relationship_continuity_audit.py`
- `DB_NAME=sc_demo bash scripts/ops/odoo_shell_exec.sh < scripts/verify/p1_formal_relationship_scope_block_smoke.py`
- 用户已验收菜单/列表稳定性验收
- P1 办理入口浏览器验收
- P1 主模型关系缺口统计验收
- 锁定事实只读策略验收

当前本地 `sc_demo` 守卫结论：

- `sc.receipt.income`：13,429 条锁定历史事实，非法改 `amount` 被拦截。
- `sc.expense.claim`：51,246 条锁定历史事实，非法改 `amount` 被拦截。
- `sc.invoice.registration`：69,485 条锁定历史事实，非法改 `amount_total` 被拦截。
- `sc.tax.deduction.registration`：5,037 条锁定历史事实，非法改 `invoice_amount_total` 被拦截。
- `sc.payment.execution`：39,903 条锁定历史事实，非法改 `planned_amount` 被拦截。
- `sc.financing.loan`：98 条锁定历史事实，非法改 `state` 被拦截；`amount`、`purpose`、`due_date`、`document_date` 等正式借款业务字段可继续维护。
- `payment.request`、`sc.settlement.order`、`sc.fund.account.operation` 已有正式来源载体记录，后续连续办理通过新单据、派生视图或非侵入式映射层承载；`sc.financing.loan` 历史确认单按正式模型字段承载后续维护，状态和身份字段仍保持锁定。

本轮运行态闭环验证：

- `scripts/verify/finance_interfund_handling_entry_audit.py`：通过，覆盖 P1 办理入口 action、业务方向字段、表单语义、附件/历史附件追溯和关键流转动作。
- `scripts/verify/user_confirmed_menu_surface_guard.py`：通过，用户确认菜单可见面未漂移。
- `scripts/verify/locked_fact_formal_model_continuity_guard.py`：通过，锁定历史事实非法写入被拦截；除借款历史确认单可维护正式业务字段外，连续办理走新单据、派生视图或非侵入式映射层。
- `scripts/verify/finance_business_fact_projection_audit.py`：通过，项目收付款来源明细与来源事实数量、金额一致。
- `scripts/verify/finance_business_project_summary_audit.py`：通过，项目收付款汇总与来源明细一致。
- `scripts/verify/interfund_movement_project_summary_audit.py`：通过，项目借还调拨汇总与来源明细一致。
- `scripts/verify/finance_project_capital_position_audit.py`：通过，项目资金总览 660 个项目口径与项目收付款汇总、借还调拨汇总一致。
- `scripts/verify/p1_locked_fact_mapping_candidate_guard.py`：通过，历史事实到正式关系的候选映射阈值未退化。
- `scripts/verify/p1_formal_relationship_continuity_audit.py`：通过，结算、付款申请、付款登记、收款、发票之间已存在的正式关系没有非锁定办理记录串项目/串合同硬错误。
- 付款申请绑定结算单时，以结算单 `settlement_unit_id or partner_id` 作为有效往来单位；当前 `sc_demo` 已修正 153 条结算单位锚点，并断开 4 条跨项目错误结算锚点，后续新办由模型约束和 scope smoke 持续阻断。
- 该审计同时识别出 `payment_execution_request_scope` 关系风险 1,034 条，均为历史付款登记与付款申请之间实际往来单位不同；后续应进入付款办理口径细化，不直接改写锁定历史事实。
- 付款登记到付款申请的安全合同锚点已补齐 6,319 条：仅在项目一致、往来单位一致、付款登记合同为空且付款申请合同存在时写入 `contract_id`。
- 付款登记、收款收入、费用/保证金的正式办理动作已增加付款/收款申请关系校验：新单据关联申请时必须匹配申请类型和项目，合同两边都有时必须一致；历史锁定事实继续只作为风险样本，不被回写。
- 运行态 smoke 已验证新建付款登记、费用/保证金、收款收入在项目与申请不一致时会被拦截并回滚。
- 固化脚本：`scripts/verify/p1_formal_relationship_scope_block_smoke.py`，用于后续持续验证正式办理动作不会再产生项目串线关系。
- 机械结算单办理对象已按旧可见字段 05 回填：561 条、15,630,457.05 元绑定到唯一往来单位；剩余 35 条、2,917,615.50 元为同名往来单位重复，73 条为旧字段为空且金额为 0，均保留为人工核对残差。验证脚本：`scripts/ops/validate_mechanical_settlement_partner.sh`。
- 付款登记到付款申请补锚点已按 `document_no/name == 付款申请编号`、唯一付款申请、项目/往来单位/合同/金额不冲突的规则回填：781 条历史付款登记绑定到付款申请，其中 325 条同步补齐缺失往来单位；剩余 76 条为重复申请号，15,235 条为无申请编号命中，保留为后续人工核对或更强证据规则。验证脚本：`scripts/ops/validate_payment_execution_request_anchor.sh`。
- 收款登记往来单位补锚点已按历史往来单位名称唯一匹配、且收款申请/合同往来单位不冲突的规则回填：87 条历史收款登记绑定到正式往来单位；剩余 1 条为历史名称无主数据匹配、8,330 条为历史往来单位为空，保留为后续更强证据规则。验证脚本：`scripts/ops/validate_receipt_income_partner_anchor.sh`。

## 第二轮再进入的范围

- 材料采购库存
- 分包劳务机械
- 现场进度质量安全

这三类数据量很大，但第一轮先不混入办理主链重构，避免在财务/合同/成本主干未稳定前扩大风险。
