# Business Handling Delivery Master Plan - 2026-06-11

## Direction

当前交付重心调整为“具体业务办理闭环”，报表和经营分析后置。后续迭代优先解决用户每天要办的登记、申请、审批、确认、执行、归档和追溯问题。

本计划承接以下已确认基础：

- 用户真实业务画像：`docs/audit/user_business_data_portrait_productization_plan_2026-06-10.md`
- SCBS55 表单办理差异计划：`docs/scbs55_form_business_parity_plan.md`
- 正式业务闭环审计：`docs/audit/business_flow_closure_audit_2026-06-09.md`
- 结算办理可用性审计：`docs/audit/user_confirmed_settlement_usability_2026-06-10.md`
- 业务分类字典设计：`docs/audit/business_classification_dictionary_design_2026-06-11.md`
- 公司与币种基线：本地开发库和开发服务器统一使用 `四川保盛建设集团有限公司`、`CNY`

## Current Business Data Reading

`sc_demo` 已识别约 411.66 万条用户业务画像记录，覆盖 11 个能力域。数据事实说明系统正式交付不能只以菜单和报表为准，必须以业务能否继续办理为准。

高权重事实：

| 事实 | 规模 | 对办理设计的含义 |
| --- | ---: | --- |
| 材料目录 | 2,288,638 | 材料链路要先保护目录、询价、采购、验收、入出库和结算口径 |
| 附件 | 607,143 | 附件是办理证据层，不能作为可选增强 |
| 历史文件索引 | 174,496 | 历史附件追溯必须纳入验收 |
| 历史待办/流程审计 | 各 79,702 | 审批轨迹和操作日志是正式交付硬门槛 |
| 项目任务/现场证据 | 约 74,000 | 现场进度、质量、安全要进入项目履约和结算依据 |
| 成本台账 | 73,068 | 付款、材料、发票、结算最终要沉淀到成本口径 |
| 发票登记 | 71,796 | 税务发票必须和项目、合同、往来单位打通 |
| 费用单据 | 65,507 | 报销、借还款、保证金、扣款类事实需要清晰办理入口 |

产品结构固定为：

- 业务办理入口：新增、保存、提交、审批、确认、执行、取消。
- 来源事实明细：历史迁移数据、旧系统来源、锁定事实、附件和流程追溯。
- 结果汇总视图：项目、合同、往来单位、账户、成本、税务等经营分析。

## Delivery Definition

一个业务入口达到正式交付，必须同时满足：

- 历史数据：至少一条用户迁移数据可打开，字段、明细、附件、流程轨迹不报错。
- 新办理：至少一条当前业务数据可新建、保存、提交或确认。
- 审批：需要审批的单据能进入待审、通过、驳回，并写入审计日志。
- 状态：草稿、提交、审批中、已批准、已完成、已取消等状态迁移只能通过正式动作。
- 明细：one2many/many2many 明细行可新增、编辑、删除或按历史锁定策略只读展示。
- 附件：上传、下载、历史附件索引和业务单据关联可用。
- 关系：项目、合同、往来单位、账户、成本科目、发票、结算关系不缺失、不错位。
- 结果：完成动作能生成或更新台账、成本、资金、发票、结算等下游事实。
- 权限：经办、审批、财务、管理层按角色看到正确入口和按钮。
- 证据：每轮有脚本审计结果，关键入口补浏览器验收截图或 JSON 产物。

## Priority Rules

1. 办理优先于报表。除非报表修复直接服务办理链路定位问题，否则不作为当前主线。
2. 正式模型优先于旧表来源。用户办理入口使用业务语言，不暴露历史表名和技术模型名。
3. 历史事实只追溯、不覆盖。用户已验收菜单、列表、锁定事实和附件不因新功能开发被改写。
4. 每次迭代只收敛一条链路。结束时必须有可执行动作、审计脚本或浏览器证据。
5. 数据关系优先补非侵入式映射和新办理必填规则，避免直接批量改写锁定事实。
6. 所有申请、审批、确认、支付、收款、结算、发票、成本沉淀动作必须可审计。
7. 菜单入口可以整合，但业务类别必须保持清晰；同一模型下的办理事项可通过 action domain、默认上下文、表单分组、状态按钮和字段显隐切分，不能让用户在一个泛化入口里重新猜业务含义。
8. 业务分类必须优先来自用户真实数据画像和历史业务名称，再沉淀为可维护字典；不能把某个旧表字段、某个客户命名或某个行业特例硬编码成长期产品结构。
9. 用户认知优先。新系统可以统一模型和入口，但显示名称、办理动作、必填关系、附件证据和审批节点要延续用户已理解的“登记、申请、审批、确认、执行、完成”语言。
10. 行业模板优先于项目定制。当前用户数据是建筑行业样本，不等于全部行业；每次实现都要判断哪些是行业共性能力、哪些是客户特例配置，能字典化配置的不要写死到模型逻辑。
11. 业务分类字典化是默认方向。费用类型、保证金类型、收付款类别、借还款类别、扣款类别、发票/税务类别、账户资金方向等分类应逐步沉淀到可维护字典，支持启停、排序、默认字段、必填规则、菜单/action 绑定和行业模板预置。
12. 办理切分方式必须服务用户认知。入口可以合并到工作台或能力域，但具体业务类别要通过动作域、默认上下文、表单分组、字段必填、按钮显隐和审计编码清楚表达，不能让用户面对一个“万能表单”自行判断该填哪些字段。
13. 用户数据是分类来源，不是产品硬编码。真实数据中出现的行业特例先进入分类候选和模板候选，再判断是否沉淀为行业默认、客户配置或一次性迁移映射。
14. 每轮任务都要回答“分类是否应字典化”。如果当前仍用 selection、文本字段、action domain 或 context 实现分类，必须记录其后续进入业务分类字典和行业模板的路径。
15. 用户业务数据体量和日常办理价值优先。当前主线必须优先处理已有大量用户业务数据、能直接影响交付使用的能力域；技术上已有模型但用户数据体量较低或交付价值较后的域，不应抢占付款费用、税务发票、账户资金、收入收款、合同结算等高权重闭环。
16. 收付款申请与往来款必须分开，但现金流口径不能断裂。`payment.request` 服务经营付款/收款、合同结算、材料结算等收付执行链路；项目借还、承包人借还、项目间/账户间调拨等往来款服务内部资金往来事实和项目资金口径，不应为了复用付款台账而强制挂结算单或收付款申请。往来款一旦形成真实资金流入/流出，必须通过来源模型和来源记录进入 `sc.treasury.ledger` 统一现金流台账，且 `payment_request_id` 保持为空。
17. 往来款边界必须从用户数据事实识别，不能从旧菜单名推断。旧系统没有统一往来款概念；旧入口只保留用户认知和追溯证据。资金责任必须围绕公司、项目、承包人三主体识别：项目借还调拨是一类，公司-承包人到款、拨付、扣款、自筹垫付和退回也是一类。
18. 项目资金状态用于约束业务办理。到款确认反映项目收款状态，本质约束公司与承包人的拨付、扣款、退回和后续办理；自筹反映承包人与公司的资金占用和归还。资金日报不作为往来责任事实，但应承接用户日报、账户收支明细和余额快照，用于约束和核对办理动作。

## Data-Driven Delivery Priority

后续推进顺序以 `docs/audit/user_business_data_portrait_productization_plan_2026-06-10.md` 的用户业务画像为准，结合“已有正式模型 + 新发生业务可办理 + 下游事实可追溯”的交付价值排序。

当前优先级：

| 优先级 | 能力域 | 用户画像记录数 | 当前交付判断 | 下一步 |
| --- | --- | ---: | --- | --- |
| P0 | 审批附件与治理 | 941,104 | 所有业务办理的证据底座，贯穿每个域 | 持续作为每条闭环门禁的必检项，不单独扩展报表 |
| P0 | 付款与费用 | 202,108 | 已有 `payment.request`、`sc.payment.execution`、`sc.expense.claim` 主链路，直接影响日常付款、报销、扣款、保证金 | 继续补分类策略、账户/合同/往来单位必填、付款撤销和浏览器抽样证据 |
| P0 | 税务与发票 | 147,753 | 已有发票登记、抵扣登记和下游税务事实门禁，和合同/收付款强相关 | 继续补合同、结算、收付款余额一致性和红冲/抵扣边界 |
| P0 | 账户与往来资金 | 84,410 | 已补账户调拨、项目借公司款、承包人借项目款、项目还公司款、承包人还项目款最小办理闭环，并接入资金事实、项目资金口径和统一现金流台账；往来款与收付款申请已拆分；已形成用户数据全覆盖边界审计和历史往来现金流台账回填只读审计 | 继续补借还款分类字典策略、资金日报台账承接、账户余额关系和正式历史回填迁移脚本 |
| P0 | 收入与收款 | 60,514 | 已有收入合同 -> 收款申请 -> 收款登记 -> 资金台账 -> 开票证据，并补齐收款登记自身动作审计 | 继续补工程进度款、自筹收入/退回、收款发票核销和合同收款/开票余额硬阻断 |
| P0 | 合同与结算 | 48,755 | 已有支出合同结算付款和收入合同收款开票闭环 | 继续补合同余额、结算余额、开票余额、回款余额硬阻断 |
| P1 | 预算成本管控 | 88,636 | 成本台账体量高，是付款、材料、发票、分包劳务机械下游口径 | 先服务高体量办理链路，不先做成本报表扩展 |
| P1 | 现场进度质量安全 | 162,639 | 数据量高，已补质量/安全最小闭环；但当前正式交付仍应先保障资金、发票、合同等高频办理 | 保留已通过门禁，后续再扩施工日志、进度、任务证据到结算依据 |
| P1 | 分包劳务机械 | 27,269 | 用户数据集中在使用记录，且和结算、成本、付款相关 | 在账户资金/收入收款后，推进“使用记录 -> 结算 -> 成本 -> 付款”闭环 |
| P2 | 项目与主数据 | 18,278 | 作为业务锚点持续补关系质量 | 随各办理链路补必填和非侵入式映射 |

材料与采购库存虽然画像记录数最高，当前已达到阶段性可交付深度，后续除正式交付阻断外转入行业模板沉淀和 backlog，不继续抢占当前主线。

## Business Classification Architecture

后续办理设计统一按“正式模型 + 业务分类字典 + 入口呈现策略”推进。

核心原则：

- 正式模型负责稳定的数据关系和状态机，例如 `payment.request`、`sc.expense.claim`、`sc.payment.execution`、`sc.receipt.income`。
- 业务分类字典负责表达用户看到的事项，例如项目费用报销、投标保证金支付、保证金退回、到款确认、往来单位付款、项目借款、扣款实缴。
- 菜单/action 负责把用户带到正确事项，可通过 domain、context、默认值、搜索过滤和表单标题减少认知成本。
- 表单负责在一个模型内按业务分类显示必要分组，隐藏无关字段，强调当前办理动作和必填关系。
- 审批和下游沉淀动作必须绑定业务分类，保证不同类别可以有不同必填字段、审批策略、台账方向和附件要求。

目标形态：

| 层级 | 责任 | 可配置项 | 不应承担 |
| --- | --- | --- | --- |
| 行业模板 | 预置行业共性分类和办理链路 | 分类树、默认菜单、默认审批策略、默认必填规则 | 固化客户私有命名 |
| 客户配置 | 适配用户历史业务认知 | 分类启停、排序、显示名称、默认值、字段必填、附件要求 | 改写核心状态机 |
| 正式模型 | 保存业务事实和状态 | 稳定字段、状态迁移、审计、下游生成 | 承载无限菜单分支 |
| 菜单/action | 提供清晰入口 | domain、context、默认分类、默认搜索 | 替代业务字典 |
| 表单分组 | 降低办理噪音 | 分类显隐、字段分组、按钮可见 | 改变历史事实 |

落地顺序：

1. 先从用户真实数据中抽取高频业务类别和历史名称，形成分类清单。
2. 对每个正式模型建立“业务类别 -> 必填关系 -> 办理动作 -> 下游事实”的矩阵。
3. 当前阶段可先用 action domain/context 和表单分组实现清晰办理。
4. 当某类分类开始跨菜单、跨模型、跨客户复用时，提升为可维护字典。
5. 字典稳定后再沉淀行业模板，模板只提供默认值，客户可维护覆盖。

分类字典至少需要支持：

- `code`：稳定编码，用于动作、审计和下游沉淀。
- `name`：用户可见名称。
- `model`：适用正式模型。
- `parent_id`：分类层级。
- `direction`：收/付/转账/非现金/收入/成本等业务方向。
- `default_values`：新建默认值。
- `domain`：入口过滤条件。
- `required_fields`：办理前必填字段。
- `attachment_policy`：附件要求。
- `approval_policy_id`：审批策略。
- `ledger_policy`：下游台账、成本、税务、结算沉淀规则。
- `active`、`sequence`：启停和排序。

当前 Phase 1 的临时实现可以继续使用 action/domain/context，但新代码和文档必须明确其最终归属：这些分类不是菜单碎片，而是将来要进入业务分类字典和行业模板的候选项。

当前已落地第一阶段业务分类字典：

- 新增 `sc.business.category`，用于维护业务分类编码、用户可见名称、能力域、正式模型、业务方向、默认值 JSON、入口过滤 JSON、必填字段 JSON、附件策略、审批策略和下游策略 JSON。
- 新增建筑行业模板种子，覆盖 7 个现场履约分类、4 个合同/结算分类、22 个财务/资金类分类、5 个发票/税务分类和 10 个材料采购库存分类，共 48 个分类候选。
- 新增模板同步边界：行业模板种子提供初始内容，升级同步只写 `template_key`、`template_version`、`action_xmlid` 等系统绑定字段，不覆盖客户维护的名称、启停、排序、默认值、必填、表单分组、附件和审批策略。
- 暂不替换现有 action/domain/context；当前字典先绑定现有办理入口，作为产品化分类元数据和后续迁移锚点，避免改变用户现有办理认知。
- 新增门禁 `DB_NAME=sc_demo scripts/ops/validate_business_category_dictionary.sh`，检查分类种子、模板版本、绑定 action、目标模型、JSON 策略和打开目标模型动作。
- 当前已验证 48 个分类的绑定入口能回到对应正式模型，其中现场履约已覆盖施工日志、质量问题/整改/复验、安全问题/整改/复验，合同域已覆盖收入合同、支出合同、收入合同结算、支出合同结算；后续新增业务类别必须先进入分类候选或字典项，再决定是 action 域切分、表单分组切分，还是沉淀为行业模板。

## Browser Acceptance Runtime Rule

浏览器级验收是交付证据，但不应在每次验证时隐式下载浏览器运行时。

后续规则：

- 验收脚本只负责运行，不负责安装 Playwright 浏览器。
- 本地、CI、开发服务器必须预置固定版本的 Chromium/Chrome 或配置 `PLAYWRIGHT_BROWSERS_PATH`。
- 如果浏览器运行时缺失，脚本应快速失败并提示环境问题，不把下载动作混入业务验收。
- 浏览器验收产物只记录业务结果：入口、页面、按钮、动作、状态、台账、截图、错误上下文。
- 环境准备单独沉淀到 ops 文档或镜像，不作为业务迭代的一部分。

## Phased Plan

### Phase 0 - Baseline And Guardrails

目标：保护用户已确认的可见面和本地/开发服务器基础一致性。

范围：

- 公司名称、币种、默认公司基线统一。
- 用户确认菜单、列表字段、历史事实连续性继续作为硬门禁。
- 用户业务数据画像纳入能力专项必跑审计。
- `formal_business_release_gate`、业务闭环审计、基线审计保持可重复执行。

验收：

- `make verify.baseline DB_NAME=sc_demo`
- 用户确认菜单/字段稳定性审计通过。
- 用户业务数据画像审计无异常退化。

### Phase 1 - Finance Handling Closure

目标：先把最直接影响日常办公的资金财务办理打通。

主链路：

- 付款申请：`payment.request`
- 付款执行：`sc.payment.execution`
- 费用/借还款/保证金/扣款：`sc.expense.claim`
- 收款登记：`sc.receipt.income`
- 结算单：`sc.settlement.order`
- 资金台账：`sc.treasury.ledger`、`payment.ledger`

必须解决：

- 支付申请、报销申请、到款确认、扣款/退回、项目借还款有清晰业务入口。
- 申请到审批、审批到执行、执行到资金台账和成本/结算关系可追溯。
- 附件、明细、金额、账户、往来单位、项目、合同字段可办理。
- 审批驳回、取消、完成等反向/终态动作受状态机保护。

第一轮实现目标：

- 输出财务办理链路 readiness audit。
- 对 `payment.request`、`sc.expense.claim`、`sc.receipt.income`、`sc.settlement.order` 做字段、按钮、状态、附件、下游台账矩阵。
- 选出一个 P0 阻断并修复，优先级为：保存失败、按钮不可执行、附件不可用、状态错位、下游台账缺失。

当前进展：

- 已补账户与往来资金最小闭环：`sc.fund.account.operation` 账户调拨、`sc.financing.loan` 项目借公司款、`sc.financing.loan` 承包人借项目款均可登记、确认、完成，并写入 `sc.audit.log`。
- 已修正资金台账边界：往来款不关联 `payment.request`，但完成后按来源模型和来源记录写入 `sc.treasury.ledger`，避免现金流台账漏记；同项目账户调拨只保留往来事实和项目内调拨口径，不重复计入项目净现金流。
- 已补账户资金办理关系门禁：账户调拨必须有转出/转入账户、不同账户、正金额且账户币种一致；余额调整必须有调整账户且调整前后金额不同；资金日报必须有账户；表单“完成”按钮只在已确认状态显示。
- 已修正借款分类口径：`项目借公司款` 不再因同时包含“项目/借/款”被误分为承包人借项目款；历史借出类按“借...项目...款”顺序语义进入 `project_to_contractor_borrow`。
- 已建立 `scripts/ops/validate_interfund_account_loan_closure.sh`，验证办理动作 -> 审计日志 -> `sc.interfund.movement.fact` -> `sc.interfund.movement.project.summary` -> `sc.finance.project.capital.position`。
- 已建立 `scripts/ops/validate_interfund_treasury_ledger_backfill_readiness.sh`，只读审计历史往来事实进入 `sc.treasury.ledger` 的回填候选、已存在台账和不可自动回填事实。
- 已建立 `make verify.interfund_user_data.full_coverage.audit`，按用户数据事实区分项目借还调拨事实、公司-承包人责任事实和状态/台账输入：账户调拨 395、借款事实 872、还款事实 671 全量进入项目往来事实；到款确认 5205、自筹正式口径 2153/1575 进入公司-承包人责任事实；资金日报 7453、余额调整 519、融资登记 152、账户收支/日报明细不作为往来责任事实。
- 已建立只读投影 `sc.company.contractor.responsibility.fact` 和 `make verify.company_contractor.responsibility_fact.audit`，把到款确认、自筹垫付、自筹退回从普通收付款分析口径中提升为公司-承包人责任事实，并保留项目资金状态影响用于约束后续办理动作。
- 已确认旧入口“承包人借项目款”验收数 227 与当前事实分类 177 的差异不是覆盖缺口，而是旧入口名称和事实分类规则不等价；后续收口前必须将借还款分类规则字典化，并由用户确认新的验收口径。

### Phase 2 - Invoice And Tax Closure

目标：让发票、抵扣、税务事实成为办理链路的一部分，不只是报表来源。

主链路：

- 进项发票登记：`sc.invoice.registration`
- 销项开票申请/登记
- 抵扣登记：`sc.tax.deduction.registration`
- 发票与项目、合同、往来单位、收付款、成本关系归集

验收：

- 发票可登记、可关联项目/合同/往来单位。
- 抵扣登记作为非现金税务事实进入项目经营口径。
- 发票完成后能参与成本、收付款、税务汇总。

当前进展：

- 已建立发票/税务分类 action 门禁，覆盖销项开票申请、销项开票登记、预缴税款、进项税额上报、抵扣登记。
- 已修正用户确认列表的后置覆盖：列表仍以用户确认历史字段优先展示，但补回正式表单、新建编辑和新办理 domain 覆盖。
- 已验证数据库最终 action：从五个入口新建的临时记录保存后仍可被当前入口搜到。
- 已补发票登记和抵扣登记动作审计：确认、登记完成、抵扣完成、取消等动作写入 `sc.audit.log`。
- 已建立发票/税务办理证据门禁，覆盖附件、状态闭环、业务锚点阻断和审计事件。
- 已建立发票/税务角色权限门禁：只读可查不可建，业务经办可发起，普通财务经办不能执行终态登记/抵扣，财务经理可完成终态。
- 已建立发票/税务下游追溯门禁：销项登记和进项上报进入 `sc.invoice.category.summary`，抵扣登记进入 `sc.finance.business.fact`、`sc.finance.business.project.summary` 和 `sc.finance.project.capital.position`。

当前门禁：

```text
DB_NAME=sc_demo scripts/ops/validate_business_category_dictionary.sh
scripts/ops/validate_invoice_tax_business_categories.sh
DB_NAME=sc_demo scripts/ops/validate_invoice_tax_business_category_runtime.sh
DB_NAME=sc_demo scripts/ops/validate_invoice_tax_handling_evidence.sh
DB_NAME=sc_demo scripts/ops/validate_invoice_tax_role_permissions.sh
DB_NAME=sc_demo scripts/ops/validate_invoice_tax_downstream_traceability.sh
```

下一步：

- 将发票/税务分类从 action/context 过渡实现推进到正式分类字段或业务分类字典绑定。
- 明确 `sc.invoice.registration` 与合同、结算、收付款、成本的关系策略；当前发票分类汇总已验证，发票成本进度类报表仍后置到 Phase 6。
- 补正式分类字段或业务分类字典绑定，替代抵扣登记当前对 `is_transfer_out` 的过渡分类依赖。

### Phase 3 - Material Procurement And Stock Closure

目标：保护最大体量材料数据，并打通采购到成本和付款。

主链路：

- 材料计划
- 材料采购申请
- 材料询价/RFQ
- 材料验收
- 入库/出库
- 材料结算
- 成本台账和付款申请

验收：

- 材料目录、历史映射、材料计划和采购办理不互相污染。
- 验收、入库、出库、结算都有状态机和审计。
- 材料结算能进入成本和付款办理。

当前进展：

- 已把材料链路纳入业务分类字典，覆盖材料计划、采购申请、材料进场验收、询比价、入库单、出库单、材料结算 7 个分类。
- 已明确历史事实入口和新办理入口边界：历史材料计划、历史入库等用户已确认来源事实继续用于追溯；新材料计划办理绑定 `action_project_material_plan_my`，新入库办理绑定 `action_sc_material_inbound_handling`。
- 已新增材料业务分类运行时门禁，逐一创建最小业务记录并验证记录能通过对应 action 入口查询到，避免 action domain/context 与保存后的业务数据脱节。
- 已补材料办理动作审计：材料计划提交/批准/完成，采购申请提交/审批，验收提交/通过，询比价提交/定价，入库提交/确认，出库提交/确认，材料结算提交/确认等关键动作写入 `sc.audit.log`。
- 已建立材料办理证据门禁，覆盖附件、状态闭环、错误状态阻断、材料明细、项目/供应商/仓库关系和审计事件。
- 已扩展库存汇总口径：`sc.material.stock.summary` 同时汇总历史材料库存事实和新办理的已入库/已出库明细，库存数量按“入库 - 出库”计算。
- 已建立材料下游追溯门禁，验证新办理入库/出库完成后进入库存汇总。
- 已打通材料结算下游闭环：材料结算确认后按明细未税金额幂等写入 `project.cost.ledger`，并按含税结算金额生成或更新草稿 `payment.request`，付款申请通过 `material_settlement_id` 反链材料结算单。
- 已建立材料跨单追溯门禁，覆盖材料计划 -> 询价/RFQ -> 采购订单 -> 验收 -> 入库，验证后端创建、界面动作、来源反链、采购单价带入和库存汇总金额一致。
- 已补齐材料计划到采购申请分支：已批准材料计划可生成采购申请，来源计划和来源计划明细可追溯，重复生成按来源计划幂等打开原申请；采购申请审批后可继续带入验收。
- 已补齐采购申请审批后的下游策略门禁：审批通过的采购申请可生成询价单，也可在维护拟采购供应商后直接生成采购订单；询价、采购订单、订单行和后续验收都能回溯到采购申请、申请明细、材料计划和计划明细。
- 已补齐材料出库到项目成本台账的办理闭环：出库确认后按明细金额幂等写入 `project.cost.ledger`，并保留来源单据和来源明细追溯。
- 已将材料成本触发策略沉淀到业务分类字典：`material.inbound`、`material.outbound`、`material.settlement` 通过 `ledger_policy_json.cost_triggers` 控制是否生成成本台账或付款申请，并已建立开关门禁。
- 已将退库、调拨、损耗纳入材料业务分类字典：`material.return`、`material.transfer`、`material.loss` 复用 `sc.material.outbound` 正式模型，通过 action/domain/context 和 `outbound_type` 保留办理边界；退库/调拨默认不进项目成本，损耗默认进项目成本，并已建立库存和成本影响门禁。
- 已补齐材料调拨双边库存事实：`material.transfer` 确认后自动生成并确认调入侧 `sc.material.inbound`，通过 `source_transfer_outbound_id` / `transfer_inbound_id` 双向追溯；库存汇总按项目和材料聚合后入出净额为零，调拨仍不进入项目成本。
- 已补齐材料损耗审批策略门禁：`material.loss` 默认可按登记类业务直接确认；启用 `sc.material.outbound` 审批策略后，损耗确认先进入统一审批，审批通过前不写项目成本，审批通过后才确认损耗并生成成本台账。
- 已打通材料结算付款执行闭环：材料结算确认后生成的付款申请可以作为材料付款依据走提交、审批、生成付款登记、登记付款和付款台账；付款台账可反查材料结算，不再强制解释为通用结算单。
- 已补齐材料办理角色门禁：物资只读不能执行办理动作；物资经办可提交但不能确认；物资审批/库管负责人确认验收、入库、出库、结算；采购经办发起询价；采购审批确认报价和生成订单；财务经办/审批承接材料结算付款申请。
- 已修正材料下游 action 返回权限：业务动作打开 RFQ、采购订单、付款申请等窗口时使用安全的 action 元数据读取，避免普通经办用户因 `ir.actions.act_window.view` 读权限被阻断。
- 已补齐材料结算分批付款门禁：已确认材料结算可以按剩余可付金额生成后续付款申请，提交、审批和强制批准时硬阻断累计付款申请金额超过结算含税金额；财务只读材料结算用于付款校验，不获得材料结算办理动作。
- 已补齐材料结算付款撤销门禁：新系统付款执行登记付款后，财务可以撤销付款执行，系统删除对应付款台账、将付款申请从完成退回已批准、恢复材料结算未付款余额，并允许重新登记付款完成闭环。
- 已补齐材料结算付款登记审批策略门禁：付款执行默认可按登记类业务免审批确认付款；启用 `sc.payment.execution` 审批策略后，未审批通过的付款执行不能登记付款，审批通过后才能写付款台账并完成付款申请。
- 已确认材料分类继续走“正式模型 + 字典分类 + action/context/表单分组切分”的过渡路线：菜单可以整合到材料能力域，但材料计划、采购申请、询价、验收、入库、出库、结算等业务类别必须按用户数据和用户认知保留清晰办理边界。
- 已把当前用户材料办理规则视为建筑行业模板样本：直接采购申请、询价采购、采购验收、库存汇总、出库成本、结算付款等默认策略要进入行业模板和分类策略，客户差异通过 `sc.business.category` 维护，不硬编码成单一客户逻辑。

当前门禁：

```text
DB_NAME=sc_demo scripts/ops/validate_business_category_dictionary.sh
DB_NAME=sc_demo scripts/ops/validate_material_business_category_runtime.sh
DB_NAME=sc_demo scripts/ops/validate_material_handling_evidence.sh
DB_NAME=sc_demo scripts/ops/validate_material_downstream_traceability.sh
DB_NAME=sc_demo scripts/ops/validate_material_cross_document_traceability.sh
DB_NAME=sc_demo scripts/ops/validate_material_plan_purchase_request_traceability.sh
DB_NAME=sc_demo scripts/ops/validate_material_purchase_request_downstream_strategy.sh
DB_NAME=sc_demo scripts/ops/validate_material_cost_trigger_policy.sh
DB_NAME=sc_demo scripts/ops/validate_material_settlement_payment_execution_traceability.sh
DB_NAME=sc_demo scripts/ops/validate_material_role_permissions.sh
DB_NAME=sc_demo scripts/ops/validate_material_settlement_split_payment.sh
DB_NAME=sc_demo scripts/ops/validate_material_settlement_payment_reversal.sh
DB_NAME=sc_demo scripts/ops/validate_material_settlement_payment_execution_approval_policy.sh
DB_NAME=sc_demo scripts/ops/validate_material_outbound_derivative_strategy.sh
DB_NAME=sc_demo scripts/ops/validate_material_loss_approval_policy.sh
```

阶段边界：

- 材料域当前已达到“阶段性可交付深度”：计划、采购申请、询比价、验收、入库、出库、退库、调拨、损耗、结算、成本、付款和角色门禁都有可重复后端证据。
- 后续不再把当前迭代继续投入材料域细节深挖；材料事项转入 backlog 和行业模板沉淀，除非出现正式交付阻断。
- 材料域后续只围绕用户认知和扩展性收敛：分类策略字典化、行业模板默认策略、退库/调拨/损耗责任归集、浏览器抽样证据。

后续计划：

- 将“直接采购”“询价采购”“框架采购”等采购分支从按钮能力继续沉淀到业务分类字典或分类策略，支持客户维护默认路径。
- 将材料结算分批付款、付款撤销、付款登记审批等策略继续沉淀到业务分类字典或行业模板默认策略。
- 深化退库、调拨、损耗：补退库来源单据、独立调拨接收确认、跨仓责任策略和损耗责任归集策略。
- 将材料角色权限门禁继续扩展到退库来源确认、调拨接收、损耗责任归集等派生动作。
- 根据用户历史材料目录、采购合同、直接验收和库存事实，继续抽取可复用的建筑行业材料模板默认规则。

### Phase 4 - Contract And Settlement Deepening

目标：让合同真正驱动收款、付款、发票、结算和成本。

范围：

- 收入合同、支出合同办理。
- 合同结算和多来源结算归集。
- 合同、结算、付款/收款、发票、成本的关系一致性。
- 三单匹配、超付策略、合同余额和结算余额控制。

验收：

- 合同维度能解释已结算、已申请、已支付/收款、已开票、成本沉淀。
- 超付、合同不一致、状态不一致被正式动作拦截。

当前转向：

- Phase 4 是材料域阶段性收束后的当前主线。
- 第一条闭环聚焦支出合同 -> 结算单 -> 付款申请 -> 付款台账 -> 合同对账，不新增泛化报表。
- 入口可以继续整合到合同/结算能力域，但收入合同、支出合同、收入结算、支出结算、付款申请、收款申请等业务类别必须按用户数据和业务动作保持清晰边界。
- 结算分类、合同分类和付款/收款分类继续遵循“正式模型 + 业务分类字典 + action/context/表单分组”的路线，后续沉淀行业模板。
- 已将 `contract.income`、`contract.expense`、`settlement.income`、`settlement.expense` 纳入 `sc.business.category`，作为合同域行业模板的第一批默认分类。

当前门禁：

```text
DB_NAME=sc_demo scripts/ops/validate_business_category_dictionary.sh
BUSINESS_CATEGORY_DICTIONARY_AUDIT: status=PASS
category_count=48
contract categories: contract.income, contract.expense, settlement.income, settlement.expense

DB_NAME=sc_demo scripts/ops/validate_contract_settlement_payment_closure.sh
CONTRACT_SETTLEMENT_PAYMENT_CLOSURE_AUDIT: status=PASS
evidence: contract=12581, settlement=3133, payment_request=36713, settlement_total=1200.0, payment_total=450.0, delta=750.0

DB_NAME=sc_demo scripts/ops/validate_income_contract_receipt_invoice_closure.sh
INCOME_CONTRACT_RECEIPT_INVOICE_CLOSURE_AUDIT: status=PASS
evidence: contract=12582, receipt_request=36714, receipt_income=351134, treasury_ledger=293722, invoice=775051, receipt_amount=800.0, invoice_total=872.0, contract_received_amount=800.0, contract_invoice_amount=872.0
```

### Phase 5 - Site Execution Closure

目标：现场进度、质量、安全、任务证据进入项目履约和结算依据。

范围：

- 施工日志
- 进度登记
- 质量问题整改
- 安全问题整改
- 现场证据
- 任务与项目履约、合同结算依据关系

验收：

- 现场数据不是孤立列表，能进入项目、合同、结算和风险追溯。
- 整改闭环包含登记、派发、处理、复查、关闭。

当前进展：

- 已将现场履约 7 个分类纳入 `sc.business.category`：施工日志、质量问题、质量整改、质量复验、安全问题、安全整改、安全复验。
- 已补质量问题和安全问题的 `sc.audit.log` 审计事件，覆盖提交、开始整改、申请复验、整改登记、复验登记、复验失败退回和闭环。
- 已建立质量/安全后端闭环门禁：质量和安全各自完成登记、整改、复验失败回退、再次复验、复验通过闭环、照片证据和闭环后照片删除阻断。

当前门禁：

```text
DB_NAME=sc_demo scripts/ops/validate_site_quality_safety_closure.sh
SITE_QUALITY_SAFETY_CLOSURE_AUDIT: status=PASS
evidence: project=2960, quality issue=31, quality rectification=31, quality failed_recheck=32, quality passed_recheck=33, safety issue=31, safety rectification=31, safety failed_recheck=32, safety passed_recheck=33
```

### Phase 6 - Reports And Analytics

目标：在办理数据可靠后再完善报表。

范围：

- 项目经营统计
- 应收应付
- 发票分析
- 成本综合
- 账户收支
- 资金日报

验收：

- 报表只读取办理链路沉淀事实或正式投影。
- 报表数字可追溯到单据、附件、审批和台账。
- 穿透动作服务用户核对，不替代办理入口。

## Iteration Gate

每轮迭代开始前回答：

- 本轮办理链路是什么？
- 涉及哪些正式模型和历史来源？
- 用户会从哪个入口开始办理？
- 办理完成后应该生成哪些下游事实？
- 哪些历史事实只读，哪些新字段需要必填？

每轮迭代结束必须提供：

- 变更范围。
- 受影响模型、视图、菜单、脚本。
- 通过的验证命令。
- 未解决风险和下一轮入口。

## Immediate Next Work

1. 材料域当前停止继续深挖，转入 backlog、行业模板沉淀和正式交付阻断修复。
2. 当前主线按用户数据体量继续推进 P0 高权重办理域：付款与费用、税务与发票、账户与往来资金、收入与收款、合同与结算。
3. 账户与往来资金已完成账户调拨、项目借公司款、承包人借项目款、项目还公司款、承包人还项目款最小闭环，并明确“往来事实进入现金流台账但不挂经营收付款申请”的边界；下一轮继续补历史往来现金流台账回填策略、资金日报/账户余额关系和账户必填规则，同时把借还款分类从 action/context 继续推进到业务分类字典策略。
4. 合同分类、结算分类、收付款分类、借还款分类和发票分类继续从 action/context 过渡到业务分类字典策略，包括必填、附件、审批、下游台账和余额控制。
5. 现场履约已补质量/安全最小闭环，但不作为当前主线继续深挖；后续仅在资金、发票、合同等 P0 闭环稳定后扩展施工日志、进度和任务证据到结算依据。

## Execution Evidence - 2026-06-11

本轮已按新方向完成三类基线验证：

Phase 1 执行拆解见：`docs/audit/finance_handling_chain_matrix_2026-06-11.md`

```text
DB_NAME=sc_demo scripts/ops/validate_business_flow_closure.sh
BUSINESS_FLOW_CLOSURE_AUDIT: status=PASS
contract_payment: contract=12230, settlement=3029, payment=36303, ledger=12363, recon_summary=29
material_stock_settlement: request=32, rfq=160, acceptance=33, inbound=13720, outbound=34, settlement=32
```

```text
DB_NAME=sc_demo scripts/ops/validate_business_action_coverage.sh
BUSINESS_ACTION_COVERAGE_AUDIT: status=PASS
covered: payment_execution, receipt_income, expense_claim, invoice_registration, tax_deduction, hr_payroll, fund_account_operation
```

```text
DB_NAME=sc_demo python3 scripts/verify/p1_daily_business_form_usability_audit.py
[p1_daily_business_form_usability_audit] PASS
entry_count=36, usable_contract_ready_count=36, needs_usability_attention_count=0
create_allowed_count=36, edit_allowed_count=36, attachment_signal_count=36, chatter_signal_count=36
artifact: docs/ops/audit/p1_daily_business_form_usability_audit.md
```

### Account And Interfund Closure Evidence

已按用户数据优先级补账户与往来资金最小办理闭环：

```text
DB_NAME=sc_demo scripts/ops/validate_interfund_account_loan_closure.sh
INTERFUND_ACCOUNT_LOAN_CLOSURE_AUDIT: status=PASS
coverage=账户调拨、项目借公司款、承包人借项目款、项目还公司款、承包人还项目款
policy=往来款不关联 payment.request，不借用经营收付款申请或结算单兜底
cash_ledger=sc.treasury.ledger source_model/source_res_id 追溯，source_kind=interfund
```

历史往来现金流台账回填只读审计：

```text
DB_NAME=sc_demo scripts/ops/validate_interfund_treasury_ledger_backfill_readiness.sh
INTERFUND_TREASURY_LEDGER_BACKFILL_READINESS_AUDIT: status=PASS
expected_ledger_entry_count=1566
missing_ledger_entry_count=1566
expected_ledger_amount=955,974,145.60
expected_inflow_amount=645,131,015.95
expected_outflow_amount=310,843,129.65
excluded_same_project_transfer=383 / 306,569,035.00
blocked_non_positive_fact_count=1
policy=只读审计，不写历史台账；同项目调拨和未分类调拨不自动回填
```

同时通过：

```text
DB_NAME=sc_demo scripts/ops/validate_business_category_dictionary.sh
BUSINESS_CATEGORY_DICTIONARY_AUDIT: status=PASS
category_count=48

DB_NAME=sc_demo scripts/ops/validate_finance_business_categories.sh
FINANCE_BUSINESS_CATEGORY_ACTION_AUDIT: status=PASS
category_count=21

DB_NAME=sc_demo scripts/ops/validate_finance_business_category_runtime.sh
FINANCE_BUSINESS_CATEGORY_RUNTIME_AUDIT: status=PASS
category_count=21

DB_NAME=sc_demo scripts/ops/validate_core_document_processing_gate.sh
CORE_DOCUMENT_PROCESSING_GATE: status=PASS
expense_claims=经营类费用/保证金保留 payment.request；往来还款无 payment.request
```

资金事实口径：

- 借款来源仍保持 872 条用户事实。
- `company_to_project_borrow` 为 695 条、313,372,157.93。
- `project_to_contractor_borrow` 为 177 条、146,206,625.38。
- `project_to_company_repay` 为 246 条、162,052,925.59，全部为流出方向且不关联收付款申请。
- `contractor_to_project_repay` 为 425 条、329,175,279.34，不关联收付款申请。
- 项目借还调拨汇总和项目资金总览均已通过一致性校验。

### Income Receipt Invoice Closure Evidence

收入与收款域按用户数据优先级补齐“收入合同 -> 收款申请 -> 收款登记 -> 资金台账 -> 销项开票 -> 合同收款/开票累计”最小闭环，并补齐 `sc.receipt.income` 自身动作审计。

```text
DB_NAME=sc_demo scripts/ops/validate_income_contract_receipt_invoice_closure.sh
INCOME_CONTRACT_RECEIPT_INVOICE_CLOSURE_AUDIT: status=PASS
coverage=收入合同、收款申请、收款登记、资金台账、销项开票、合同累计收款/开票
receipt_events=receipt_income_confirmed, receipt_income_received
request_events=payment_submitted, payment_approved, payment_paid
invoice_events=invoice_confirmed, invoice_registered
```

同时通过：

```text
DB_NAME=sc_demo scripts/ops/validate_finance_downstream_traceability.sh
FINANCE_DOWNSTREAM_TRACEABILITY_AUDIT: status=PASS

DB_NAME=sc_demo scripts/ops/validate_core_document_processing_gate.sh
CORE_DOCUMENT_PROCESSING_GATE: status=PASS

DB_NAME=sc_demo scripts/ops/validate_finance_business_category_runtime.sh
FINANCE_BUSINESS_CATEGORY_RUNTIME_AUDIT: status=PASS

DB_NAME=sc_demo scripts/ops/validate_finance_relation_required.sh
FINANCE_RELATION_REQUIRED_AUDIT: status=PASS
covered: payment_execution, receipt_income, expense_claim, fund_account_operation
```

结论：

- 当前没有发现 P1 日常表单的 P0 阻断。
- 后端办理动作已覆盖付款执行、收款、费用、发票、抵扣、账户调拨等核心流转。
- 第一条继续推进链路确定为 Phase 1 财务办理闭环，不再扩展报表功能。

下一轮实施目标：

- 将 `payment.request -> sc.payment.execution -> payment.ledger`、`payment.request(receive) -> sc.receipt.income -> sc.treasury.ledger`、经营类 `sc.expense.claim -> payment.request/payment.ledger`、往来类 `sc.expense.claim -> sc.interfund.movement.fact -> sc.treasury.ledger(source_kind=interfund)` 整理成一张用户办理链路矩阵。
- 对“支付申请、往来单位付款、到款确认表、报销/保证金/扣款、账户调拨”补充入口级业务语言和验收证据。
- 下一轮优先基于公司-承包人责任事实补到款确认、自筹收入/退回、拨付/扣款约束、收款发票核销和合同收款/开票余额硬阻断；若审计继续无 P0 阻断，再补入口清晰度、关系必填规则和下游事实追溯，不做报表扩展。
