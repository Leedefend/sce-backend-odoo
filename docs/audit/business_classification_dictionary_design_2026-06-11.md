# Business Classification Dictionary Design - 2026-06-11

## Purpose

本设计用于约束后续业务办理迭代：入口可以整合，模型可以统一，但用户可见的业务类别必须清晰、可维护、可扩展。

当前用户数据来自建筑行业，是重要样本，但不是产品边界。系统要从用户数据中提炼行业模板，同时保留客户配置能力，避免把单一客户、单一旧系统表名或单一行业习惯硬编码成长期产品结构。

## Design Goal

形成统一结构：

```text
用户历史业务名称
  -> 标准业务分类字典
  -> 行业模板默认分类
  -> 客户可维护分类配置
  -> 菜单/action/domain/context
  -> 表单分组/字段必填/按钮动作
  -> 审批策略/附件策略/下游台账策略
```

交付目标不是“菜单很多”，也不是“模型很多”，而是用户进入系统后能用熟悉的业务语言快速完成登记、申请、审批、确认、执行、完成，并且每个动作都有审计、附件和下游事实。

## Core Principles

- 用户认知优先：保留用户看得懂的业务名称，例如项目费用报销、投标保证金支付、到款确认、往来单位付款。
- 正式模型稳定：`payment.request`、`sc.expense.claim`、`sc.payment.execution`、`sc.receipt.income` 等模型承载事实和状态，不因菜单分类无限膨胀。
- 分类可维护：业务类别不是代码常量，客户应能启停、改名、排序、配置必填字段、附件要求和审批策略。
- 行业模板可复制：建筑行业模板提供默认分类、默认字段和默认策略，但客户可以覆盖。
- 样本不等于边界：当前用户数据只代表建筑行业的一个高价值样本；实现时必须提炼行业共性模板，不能把单一客户字段、菜单或历史表名固化为产品边界。
- 历史事实只映射：历史来源表和旧字段用于分类识别和追溯，不直接成为用户长期办理入口。
- 下游策略跟随分类：台账方向、成本口径、税务口径、结算口径应挂到分类上，而不是散落在按钮和菜单里。
- 动作域清晰：菜单入口可以整合，但登记、申请、审批、确认、执行、完成等业务动作必须按用户数据和用户认知切分；短期可通过 action domain/context、表单分组、状态按钮和角色门禁实现，长期沉淀到分类策略。
- 先分类后实现：新增办理事项必须先明确业务分类编码、用户可见名称、正式模型、动作域、表单切分方式和下游事实，再决定是复用模型、增加字段还是新增模型。
- 后端门禁优先：按钮显隐和菜单分组只减少误操作，正式可交付标准必须有后端动作权限、ACL、记录追溯和自动化门禁共同验证。

## Dictionary Model Proposal

已新增业务分类模型：`sc.business.category`。

核心字段：

| 字段 | 用途 |
| --- | --- |
| `code` | 稳定编码，例如 `finance.deposit.bid.pay` |
| `template_key` | 行业模板同步键，默认与稳定编码一致 |
| `template_version` | 模板同步版本 |
| `name` | 用户可见名称 |
| `target_model` | 适用正式模型 |
| `action_xmlid` | 绑定办理入口 action |
| `parent_id` | 分类层级 |
| `industry_template` | 所属行业模板 |
| `direction` | 付款、收款、转账、非现金、成本、收入、税务等 |
| `source_aliases` | 历史名称、旧系统名称、用户别名 |
| `default_values_json` | 新建默认值，例如 `claim_type`、`expense_type` |
| `domain_json` | 入口过滤条件 |
| `required_fields_json` | 办理前必填字段 |
| `visible_groups_json` | 表单分组显隐策略 |
| `attachment_policy` | 附件要求：无、建议、必填 |
| `approval_policy_id` | 默认审批策略 |
| `ledger_policy_json` | 下游台账和成本/税务沉淀策略 |
| `active` | 启停 |
| `sequence` | 排序 |

当前实现说明：

- `sc.business.category` 独立于轻量基础字典 `sc.dictionary`，避免把业务办理策略塞进基础名称字典。
- 第一阶段承载分类元数据、行业模板种子和办理入口绑定，不直接替换正式模型字段和现有 action。
- `default_values_json`、`domain_json`、`required_fields_json`、`visible_groups_json`、`ledger_policy_json` 已加 JSON 顶层类型校验。
- 业务配置管理员可在“业务配置 / 业务分类字典”维护启停、排序、名称、默认值、必填、附件策略、审批策略和下游策略。
- `action_open_bound_entry` 可从字典项打开已绑定办理入口，并把分类默认值写入 action context。
- `business_category_template_binding_sync.xml` 通过模型方法同步系统绑定字段，绕开历史种子 `noupdate=1` 导致的升级不生效问题。
- 材料结算已作为下游策略样例落地：`material.settlement` 确认后按未税金额进入成本台账、按含税金额生成付款申请；后续应把该策略从模型固定逻辑逐步提升到 `ledger_policy_json`/行业模板默认策略。
- 材料角色门禁已作为动作域样例落地：物资经办、物资审批/库管、采购经办、采购审批、财务经办、财务审批按动作边界办理；后续派生动作必须延续“分类策略 + 后端门禁 + 审计脚本”的实现方式。
- 材料调拨已作为“同模型分类切分 + 下游事实自动生成”样例落地：`material.transfer` 复用 `sc.material.outbound`，通过 `outbound_type` 和入口 action 保留用户认知，确认后自动生成调入侧 `sc.material.inbound`，用双向来源字段保证追溯。
- 材料损耗已作为“分类策略 + 可选统一审批 + 下游成本门禁”样例落地：`material.loss` 复用 `sc.material.outbound`，启用审批策略后确认动作只发起审批，审批通过前不写项目成本，审批通过后才完成损耗确认和成本沉淀。
- 材料结算分批付款、付款撤销和付款登记审批已作为分类策略样例落地：同一材料结算允许多个付款申请，剩余付款申请、累计金额占用、超付阻断、付款汇总、撤销后余额恢复和付款执行审批开关当前在模型门禁/审批策略中实现；后续应沉淀到 `material.settlement` 的付款策略或行业模板默认策略，允许客户配置是否允许分批、是否需要付款登记审批和撤销规则。
- 材料采购库存已接入正式记录级分类锚点：`project.material.plan.business_category_id`、`sc.material.purchase.request.business_category_id`、`sc.material.acceptance.business_category_id`、`sc.material.inbound.business_category_id`、`sc.material.outbound.business_category_id`、`sc.material.rfq.business_category_id` 和 `sc.material.settlement.business_category_id` 均绑定 `sc.business.category`。入口 action 以 `business_category_id.code` 为长期分类锚点，`outbound_type` 继续保留为出库、退库、调拨、损耗的业务事实。
- 合同与结算已作为 Phase 4 分类字典样例落地：`contract.income`、`contract.expense` 已接入 `construction.contract.business_category_id` 并通过收入/支出合同包装模型透出；`settlement.income`、`settlement.expense` 已接入 `sc.settlement.order.business_category_id`。合同/结算分类入口 domain 只按 `business_category_id.code` 收口；`type`、`settlement_type`、legacy 可见性字段保留为业务事实、执行态过滤或历史映射依据，但不再作为分类 fallback。
- 跨域只读权限可以服务下游校验，例如财务只读材料结算用于付款金额校验；但动作权限仍必须归属原能力域，不能因为下游付款需要读取材料结算就扩大材料结算的提交、确认、生成后续付款等办理权限。
- 收付款申请与往来款已作为资金域分类边界样例落地：`finance.payment.apply.pay`、`finance.payment.apply.receive` 已接入 `payment.request.business_category_id`，付款/收款申请入口 domain 使用 `business_category_id.code`，`type` 保留为新建默认值和业务事实字段；`finance.payment.execution.partner`、`finance.payment.execution.company` 已接入 `sc.payment.execution.business_category_id`，这里的“往来单位付款”是付款执行分类，不等同于内部往来款；`finance.loan.*`、`finance.repayment.*`、`finance.fund.transfer` 分类进入内部往来事实、项目资金口径和 `sc.treasury.ledger` 统一现金流台账，但不强制挂经营收付款申请或结算单，台账通过 `source_model/source_res_id` 追溯原始往来单据。
- 往来款分类必须按业务事实识别，不按旧菜单名硬切。旧系统没有统一“往来款”概念；系统口径必须围绕公司、项目、承包人三主体。项目借公司款、承包人借项目款、项目还公司款、承包人还项目款、跨项目/账户调拨属于项目借还调拨事实；到款确认、自筹垫付、自筹退回属于公司-承包人责任事实，项目用于归集资金状态和约束后续办理；资金日报、余额调整属于状态和台账输入。
- 公司-承包人责任已进入正式业务分类字典：`finance.responsibility.arrival_confirmation`、`finance.responsibility.self_funding_income`、`finance.responsibility.self_funding_refund` 和 `finance.responsibility.company_contractor.balance` 分别表达到款确认责任、自筹垫付责任、自筹退回责任和只读责任余额。到款确认仍保留用户认知为项目收款状态，自筹仍保留用户认知为承包人与公司的资金占用/退回；分类策略只负责把这些事实提升为办理约束，不把它们改造成普通收付款申请。
- 当多个业务分类共用同一个 action 时，`action_open_bound_entry` 必须把分类 `domain_json` 叠加到 action domain，确保入口可以整合、业务类别仍按用户数据切分。
- 借款分类已从文本推断推进到正式分类锚点：`sc.financing.loan.business_category_id` 绑定 `sc.business.category`，`finance.loan.project_borrow_company`、`finance.loan.contractor_project_borrow` 的入口 domain、默认值和下游台账策略已由业务分类承接。历史活动借款往来 645 条本地回填后全部有分类字段，`project_to_contractor_borrow` 89 条、`company_to_project_borrow` 556 条，往来事实 `classification_confidence=high` 覆盖 645 条。
- 借还款历史数据仍保留一项用户验收差异：旧入口“承包人借项目款”活动记录为 166 条，但当前旧入口内部按三主体事实分类为 `project_to_contractor_borrow` 68 条、`company_to_project_borrow` 98 条。差异说明旧入口名称、用途文本和责任主体分类不能互相替代；后续应由客户确认旧入口中“借某项目工程款付材料款/借公司款/项目周转”等记录的验收分类，并把确认后的规则继续沉淀为可维护分类字典或配套分类规则表。
- 往来资金台账同步已按业务事实口径收紧：`sc.treasury.ledger` 对 `source_model/source_res_id/project/direction/source_kind=interfund` 幂等刷新，模块升级同步会作废不再匹配当前往来事实的历史残留。这样现金流台账跟随办理事实，不把资金日报、余额调整或已失效来源误算为责任事实。
- 公司-承包人责任事实必须同时覆盖历史事实和新系统正式办理事实：到款确认来自 `sc.legacy.fund.confirmation.document`，历史自筹来自 `sc.legacy.self.funding.fact` 的 `income/refund` 正式族，新发生自筹来自 `sc.self.funding.registration` 完成单据。资金日报、余额调整和自筹可见参考族不得进入责任余额，只能作为状态、台账或用户旧入口追溯证据。
- 发票/税务分类已从纯 action/context 推进到正式分类锚点：`sc.invoice.registration.business_category_id` 和 `sc.tax.deduction.registration.business_category_id` 绑定 `sc.business.category`，新办理按入口上下文或业务字段自动落类，升级时只给空值历史/既有记录补映射。发票/税务办理入口 domain 只按 `business_category_id.code` 收口；`source_kind`、`direction`、`invoice_content`、`is_transfer_out` 继续保留为业务事实字段和历史映射依据，但不再作为 action fallback。

客户可维护字段：

- `name`
- `active`
- `sequence`
- `required_fields_json`
- `visible_groups_json`
- `attachment_policy`
- `approval_policy_id`
- `default_values_json` 中非系统保留项
- `source_aliases`
- `note`

系统保留字段：

- `code`
- `target_model`
- `direction`
- `template_key`
- `template_version`
- `action_xmlid`
- 核心状态机相关策略
- 已用于审计和下游事实的编码

## Template Sync Boundary

行业模板升级必须分清“系统绑定字段”和“客户维护字段”。

当前同步策略：

- `business_category_seed.xml` 使用 `noupdate=1` 提供初始行业模板内容，适合新库安装。
- `business_category_template_binding_sync.xml` 使用 `noupdate=0` 调用 `_sync_template_action_bindings()`，只同步 `template_key`、`template_version`、`action_xmlid`。
- 同步方法按稳定 `code` 查找分类，不依赖历史外部 ID 是否仍处于 `noupdate=1`。
- 同步过程不覆盖 `name`、`active`、`sequence`、`default_values_json`、`required_fields_json`、`visible_groups_json`、`attachment_policy`、`approval_policy_id`、`ledger_policy_json` 等客户可维护字段。

后续模板升级规则：

- 行业共性分类新增时，可以追加新的模板种子。
- 已存在分类的入口绑定、模板版本等系统字段可同步。
- 客户名称、启停、排序、附件、审批和表单分组规则不得被模板升级直接覆盖。
- 若确实需要迁移客户维护字段，必须单独提供迁移脚本、审计报告和回滚说明。
- 每次模板同步后必须跑 `DB_NAME=sc_demo scripts/ops/validate_business_category_dictionary.sh`，确认分类、入口 action、目标模型和下游策略仍一致。

## Template Boundary

行业模板只提供默认配置，不直接锁死客户。

建筑行业模板候选：

| 能力域 | 默认分类示例 |
| --- | --- |
| 财务收付 | 付款申请、收款申请、往来单位付款、到款确认 |
| 费用与保证金 | 项目费用报销、投标保证金支付/退回、合同保证金支付/退回 |
| 扣款与税务 | 扣款单、扣款实缴、扣款退回、进项发票、销项开票、税款抵扣 |
| 账户资金 | 账户间资金往来、项目借款、承包人还款 |
| 合同结算 | 收入合同结算、支出合同结算、工程进度款、尾款、质保金 |
| 材料采购 | 材料计划、采购申请、询价、验收、入库、出库、材料结算 |
| 现场履约 | 施工日志、进度登记、质量整改、安全整改、现场签证 |

客户配置可以：

- 停用不用的分类。
- 修改显示名称。
- 增加客户自定义分类。
- 调整必填字段和附件规则。
- 绑定不同审批策略。

客户配置不能：

- 改变已完成历史事实的分类编码。
- 绕过正式模型状态机。
- 删除已被审计日志、台账或审批记录引用的分类。

## Implementation Sequence

### Step 1 - Classification Inventory

从用户真实数据和当前菜单抽取分类候选。

输入：

- 历史业务字段，例如 `expense_type`、`receipt_type`、`source_family`、`source_kind`。
- 已确认菜单和 action。
- 用户高频办理事项。
- 后端办理链路审计结果。

输出：

- 分类候选表。
- 每个分类对应的正式模型。
- 每个分类对应的必填关系、办理动作、附件策略和下游事实。

### Step 2 - Action Context Normalization

短期继续使用 action/domain/context 实现清晰入口，但要统一命名和默认值。

要求：

- 每个 action 对应一个明确分类编码候选。
- action context 中保留默认业务类型。
- action domain 保证新建保存后仍留在当前入口。
- 菜单名称使用用户业务语言，不使用旧表名和技术模型名。
- 跨域 action 入口必须同时校验 action groups、模型 ACL 和后端动作权限，避免“看得见但办不了”或“能调用但不能追溯”的半成品入口。

### Step 3 - Form Group Mapping

同一模型内按分类控制表单分组。

要求：

- 当前办理事项优先显示。
- 无关字段隐藏或后置。
- 必填字段和附件要求按分类计算。
- 按钮只暴露当前状态可执行动作。
- 按钮可见性必须和后端动作门禁同向；如果业务动作跨越材料、采购、财务等能力域，优先在分类策略中表达动作责任，而不是复制多个认知相近的菜单。

### Step 4 - Dictionary Model Introduction

当分类候选稳定后，引入正式字典模型。

迁移策略：

- 先新增字典，不替换现有字段。
- 为现有 action 绑定分类编码。
- 为历史记录回填分类编码时只做映射，不改写历史可见字段。
- 新办理记录保存分类编码，同时保留用户可见分类名称。

### Step 5 - Industry Template Extraction

把稳定分类沉淀为行业模板。

要求：

- 模板可重复安装。
- 客户可覆盖显示名称和规则。
- 模板升级不能覆盖客户已维护配置。
- 模板变更必须有迁移脚本和审计报告。

## Finance Phase 1 Mapping

当前财务分类候选应作为第一批字典验证样本。

| 分类编码 | 当前实现方式 | 后续字典化动作 |
| --- | --- | --- |
| `finance.payment.apply.pay` | `payment.request.business_category_id` | 已接入正式分类入口锚点；付款申请入口按 `business_category_id.code` 展示，`type=pay` 保留为收付事实字段 |
| `finance.payment.apply.receive` | `payment.request.business_category_id` | 已接入正式分类入口锚点；收款申请入口按 `business_category_id.code` 展示，`type=receive` 保留为收付事实字段 |
| `finance.payment.execution.partner` | `sc.payment.execution.business_category_id` | 已接入正式分类入口锚点；往来单位付款入口按 `business_category_id.code` 展示，`payment_family` 和历史来源保留为付款事实 |
| `finance.payment.execution.company` | `sc.payment.execution.business_category_id` | 已接入正式分类入口锚点；公司财务支出入口按 `business_category_id.code` 展示，`payment_family` 保留为付款事实 |
| `finance.receipt.income.project` | `sc.receipt.income.business_category_id` | 已接入正式分类锚点；收入入口按 `business_category_id.code` 展示，继续配置收款申请同步和责任余额策略 |
| `finance.receipt.income.progress` | `sc.receipt.income.business_category_id` | 已接入正式分类锚点；工程进度款收入入口按 `business_category_id.code` 展示，`income_category` 保留为业务事实 |
| `finance.expense.reimbursement` | `sc.expense.claim.business_category_id` | 已接入正式分类入口锚点；继续配置费用报销必填账户和付款台账策略 |
| `finance.deposit.bid.pay` | `sc.expense.claim.business_category_id` | 已接入正式分类入口锚点；配置保证金付款方向和附件策略 |
| `finance.deposit.bid.return` | `sc.expense.claim.business_category_id` | 已接入正式分类入口锚点；配置保证金退回方向和资金台账策略 |
| `finance.deposit.contract.pay` | `sc.expense.claim.business_category_id` | 已接入正式分类入口锚点；配置合同保证金付款方向 |
| `finance.deposit.contract.return` | `sc.expense.claim.business_category_id` | 已接入正式分类入口锚点；配置合同保证金退回方向 |
| `finance.deduction.bill` | `sc.expense.claim.business_category_id` | 已接入正式分类入口锚点；保持非现金扣款事实边界 |
| `finance.fund.transfer` | `sc.fund.account.operation.business_category_id` | 已接入正式分类锚点；账户划拨/调拨按入口上下文或 `operation_type` 自动绑定，继续配置账户方向必填和资金事实策略 |
| `finance.self_funding.income` | `sc.self.funding.registration.business_category_id` | 已接入正式分类入口锚点；自筹垫付办理入口 domain 使用 `business_category_id.code`，`funding_type` 仅保留为新建默认值和自筹事实字段 |
| `finance.self_funding.refund` | `sc.self.funding.registration.business_category_id` | 已接入正式分类入口锚点；自筹退回办理入口 domain 使用 `business_category_id.code`，`funding_type` 仅保留为新建默认值和自筹事实字段 |
| `finance.loan.borrowing` | `sc.financing.loan.business_category_id` | 已接入正式分类入口锚点；借款申请入口按 `business_category_id.code` 展示，`loan_type` 保留为借款事实字段 |
| `finance.loan.project_borrow_company` | `sc.financing.loan` | 公司借款给项目；进入内部往来事实和项目资金台账，不挂经营收付款申请 |
| `finance.loan.contractor_project_borrow` | `sc.financing.loan` | 项目借款给承包人；当前由历史用途文本推断，后续沉淀为可维护分类规则 |
| `finance.repayment.project_company` | `sc.expense.claim.business_category_id` | 已接入正式分类入口锚点；项目还公司款进入内部往来清偿事实 |
| `finance.repayment.contractor_project` | `sc.expense.claim.business_category_id` | 已接入正式分类入口锚点；承包人还项目款进入内部往来清偿事实 |
| `finance.fund.daily_report` | `sc.fund.account.operation.business_category_id` | 已接入正式分类锚点；入口 domain 使用 `business_category_id.code`，`operation_type` 仅保留为新建默认值和资金日报事实字段 |
| `finance.fund.balance_adjustment` | `sc.fund.account.operation.business_category_id` | 已接入正式分类锚点；入口 domain 使用 `business_category_id.code`，`operation_type` 仅保留为新建默认值和余额校准事实字段 |
| `finance.loan.registration` | `sc.financing.loan` | 融资债务登记，独立于内部往来款闭环 |

## Contract Phase 4 Mapping

合同与结算分类作为第三批行业模板样本。当前方向是：入口可以整合到合同/结算能力域，但收入合同、支出合同、收入结算、支出结算不能被泛化入口吞掉，必须按用户业务数据和办理动作保留清晰类别。

| 分类编码 | 当前实现方式 | 后续字典化动作 |
| --- | --- | --- |
| `contract.income` | `construction.contract.business_category_id`，通过 `construction.contract.income` 包装模型展示，入口默认 `contract.income` | 配置收入合同必填字段、附件策略、收款/开票/收入结算下游策略 |
| `contract.expense` | `construction.contract.business_category_id`，通过 `construction.contract.expense` 包装模型展示，入口默认 `contract.expense` | 配置支出合同必填字段、附件策略、结算/付款/进项发票下游策略 |
| `settlement.income` | `sc.settlement.order.business_category_id`，收入结算入口 domain 使用 `business_category_id.code='settlement.income'`，`settlement_type=in` 仅作事实和历史映射依据 | 配置收入结算、收款申请、销项开票和回款余额策略 |
| `settlement.expense` | `sc.settlement.order.business_category_id`，支出结算入口 domain 使用 `business_category_id.code='settlement.expense'`，`settlement_type=out` 仅作事实和历史映射依据 | 配置支出结算、付款申请、进项发票、超付阻断和结算余额策略 |

当前门禁：

```text
DB_NAME=sc_demo scripts/ops/validate_business_category_dictionary.sh
BUSINESS_CATEGORY_DICTIONARY_AUDIT: status=PASS
category_count=54
contract categories: contract.income, contract.expense, settlement.income, settlement.expense

DB_NAME=sc_demo scripts/ops/validate_contract_business_categories.sh
CONTRACT_BUSINESS_CATEGORY_ACTION_AUDIT: status=PASS
category_count=4

DB_NAME=sc_demo scripts/ops/validate_contract_business_category_binding.sh
CONTRACT_BUSINESS_CATEGORY_BINDING_AUDIT: status=PASS
contract.expense=9294, contract.income=1810, settlement.expense=2674, settlement.income=73, mismatch=0
```

## Material Phase 3 Mapping

材料采购库存分类作为第二批高体量行业模板样本。当前用户数据中材料目录和采购库存事实体量最大，因此材料链路不能只做报表口径，必须先保证办理入口、历史追溯和新数据保存一致。

| 分类编码 | 当前实现方式 | 后续字典化动作 |
| --- | --- | --- |
| `material.plan` | `project.material.plan.business_category_id`，绑定“我的物资计划”新办理入口 | 配置计划明细必填、附件要求和后续采购/询价策略 |
| `material.purchase.request` | `sc.material.purchase.request.business_category_id` | 配置采购申请审批、供应商和材料明细必填策略 |
| `material.acceptance` | `sc.material.acceptance.business_category_id` | 配置验收动作、验收证据和入库联动策略 |
| `material.rfq` | `sc.material.rfq.business_category_id` | 配置询比价供应商、报价明细和中选策略 |
| `material.inbound` | `sc.material.inbound.business_category_id`，绑定新“入库办理”入口 | 配置库存位置、验收入库来源和库存汇总策略 |
| `material.outbound` | `sc.material.outbound.business_category_id`，`outbound_type=issue` 作为业务事实 | 配置领用出库、成本科目和项目成本沉淀策略 |
| `material.return` | `sc.material.outbound.business_category_id`，`outbound_type=return` 和“退库办理”入口切分 | 配置退库来源、供应商退货和库存扣减策略 |
| `material.transfer` | `sc.material.outbound.business_category_id`，`outbound_type=transfer` 和“材料调拨”入口切分；确认后自动生成 `sc.material.inbound` 调入事实 | 配置独立调拨接收确认、跨仓责任和仓间库存双边策略 |
| `material.loss` | `sc.material.outbound.business_category_id`，`outbound_type=loss` 和“材料损耗”入口切分；启用审批后确认前必须通过统一审批 | 配置损耗原因、审批、责任归集和项目成本沉淀策略 |
| `material.settlement` | `sc.material.settlement.business_category_id` | 配置材料结算、成本台账、分批付款、付款撤销、付款登记审批、付款申请衔接和超付阻断策略 |

边界说明：

- 历史材料计划、直接验收、历史入库等用户已确认列表继续作为来源事实和追溯入口，不被新办理 action 覆盖。
- 新材料计划办理使用 `action_project_material_plan_my`，避免把历史只读事实和当前待办计划混在同一入口。
- 新入库办理使用 `action_sc_material_inbound_handling`，避免沿用历史“入库”来源事实 action 的 `legacy_fact_model` / `legacy_fact_type` 过滤。
- 材料链路已从 action/context 过渡到记录级 `business_category_id` 分类锚点；当前已补材料动作审计、记录绑定审计、办理证据、角色权限、下游成本/付款追溯、结算分批付款、付款撤销、付款登记审批、退库、调拨双边库存事实和损耗审批门禁，下一步继续把采购分支、退库来源、独立调拨接收、损耗责任归集等派生规则沉淀为分类策略。

本轮记录级分类锚点校验：

```text
DB_NAME=sc_demo scripts/ops/validate_material_business_categories.sh
MATERIAL_BUSINESS_CATEGORY_ACTION_AUDIT: status=PASS, category_count=10

DB_NAME=sc_demo scripts/ops/validate_material_business_category_binding.sh
MATERIAL_BUSINESS_CATEGORY_BINDING_AUDIT: status=PASS
material.inbound=13639, material.plan=687, material.rfq=126, material.outbound=3, mismatch=0
```

## Acceptance Rules

分类字典化不是完成文档即可，需要满足以下验收：

- 每个高频用户入口都有分类编码。
- 每个分类编码能说明正式模型、方向、必填关系、审批策略和下游事实。
- 每个 action 保存后的记录仍能被当前入口看到。
- 每个分类至少有一个后端办理闭环验证。
- P0 分类至少有浏览器级办理截图或 JSON 产物。
- 客户可维护项和系统保留项边界清楚。
- 行业模板默认项不会覆盖客户配置。

当前过渡门禁：

```text
DB_NAME=sc_demo scripts/ops/validate_business_category_dictionary.sh
scripts/ops/validate_finance_business_categories.sh
DB_NAME=sc_demo scripts/ops/validate_finance_business_category_runtime.sh
scripts/ops/validate_invoice_tax_business_categories.sh
DB_NAME=sc_demo scripts/ops/validate_invoice_tax_business_category_runtime.sh
DB_NAME=sc_demo scripts/ops/validate_invoice_tax_handling_evidence.sh
DB_NAME=sc_demo scripts/ops/validate_invoice_tax_role_permissions.sh
DB_NAME=sc_demo scripts/ops/validate_invoice_tax_downstream_traceability.sh
DB_NAME=sc_demo scripts/ops/validate_material_business_categories.sh
DB_NAME=sc_demo scripts/ops/validate_material_business_category_binding.sh
DB_NAME=sc_demo scripts/ops/validate_material_business_category_runtime.sh
DB_NAME=sc_demo scripts/ops/validate_material_handling_evidence.sh
DB_NAME=sc_demo scripts/ops/validate_material_downstream_traceability.sh
DB_NAME=sc_demo scripts/ops/validate_material_cost_trigger_policy.sh
DB_NAME=sc_demo scripts/ops/validate_material_outbound_derivative_strategy.sh
DB_NAME=sc_demo scripts/ops/validate_material_loss_approval_policy.sh
```

这些门禁在正式字典模型落地前检查分类候选：

- 静态门禁检查 XML 中的 action/domain/context/menu 绑定。
- 运行时门禁读取数据库中最终生效的 action，创建临时业务记录，再验证当前 action domain 可以搜到该记录。
- 重点保证“分类清晰”和“新建保存后不丢入口”。
- 下游追溯门禁检查“办理完成后进入正确事实层”，避免分类只停留在菜单可见性。
- 策略门禁检查分类下游成本、付款和审批开关，避免客户启用策略后绕过办理闭环。

## Current Decision

Phase 1 财务办理、Phase 2 发票税务、Phase 3 材料采购库存、Phase 4 合同结算和 Phase 5 现场质量安全已进入分类字典门禁。分类字典模型不立即替换现有 action/context，但所有新增业务类别必须先形成字典项或分类候选，再决定动作域切分、表单分组切分和行业模板沉淀方式。

接下来的实现顺序：

1. 固定财务分类候选和 action/context 对应关系。
2. 增加静态审计，检查高频 action 是否具备稳定分类编码候选、默认值和 domain。
3. 把费用/保证金/扣款类办理从菜单碎片推进到分类矩阵。
4. 浏览器验收按分类抽样执行，而不是只按模型抽样。
5. 让 action、表单和审批逐步读取业务分类字典中的默认值、必填字段、附件策略和下游策略。

## Site Phase 5 Mapping

现场履约分类作为第四批行业模板样本。当前先覆盖质量/安全整改闭环和施工日志证据入口，避免现场数据停留在孤立列表或报表字段。

| 分类编码 | 当前实现方式 | 后续字典化动作 |
| --- | --- | --- |
| `site.construction.diary` | `sc.construction.diary`，绑定施工日志入口 | 配置日志内容必填、附件策略、项目履约和结算依据策略 |
| `site.quality.issue` | `sc.quality.issue`，质量问题登记入口 | 配置问题登记、责任单位、整改期限、照片证据和逾期策略 |
| `site.quality.rectification` | `sc.quality.rectification`，质量整改执行入口 | 配置整改结果、附件/照片必填和问题状态同步策略 |
| `site.quality.recheck` | `sc.quality.recheck`，质量复验入口 | 配置复验通过闭环、复验失败退回整改和审计策略 |
| `site.safety.issue` | `sc.safety.issue`，安全问题登记入口 | 配置安全隐患登记、危险源/巡检来源和逾期责任策略 |
| `site.safety.rectification` | `sc.safety.rectification`，安全整改执行入口 | 配置整改结果、附件/照片必填和问题状态同步策略 |
| `site.safety.recheck` | `sc.safety.recheck`，安全复验入口 | 配置复验通过闭环、复验失败退回整改和审计策略 |

当前门禁：

```text
DB_NAME=sc_demo scripts/ops/validate_business_category_dictionary.sh
BUSINESS_CATEGORY_DICTIONARY_AUDIT: status=PASS
category_count=54
site categories: site.construction.diary, site.quality.issue, site.quality.rectification, site.quality.recheck, site.safety.issue, site.safety.rectification, site.safety.recheck

DB_NAME=sc_demo scripts/ops/validate_site_quality_safety_closure.sh
SITE_QUALITY_SAFETY_CLOSURE_AUDIT: status=PASS
evidence: quality issue=31, rectification=31, failed_recheck=32, passed_recheck=33; safety issue=31, rectification=31, failed_recheck=32, passed_recheck=33
```

## Iteration Evidence - 2026-06-11

已落地第一阶段可维护业务分类字典：

```text
DB_NAME=sc_demo scripts/ops/validate_business_category_dictionary.sh
BUSINESS_CATEGORY_DICTIONARY_AUDIT: status=PASS
category_count=48
```

覆盖分类：

| 分类编码 | 用户可见事项 | 正式模型 | 方向 |
| --- | --- | --- | --- |
| `site.construction.diary` | 施工日志 | `sc.construction.diary` | 追溯参考 |
| `site.quality.issue` | 质量问题 | `sc.quality.issue` | 追溯参考 |
| `site.quality.rectification` | 质量整改 | `sc.quality.rectification` | 追溯参考 |
| `site.quality.recheck` | 质量复验 | `sc.quality.recheck` | 追溯参考 |
| `site.safety.issue` | 安全问题 | `sc.safety.issue` | 追溯参考 |
| `site.safety.rectification` | 安全整改 | `sc.safety.rectification` | 追溯参考 |
| `site.safety.recheck` | 安全复验 | `sc.safety.recheck` | 追溯参考 |
| `contract.income` | 收入合同 | `construction.contract.income` | 收入 |
| `contract.expense` | 支出合同 | `construction.contract.expense` | 成本 |
| `settlement.income` | 收入合同结算 | `sc.settlement.order` | 收入 |
| `settlement.expense` | 支出合同结算 | `sc.settlement.order` | 成本 |
| `finance.payment.apply.pay` | 付款申请 | `payment.request` | 付款 |
| `finance.payment.apply.receive` | 收款申请 | `payment.request` | 收款 |
| `finance.payment.execution.partner` | 往来单位付款 | `sc.payment.execution` | 付款 |
| `finance.payment.execution.company` | 公司财务支出 | `sc.payment.execution` | 付款 |
| `finance.receipt.income.project` | 收入/到款确认 | `sc.receipt.income` | 收款 |
| `finance.receipt.income.progress` | 工程进度款收入登记 | `sc.receipt.income` | 收款 |
| `finance.expense.reimbursement` | 报销申请 | `sc.expense.claim` | 付款 |
| `finance.expense.project` | 项目费用报销单 | `sc.expense.claim` | 付款 |
| `finance.deposit.bid.pay` | 投标保证金缴纳 | `sc.expense.claim` | 付款 |
| `finance.deposit.bid.return` | 投标保证金退回 | `sc.expense.claim` | 收款/退回 |
| `finance.deposit.contract.pay` | 合同保证金登记 | `sc.expense.claim` | 付款 |
| `finance.deposit.contract.return` | 合同保证金退回 | `sc.expense.claim` | 收款/退回 |
| `finance.deduction.bill` | 扣款单 | `sc.expense.claim` | 复合/扣款 |
| `finance.deduction.paid` | 扣款实缴登记 | `sc.expense.claim` | 付款 |
| `finance.deduction.refund` | 扣款实缴退回 | `sc.expense.claim` | 收款/退回 |
| `finance.fund.transfer` | 账户间资金往来 | `sc.fund.account.operation` | 转账，跨项目流入/流出进入现金流台账 |
| `finance.fund.daily_report` | 资金日报表 | `sc.fund.account.operation` | 日报型现金流输入，不进入往来款事实 |
| `finance.fund.balance_adjustment` | 余额调整 | `sc.fund.account.operation` | 账户状态校准，不进入现金流和往来款事实 |
| `finance.self_funding.income` | 自筹垫付办理 | `sc.self.funding.registration` | 自筹流入责任，进入责任余额和现金流台账 |
| `finance.self_funding.refund` | 自筹退回办理 | `sc.self.funding.registration` | 自筹退回责任，进入责任余额和现金流台账 |
| `finance.loan.borrowing` | 借款申请 | `sc.financing.loan` | 借入，进入现金流台账，不关联收付款申请 |
| `finance.loan.contractor_project_borrow` | 承包人借项目款 | `sc.financing.loan` | 借出，当前按“借...项目...款”顺序语义兼容历史数据，进入现金流台账 |
| `finance.loan.project_borrow_company` | 项目借公司款登记 | `sc.financing.loan` | 借入，排除“借...项目...款”借出语义，进入现金流台账 |
| `finance.repayment.registration` | 还款登记 | `sc.expense.claim` | 往来付款，进入现金流台账，不关联收付款申请 |
| `finance.repayment.contractor_project` | 承包人还项目款 | `sc.expense.claim` | 往来收款，进入现金流台账，不关联收付款申请 |
| `finance.repayment.project_company` | 项目还公司款登记 | `sc.expense.claim` | 往来付款，进入现金流台账，不关联收付款申请 |
| `invoice.output.application` | 销项开票申请 | `sc.invoice.registration` | 收入/销项 |
| `invoice.output.registration` | 销项开票登记 | `sc.invoice.registration` | 收入/销项 |
| `invoice.input.report` | 进项税额上报 | `sc.invoice.registration` | 成本/进项 |
| `invoice.prepaid_tax` | 预缴税款 | `sc.invoice.registration` | 非现金税务 |
| `tax.deduction.registration` | 抵扣登记 | `sc.tax.deduction.registration` | 非现金税务 |
| `material.plan` | 材料计划 | `project.material.plan` | 成本 |
| `material.purchase.request` | 采购申请 | `sc.material.purchase.request` | 成本 |
| `material.acceptance` | 材料进场验收 | `sc.material.acceptance` | 成本 |
| `material.rfq` | 询比价 | `sc.material.rfq` | 成本 |
| `material.inbound` | 入库单 | `sc.material.inbound` | 成本 |
| `material.outbound` | 出库单 | `sc.material.outbound` | 成本 |
| `material.return` | 退库办理 | `sc.material.outbound` | 成本转回 |
| `material.transfer` | 材料调拨 | `sc.material.outbound` | 转移 |
| `material.loss` | 材料损耗 | `sc.material.outbound` | 成本 |
| `material.settlement` | 材料结算 | `sc.material.settlement` | 成本 |

本轮结论：

- 业务分类已经从文档原则推进到可维护模型和行业模板种子。
- 当前不改变用户办理入口，避免一次性替换 action/context 引入认知变化。
- 下一步应让 action、表单分组和审批策略逐步绑定 `sc.business.category`，并设计模板升级不覆盖客户维护项的迁移策略。

已完成第一版财务分类 action 映射审计：

```text
scripts/ops/validate_finance_business_categories.sh
FINANCE_BUSINESS_CATEGORY_ACTION_AUDIT: status=PASS
category_count=21
```

```text
DB_NAME=sc_demo scripts/ops/validate_finance_business_category_runtime.sh
FINANCE_BUSINESS_CATEGORY_RUNTIME_AUDIT: status=PASS
category_count=21
```

本轮结论：

- 财务 Phase 1 的 21 个高频分类候选已具备稳定编码、用户可见事项、正式模型、action、menu、context 默认值和 domain 覆盖关系。
- 运行时数据库最终生效 action 已验证：按分类默认值新建的临时记录可被当前入口 domain 搜到。
- 当前已新增正式业务分类字典模型；action/context 仍作为过渡入口呈现层。
- 下一步应把业务分类字典门禁纳入常规验证，再按同样方法扩展到合同结算和现场履约分类。

## Iteration Evidence - 2026-06-11 Invoice And Tax Categories

已把同一分类字典化方法扩展到发票/税务高频入口：

```text
scripts/ops/validate_invoice_tax_business_categories.sh
INVOICE_TAX_BUSINESS_CATEGORY_ACTION_AUDIT: status=PASS
category_count=5
```

```text
DB_NAME=sc_demo scripts/ops/validate_invoice_tax_business_category_runtime.sh
INVOICE_TAX_BUSINESS_CATEGORY_RUNTIME_AUDIT: status=PASS
category_count=5
```

覆盖分类候选：

| 分类编码 | 用户可见事项 | 当前模型 | 当前实现方式 | 后续字典化动作 |
| --- | --- | --- | --- | --- |
| `invoice.output.application` | 销项开票申请 | `sc.invoice.registration.business_category_id` | 入口 domain 使用 `business_category_id.code='invoice.output.application'`；`source_kind/direction/invoice_content` 仅保留为业务事实字段和历史映射依据 | 绑定销项申请审批、附件和合同/收款关系策略 |
| `invoice.output.registration` | 销项开票登记 | `sc.invoice.registration.business_category_id` | 用户确认列表和正式表单均写入 `default_business_category_code`，入口 domain 使用 `business_category_id.code='invoice.output.registration'` | 绑定开票完成、税务口径和收入合同关系策略 |
| `invoice.prepaid_tax` | 预缴税款 | `sc.invoice.registration.business_category_id` | 入口 domain 使用 `business_category_id.code='invoice.prepaid_tax'`；`prepaid_tax/prepaid` 仅保留为业务事实字段和历史映射依据 | 绑定完税凭证和项目税务事实策略 |
| `invoice.input.report` | 进项税额上报 | `sc.invoice.registration.business_category_id` | 用户确认列表和正式表单均写入 `default_business_category_code`，入口 domain 使用 `business_category_id.code='invoice.input.report'` | 绑定进项发票、成本和抵扣来源关系策略 |
| `tax.deduction.registration` | 抵扣登记 | `sc.tax.deduction.registration.business_category_id` | 入口 domain 使用 `business_category_id.code='tax.deduction.registration'`；`is_transfer_out` 仅保留为业务事实字段和历史映射依据 | 后续继续区分抵扣、转出、扣款抵扣的更细分类 |

本轮结论：

- 发票/税务入口不再只作为历史清单或报表来源，已具备从入口新建并回到同一入口的办理基础。
- 后置用户确认列表仍保留为首屏，避免改变用户对历史字段和业务名称的认知。
- 当前入口已从 action 文本条件推进到 `business_category_id.code` 稳定分类锚点；`source_kind`、`direction`、`invoice_content`、`is_transfer_out` 继续作为业务事实字段和历史兼容条件，不再作为入口长期分类锚点。

## Iteration Evidence - 2026-06-11 Invoice And Tax Handling

已把发票/税务从“分类入口可用”推进到“办理动作可审计”：

```text
DB_NAME=sc_demo scripts/ops/validate_invoice_tax_handling_evidence.sh
INVOICE_TAX_HANDLING_EVIDENCE_AUDIT: status=PASS
covered: invoice_registration, tax_deduction_registration
evidence: attachment, state closure, business anchor blocking, audit event
```

本轮新增动作审计：

| 模型 | 动作 | 审计事件 |
| --- | --- | --- |
| `sc.invoice.registration` | `action_confirm` | `invoice_submitted` 或 `invoice_confirmed` |
| `sc.invoice.registration` | `action_on_tier_approved` | `invoice_confirmed` |
| `sc.invoice.registration` | `action_on_tier_rejected` | `invoice_rejected` |
| `sc.invoice.registration` | `action_register` | `invoice_registered` |
| `sc.invoice.registration` | `action_cancel` | `invoice_cancelled` |
| `sc.tax.deduction.registration` | `action_confirm` | `tax_deduction_confirmed` |
| `sc.tax.deduction.registration` | `action_deduct` | `tax_deduction_deducted` |
| `sc.tax.deduction.registration` | `action_cancel` | `tax_deduction_cancelled` |

本轮结论：

- 发票登记已覆盖发票号/完税凭证、金额、合同项目/往来单位一致性等业务锚点阻断。
- 抵扣登记已覆盖发票号、认证日期、抵扣税额大于 0、抵扣税额不超过发票税额等业务锚点阻断。
- 动作审计只记录正式办理事实和状态变化，不改变用户可见业务名称和历史来源字段。
- 下一步仍需要把发票/抵扣结果进一步沉淀到项目经营、成本和税务口径，并把分类锚点从 action/context 迁移到正式业务分类字典。

## Iteration Evidence - 2026-06-11 Invoice And Tax Role Permissions

已把发票/税务终态动作纳入角色权限门禁：

```text
DB_NAME=sc_demo scripts/ops/validate_invoice_tax_role_permissions.sh
INVOICE_TAX_ROLE_PERMISSION_AUDIT: status=PASS
covered: invoice_registration, tax_deduction_registration
roles: finance_read, business_initiator, finance_user, finance_manager
```

权限边界：

| 角色 | 发票/税务权限结论 |
| --- | --- |
| 财务只读 | 可以查看，不能创建 |
| 业务经办 | 可以创建并发起/确认草稿，不可执行终态登记/抵扣 |
| 财务经办 | 可以办理草稿和编辑，不可执行终态登记/抵扣 |
| 财务经理 | 可以执行发票登记完成和税务抵扣完成 |

本轮结论：

- 发票登记 `action_register` 已显式要求财务确认权限。
- 抵扣登记 `action_deduct` 已显式要求财务确认权限。
- 权限门禁与办理证据门禁共同验证，避免只靠菜单可见性或 access.csv 静态配置判断可交付性。

## Iteration Evidence - 2026-06-11 Invoice And Tax Downstream Traceability

已把发票/税务分类从“入口可见、动作可审计”推进到“办理结果可追溯”：

```text
DB_NAME=sc_demo scripts/ops/validate_invoice_tax_downstream_traceability.sh
INVOICE_TAX_DOWNSTREAM_TRACEABILITY_AUDIT: status=PASS
covered: output invoice registration, input invoice report, tax deduction
```

已验证沉淀路径：

| 分类编码 | 办理完成状态 | 下游事实 | 追溯动作 |
| --- | --- | --- | --- |
| `invoice.output.registration` | `registered` | `sc.invoice.category.summary` | 汇总项可打开回 `sc.invoice.registration` 来源发票 |
| `invoice.input.report` | `registered` | `sc.invoice.category.summary` | 汇总项可打开回 `sc.invoice.registration` 来源发票 |
| `tax.deduction.registration` | `deducted` | `sc.finance.business.fact` / `sc.finance.business.project.summary` / `sc.finance.project.capital.position` | 税务事实可打开来源抵扣单，也可回到同类正式办理入口 |

本轮边界：

- 发票登记本身是发票事实和税务/成本依据，不直接改变项目资金余额。
- 抵扣登记以 `noncash_tax` 进入项目经营税务事实，余额影响为 0。
- `sc.invoice_cost_progress_summary` 等偏报表口径仍后置到报表阶段；当前主线只要求办理完成后进入可追溯事实层。

后续字典化要求：

- 发票/税务分类已从 `source_kind`、`direction`、`invoice_content`、`is_transfer_out` 等过渡锚点迁移到 `business_category_id.code` 入口锚点。
- 字典项应绑定下游策略：发票分类汇总、抵扣税务事实、成本归集候选、合同/结算关系要求。
- 建筑行业模板可以预置进项、销项、预缴、抵扣、转出等分类，但客户应能维护显示名称、启停、排序、附件要求和审批策略。
